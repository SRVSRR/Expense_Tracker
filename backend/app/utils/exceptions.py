"""Custom exceptions and error handling utilities."""
from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.exception_handlers import http_exception_handler
from sqlalchemy.exc import IntegrityError, OperationalError, SQLAlchemyError
from starlette.status import (
    HTTP_400_BAD_REQUEST,
    HTTP_409_CONFLICT,
    HTTP_422_UNPROCESSABLE_ENTITY,
    HTTP_500_INTERNAL_SERVER_ERROR,
    HTTP_503_SERVICE_UNAVAILABLE,
)


class AppError(Exception):
    """Base application exception with error code."""

    def __init__(
        self,
        message: str,
        code: str = "INTERNAL_ERROR",
        status_code: int = HTTP_500_INTERNAL_SERVER_ERROR,
        details: dict | None = None,
    ):
        self.message = message
        self.code = code
        self.status_code = status_code
        self.details = details or {}
        super().__init__(message)


class ValidationError(AppError):
    """Validation error."""

    def __init__(self, message: str, details: dict | None = None):
        super().__init__(
            message=message,
            code="VALIDATION_ERROR",
            status_code=HTTP_422_UNPROCESSABLE_ENTITY,
            details=details,
        )


class NotFoundError(AppError):
    """Resource not found."""

    def __init__(self, resource: str, identifier: str):
        super().__init__(
            message=f"{resource} with id '{identifier}' not found",
            code="NOT_FOUND",
            status_code=404,
            details={"resource": resource, "identifier": identifier},
        )


class ConflictError(AppError):
    """Resource conflict (e.g., duplicate)."""

    def __init__(self, resource: str, details: dict | None = None):
        super().__init__(
            message=f"{resource} already exists",
            code="CONFLICT",
            status_code=HTTP_409_CONFLICT,
            details=details,
        )


class DatabaseError(AppError):
    """Database operation failed."""

    def __init__(self, message: str, details: dict | None = None):
        super().__init__(
            message=message,
            code="DATABASE_ERROR",
            status_code=HTTP_500_INTERNAL_SERVER_ERROR,
            details=details,
        )


class MigrationError(AppError):
    """Migration operation failed."""

    def __init__(self, message: str, details: dict | None = None):
        super().__init__(
            message=message,
            code="MIGRATION_ERROR",
            status_code=HTTP_500_INTERNAL_SERVER_ERROR,
            details=details,
        )


class ExternalServiceError(AppError):
    """External service unavailable."""

    def __init__(self, service: str, message: str | None = None):
        super().__init__(
            message=message or f"External service '{service}' unavailable",
            code="EXTERNAL_SERVICE_UNAVAILABLE",
            status_code=HTTP_503_SERVICE_UNAVAILABLE,
            details={"service": service},
        )


# Exception handlers
async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
    """Handle application errors with consistent format."""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": exc.code,
                "message": exc.message,
                "details": exc.details,
            }
        },
    )


async def sqlalchemy_error_handler(request: Request, exc: SQLAlchemyError) -> JSONResponse:
    """Handle SQLAlchemy errors."""
    if isinstance(exc, IntegrityError):
        # Check for unique constraint violation
        if "unique constraint" in str(exc.orig).lower() or "duplicate key" in str(exc.orig).lower():
            return JSONResponse(
                status_code=HTTP_409_CONFLICT,
                content={
                    "error": {
                        "code": "CONFLICT",
                        "message": "Resource already exists",
                        "details": {"constraint": str(exc.orig)},
                    },
                },
            )
        # Foreign key violation
        if "foreign key constraint" in str(exc.orig).lower():
            return JSONResponse(
                status_code=HTTP_400_BAD_REQUEST,
                content={
                    "error": {
                        "code": "INVALID_REFERENCE",
                        "message": "Referenced resource does not exist",
                        "details": {"constraint": str(exc.orig)},
                    },
                },
            )
    # Operational error (connection issues, etc.)
    if isinstance(exc, OperationalError):
        return JSONResponse(
            status_code=HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "error": {
                    "code": "DATABASE_UNAVAILABLE",
                    "message": "Database temporarily unavailable",
                    "details": {"error": str(exc.orig)},
                },
            },
        )
    # Generic SQLAlchemy error
    return JSONResponse(
        status_code=HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": {
                "code": "DATABASE_ERROR",
                "message": "Database operation failed",
                "details": {"error": str(exc)},
            },
        },
    )


def register_exception_handlers(app):
    """Register all exception handlers with the FastAPI app."""
    app.add_exception_handler(AppError, app_error_handler)
    app.add_exception_handler(SQLAlchemyError, sqlalchemy_error_handler)
    app.add_exception_handler(IntegrityError, sqlalchemy_error_handler)
    app.add_exception_handler(OperationalError, sqlalchemy_error_handler)