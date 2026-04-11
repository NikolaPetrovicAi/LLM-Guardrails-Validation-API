from typing import Any

from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.status import (
    HTTP_400_BAD_REQUEST,
    HTTP_408_REQUEST_TIMEOUT,
    HTTP_500_INTERNAL_SERVER_ERROR,
)


class AppError(Exception):
    """Base class for all application-specific exceptions."""

    def __init__(
        self,
        message: str,
        status_code: int = HTTP_500_INTERNAL_SERVER_ERROR,
        error_code: str = "INTERNAL_ERROR",
        details: Any = None,
    ):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.error_code = error_code
        self.details = details


class LLMValidationError(AppError):
    """Raised when the LLM output fails schema validation."""

    def __init__(self, message: str, details: Any = None):
        super().__init__(
            message=message,
            status_code=HTTP_400_BAD_REQUEST,
            error_code="LLM_VALIDATION_ERROR",
            details=details,
        )


class LLMTimeoutError(AppError):
    """Raised when the LLM provider times out."""

    def __init__(self, message: str = "LLM request timed out"):
        super().__init__(
            message=message,
            status_code=HTTP_408_REQUEST_TIMEOUT,
            error_code="LLM_TIMEOUT_ERROR",
        )


class ConfigurationError(AppError):
    """Raised when there is a configuration-related issue."""

    def __init__(self, message: str):
        super().__init__(
            message=message,
            status_code=HTTP_500_INTERNAL_SERVER_ERROR,
            error_code="CONFIGURATION_ERROR",
        )


async def app_exception_handler(request: Request, exc: AppError) -> JSONResponse:
    """
    Global exception handler for AppError.
    Returns an RFC 7807 compliant JSON response.
    """
    error_type_url = (
        f"https://api.example.com/errors/{exc.error_code.lower().replace('_', '-')}"
    )
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "type": error_type_url,
            "title": exc.error_code,
            "status": exc.status_code,
            "detail": exc.message,
            "instance": str(request.url),
            "errors": exc.details,
        },
        headers={"Content-Type": "application/problem+json"},
    )
