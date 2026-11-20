"""Tests for the sdp-tools console script entry point."""

import importlib
import os
import sys
from pathlib import Path

import pytest

if sys.version_info >= (3, 11):
    import tomllib
else:
    import tomli as tomllib

PYPROJECT = Path(__file__).parent.parent / "pyproject.toml"


def _entry_point_target():
    """Return the 'module:attr' target of the sdp-tools script in pyproject.toml."""
    with open(PYPROJECT, "rb") as f:
        pyproject = tomllib.load(f)
    return pyproject["project"]["scripts"]["sdp-tools"]


class TestEntryPoint:
    """Test the sdp-tools console script."""

    def test_entry_point_target_is_callable_main(self):
        """The configured entry point resolves to a callable main."""
        module_name, _, attr = _entry_point_target().partition(":")
        assert attr == "main"
        module = importlib.import_module(module_name)
        assert callable(getattr(module, attr))

    def test_installed_entry_point_matches_pyproject(self):
        """The installed console script (if any) points at the same target."""
        from importlib.metadata import entry_points

        eps = entry_points()
        if hasattr(eps, "select"):
            scripts = eps.select(group="console_scripts", name="sdp-tools")
        else:  # Python 3.9
            scripts = [ep for ep in eps.get("console_scripts", []) if ep.name == "sdp-tools"]
        scripts = list(scripts)
        if not scripts:
            pytest.skip("sdp-tools is not installed in this environment")
        assert scripts[0].value == _entry_point_target()
        assert callable(scripts[0].load())

    @pytest.mark.parametrize("flag", ["-h", "--help"])
    def test_help_exits_zero_without_minio(self, flag, monkeypatch, capsys):
        """--help prints usage and returns 0 without creating a MinIO client."""
        module = importlib.import_module("minio_file.minio_file")

        for key in list(os.environ):
            if key.startswith("MINIO_"):
                monkeypatch.delenv(key)

        def fail(*args, **kwargs):
            raise AssertionError("MinIO client must not be created for --help")

        monkeypatch.setattr(module, "minio_file", fail)
        monkeypatch.setattr(module, "Minio", fail)

        assert module.main([flag]) == 0
        assert "usage: sdp-tools" in capsys.readouterr().out

    def test_help_via_sys_argv(self, monkeypatch, capsys):
        """main() reads sys.argv when no arguments are passed."""
        module = importlib.import_module("minio_file.minio_file")

        monkeypatch.setattr(module, "argv", ["sdp-tools", "--help"])
        monkeypatch.setattr(module, "minio_file", lambda *a, **k: pytest.fail("client created"))

        assert module.main() == 0
        assert "usage: sdp-tools" in capsys.readouterr().out


class TestDownload:
    """Test the two-argument download form of sdp-tools."""

    @pytest.fixture
    def module(self, monkeypatch, tmp_path):
        """Return the CLI module with dummy HO credentials and tmp_path as cwd."""
        monkeypatch.setenv("MINIO_HO_ENDPOINT", "https://minio.invalid")
        monkeypatch.setenv("MINIO_HO_ACCESS_KEY", "dummy-access")
        monkeypatch.setenv("MINIO_HO_SECRET_KEY", "dummy-secret")
        monkeypatch.setenv("MINIO_HO_BUCKET", "dummy-bucket")
        monkeypatch.chdir(tmp_path)
        return importlib.import_module("minio_file.minio_file")

    @pytest.fixture
    def fget(self, monkeypatch):
        """Mock Minio.fget_object and record its calls."""
        calls = []

        def fake_fget_object(self, *args, **kwargs):
            calls.append(kwargs)

        monkeypatch.setattr("minio.Minio.fget_object", fake_fget_object)
        return calls

    def test_downloads_file_to_target(self, module, fget):
        """FILE is the object name in the bucket, TARGET the local destination."""
        assert module.main(["remote/data.csv", "local/copy.csv"]) == 0

        assert len(fget) == 1
        assert fget[0]["bucket_name"] == "dummy-bucket"
        assert fget[0]["object_name"] == "remote/data.csv"
        assert fget[0]["file_path"] == str(Path("local/copy.csv"))

    def test_skips_existing_target(self, module, fget, tmp_path, capsys):
        """An existing TARGET is not overwritten and is named in the output."""
        (tmp_path / "copy.csv").write_text("existing")

        assert module.main(["remote/data.csv", "copy.csv"]) == 0

        assert fget == []
        assert "copy.csv" in capsys.readouterr().out
        assert (tmp_path / "copy.csv").read_text() == "existing"

    def test_local_file_named_like_object_does_not_block_download(self, module, fget, tmp_path):
        """A local file named FILE no longer suppresses the download to TARGET."""
        (tmp_path / "data.csv").write_text("unrelated")

        assert module.main(["data.csv", "copy.csv"]) == 0

        assert len(fget) == 1
        assert fget[0]["object_name"] == "data.csv"
        assert fget[0]["file_path"] == "copy.csv"

    def test_help_describes_file_and_target(self, capsys):
        """The usage text explains FILE and TARGET."""
        module = importlib.import_module("minio_file.minio_file")

        assert module.main(["-h"]) == 0
        out = capsys.readouterr().out
        assert "FILE        object name in the HO bucket" in out
        assert "TARGET      local path to save it to" in out
