"""Test the new functional MinIO API."""

import os
from unittest.mock import MagicMock, patch

import pytest

from minio_file import MinioConnection, create_connection, download_file, get_buckets, list_files, upload_file


class TestCreateConnection:
    """Test create_connection function."""

    def test_create_connection_with_account(self):
        """Test creating connection with account name."""
        with patch.dict(
            os.environ,
            {
                "MINIO_HO_ENDPOINT": "https://minio.example.com",
                "MINIO_HO_ACCESS_KEY": "test-key",
                "MINIO_HO_SECRET_KEY": "test-secret",
                "MINIO_HO_BUCKET": "test-bucket",
            },
        ):
            conn = create_connection(account="HO")
            assert isinstance(conn, MinioConnection)
            assert conn.bucket_name == "test-bucket"

    def test_create_connection_with_explicit_credentials(self):
        """Test creating connection with explicit credentials."""
        conn = create_connection(
            endpoint="https://minio.example.com",
            access_key="test-key",
            secret_key="test-secret",
            bucket="my-bucket",
        )
        assert isinstance(conn, MinioConnection)
        assert conn.bucket_name == "my-bucket"

    def test_create_connection_invalid_account(self):
        """Test creating connection with invalid account raises error."""
        with pytest.raises(ValueError, match="Invalid account"):
            create_connection(account="INVALID")

    def test_create_connection_missing_env_vars(self):
        """Test creating connection with missing env vars raises error."""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError, match="Missing required environment variables"):
                create_connection(account="HO")

    def test_create_connection_missing_explicit_credentials(self):
        """Test creating connection with incomplete explicit credentials raises error."""
        with pytest.raises(ValueError, match="you must provide"):
            create_connection(endpoint="https://minio.example.com", access_key="key")


class TestFunctionalOperations:
    """Test functional API operations."""

    @pytest.fixture
    def mock_connection(self):
        """Create a mock connection for testing."""
        mock_client = MagicMock()
        conn = MinioConnection(client=mock_client, bucket_name="test-bucket")
        return conn

    def test_upload_file(self, mock_connection):
        """Test upload_file function."""
        upload_file(mock_connection, "local.txt", "remote.txt")
        mock_connection.client.fput_object.assert_called_once_with(
            bucket_name="test-bucket", file_path="local.txt", object_name="remote.txt"
        )

    def test_upload_file_custom_bucket(self, mock_connection):
        """Test upload_file with custom bucket."""
        upload_file(mock_connection, "local.txt", "remote.txt", bucket="other-bucket")
        mock_connection.client.fput_object.assert_called_once_with(
            bucket_name="other-bucket", file_path="local.txt", object_name="remote.txt"
        )

    def test_download_file(self, mock_connection):
        """Test download_file function."""
        download_file(mock_connection, "remote.txt", "local.txt")
        mock_connection.client.fget_object.assert_called_once_with(
            bucket_name="test-bucket", object_name="remote.txt", file_path="local.txt"
        )

    def test_download_file_custom_bucket(self, mock_connection):
        """Test download_file with custom bucket."""
        download_file(mock_connection, "remote.txt", "local.txt", bucket="other-bucket")
        mock_connection.client.fget_object.assert_called_once_with(
            bucket_name="other-bucket", object_name="remote.txt", file_path="local.txt"
        )

    def test_list_files(self, mock_connection):
        """Test list_files function."""
        # Mock the list_objects return value
        mock_obj1 = MagicMock()
        mock_obj1.object_name = "file1.txt"
        mock_obj1.size = 100
        mock_obj1.last_modified = "2025-01-01"
        mock_obj1.etag = "abc123"

        mock_obj2 = MagicMock()
        mock_obj2.object_name = "file2.txt"
        mock_obj2.size = 200
        mock_obj2.last_modified = "2025-01-02"
        mock_obj2.etag = "def456"

        mock_connection.client.list_objects.return_value = [mock_obj1, mock_obj2]

        files = list_files(mock_connection)

        assert len(files) == 2
        assert files[0]["object_name"] == "file1.txt"
        assert files[0]["size"] == 100
        assert files[1]["object_name"] == "file2.txt"
        assert files[1]["size"] == 200

    def test_list_files_with_prefix(self, mock_connection):
        """Test list_files with prefix filter."""
        mock_connection.client.list_objects.return_value = []

        list_files(mock_connection, prefix="uploads/")

        mock_connection.client.list_objects.assert_called_once_with(
            "test-bucket", prefix="uploads/", recursive=True
        )

    def test_get_buckets(self, mock_connection):
        """Test get_buckets function."""
        mock_bucket1 = MagicMock()
        mock_bucket1.name = "bucket1"
        mock_bucket2 = MagicMock()
        mock_bucket2.name = "bucket2"

        mock_connection.client.list_buckets.return_value = [mock_bucket1, mock_bucket2]

        buckets = get_buckets(mock_connection)

        assert buckets == ["bucket1", "bucket2"]


class TestBackwardCompatibility:
    """Test that old class-based API still works."""

    def test_legacy_class_still_works(self):
        """Test that minio_file class is still importable and works."""
        from minio_file import minio_file

        with patch.dict(
            os.environ,
            {
                "MINIO_HO_ENDPOINT": "https://minio.example.com",
                "MINIO_HO_ACCESS_KEY": "test-key",
                "MINIO_HO_SECRET_KEY": "test-secret",
                "MINIO_HO_BUCKET": "test-bucket",
            },
        ):
            ho = minio_file("HO")
            assert ho._conn.bucket_name == "test-bucket"


class TestConnectionHandler:
    """Test MinioConnection class."""

    def test_connection_has_required_attributes(self):
        """Test MinioConnection has client and bucket_name."""
        mock_client = MagicMock()
        conn = MinioConnection(client=mock_client, bucket_name="test")

        assert conn.client == mock_client
        assert conn.bucket_name == "test"
