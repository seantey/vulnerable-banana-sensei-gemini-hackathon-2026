"""FastAPI dependencies for dependency injection."""

from fastapi import Request

from vulnerable_banana.storage.base import StorageBackend


def get_storage(request: Request) -> StorageBackend:
    """Get storage backend from app state.

    Args:
        request: FastAPI request object

    Returns:
        Storage backend instance
    """
    return request.app.state.storage
