"""Test package building and distribution."""

import os
import shutil
import subprocess
from pathlib import Path

import pytest

# Skip tests that require uv if not available
uv_available = shutil.which("uv") is not None


class TestPackageBuilding:
    """Test package can be built correctly."""

    @pytest.mark.skipif(not uv_available, reason="uv not available")
    def test_package_can_be_built(self):
        """Test package builds without errors."""
        # Change to project root
        project_root = Path(__file__).parent.parent
        original_cwd = os.getcwd()

        try:
            os.chdir(project_root)

            # Clean previous builds
            dist_dir = project_root / "dist"
            if dist_dir.exists():
                shutil.rmtree(dist_dir)

            # Build package
            result = subprocess.run(['uv', 'build'], capture_output=True, text=True)

            assert result.returncode == 0, f"Build failed: {result.stderr}"

            # Check build outputs exist
            assert dist_dir.exists(), "dist directory not created"

            dist_files = list(dist_dir.glob("*"))
            assert len(dist_files) > 0, "No files in dist directory"

            # Should have both wheel and tarball
            wheel_files = list(dist_dir.glob("*.whl"))
            tar_files = list(dist_dir.glob("*.tar.gz"))

            assert len(wheel_files) > 0, "No wheel file created"
            assert len(tar_files) > 0, "No source tarball created"

        finally:
            os.chdir(original_cwd)

    def test_built_package_structure(self):
        """Test built package has correct structure."""
        project_root = Path(__file__).parent.parent
        dist_dir = project_root / "dist"

        if not dist_dir.exists():
            pytest.skip("No dist directory found - run build test first")

        wheel_files = list(dist_dir.glob("*.whl"))
        if not wheel_files:
            pytest.skip("No wheel file found - run build test first")

        # We could unzip and check contents here if needed
        wheel_file = wheel_files[0]
        assert wheel_file.name.startswith("minio_file-"), "Wheel file has wrong name"
        assert "2025.1.6" in wheel_file.name, "Version not in wheel name"


class TestInstallationFromBuilds:
    """Test package can be installed from built artifacts."""

    @pytest.mark.slow
    def test_install_from_wheel(self):
        """Test package can be installed from wheel."""
        import tempfile

        project_root = Path(__file__).parent.parent
        dist_dir = project_root / "dist"

        if not dist_dir.exists():
            pytest.skip("No dist directory found")

        wheel_files = list(dist_dir.glob("*.whl"))
        if not wheel_files:
            pytest.skip("No wheel file found")

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
    def test_install_from_source(self):
        """Test package can be installed from source distribution."""
        import tempfile

        project_root = Path(__file__).parent.parent
        dist_dir = project_root / "dist"

        if not dist_dir.exists():
            pytest.skip("No dist directory found")

        tar_files = list(dist_dir.glob("*.tar.gz"))
        if not tar_files:
            pytest.skip("No source tarball found")

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

    def test_version_consistency(self):
        """Test version is consistent across package and builds."""
        import minio_file

        package_version = minio_file.__version__

        project_root = Path(__file__).parent.parent
        dist_dir = project_root / "dist"

        if dist_dir.exists():
            # Check wheel filename contains version
            wheel_files = list(dist_dir.glob("*.whl"))
            if wheel_files:
                wheel_name = wheel_files[0].name
                assert package_version in wheel_name, f"Version {package_version} not in wheel name {wheel_name}"

            # Check source tarball filename contains version
            tar_files = list(dist_dir.glob("*.tar.gz"))
            if tar_files:
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
