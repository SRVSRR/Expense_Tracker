"""Request logging middleware with correlation IDs, timing, and structured JSON logs."""

import logging
import time
import uuid
from typing import Callable

from fastapi import Request, Response

from app.utils.logging import (
    extract_user_id_from_token,
    redact_query_string,
    request_id_var,
    request_user_var,
)
from app.utils.sentry import capture_user_context

logger = logging.getLogger("expense_tracker.request")
# Known safe service identifier
SERVICE_NAME = "expense-tracker"


async def logging_middleware(request: Request, call_next: Callable) -> Response:
    """Middleware that logs every request with structured JSON.

    - Generates or propagates X-Request-ID
    - Measures latency
    - Extracts user_id from Bearer token (without verification) for logging context
    - Redacts sensitive query params in logged path
    - Adds X-Request-ID to response headers
    - Never logs Authorization header values or body secrets
    """
    # Correlation ID: use incoming header if present, else generate
    incoming_id = request.headers.get("X-Request-ID") or request.headers.get("x-request-id")
    request_id = incoming_id if incoming_id else f"req_{uuid.uuid4().hex[:12]}"

    # Set context vars for downstream use
    token_request_id = request_id_var.set(request_id)
    # Extract user_id for logging context (non-auth, just for bucketing/logging)
    user_id: str | None = None
    auth = request.headers.get("Authorization") or request.headers.get("authorization") or ""
    if auth.lower().startswith("bearer "):
        token = auth[7:].strip()
        user_id = extract_user_id_from_token(token)
        # Attach to Sentry scope (non-auth, best-effort)
        capture_user_context(user_id)
    user_token = request_user_var.set(user_id)

    # Also set on request.state for route handlers if needed
    request.state.request_id = request_id
    if user_id:
        request.state.user_id = user_id

    start = time.perf_counter()
    status_code = 500
    response: Response | None = None

    try:
        response = await call_next(request)
        status_code = response.status_code
        return response
    except Exception:
        # Log exception with structured context; re-raise for global handler
        logger.exception(
            "request failed",
            extra={
                "request_id": request_id,
                "user_id": user_id or "anonymous",
                "method": request.method,
                "path": _safe_path(request),
                "status": 500,
                "latency_ms": int((time.perf_counter() - start) * 1000),
                "service": SERVICE_NAME,
            },
        )
        raise
    finally:
        # Always emit structured access log (even on exception if we have status)
        latency_ms = int((time.perf_counter() - start) * 1000)
        # If response exists, ensure header is set
        if response is not None:
            response.headers["X-Request-ID"] = request_id

        # Use get attribute for status if response existed else 500
        final_status = status_code
        if response is not None:
            final_status = response.status_code

        # Structured log - no headers, no body, no tokens
        logger.info(
            "request completed",
            extra={
                "request_id": request_id,
                "user_id": user_id or "anonymous",
                "method": request.method,
                "path": _safe_path(request),
                "status": final_status,
                "latency_ms": latency_ms,
                "service": SERVICE_NAME,
            },
        )
        # Reset context vars
        request_id_var.reset(token_request_id)
        request_user_var.reset(user_token)


def _safe_path(request: Request) -> str:
    """Return path with redacted query string, never including raw tokens."""
    path = request.url.path
    query = request.url.query
    if query:
        redacted = redact_query_string(query)
        return f"{path}?{redacted}" if redacted else path
    return path

# For use with app.middleware("http") decorator pattern if preferred
# This function is compatible with Starlette's @app.middleware("http") signature
async def request_logging_middleware(request: Request, call_next):
    return await logging_middleware(request, call_next)
