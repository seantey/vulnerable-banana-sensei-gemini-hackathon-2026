"""Base model with automatic snake_case to camelCase conversion."""

from pydantic import BaseModel, ConfigDict
from humps import camelize


class ApiModel(BaseModel):
    """Base model for all API responses with automatic camelCase conversion.

    - Python code uses snake_case field names
    - JSON serialization automatically converts to camelCase
    - Enum/status values pass through unchanged (SCREAMING_SNAKE_CASE)
    """

    model_config = ConfigDict(
        alias_generator=camelize,
        populate_by_name=True,
        serialize_by_alias=True,
    )
