# FastAPI Application Package
from fastapi import FastAPI


def create_app() -> FastAPI:
    """Create and configure FastAPI application."""
    from app.routes import transactions, accounts, categories, forecast, budget, auth
    
    app = FastAPI(
        title="Expense Tracker API",
        description="AI-powered personal finance app with forecasting",
        version="0.1.0",
    )
    
    # Include routers
    app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
    app.include_router(accounts.router, prefix="/api/accounts", tags=["accounts"])
    app.include_router(transactions.router, prefix="/api/transactions", tags=["transactions"])
    app.include_router(categories.router, prefix="/api/categories", tags=["categories"])
    app.include_router(forecast.router, prefix="/api/forecast", tags=["forecast"])
    app.include_router(budget.router, prefix="/api/budget", tags=["budget"])
    
    return app
