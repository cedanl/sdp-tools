#!/usr/bin/env python3
"""MinIO Upload Script using Environment Variables
Uploads files to MinIO using credentials from environment variables.
"""

from os import getenv
from pathlib import Path
from sys import argv

import urllib3
from minio import Minio as m

# Disable SSL warnings if using self-signed certificates
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class minio_file:
    """the main class"""

    def _get_credentials(self):
        return {
            "bucket_name": getenv(f"MINIO_{self.account}_BUCKET"),
            "access_key": getenv(f"MINIO_{self.account}_ACCESS_KEY"),
            "secret_key": getenv(f"MINIO_{self.account}_SECRET_KEY"),
            "endpoint": getenv(f"MINIO_{self.account}_ENDPOINT"),
        }

    def _get_client(self):
        cred = self._get_credentials()
        self.bucket_name = cred["bucket_name"]
        endpoint_url = cred["endpoint"].replace("http://", "").replace("https://", "")
        secure = cred["endpoint"].startswith("https://")

        self.client = m(
            endpoint_url,
            access_key=cred["access_key"],
            secret_key=cred["secret_key"],
            secure=secure,
        )

    def __init__(self, account):
        """Depending on the account, the env variables that are used change"""
        if account not in ["WO", "HO", "ML", "VIZ"]:
            raise (f"Incorrect account {account}")
        self.account = account
        self._get_client()

    def get_buckets(self):
        """Retrieve all the buckets available"""
        return list(self.client.list_buckets())

    def upload_file(self, file_name, full_name):
        """Upload a file"""
        self.client.fput_object(bucket_name=self.bucket_name, file_path=file_name, object_name=full_name)

    def get_file_list(self):
        """Retrieve all files in the bucket"""
        objects = self.client.list_objects(self.bucket_name, recursive=True)
        for obj in objects:
            print(f"{obj.object_name} ({obj.size} bytes)")

    def download_file(self, file_name, full_name):
        """Download a file"""
        self.client.fget_object(file_path=file_name, object_name=full_name, bucket_name=self.bucket_name)


def main():
    """Main function (for CLI)"""
    ho = minio_file("HO")
    # Handle commanod line arguments
    if len(argv) == 3:
        ho_file = argv[1]
        ho_obj = Path(ho_file)
        # ml_file = argv[2]
        # ml_obj = Path(ml_file)

        if ho_obj.is_file():
            print(f"Skipping existing file: {ho_obj}")
        else:
            ho.download_file(ho_file, str(ho_obj))
    else:
        # List uploaded objects
        print("\nListing objects in bucket:")
        ho.get_file_list()


if __name__ == "__main__":
    main()
