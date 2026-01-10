"""Local filesystem storage backend for development."""

from pathlib import Path

from vulnerable_banana.storage.base import StorageBackend


class LocalStorage(StorageBackend):
    """Local filesystem storage - serves files via backend API.

    Used for local development. Files are stored in a local directory
    and served via the backend's static file mount.
    """

    def __init__(self, base_path: str, base_url: str) -> None:
        """Initialize local storage.

        Args:
            base_path: Local directory to store files (e.g., "/data")
            base_url: URL prefix for serving files (e.g., "http://localhost:8000/files")
        """
        self.base_path = Path(base_path)
        self.base_url = base_url.rstrip("/")

    async def upload(self, path: str, data: bytes, content_type: str) -> str:
        """Upload file to local filesystem.

        Args:
            path: Relative path for the file
            data: File content as bytes
            content_type: MIME type (unused for local storage)

        Returns:
            URL to access the file via backend static files
        """
        file_path = self.base_path / path
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_bytes(data)
        return f"{self.base_url}/{path}"

    async def get_url(self, path: str) -> str:
        """Get URL for a stored file.

        Args:
            path: Relative path for the file

        Returns:
            URL to access the file via backend static files
        """
        return f"{self.base_url}/{path}"
