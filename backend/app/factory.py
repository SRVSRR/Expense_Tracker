"""Application factory for creating the FastAPI app."""
import logging
import os
from contextlib import asynccontextmanager

from alembic import command
from alembic.config import Config
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from sqlalchemy import text

from app.db.database import dispose_engine, engine, get_database_url, get_engine
from app.middleware.logging import logging_middleware
from app.routes import (
    auth,
    accounts,
    budget,
    categories,
    categorize,
    forecast,
    recurring,
    transactions,
)
from app.utils.exceptions import register_exception_handlers
from app.utils.logging import setup_logging
from app.utils.rate_limit import limiter

# Configure JSON structured logging at import time
setup_logging()
logger = logging.getLogger("expense_tracker")

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ALEMBIC_INI = os.path.join(BACKEND_DIR, "alembic.ini")


def get_cors_origins() -> list[str]:
    """Resolve allowed CORS origins from the ``CORS_ORIGINS`` env var.

    ``CORS_ORIGINS`` is a comma-separated list of concrete origins. Wildcard
    origins are rejected and a missing value fails fast, so production can
    never silently ship a permissive CORS configuration. Tests may use "*".
    """
    if os.getenv("TESTING") == "1":
        return ["*"]
    raw = os.getenv("CORS_ORIGINS")
    if not raw or not raw.strip():
        raise RuntimeError(
            "CORS_ORIGINS is not set. Configure comma-separated origin URLs "
            "for this environment (e.g. "
            "CORS_ORIGINS=https://app.example.com,http://localhost:3000). "
            "Wildcard '*' CORS is disallowed outside tests."
        )
    origins = [origin.strip() for origin in raw.split(",") if origin.strip()]
    if "*" in origins:
        raise RuntimeError(
            "CORS_ORIGINS must not contain '*'. List concrete origins so "
            "production never serves wildcard CORS."
        )
    return origins


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup/shutdown lifecycle: validate config, run Alembic migrations, init Sentry."""
    # Initialize Sentry first (optional — no-op if SENTRY_DSN not set or TESTING=1)
    try:
        from app.utils.sentry import init_sentry

        init_sentry()
    except Exception:
        logger.warning("Sentry init error ignored", exc_info=True)

    # Validate DATABASE_URL and init engine — fail-fast in production,
    # but allow TESTING=1 runs (pytest, CI) with no env file or DB.
    if os.getenv("TESTING") == "1":
        logger.info("TESTING=1 — skipping DATABASE_URL validation and migrations at startup")
    else:
        try:
            get_database_url()
            get_engine()
        except RuntimeError as exc:
            logger.exception("Database configuration missing at startup")
            raise

        logger.info("Running database migrations...")
        alembic_cfg = Config(ALEMBIC_INI)
        try:
            command.upgrade(alembic_cfg, "head")
        except Exception as exc:
            logger.exception("Database migration failed during startup")
            # Also report to Sentry if enabled
            try:
                import sentry_sdk

                sentry_sdk.capture_exception(exc)
            except Exception:
                pass
            raise
        logger.info("Migrations complete.")
    yield
    logger.info("Shutting down...")
    # Dispose engine on shutdown (lazy — no-op if never created, e.g., in tests)
    try:
        await dispose_engine()
    except Exception:
        logger.warning("Engine dispose failed", exc_info=True)


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    from dotenv import load_dotenv

    load_dotenv()

    security_scheme = HTTPBearer(
        scheme_name="Bearer Token",
        description="Supabase-issued JWT token. Obtain via Supabase Auth (email/password or OAuth).",
        auto_error=True,
    )

    app = FastAPI(
        title="Expense Tracker API",
        description="""
# Expense Tracker API

A personal finance API for tracking income and expenses with AI-powered forecasting and categorization.

## Features

- **Account Management**: Create and manage financial accounts with balances
- **Transaction Tracking**: Record income and expenses with categories, merchants, and descriptions
- **Category Management**: Organize transactions with hierarchical categories
- **Recurring Transactions**: Set up and track recurring income/expenses
- **Forecasting**: AI-powered cash flow, runway, and anomaly detection
- **Budgeting**: Rule-based budget recommendations and spending analysis
- **ML Categorization**: LightGBM-based automatic transaction categorization

