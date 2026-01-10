"""Custom API error handling."""

from fastapi import Request
from fastapi.responses import JSONResponse


class ApiError(Exception):
    """Base API error with structured response format."""

    def __init__(self, code: str, message: str, status_code: int = 400) -> None:
        """Initialize API error.

        Args:
            code: Machine-readable error code (e.g., "INVALID_FILE_TYPE")
            message: Human-readable error description
            status_code: HTTP status code
        """
        self.code = code
        self.message = message
        self.status_code = status_code
        super().__init__(message)


async def api_error_handler(request: Request, exc: ApiError) -> JSONResponse:
    """Handle ApiError exceptions with consistent JSON response.

    Args:
        request: FastAPI request
        exc: The raised ApiError

    Returns:
        JSONResponse with error code and message
    """
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.code, "message": exc.message},
    )


class InvalidFileTypeError(ApiError):
    """Raised when uploaded file type is not supported."""

    def __init__(self, message: str = "Only package.json, requirements.txt, and pyproject.toml are supported") -> None:
        super().__init__("INVALID_FILE_TYPE", message, 400)


class FileTooLargeError(ApiError):
    """Raised when uploaded file exceeds size limit."""

    def __init__(self, message: str = "File exceeds maximum size of 1MB") -> None:
        super().__init__("FILE_TOO_LARGE", message, 400)


class ParseError(ApiError):
    """Raised when dependency file cannot be parsed."""

    def __init__(self, message: str) -> None:
        super().__init__("PARSE_ERROR", message, 400)


class NotFoundError(ApiError):
    """Raised when requested resource is not found."""

    def __init__(self, resource: str, identifier: str) -> None:
        super().__init__(f"{resource.upper()}_NOT_FOUND", f"{resource} '{identifier}' not found", 404)


class GenerationFailedError(ApiError):
    """Raised when comic/report generation fails."""

    def __init__(self, message: str) -> None:
        super().__init__("GENERATION_FAILED", message, 500)


class ExternalApiError(ApiError):
    """Raised when external API (OSV, Gemini) fails."""

    def __init__(self, service: str, message: str) -> None:
        super().__init__("EXTERNAL_API_ERROR", f"{service} API error: {message}", 502)
