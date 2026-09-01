from dotenv import load_dotenv
load_dotenv()

import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from alembic.config import Config
from alembic import command

from app.routes import transactions, accounts, categories, forecast, budget, auth, recurring, categorize


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


app = FastAPI(
    title="Expense Tracker API",
    description="AI-powered personal finance app with forecasting",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routes
app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(accounts.router, prefix="/api/accounts", tags=["accounts"])
app.include_router(transactions.router, prefix="/api/transactions", tags=["transactions"])
app.include_router(categories.router, prefix="/api/categories", tags=["categories"])
app.include_router(forecast.router, prefix="/api/forecast", tags=["forecast"])
app.include_router(budget.router, prefix="/api/budget", tags=["budget"])
app.include_router(recurring.router, prefix="/api/recurring", tags=["recurring"])
app.include_router(categorize.router, prefix="/api/categorize", tags=["categorize"])


@app.get("/")
async def root():
    return {
        "message": "Expense Tracker API",
        "docs": "/docs",
        "redoc": "/redoc",
    }


@app.get("/health")
async def health_check():
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
