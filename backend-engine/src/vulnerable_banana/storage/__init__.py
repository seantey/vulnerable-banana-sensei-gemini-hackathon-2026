"""Storage backends for comics and reports."""

from typing import TYPE_CHECKING

from vulnerable_banana.storage.base import StorageBackend
from vulnerable_banana.storage.gcs import GCSStorage
from vulnerable_banana.storage.local import LocalStorage

if TYPE_CHECKING:
    from vulnerable_banana.config import Settings


def get_storage_backend(settings: "Settings") -> StorageBackend:
    """Get the appropriate storage backend based on settings.

    Args:
        settings: Application settings

    Returns:
        StorageBackend instance (LocalStorage or GCSStorage)
    """
    if settings.storage_mode == "local":
        return LocalStorage(
            base_path=settings.local_storage_path,
            base_url=f"{settings.backend_url}/files",
        )
    else:
        return GCSStorage(bucket_name=settings.gcp_storage_bucket)


__all__ = ["StorageBackend", "LocalStorage", "GCSStorage", "get_storage_backend"]
