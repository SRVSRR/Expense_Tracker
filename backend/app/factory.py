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

from app.db.database import engine
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
from app.utils.rate_limit import limiter

logging.basicConfig(level=logging.INFO)
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
    """Startup/shutdown lifecycle: run Alembic migrations and fail loudly on error."""
    logger.info("Running database migrations...")
    alembic_cfg = Config(ALEMBIC_INI)
    try:
        command.upgrade(alembic_cfg, "head")
    except Exception as exc:
        logger.exception("Database migration failed during startup")
        raise
    logger.info("Migrations complete.")
    yield
    logger.info("Shutting down...")


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

- Auth endpoints: 5 req/min (register), 10 req/min (login)
- Categorization training: 2 req/hour
- General endpoints: No explicit limit (protected by Supabase Auth rate limits)

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
    async def log_requests(request: Request, call_next):
        logger.info(f">>> {request.method} {request.url.path}")
        response = await call_next(request)
        logger.info(f"<<< {response.status_code}")
        return response

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
        """Health check with database connectivity verification."""
        db_status = "ok"
        try:
            async with engine.connect() as conn:
                await conn.execute(text("SELECT 1"))
        except Exception as exc:
            logger.warning("Health check database failure: %s", exc)
            db_status = f"error: {exc}"
        return {"status": "ok", "database": db_status}

    return app