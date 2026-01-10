"""FastAPI application entry point."""

from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncGenerator

import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from vulnerable_banana.api.routes import router
from vulnerable_banana.config import get_settings
from vulnerable_banana.errors import ApiError, api_error_handler
from vulnerable_banana.logging import setup_logging
from vulnerable_banana.storage.base import StorageBackend
from vulnerable_banana.storage.gcs import GCSStorage
from vulnerable_banana.storage.local import LocalStorage

logger = structlog.get_logger()


def get_storage_backend(settings: "Settings") -> StorageBackend:  # type: ignore[name-defined]
    """Create storage backend based on settings.

    Args:
        settings: Application settings

    Returns:
        Appropriate storage backend (local or GCS)
    """
    if settings.storage_mode == "local":
        return LocalStorage(
            base_path=settings.local_storage_path,
            base_url=f"{settings.backend_url}/files",
        )
    else:
        return GCSStorage(bucket_name=settings.gcp_storage_bucket)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan manager for startup/shutdown.

    Initializes shared state on startup and cleans up on shutdown.
    """
    settings = get_settings()

    # Setup logging
    setup_logging(settings.log_level)

    # Initialize storage backend
    app.state.storage = get_storage_backend(settings)
    logger.info("storage_initialized", mode=settings.storage_mode)

    # Mount static files for local storage mode
    if settings.storage_mode == "local":
        storage_path = Path(settings.local_storage_path)
        storage_path.mkdir(parents=True, exist_ok=True)
        app.mount("/files", StaticFiles(directory=str(storage_path)), name="files")
        logger.info("static_files_mounted", path=settings.local_storage_path)

    logger.info("app_started", version=settings.app_version)

    yield

    logger.info("app_shutdown")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application.

    Returns:
        Configured FastAPI app instance
    """
    settings = get_settings()

    app = FastAPI(
        title="Vulnerable Banana API",
        description="Security comics generator - transforms dependency vulnerabilities into educational comics",
        version=settings.app_version,
        lifespan=lifespan,
    )

    # CORS configuration
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:3000",
            settings.frontend_url,
        ],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Error handlers
    app.add_exception_handler(ApiError, api_error_handler)

    # Include API routes
    app.include_router(router)

    return app


# Create app instance for uvicorn
app = create_app()
