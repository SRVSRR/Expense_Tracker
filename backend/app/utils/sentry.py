"""Sentry integration — optional, enabled only when SENTRY_DSN is set.

Initializes sentry-sdk with FastAPI and SQLAlchemy integrations when a DSN
is configured. In TESTING mode Sentry is always disabled (no network calls
during tests). User context (sub claim) is attached for error grouping without
performing authentication — actual auth is handled by get_current_user.
"""

import logging
import os

logger = logging.getLogger("expense_tracker.sentry")

_initialized = False


def init_sentry() -> bool:
    """Initialize Sentry if SENTRY_DSN is configured. Returns True if enabled."""
    global _initialized
    if _initialized:
        return True

    # Never enable during isolated tests
    if os.getenv("TESTING") == "1":
        logger.info("Sentry disabled in TESTING mode")
        return False

    dsn = os.getenv("SENTRY_DSN")
    if not dsn:
        logger.info("Sentry disabled: SENTRY_DSN not set")
        return False

    try:
        import sentry_sdk
        from sentry_sdk.integrations.fastapi import FastApiIntegration
        from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
        from sentry_sdk.integrations.logging import LoggingIntegration

        environment = os.getenv("ENVIRONMENT", os.getenv("APP_ENV", "production"))
        release = os.getenv("SENTRY_RELEASE") or os.getenv("GIT_SHA")

        sentry_sdk.init(
            dsn=dsn,
            environment=environment,
            release=release,
            integrations=[
                FastApiIntegration(transaction_style="endpoint"),
                SqlalchemyIntegration(),
                LoggingIntegration(level=logging.INFO, event_level=logging.ERROR),
            ],
            traces_sample_rate=float(os.getenv("SENTRY_TRACES_SAMPLE_RATE", "0.1")),
            profiles_sample_rate=float(os.getenv("SENTRY_PROFILES_SAMPLE_RATE", "0.0")),
            send_default_pii=False,
            attach_stacktrace=True,
        )
        _initialized = True
        logger.info("Sentry initialized", extra={"environment": environment})
        return True
    except Exception as exc:
        logger.warning("Sentry init failed: %s", exc)
        return False


def capture_user_context(user_id: str | None) -> None:
    """Attach user_id to Sentry scope for error grouping (non-auth)."""
    if not _initialized or not user_id:
        return
    try:
        import sentry_sdk

        sentry_sdk.set_user({"id": user_id})
    except Exception:
        pass


def is_sentry_enabled() -> bool:
    return _initialized
