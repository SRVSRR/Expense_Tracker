"""Tests for per-endpoint rate-limit tiers and bucket keying.

Rate limiting is disabled under TESTING=1 by design (NoOpLimiter), so these
tests cover the tier contract, the user-or-IP key function, and OpenAPI
documentation of 429 responses — not live 429 enforcement.
"""
import base64
import json

from starlette.requests import Request

from app.factory import create_app
from app.utils.rate_limit import (
    ANALYTICS_LIMIT,
    AUTH_LIMIT,
    READ_LIMIT,
    TRAIN_LIMIT,
    WRITE_LIMIT,
    user_or_ip_key,
)


def _b64(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode().rstrip("=")


def _unsigned_token(payload: dict) -> str:
    return f"{_b64(b'{{}}')}.{_b64(json.dumps(payload).encode())}.sig"


def _make_request(authorization: str | None = None) -> Request:
    headers = []
    if authorization is not None:
        headers.append((b"authorization", authorization.encode()))
    scope = {
        "type": "http",
        "method": "GET",
        "headers": headers,
        "client": ("203.0.113.7", 50000),
        "server": ("testserver", 80),
        "scheme": "http",
        "path": "/",
    }
    return Request(scope)


def test_tier_values():
    assert AUTH_LIMIT == "60/minute"
    assert READ_LIMIT == "120/minute"
    assert WRITE_LIMIT == "30/minute"
    assert ANALYTICS_LIMIT == "60/hour"
    assert TRAIN_LIMIT == "2/hour"


def test_tier_strings_parse():
    from limits import parse

    for tier in (AUTH_LIMIT, READ_LIMIT, WRITE_LIMIT, ANALYTICS_LIMIT, TRAIN_LIMIT):
        assert parse(tier) is not None


def test_key_uses_bearer_sub():
    token = _unsigned_token({"sub": "user-123"})
    request = _make_request(f"Bearer {token}")
    assert user_or_ip_key(request) == "user:user-123"


def test_key_falls_back_to_ip_without_auth():
    assert user_or_ip_key(_make_request()) == "203.0.113.7"


def test_key_falls_back_to_ip_for_non_bearer_scheme():
    request = _make_request("Basic dXNlcjpwYXNz")
    assert user_or_ip_key(request) == "203.0.113.7"


def test_key_falls_back_to_ip_for_malformed_token():
    request = _make_request("Bearer not-a-jwt")
    assert user_or_ip_key(request) == "203.0.113.7"


def test_key_falls_back_to_ip_when_sub_missing():
    token = _unsigned_token({"iss": "https://example.supabase.co/auth/v1"})
    request = _make_request(f"Bearer {token}")
    assert user_or_ip_key(request) == "203.0.113.7"


def test_all_api_operations_document_429():
    app = create_app()
    schema = app.openapi()
    missing = []
    for path, operations in schema["paths"].items():
        if not path.startswith("/api/"):
            continue
        for method, operation in operations.items():
            if method.lower() not in ("get", "post", "put", "delete"):
                continue
            if "429" not in operation.get("responses", {}):
                missing.append(f"{method.upper()} {path}")
    assert not missing, f"operations missing 429 documentation: {missing}"
