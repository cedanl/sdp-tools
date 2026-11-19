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
