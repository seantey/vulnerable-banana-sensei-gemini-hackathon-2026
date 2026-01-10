"""Google Cloud Storage backend for production."""

from google.cloud import storage

from vulnerable_banana.storage.base import StorageBackend


class GCSStorage(StorageBackend):
    """Google Cloud Storage - public URLs via GCS.

    Used for production. Files are stored in a GCS bucket with
    public read access for sharing.
    """

    def __init__(self, bucket_name: str) -> None:
        """Initialize GCS storage.

        Args:
            bucket_name: Name of the GCS bucket
        """
        self.client = storage.Client()
        self.bucket = self.client.bucket(bucket_name)

    async def upload(self, path: str, data: bytes, content_type: str) -> str:
        """Upload file to GCS.

        Args:
            path: Relative path for the file
            data: File content as bytes
            content_type: MIME type for the file

        Returns:
            Public URL to access the file
        """
        blob = self.bucket.blob(path)
        blob.upload_from_string(data, content_type=content_type)
        return blob.public_url

    async def get_url(self, path: str) -> str:
        """Get public URL for a stored file.

        Args:
            path: Relative path for the file

        Returns:
            Public URL to access the file
        """
        return self.bucket.blob(path).public_url
