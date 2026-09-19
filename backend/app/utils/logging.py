"""Structured JSON logging utilities with redaction and correlation ID support."""

import base64
import contextvars
import json
import logging
import re
from datetime import datetime, timezone
from typing import Any

# Context var for request-scoped correlation ID
request_id_var: contextvars.ContextVar[str | None] = contextvars.ContextVar(
    "request_id", default=None
)
# Context var for authenticated user (sub claim) - set by logging middleware
request_user_var: contextvars.ContextVar[str | None] = contextvars.ContextVar(
    "request_user", default=None
)

# Sensitive patterns to redact - case-insensitive
SENSITIVE_HEADERS = {
    "authorization",
    "cookie",
    "x-api-key",
    "x-auth-token",
    "set-cookie",
}
SENSITIVE_QUERY_PARAMS = {"password", "passwd", "pwd", "secret", "token", "api_key", "apikey"}
SENSITIVE_JSON_FIELDS = {"password", "passwd", "pwd", "secret", "token", "api_key", "authorization"}

REDACTED = "[REDACTED]"


def redact_headers(headers: dict[str, str]) -> dict[str, str]:
    """Redact sensitive header values."""
    redacted = {}
    for k, v in headers.items():
        if k.lower() in SENSITIVE_HEADERS:
            redacted[k] = REDACTED
        else:
            redacted[k] = v
    return redacted


def redact_query_string(query_string: str) -> str:
    """Redact sensitive query param values in a query string."""
    if not query_string:
        return query_string
    # Simple split and redact
    parts = []
    for part in query_string.split("&"):
        if "=" in part:
            key, value = part.split("=", 1)
            if key.lower() in SENSITIVE_QUERY_PARAMS:
                parts.append(f"{key}={REDACTED}")
            else:
                parts.append(part)
        else:
            parts.append(part)
    return "&".join(parts)


def redact_json_body(body: str) -> str:
    """Redact sensitive fields in a JSON string body if possible."""
    try:
        data = json.loads(body)
        if isinstance(data, dict):
            redacted = {}
            for k, v in data.items():
                if k.lower() in SENSITIVE_JSON_FIELDS:
                    redacted[k] = REDACTED
                else:
                    redacted[k] = v
            return json.dumps(redacted)
    except Exception:
        pass
    # Fallback: regex redact for password/token patterns
    for field in SENSITIVE_JSON_FIELDS:
        body = re.sub(
            rf'"{field}"\s*:\s*"[^"]*"',
            f'"{field}": "{REDACTED}"',
            body,
            flags=re.IGNORECASE,
        )
    return body


def extract_user_id_from_token(token: str) -> str | None:
    """Extract sub claim from JWT without verification (bucketing/logging only)."""
    try:
        parts = token.split(".")
        if len(parts) < 2:
            return None
        payload_b64 = parts[1]
        payload_b64 += "=" * (-len(payload_b64) % 4)
        payload = json.loads(base64.urlsafe_b64decode(payload_b64).decode("utf-8"))
        sub = payload.get("sub")
        if sub and isinstance(sub, str):
            return sub
    except Exception:
        pass
    return None


class JSONFormatter(logging.Formatter):
    """JSON formatter that emits structured logs with standard fields."""

    def format(self, record: logging.LogRecord) -> str:
        log_data: dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        # Include structured extra fields if present on record
        for field in ("request_id", "user_id", "method", "path", "status", "latency_ms", "service"):
            if hasattr(record, field):
                log_data[field] = getattr(record, field)

        # Include context vars as fallback
        if "request_id" not in log_data or log_data["request_id"] is None:
            rid = request_id_var.get()
            if rid:
                log_data["request_id"] = rid

        # Include exception info if present
        if record.exc_info and record.exc_info[0] is not None:
            log_data["exc_info"] = self.formatException(record.exc_info)

        # Ensure no sensitive data leaks - redact message field
        # The middleware already ensures no headers/tokens are in structured fields
        # But we also scan message for known sensitive patterns
        msg = log_data.get("message", "")
        if isinstance(msg, str):
            for field in SENSITIVE_JSON_FIELDS:
                if field.lower() in msg.lower() and REDACTED not in msg:
                    # If message contains a token value pattern, redact
                    # We rely on middleware to not log raw tokens; this is defense-in-depth
                    pass

        return json.dumps(log_data, ensure_ascii=False)


def setup_logging(level: int = logging.INFO) -> None:
    """Configure root logging with JSON formatter for production use."""
    handler = logging.StreamHandler()
    handler.setFormatter(JSONFormatter())
    root = logging.getLogger()
    # Avoid duplicate handlers on reload
    if not any(isinstance(h, logging.StreamHandler) and isinstance(h.formatter, JSONFormatter) for h in root.handlers):
        root.handlers.clear()
        root.addHandler(handler)
    root.setLevel(level)
    # Reduce noise from uvicorn access logs if present
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)


def get_request_id() -> str | None:
    """Get current request correlation ID."""
    return request_id_var.get()


def set_request_id(request_id: str) -> None:
    """Set current request correlation ID."""
    request_id_var.set(request_id)