## Authentication

All endpoints require a valid **Supabase-issued JWT** (RS256) passed as a Bearer token:

```
Authorization: Bearer <supabase_jwt_token>
```

Tokens are obtained via Supabase Auth (email/password, magic link, or OAuth providers like Google, GitHub, Apple).

The backend validates tokens using Supabase's JWKS endpoint. No local registration or login endpoints exist — all auth is handled by Supabase Auth.

## Rate Limiting

Limits are enforced per route via slowapi. Exceeding a limit returns `429`
with a `Retry-After` header. Buckets are keyed by the authenticated user
(Bearer token `sub` claim) with client-IP fallback:

- Auth (`GET /api/auth/me`): 60/minute
- Reads (GET list/detail): 120/minute
- Writes (POST/PUT/DELETE, corrections): 30/minute
- Analytics (forecast, budget, categorize/suggest): 60/hour
- ML training (`POST /api/categorize/train`): 2/hour

## Error Responses

| Code | Description |
|------|-------------|
| 400 | Bad Request - Invalid input or validation error |
| 401 | Unauthorized - Missing or invalid JWT token |
| 404 | Not Found - Resource doesn't exist or access denied |
| 422 | Unprocessable Entity - Validation error on request body |
| 429 | Too Many Requests - Rate limit exceeded |
| 500 | Internal Server Error |

## Data Isolation

All endpoints are strictly scoped to the authenticated user. Cross-user access returns 404 (not 403) to prevent user enumeration.

## Versioning

Current version: **0.1.0** (pre-release)

Breaking changes may occur without notice. API stability not guaranteed until v1.0.

## Support

