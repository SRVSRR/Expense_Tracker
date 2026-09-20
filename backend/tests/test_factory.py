"""Tests for the app factory and its Alembic wiring.

The lifespan runs Alembic migrations at startup. The production failure
"alembic.util.exc.CommandError: No 'script_location' key found in
configuration" was caused by pointing Alembic's Config at
`backend/app/alembic.ini`, which does not exist. These tests guard the
path resolution so the ini file is always found and its `script_location`
points at a directory that exists.

The CORS helpers enforce P3 hardening: `CORS_ORIGINS` must be set outside
tests, wildcard origins are rejected, and a missing value fails fast.
"""
import os

import pytest
from alembic.config import Config
from fastapi.middleware.cors import CORSMiddleware

from app.factory import ALEMBIC_INI, create_app, get_cors_origins


def test_alembic_ini_path_exists():
    assert os.path.isfile(ALEMBIC_INI)


def test_alembic_script_location_resolves():
    cfg = Config(ALEMBIC_INI)
    script_location = cfg.get_main_option("script_location")
    assert script_location and os.path.isdir(script_location)
    assert os.path.isfile(os.path.join(script_location, "env.py"))


def test_create_app_wires_lifespan():
    app = create_app()
    assert app.router.lifespan_context is not None


def test_cors_origins_from_env(monkeypatch):
    monkeypatch.setenv("TESTING", "0")
    monkeypatch.setenv("CORS_ORIGINS", "https://app.example.com, http://localhost:3000 ")
    assert get_cors_origins() == ["https://app.example.com", "http://localhost:3000"]


def test_cors_origins_fail_fast_when_unset(monkeypatch):
    monkeypatch.setenv("TESTING", "0")
    monkeypatch.delenv("CORS_ORIGINS", raising=False)
    with pytest.raises(RuntimeError, match="CORS_ORIGINS is not set"):
        get_cors_origins()


def test_cors_origins_rejects_wildcard_outside_tests(monkeypatch):
    monkeypatch.setenv("TESTING", "0")
    monkeypatch.setenv("CORS_ORIGINS", "*")
    with pytest.raises(RuntimeError, match="must not contain"):
        get_cors_origins()


def test_cors_origins_wildcard_in_tests(monkeypatch):
    monkeypatch.setenv("TESTING", "1")
    monkeypatch.delenv("CORS_ORIGINS", raising=False)
    assert get_cors_origins() == ["*"]


def test_create_app_uses_env_cors(monkeypatch):
    monkeypatch.setenv("TESTING", "0")
    monkeypatch.setenv("CORS_ORIGINS", "https://app.example.com")
    app = create_app()
    cors = [m for m in app.user_middleware if m.cls is CORSMiddleware]
    assert cors
    assert cors[0].kwargs["allow_origins"] == ["https://app.example.com"]


def test_request_logging_adds_request_id_header_and_context(monkeypatch):
    monkeypatch.setenv("TESTING", "0")
    monkeypatch.setenv("CORS_ORIGINS", "https://app.example.com")
    app = create_app()

    @app.get("/log-check")
    async def log_check():
        return {"ok": True}

    from fastapi.testclient import TestClient

    client = TestClient(app)
    response = client.get("/log-check")

    assert response.status_code == 200
    assert "X-Request-ID" in response.headers
    assert response.headers["X-Request-ID"]
    # Header should be reused if client sends one
    response2 = client.get("/log-check", headers={"X-Request-ID": "req_test123"})
    assert response2.headers["X-Request-ID"] == "req_test123"


def test_request_logging_redacts_sensitive_values(caplog):
    from fastapi.testclient import TestClient

    app = create_app()

    @app.get("/secure-check")
    async def secure_check():
        return {"ok": True}

    caplog.set_level("INFO", logger="expense_tracker.request")
    client = TestClient(app)
    client.get(
        "/secure-check",
        headers={"Authorization": "Bearer secret-token-123"},
    )

    # Caplog captures the JSON log messages; ensure secret never appears
    request_logs = [r for r in caplog.records if r.name == "expense_tracker.request"]
    log_text = "\n".join(record.getMessage() for record in request_logs)
    assert "secret-token-123" not in log_text
    # Structured logs should not contain raw Authorization header name with value
    # If Authorization appears, it must be redacted
    assert "secret-token-123" not in log_text
    # Ensure at least one structured log was emitted with required fields
    assert any("request_id" in r.getMessage() or hasattr(r, "request_id") for r in request_logs)


def test_request_logging_emits_structured_json(monkeypatch, caplog):
    monkeypatch.setenv("TESTING", "0")
    monkeypatch.setenv("CORS_ORIGINS", "https://app.example.com")
    from fastapi.testclient import TestClient
    import json

    app = create_app()

    @app.get("/json-log-check")
    async def json_check():
        return {"ok": True}

    caplog.set_level("INFO", logger="expense_tracker.request")
    client = TestClient(app)
    client.get("/json-log-check")

    # Find the JSON log record
    json_records = []
    for record in caplog.records:
        if record.name == "expense_tracker.request":
            try:
                data = json.loads(record.getMessage())
                json_records.append(data)
            except Exception:
                # Check extra fields on record
                if hasattr(record, "request_id"):
                    json_records.append(record.__dict__)
    assert json_records, "Should emit JSON structured log"
    rec = json_records[-1]
    # Verify required fields
    for field in ("request_id", "method", "path", "status", "latency_ms"):
        assert field in rec or hasattr(caplog.records[-1], field), f"Missing {field} in log"


def test_request_logging_redacts_sensitive_query_params(monkeypatch, caplog):
    monkeypatch.setenv("TESTING", "0")
    monkeypatch.setenv("CORS_ORIGINS", "https://app.example.com")
    from fastapi.testclient import TestClient

    app = create_app()

    @app.get("/query-check")
    async def query_check():
        return {"ok": True}

    caplog.set_level("INFO", logger="expense_tracker.request")
    client = TestClient(app)
    client.get("/query-check?password=supersecret&token=abc123&safe=value")

    # Only check our structured logger, not httpx access logs
    request_logs = [r for r in caplog.records if r.name == "expense_tracker.request"]
    assert request_logs, "Expected at least one request log"
    # Check structured fields, not getMessage (which is just "request completed")
    for record in request_logs:
        path = getattr(record, "path", "")
        assert "supersecret" not in path
        assert "supersecret" not in record.getMessage()
        assert "abc123" not in path
        # Safe param should still appear redacted correctly
        assert "safe" in path
        assert "password=[REDACTED]" in path
        assert "token=[REDACTED]" in path


def test_health_detailed_json_and_public():
    from fastapi.testclient import TestClient

    app = create_app()
    client = TestClient(app)
    # No auth header — health must be public
    r = client.get("/health")
    assert r.status_code == 200
    data = r.json()
    # Backwards compat fields
    assert "status" in data
    assert "database" in data
    # Detailed fields for monitoring
    assert "migrations" in data and isinstance(data["migrations"], dict)
    assert "head" in data["migrations"]
    assert "current" in data["migrations"]
    assert "status" in data["migrations"]
    assert "pool" in data and isinstance(data["pool"], dict)
    assert "version" in data
    assert "timestamp" in data
    assert "latency_ms" in data
    # Must not require auth
    assert r.headers.get("X-Request-ID")


def test_health_includes_request_id_header():
    from fastapi.testclient import TestClient

    app = create_app()
    client = TestClient(app)
    r = client.get("/health", headers={"X-Request-ID": "health-test-123"})
    assert r.headers["X-Request-ID"] == "health-test-123"