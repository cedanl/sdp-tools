# MinIO Uploader

A Python tool to upload files to MinIO using credentials from environment variables.

## Features

- 🔐 Configuration via environment variables
- 📁 Upload single files or entire directories
- 🪣 Automatic bucket creation
- 🔍 List and verify uploaded objects
- ⚡ Built with modern Python tooling (uv)
- 🛠️ Download files from MinIO

## Quick Start

### Prerequisites

- [uv](https://docs.astral.sh/uv/) installed
- MinIO server with valid credentials

### Installation

```bash
# Clone/download the project
git clone <your-repo> minio-uploader
cd minio-uploader

# Install with uv
uv sync

# Or install in development mode
uv sync --dev
```

### Configuration

Set the required environment variables:

```bash
export MINIO_ACCESS_KEY="your-access-key"
export MINIO_SECRET_KEY="your-secret-key"
export MINIO_ENDPOINT="https://minio.example.com"
export MINIO_BUCKET="your-bucket-name"  # Optional, defaults to "instroom-ml"
```

Or create a `.env` file:

```bash
# .env file
MINIO_ACCESS_KEY=your-access-key
MINIO_SECRET_KEY=your-secret-key
MINIO_ENDPOINT=https://minio.example.com
MINIO_BUCKET=your-bucket-name
```

### Usage

```bash
# Upload a single file
uv run minio-upload /path/to/file.txt

# Upload a directory
uv run minio-upload /path/to/directory

# Run with test data (creates and uploads test files)
uv run minio-upload

# Or run the module directly
uv run python -m minio_uploader /path/to/file.txt

# Get help
uv run minio-upload --help
```

## Environment Variables

| Variable | Required | Description | Default |
|----------|----------|-------------|---------|
| `MINIO_ACCESS_KEY` | ✅ | MinIO access key | - |
| `MINIO_SECRET_KEY` | ✅ | MinIO secret key | - |
| `MINIO_ENDPOINT` | ✅ | MinIO endpoint URL (e.g., `https://minio.example.com`) | - |
| `MINIO_BUCKET` | ❌ | Target bucket name | `instroom-ml` |

## Examples

### Basic file upload
```bash
export MINIO_ACCESS_KEY="minioadmin"
export MINIO_SECRET_KEY="minioadmin"
export MINIO_ENDPOINT="http://localhost:9000"

uv run minio-upload /path/to/document.pdf
```

### Using as a Python module
```python
from minio_uploader import MinIOUploader

uploader = MinIOUploader(bucket_name="my-bucket")
uploader.get_credentials_from_environment()
uploader.setup_minio_client()
uploader.upload_file("/path/to/file.txt")
```

## Development

```bash
# Install development dependencies
uv sync --dev

# Run tests
uv run pytest

# Format code
uv run black .

# Lint code
uv run ruff check .

# Type check
uv run mypy .
```

## Project Structure

```
minio-uploader/
├── pyproject.toml          # Project configuration
├── README.md              # This file
├── minio_uploader.py      # Main module
├── .env.example           # Example environment file
└── tests/                 # Test files (optional)
```

## Troubleshooting

### Missing environment variables
```
Missing required environment variables: MINIO_ACCESS_KEY, MINIO_SECRET_KEY
```
Solution: Set all required environment variables as shown in the configuration section.

### Connection refused
```
Failed to connect to MinIO: MaxRetryError(...)
```
Solution: Check if the `MINIO_ENDPOINT` is correct and accessible.

### SSL certificate verification failed
```
Failed to connect to MinIO: SSLError(...)
```
Solution: If using self-signed certificates, the script automatically disables SSL warnings. For production, use valid SSL certificates.

### Access denied
```
Failed to upload: AccessDenied
```
Solution: Verify that your `MINIO_ACCESS_KEY` and `MINIO_SECRET_KEY` have the necessary permissions for the bucket.

## Features

- ✅ Upload single files
- ✅ Upload entire directories (recursive)
- ✅ Download files
- ✅ List bucket contents
- ✅ Automatic bucket creation
- ✅ Environment variable configuration
- ✅ Error handling and validation
- ✅ Type hints
- ✅ Modern Python packaging