- Documentation: `/docs` (Swagger UI) and `/redoc` (ReDoc)
- Issues: GitHub repository
""",
        version="0.1.0",
        contact={
            "name": "Expense Tracker Team",
            "url": "https://github.com/your-org/expense-tracker",
            "email": "support@expense-tracker.example.com",
        },
        license_info={
            "name": "MIT",
            "url": "https://opensource.org/licenses/MIT",
        },
        servers=[
            {"url": "https://api.expense-tracker.example.com", "description": "Production"},
            {"url": "https://staging-api.expense-tracker.example.com", "description": "Staging"},
            {"url": "http://localhost:8000", "description": "Local development"},
        ],
        openapi_tags=[
            {"name": "auth", "description": "Authentication: get current user (Supabase Auth handles registration/login)"},
            {"name": "accounts", "description": "Account management: create, list, get, update, delete financial accounts"},
            {"name": "transactions", "description": "Transaction management: create, list, filter, get, update, delete income/expense records"},
            {"name": "categories", "description": "Category management: create, list, get, update, delete with hierarchical support"},
            {"name": "forecast", "description": "AI-powered forecasting: cash flow, runway, and anomaly detection"},
            {"name": "budget", "description": "Budget recommendations and spending analysis by category"},
            {"name": "recurring", "description": "Recurring transaction rules: create, list, get upcoming occurrences"},
            {"name": "categorize", "description": "ML-based transaction categorization: suggest, log corrections, train model"},
        ],
        components={"securitySchemes": {"Bearer Token": {"type": "http", "scheme": "bearer", "bearerFormat": "JWT"}}},
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=get_cors_origins(),
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.middleware("http")
    async def _request_logging_middleware(request: Request, call_next):
        return await logging_middleware(request, call_next)

    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
    register_exception_handlers(app)

    app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
    app.include_router(accounts.router, prefix="/api/accounts", tags=["accounts"])
    app.include_router(transactions.router, prefix="/api/transactions", tags=["transactions"])
    app.include_router(categories.router, prefix="/api/categories", tags=["categories"])
    app.include_router(forecast.router, prefix="/api/forecast", tags=["forecast"])
    app.include_router(budget.router, prefix="/api/budget", tags=["budget"])
    app.include_router(recurring.router, prefix="/api/recurring", tags=["recurring"])
    app.include_router(categorize.router, prefix="/api/categorize", tags=["categorize"])

    @app.get("/", include_in_schema=False)
    async def root():
        return {
            "message": "Expense Tracker API",
            "docs": "/docs",
            "redoc": "/redoc",
        }

    @app.get("/health", tags=["health"])
    async def health_check():
        """Detailed health check for monitoring — DB, migrations, pool, latency."""
        import time
        from datetime import datetime, timezone

        started = time.perf_counter()
        # In TESTING mode, avoid real DB hits that may be loop-bound (TestClient
        # creates a new event loop per request, which breaks the singleton engine).
        # Return a fast synthetic ok for tests; real DB is exercised via
        # dependency-overridden routes in integration tests.
        if os.getenv("TESTING") == "1":
            return {
                "status": "ok",
                "database": "ok",
                "migrations": {"status": "ok", "head": "test", "current": "test"},
                "pool": {"status": "test"},
                "latency_ms": 0,
                "total_latency_ms": 0,
                "version": app.version,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "database_error": None,
            }

        db_status = "ok"
        db_latency_ms: int | None = None
        db_error: str | None = None
        try:
            t0 = time.perf_counter()
            async with get_engine().connect() as conn:
                await conn.execute(text("SELECT 1"))
            db_latency_ms = int((time.perf_counter() - t0) * 1000)
        except Exception as exc:
            logger.warning("Health check database failure: %s", exc)
            db_status = f"error: {exc}"
            db_error = str(exc)

        # Migrations: compare head vs alembic_version table (no write)
        migrations: dict = {"status": "unknown", "head": None, "current": None}
        try:
            from alembic.script import ScriptDirectory

            cfg = Config(ALEMBIC_INI)
            # get_current_head() may be None if no versions
            head = ScriptDirectory.from_config(cfg).get_current_head()
            migrations["head"] = head
            # Query DB for current version (if table exists)
            try:
                async with get_engine().connect() as conn:
                    result = await conn.execute(text("SELECT version_num FROM alembic_version"))
                    row = result.fetchone()
                    current = row[0] if row else None
                    migrations["current"] = current
                    if head is None:
                        migrations["status"] = "ok"
                    elif current == head:
                        migrations["status"] = "ok"
                    elif current is None:
                        migrations["status"] = "error: no version table"
                    else:
                        migrations["status"] = "behind"
            except Exception as exc:
                # No alembic_version table yet (fresh DB) is not an error for health
                msg = str(exc).lower()
                if "no such table" in msg or "alembic_version" in msg:
                    migrations["status"] = "ok"
                    migrations["current"] = None
                else:
                    migrations["status"] = f"error: {exc}"
        except Exception as exc:
            migrations["status"] = f"error: {exc}"

        # Pool health (best-effort, driver-dependent)
        pool: dict = {}
        try:
            p = get_engine().pool
            # Async engine pool may be wrapped; try common attrs
            for attr in ("size", "checkedin", "checkedout", "overflow", "invalidated"):
                if hasattr(p, attr):
                    try:
                        val = getattr(p, attr)
                        pool[attr] = val() if callable(val) else val
                    except Exception:
                        pass
            if not pool:
                # Fallback status string if pool doesn't expose metrics
                pool = {"status": str(type(p).__name__)}
        except Exception as exc:
            pool = {"status": f"error: {exc}"}

        total_latency_ms = int((time.perf_counter() - started) * 1000)
        # Overall status: ok if DB ok and migrations not error/behind
        overall = "ok"
        if db_status != "ok":
            overall = "error"
        elif migrations.get("status") not in ("ok", "unknown"):
            # "behind" is degraded but not error — still report degraded
            overall = "degraded" if migrations["status"] == "behind" else "error"

        return {
            "status": overall,
            "database": db_status,
            "migrations": migrations,
            "pool": pool,
            "latency_ms": db_latency_ms,
            "total_latency_ms": total_latency_ms,
            "version": app.version,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "database_error": db_error,
        }

    return app