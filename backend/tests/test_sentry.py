"""Tests for Sentry integration (optional, disabled in TESTING mode)."""

import os


def test_sentry_disabled_in_testing(monkeypatch):
    monkeypatch.setenv("TESTING", "1")
    monkeypatch.delenv("SENTRY_DSN", raising=False)
    # Need to reload module to reset _initialized flag
    import app.utils.sentry as sentry_mod

    # Reset flag
    sentry_mod._initialized = False
    result = sentry_mod.init_sentry()
    assert result is False
    assert sentry_mod.is_sentry_enabled() is False


def test_sentry_disabled_without_dsn(monkeypatch):
    monkeypatch.setenv("TESTING", "0")
    monkeypatch.delenv("SENTRY_DSN", raising=False)
    import app.utils.sentry as sentry_mod

    sentry_mod._initialized = False
    result = sentry_mod.init_sentry()
    assert result is False


def test_capture_user_context_noop_when_disabled(monkeypatch):
    monkeypatch.setenv("TESTING", "1")
    import app.utils.sentry as sentry_mod

    sentry_mod._initialized = False
    # Should not raise even when not initialized
    sentry_mod.capture_user_context("user-123")
    sentry_mod.capture_user_context(None)
