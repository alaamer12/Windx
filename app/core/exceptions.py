"""Custom exceptions and exception handlers.

This module defines custom exceptions for the application and provides
global exception handlers for consistent error responses.

Public Classes:
    AppException: Base exception for all application exceptions
    DatabaseException: Database-related exceptions
    AuthenticationException: Authentication-related exceptions
    AuthorizationException: Authorization-related exceptions
    ValidationException: Validation-related exceptions
    NotFoundException: Resource not found exceptions
    ConflictException: Resource conflict exceptions
    RateLimitException: Rate limit exceeded exceptions

Public Functions:
    setup_exception_handlers: Setup global exception handlers

Features:
    - Custom exception hierarchy
    - Consistent error response format
    - Automatic logging
    - HTTP status code mapping
    - Request ID tracking
"""

import logging
import traceback
from typing import Any

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from sqlalchemy.exc import IntegrityError, OperationalError

__all__ = [
    "AppException",
    "DatabaseException",
    "AuthenticationException",
    "AuthorizationException",
    "ValidationException",
    "NotFoundException",
    "ConflictException",
    "RateLimitException",
    "setup_exception_handlers",
]

logger = logging.getLogger(__name__)


# ============================================================================
# Error Response Models
# ============================================================================


class ErrorDetail(BaseModel):
    """Error detail model.

    Attributes:
        type: Error type
        message: Error message
        field: Optional field name for validation errors
    """

    type: str = Field(description="Error type")
    message: str = Field(description="Error message")
    field: str | None = Field(default=None, description="Field name for validation errors")


class ErrorResponse(BaseModel):
    """Standard error response model.

    Attributes:
        error: Error type
        message: Human-readable error message
        details: Optional list of error details
        request_id: Optional request ID for tracking
    """

    error: str = Field(description="Error type")
    message: str = Field(description="Human-readable error message")
    details: list[ErrorDetail] | None = Field(default=None, description="Error details")
    request_id: str | None = Field(default=None, description="Request ID for tracking")


# ============================================================================
# Custom Exception Classes
# ============================================================================


class AppException(Exception):
    """Base exception for all application exceptions.

    Attributes:
        message: Error message
        status_code: HTTP status code
        error_type: Error type identifier
        details: Additional error details
    """

    def __init__(
        self,
        message: str,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        error_type: str = "app_error",
        details: dict[str, Any] | None = None,
    ) -> None:
        """Initialize application exception.

        Args:
            message (str): Error message
            status_code (int): HTTP status code
            error_type (str): Error type identifier
            details (dict | None): Additional error details
        """
        self.message = message
        self.status_code = status_code
        self.error_type = error_type
        self.details = details or {}
        super().__init__(self.message)


class DatabaseException(AppException):
    """Database-related exceptions.

    Raised when database operations fail.
    """

    def __init__(
        self,
        message: str = "Database operation failed",
        details: dict[str, Any] | None = None,
    ) -> None:
        """Initialize database exception.

        Args:
            message (str): Error message
            details (dict | None): Additional error details
        """
        super().__init__(
            message=message,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            error_type="database_error",
            details=details,
        )


class AuthenticationException(AppException):
    """Authentication-related exceptions.

    Raised when authentication fails.
    """

    def __init__(
        self,
        message: str = "Authentication failed",
        details: dict[str, Any] | None = None,
    ) -> None:
        """Initialize authentication exception.

        Args:
            message (str): Error message
            details (dict | None): Additional error details
        """
        super().__init__(
            message=message,
            status_code=status.HTTP_401_UNAUTHORIZED,
            error_type="authentication_error",
            details=details,
        )


class AuthorizationException(AppException):
    """Authorization-related exceptions.

    Raised when user lacks required permissions.
    """

    def __init__(
        self,
        message: str = "Insufficient permissions",
        details: dict[str, Any] | None = None,
    ) -> None:
        """Initialize authorization exception.

        Args:
            message (str): Error message
            details (dict | None): Additional error details
        """
        super().__init__(
            message=message,
            status_code=status.HTTP_403_FORBIDDEN,
            error_type="authorization_error",
            details=details,
        )


class ValidationException(AppException):
    """Validation-related exceptions.

    Raised when input validation fails.
    """

    def __init__(
        self,
        message: str = "Validation failed",
        details: dict[str, Any] | None = None,
    ) -> None:
        """Initialize validation exception.

        Args:
            message (str): Error message
            details (dict | None): Additional error details
        """
        super().__init__(
            message=message,
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            error_type="validation_error",
            details=details,
        )


