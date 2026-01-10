"""Application configuration from environment variables."""

from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment."""

    # Google AI
    gemini_api_key: str = ""

    # GCP Storage
    gcp_project_id: str = ""
    gcp_storage_bucket: str = ""

    # App Config
    frontend_url: str = "http://localhost:3000"
    backend_url: str = "http://localhost:8000"

    # Storage mode: local for dev, gcs for production
    storage_mode: Literal["local", "gcs"] = "local"
    local_storage_path: str = "/data"

    # Logging
    log_level: str = "INFO"

    # App info
    app_version: str = "0.1.0"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
