"""Application factory for creating the FastAPI app."""
from contextlib import asynccontextmanager
import os
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("expense_tracker")


@asynccontextmanager
async def lifespan(app: "FastAPI"):
    # Startup: run Alembic migrations instead of create_all
    print("Starting up — running database migrations...")
    alembic_cfg = Config(os.path.join(os.path.dirname(__file__), "alembic.ini"))
    command.upgrade(alembic_cfg, "head")
    print("Migrations complete.")
    yield
    # Shutdown
    print("Shutting down...")


def create_app() -> "FastAPI":
    """Create and configure the FastAPI application."""
    from dotenv import load_dotenv
    load_dotenv()

    import os
    import logging
    from fastapi import FastAPI, Request
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi.security import HTTPBearer
    from contextlib import asynccontextmanager
    from alembic.config import Config
    from alembic import command
    from sqlalchemy import text
    from slowapi import _rate_limit_exceeded_handler
    from slowapi.errors import RateLimitExceeded
    from sqlalchemy.exc import SQLAlchemyError, IntegrityError, OperationalError
    from slowapi import _rate_limit_exceeded_handler
    from slowapi.errors import RateLimitExceeded

    from app.routes import transactions, accounts, categories, forecast, budget, auth, recurring, categorize
    from app.db.database import engine
    from app.utils.rate_limit import limiter
    from app.utils.exceptions import register_exception_handlers

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
    )

    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

    # Register custom exception handlers
    from app.utils.exceptions import register_exception_handlers
    register_exception_handlers(app)

    return app