class NotFoundException(AppException):
    """Resource not found exceptions.

    Raised when requested resource doesn't exist.
    """

    def __init__(
        self,
        message: str = "Resource not found",
        resource: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        """Initialize not found exception.

        Args:
            message (str): Error message
            resource (str | None): Resource type
            details (dict | None): Additional error details
        """
        if resource:
            message = f"{resource} not found"

        super().__init__(
            message=message,
            status_code=status.HTTP_404_NOT_FOUND,
            error_type="not_found_error",
            details=details,
        )


class ConflictException(AppException):
    """Resource conflict exceptions.

    Raised when resource already exists or conflicts with existing data.
    """

    def __init__(
        self,
        message: str = "Resource conflict",
        details: dict[str, Any] | None = None,
    ) -> None:
        """Initialize conflict exception.

        Args:
            message (str): Error message
            details (dict | None): Additional error details
        """
        super().__init__(
            message=message,
            status_code=status.HTTP_409_CONFLICT,
            error_type="conflict_error",
            details=details,
        )


class RateLimitException(AppException):
    """Rate limit exceeded exceptions.

    Raised when rate limit is exceeded.
    """

    def __init__(
        self,
        message: str = "Rate limit exceeded",
        retry_after: int | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        """Initialize rate limit exception.

        Args:
            message (str): Error message
            retry_after (int | None): Seconds until retry is allowed
            details (dict | None): Additional error details
        """
        if retry_after:
            details = details or {}
            details["retry_after"] = retry_after

        super().__init__(
            message=message,
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            error_type="rate_limit_error",
            details=details,
        )


# ============================================================================
# Exception Handlers
# ============================================================================


async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
    """Handle custom application exceptions.

    Args:
        request (Request): FastAPI request
        exc (AppException): Application exception

    Returns:
        JSONResponse: Error response
    """
    # Log the error
    logger.error(
        f"Application error: {exc.error_type} - {exc.message}",
        extra={
            "error_type": exc.error_type,
            "status_code": exc.status_code,
            "details": exc.details,
            "path": request.url.path,
            "method": request.method,
        },
    )

    # Build error response
    error_response = ErrorResponse(
        error=exc.error_type,
        message=exc.message,
        details=[ErrorDetail(type=exc.error_type, message=exc.message)] if exc.details else None,
        request_id=request.headers.get("X-Request-ID"),
    )

    return JSONResponse(
        status_code=exc.status_code,
        content=error_response.model_dump(exclude_none=True),
    )


async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError,
) -> JSONResponse:
    """Handle Pydantic validation errors.

    Args:
        request (Request): FastAPI request
        exc (RequestValidationError): Validation error

    Returns:
        JSONResponse: Error response
    """
    # Log validation error
    logger.warning(
        f"Validation error: {request.url.path}",
        extra={
            "errors": exc.errors(),
            "body": exc.body,
            "path": request.url.path,
            "method": request.method,
        },
    )

    # Build error details
    details = [
        ErrorDetail(
            type=error["type"],
            message=error["msg"],
            field=".".join(str(loc) for loc in error["loc"]),
        )
        for error in exc.errors()
    ]

    error_response = ErrorResponse(
        error="validation_error",
        message="Request validation failed",
        details=details,
        request_id=request.headers.get("X-Request-ID"),
    )

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
        content=error_response.model_dump(exclude_none=True),
    )


async def integrity_error_handler(
    request: Request,
    exc: IntegrityError,
) -> JSONResponse:
    """Handle SQLAlchemy integrity errors.

    Args:
        request (Request): FastAPI request
        exc (IntegrityError): Integrity error

    Returns:
        JSONResponse: Error response
    """
    # Log integrity error
    logger.error(
        f"Database integrity error: {request.url.path}",
        extra={
            "error": str(exc),
            "path": request.url.path,
            "method": request.method,
        },
    )

    # Determine if it's a unique constraint violation
    error_message = "Resource already exists"
    if "unique" in str(exc).lower() or "duplicate" in str(exc).lower():
        error_message = "Resource with this identifier already exists"

    error_response = ErrorResponse(
        error="conflict_error",
        message=error_message,
        request_id=request.headers.get("X-Request-ID"),
    )

    return JSONResponse(
        status_code=status.HTTP_409_CONFLICT,
        content=error_response.model_dump(exclude_none=True),
    )


async def operational_error_handler(
    request: Request,
    exc: OperationalError,
) -> JSONResponse:
    """Handle SQLAlchemy operational errors.

    Args:
        request (Request): FastAPI request
        exc (OperationalError): Operational error

    Returns:
        JSONResponse: Error response
    """
    # Log operational error
    logger.error(
        f"Database operational error: {request.url.path}",
        extra={
            "error": str(exc),
            "path": request.url.path,
            "method": request.method,
        },
    )

    error_response = ErrorResponse(
        error="database_error",
        message="Database operation failed",
        request_id=request.headers.get("X-Request-ID"),
    )

    return JSONResponse(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        content=error_response.model_dump(exclude_none=True),
    )


async def generic_exception_handler(
    request: Request,
    exc: Exception,
) -> JSONResponse:
    """Handle unexpected exceptions.

    Args:
        request (Request): FastAPI request
        exc (Exception): Unexpected exception

    Returns:
        JSONResponse: Error response
    """
    # Log unexpected error with full traceback
    logger.error(
        f"Unexpected error: {request.url.path}",
        extra={
            "error": str(exc),
            "error_type": type(exc).__name__,
            "path": request.url.path,
            "method": request.method,
            "traceback": traceback.format_exc(),
        },
    )

    error_response = ErrorResponse(
        error="internal_server_error",
        message="An unexpected error occurred",
        request_id=request.headers.get("X-Request-ID"),
    )

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=error_response.model_dump(exclude_none=True),
    )


# ============================================================================
# Setup Function
# ============================================================================


def setup_exception_handlers(app: FastAPI) -> None:
    """Setup global exception handlers for the application.

    Args:
        app (FastAPI): FastAPI application instance

    Example:
        app = FastAPI()
        setup_exception_handlers(app)
    """
    # Custom application exceptions
    app.add_exception_handler(AppException, app_exception_handler)

    # Pydantic validation errors
    app.add_exception_handler(RequestValidationError, validation_exception_handler)

    # SQLAlchemy errors
    app.add_exception_handler(IntegrityError, integrity_error_handler)
    app.add_exception_handler(OperationalError, operational_error_handler)

    # Generic exception handler (catch-all)
    app.add_exception_handler(Exception, generic_exception_handler)

    logger.info("[OK] Exception handlers configured")
