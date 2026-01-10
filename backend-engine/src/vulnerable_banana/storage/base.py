"""Abstract storage backend interface."""

from abc import ABC, abstractmethod


class StorageBackend(ABC):
    """Abstract storage backend for comics and reports."""

    @abstractmethod
    async def upload(self, path: str, data: bytes, content_type: str) -> str:
        """Upload file and return public URL.

        Args:
            path: Relative path for the file (e.g., "pages/pg_abc123.png")
            data: File content as bytes
            content_type: MIME type (e.g., "image/png")

        Returns:
            Public URL to access the uploaded file
        """
        pass

    @abstractmethod
    async def get_url(self, path: str) -> str:
        """Get public URL for a stored file.

        Args:
            path: Relative path for the file

        Returns:
            Public URL to access the file
        """
        pass
