"""Test package building and distribution."""

import os
import shutil
import subprocess
from pathlib import Path

import pytest

# Skip tests that require uv if not available
uv_available = shutil.which("uv") is not None


PROJECT_ROOT = Path(__file__).parent.parent


@pytest.fixture(scope="module")
def built_dist(tmp_path_factory):
    """Build the package once into a temporary directory and return that directory.

    Building outside the repository keeps the project's own ``dist/`` untouched, so later
    publishing steps never pick up artifacts left behind by the test suite.
    """
    if not uv_available:
        pytest.skip("uv not available")

    out_dir = tmp_path_factory.mktemp("dist")
    result = subprocess.run(
        ["uv", "build", "--out-dir", str(out_dir)], cwd=PROJECT_ROOT, capture_output=True, text=True
    )
    assert result.returncode == 0, f"Build failed: {result.stderr}"
    return out_dir


class TestPackageBuilding:
    """Test package can be built correctly."""

    def test_package_can_be_built(self, built_dist):
        """Test package builds without errors."""
        dist_files = list(built_dist.glob("*"))
        assert len(dist_files) > 0, "No files in dist directory"

        # Should have both wheel and tarball
        wheel_files = list(built_dist.glob("*.whl"))
        tar_files = list(built_dist.glob("*.tar.gz"))

        assert len(wheel_files) > 0, "No wheel file created"
        assert len(tar_files) > 0, "No source tarball created"

    def test_built_package_structure(self, built_dist):
        """Test built package has correct structure."""
        # Read expected version from pyproject.toml
        import sys

        if sys.version_info >= (3, 11):
            import tomllib
        else:
            import tomli as tomllib

        pyproject_path = PROJECT_ROOT / "pyproject.toml"

        with open(pyproject_path, "rb") as f:
            pyproject = tomllib.load(f)
        expected_version = pyproject["project"]["version"]

        wheel_files = list(built_dist.glob("*.whl"))
        assert wheel_files, "No wheel file built"

        # We could unzip and check contents here if needed
        wheel_file = wheel_files[0]
        assert wheel_file.name.startswith("sdp_tools-"), "Wheel file has wrong name"
        assert expected_version in wheel_file.name, f"Version {expected_version} not in wheel name"


class TestInstallationFromBuilds:
    """Test package can be installed from built artifacts."""

    @pytest.mark.slow
    def test_install_from_wheel(self, built_dist):
        """Test package can be installed from wheel."""
        import tempfile

        wheel_files = list(built_dist.glob("*.whl"))
        assert wheel_files, "No wheel file built"

        wheel_file = wheel_files[0]

        # Create temporary environment
        with tempfile.TemporaryDirectory() as temp_dir:
            venv_dir = Path(temp_dir) / "test_venv"

            # Create virtual environment
            subprocess.run(['python', '-m', 'venv', str(venv_dir)], check=True)

            # Determine pip path
            if os.name == 'nt':  # Windows
                pip_path = venv_dir / "Scripts" / "pip"
                python_path = venv_dir / "Scripts" / "python"
            else:  # Unix-like
                pip_path = venv_dir / "bin" / "pip"
                python_path = venv_dir / "bin" / "python"

            # Install package
            result = subprocess.run([str(pip_path), 'install', str(wheel_file)], capture_output=True, text=True)
            assert result.returncode == 0, f"Install failed: {result.stderr}"

            # Test import
            result = subprocess.run(
                [str(python_path), '-c', 'import minio_file; print("OK")'], capture_output=True, text=True
            )
            assert result.returncode == 0, f"Import failed: {result.stderr}"
            assert "OK" in result.stdout

    @pytest.mark.slow
    def test_install_from_source(self, built_dist):
        """Test package can be installed from source distribution."""
        import tempfile

        tar_files = list(built_dist.glob("*.tar.gz"))
        assert tar_files, "No source tarball built"

        tar_file = tar_files[0]

        # Create temporary environment
        with tempfile.TemporaryDirectory() as temp_dir:
            venv_dir = Path(temp_dir) / "test_venv"

            # Create virtual environment
            subprocess.run(['python', '-m', 'venv', str(venv_dir)], check=True)

            # Determine paths
            if os.name == 'nt':  # Windows
                pip_path = venv_dir / "Scripts" / "pip"
                python_path = venv_dir / "Scripts" / "python"
            else:  # Unix-like
                pip_path = venv_dir / "bin" / "pip"
                python_path = venv_dir / "bin" / "python"

            # Install package
            result = subprocess.run([str(pip_path), 'install', str(tar_file)], capture_output=True, text=True)
            assert result.returncode == 0, f"Install failed: {result.stderr}"

            # Test import
            result = subprocess.run(
                [str(python_path), '-c', 'import minio_file; print("OK")'], capture_output=True, text=True
            )
            assert result.returncode == 0, f"Import failed: {result.stderr}"
            assert "OK" in result.stdout


class TestPackageMetadataInBuilds:
    """Test package metadata is correct in built packages."""

    def test_version_consistency(self, built_dist):
        """Test version is consistent across package and builds."""
        import minio_file

        package_version = minio_file.__version__

        # Check wheel filename contains version
        wheel_files = list(built_dist.glob("*.whl"))
        assert wheel_files, "No wheel file built"
        wheel_name = wheel_files[0].name
        assert package_version in wheel_name, f"Version {package_version} not in wheel name {wheel_name}"

        # Check source tarball filename contains version
        tar_files = list(built_dist.glob("*.tar.gz"))
        assert tar_files, "No source tarball built"
        tar_name = tar_files[0].name
        assert package_version in tar_name, f"Version {package_version} not in tarball name {tar_name}"


class TestDevelopmentInstallation:
    """Test development installation works correctly."""

    def test_editable_install_reflects_changes(self):
        """Test editable install reflects code changes."""
        import os

        import minio_file

        package_path = minio_file.__file__
        normalized_path = os.path.normpath(package_path)

        # Check if we're in development mode (src directory structure)
        # Use os.sep to handle both Windows and Unix path separators
        is_dev_mode = os.sep + 'src' + os.sep in normalized_path

        # In CI environments, the package might be installed differently
        if not is_dev_mode:
            if 'CI' in os.environ or 'GITHUB_ACTIONS' in os.environ:
                pytest.skip("Package not in development mode (acceptable in CI)")
            elif 'site-packages' in normalized_path:
                pytest.skip("Package installed in site-packages rather than development mode")

        assert is_dev_mode, f"Package should be in development mode, found at: {normalized_path}"

    def test_package_reloads_correctly(self):
        """Test package can be reloaded."""
        import importlib

        import minio_file

        # Get original version
        original_version = minio_file.__version__

        # Reload package
        importlib.reload(minio_file)

        # Should still work
        assert minio_file.__version__ == original_version
