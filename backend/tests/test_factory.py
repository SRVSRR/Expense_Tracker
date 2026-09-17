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