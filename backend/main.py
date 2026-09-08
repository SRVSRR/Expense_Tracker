from dotenv import load_dotenv
load_dotenv()

import os
import logging
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from alembic.config import Config
from alembic import command
from sqlalchemy import text
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from sqlalchemy.exc import SQLAlchemyError, IntegrityError, OperationalError

from app.routes import transactions, accounts, categories, forecast, budget, auth, recurring, categorize
from app.db.database import engine
from app.utils.rate_limit import limiter
from app.utils.exceptions import register_exception_handlers

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("expense_tracker")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: run Alembic migrations instead of create_all
    print("Starting up — running database migrations...")
    alembic_cfg = Config(os.path.join(os.path.dirname(__file__), "alembic.ini"))
    command.upgrade(alembic_cfg, "head")
    print("Migrations complete.")
    yield
    # Shutdown
    print("Shutting down...")


# Use the factory to create the app
from app.factory import create_app
app = create_app()

# The factory already sets up CORS, exception handlers, rate limiting, etc.
# Just need to add our custom middleware and routes

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
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


# Routes
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
    except Exception as e:
        db_status = f"error: {e}"
    return {"status": "ok", "database": db_status}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)