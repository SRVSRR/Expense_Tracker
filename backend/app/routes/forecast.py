"""Forecasting routes (AI/ML features) — LightGBM-powered forecasting with confidence intervals."""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from datetime import datetime, timedelta

from app.db.database import get_db
from app.models import Transaction, Account
from app.utils import get_current_user, with_retry
from app.services.prediction_cache import get_cached_prediction, store_prediction
from app.ml.forecasting import get_forecast_manager
from app.schemas import (
    CashflowForecast,
    RunwayForecast,
    AnomaliesResponse,
)

router = APIRouter()


def _convert_ml_forecast_to_cashflow(ml_data: dict, days: int) -> dict:
    """Convert ML forecast output to CashflowForecast schema format."""
    forecast = ml_data.get("forecast", [])
    
    # Calculate average daily income/expense from ML forecast
    total_income = sum(f.get("expected_income", 0) for f in forecast)
    total_expense = sum(f.get("expected_expense", 0) for f in forecast)
    num_days = len(forecast) if forecast else 1
    avg_daily_income = total_income / num_days
    avg_daily_expense = total_expense / num_days
    
    # Convert ML forecast format to CashflowForecastDay format
    forecast_days = []
    for f in forecast:
        forecast_days.append({
            "date": f["date"],
            "projected_balance": f["projected_balance"],
            "expected_income": f["expected_income"],
            "expected_expense": f["expected_expense"],
            "income_confidence_interval": f.get("income_confidence_interval"),
            "expense_confidence_interval": f.get("expense_confidence_interval"),
        })
    
    return {
        "period_days": len(forecast_days),
        "avg_daily_income": round(avg_daily_income, 2),
        "avg_daily_expense": round(avg_daily_expense, 2),
        "forecast": forecast_days,
    }


CASHFLOW_200_EXAMPLE = {
    "period_days": 30,
    "avg_daily_income": 100.0,
    "avg_daily_expense": 85.5,
    "forecast": [
        {
            "date": "2026-09-08",
            "projected_balance": 5114.5,
            "expected_income": 100.0,
            "expected_expense": 85.5,
            "income_confidence_interval": {"lower": 75.0, "upper": 125.0},
            "expense_confidence_interval": {"lower": 60.0, "upper": 110.0}
        },
        {
            "date": "2026-09-09",
            "projected_balance": 5129.0,
            "expected_income": 100.0,
            "expected_expense": 85.5,
            "income_confidence_interval": {"lower": 75.0, "upper": 125.0},
            "expense_confidence_interval": {"lower": 60.0, "upper": 110.0}
        },
        {
            "date": "2026-09-10",
            "projected_balance": 5143.5,
            "expected_income": 100.0,
            "expected_expense": 85.5,
            "income_confidence_interval": {"lower": 75.0, "upper": 125.0},
            "expense_confidence_interval": {"lower": 60.0, "upper": 110.0}
        }
    ]
}

RUNWAY_200_EXAMPLE = {
    "current_balance": 15000.0,
    "avg_daily_income": 100.0,
    "avg_daily_expense": 120.0,
    "net_daily_burn": 20.0,
    "threshold": 1000.0,
    "days_until_threshold": 450
}

ANOMALIES_200_EXAMPLE = {
    "total_transactions_analyzed": 45,
    "anomalies_found": 2,
    "anomalies": [
        {
            "transaction_id": "txn_abc123",
            "amount": 500.0,
            "category": "Food & Dining",
            "description": "Expensive dinner",
            "date": "2026-09-01T19:30:00",
            "category_avg": 45.0,
            "deviation_ratio": 11.11
        },
        {
            "transaction_id": "txn_def456",
            "amount": 2500.0,
            "category": "Electronics",
            "description": "New laptop",
            "date": "2026-09-05T14:22:00",
            "category_avg": 120.0,
            "deviation_ratio": 20.83
        }
    ]
}

ERROR_401 = {
    "description": "Unauthorized - Missing or invalid JWT token",
    "content": {
        "application/json": {
            "example": {
                "error": {
                    "code": "UNAUTHORIZED",
                    "message": "Could not validate credentials",
                    "details": {}
                }
            }
        }
    }
}

ERROR_404 = {
    "description": "Not Found - Resource doesn't exist or access denied",
    "content": {
        "application/json": {
            "example": {
                "error": {
                    "code": "NOT_FOUND",
                    "message": "Resource not found",
                    "details": {}
                }
            }
        }
    }
}

ERROR_422 = {
    "description": "Validation Error",
    "content": {
        "application/json": {
            "example": {
                "detail": [
                    {
                        "loc": ["query", "days"],
                        "msg": "ensure this value is greater than or equal to 7",
                        "type": "value_error.number.not_ge",
                        "input": 5
                    }
                ]
            }
        }
    }
}

ERROR_500 = {
    "description": "Internal Server Error",
    "content": {
        "application/json": {
            "example": {
                "error": {
                    "code": "INTERNAL_ERROR",
                    "message": "An unexpected error occurred",
                    "details": {}
                }
            }
        }
    }
}

COMMON_ERRORS = {
    401: ERROR_401,
    404: ERROR_404,
    422: ERROR_422,
    500: ERROR_500,
}


@router.get(
    "/cashflow",
    response_model=CashflowForecast,
    summary="Cash flow forecast",
    description="Returns an ML-powered cash flow forecast with confidence intervals for the specified number of days. Cached for 24 hours.",
    responses={
        200: {
            "description": "Successful response with forecast data",
            "content": {
                "application/json": {
                    "example": CASHFLOW_200_EXAMPLE
                }
            }
        },
        401: ERROR_401,
        422: ERROR_422,
        500: ERROR_500,
    },
)
async def get_cashflow_forecast(
    days: int = Query(default=30, ge=7, le=365, description="Number of days to forecast"),
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user),
):
    """ML-powered cash flow forecast with confidence intervals — cached in predictions table (24h TTL)."""
    cached = await get_cached_prediction(db, current_user.id, "cashflow")
    if cached and cached.get("period_days") == days:
        return cached

    forecast_manager = get_forecast_manager()
    ml_data = await forecast_manager.generate_forecasts(db, current_user.id, days)
    
    # Convert ML forecast to CashflowForecast schema format
    data = _convert_ml_forecast_to_cashflow(ml_data, days)
    
    await store_prediction(db, current_user.id, "cashflow", data)
    return data


@router.get(
    "/runway",
    response_model=RunwayForecast,
    summary="Runway prediction",
    description="Computes days until balance hits a threshold based on ML-projected net daily burn rate. Cached for 12 hours.",
    responses={
        200: {
            "description": "Successful response with runway data",
            "content": {
                "application/json": {
                    "example": RUNWAY_200_EXAMPLE
                }
            }
        },
        401: ERROR_401,
        422: ERROR_422,
        500: ERROR_500,
    },
)
async def get_runway_forecast(
    threshold: float = Query(default=0.0, description="Balance threshold (default 0)"),
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user),
):
    """Runway prediction with ML-projected net daily burn — cached in predictions table (12h TTL)."""
    cached = await get_cached_prediction(db, current_user.id, "runway")
    if cached and cached.get("threshold") == threshold:
        return cached

    forecast_manager = get_forecast_manager()
    forecast_data = await forecast_manager.generate_forecasts(db, current_user.id, 365)
    
    # Compute runway from ML forecast
    current_balance = forecast_data.get("current_balance", 0)
    forecast = forecast_data.get("forecast", [])
    
    total_income = sum(f.get("expected_income", 0) for f in forecast)
    total_expense = sum(f.get("expected_expense", 0) for f in forecast)
    avg_daily_income = total_income / 365 if forecast else 0
    avg_daily_expense = total_expense / 365 if forecast else 0
    net_daily_burn = avg_daily_expense - avg_daily_income
    
    if net_daily_burn <= 0:
        days_remaining = None
    else:
        days_remaining = max(0, int((current_balance - threshold) / net_daily_burn))
    
    data = {
        "current_balance": round(current_balance, 2),
        "avg_daily_income": round(avg_daily_income, 2),
        "avg_daily_expense": round(avg_daily_expense, 2),
        "net_daily_burn": round(net_daily_burn, 2),
        "threshold": threshold,
        "days_until_threshold": days_remaining,
    }
    await store_prediction(db, current_user.id, "runway", data)
    return data


@router.get(
    "/anomalies",
    response_model=AnomaliesResponse,
    summary="Anomaly detection",
    description="Detects per-category expense outliers (>2x category average). Cached for 24 hours.",
    responses={
        200: {
            "description": "Successful response with anomaly data",
            "content": {
                "application/json": {
                    "example": ANOMALIES_200_EXAMPLE
                }
            }
        },
        401: ERROR_401,
        500: ERROR_500,
    },
)
async def detect_anomalies(
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user),
):
    """Anomaly detection — cached in predictions table (24h TTL)."""
    cached = await get_cached_prediction(db, current_user.id, "anomaly")
    if cached:
        return cached

    data = await _compute_anomalies(db, current_user.id)
    await store_prediction(db, current_user.id, "anomaly", data)
    return data


@with_retry(max_retries=3, base_delay=0.5, max_delay=5.0)
async def _compute_anomalies(db: AsyncSession, user_id: str) -> dict:
    """Compute naive anomaly detection (2x category average)."""
    result = await db.execute(
        select(Transaction).where(Transaction.auth_user_id == user_id)
    )
    transactions = result.scalars().all()

    category_totals = {}
    category_counts = {}
    for tx in transactions:
        if tx.type.value == "expense":
            cat = tx.category
            category_totals[cat] = category_totals.get(cat, 0) + tx.amount
            category_counts[cat] = category_counts.get(cat, 0) + 1

    category_avg = {}
    for cat in category_totals:
        category_avg[cat] = category_totals[cat] / max(category_counts[cat], 1)

    anomalies = []
    for tx in transactions:
        if tx.type.value == "expense":
            avg = category_avg.get(tx.category, 0)
            if avg > 0 and tx.amount > 2 * avg:
                anomalies.append({
                    "transaction_id": tx.id,
                    "amount": tx.amount,
                    "category": tx.category,
                    "description": tx.description,
                    "date": tx.date.isoformat(),
                    "category_avg": round(avg, 2),
                    "deviation_ratio": round(tx.amount / avg, 2) if avg > 0 else 0,
                })

    return {
        "total_transactions_analyzed": len(transactions),
        "anomalies_found": len(anomalies),
        "anomalies": anomalies,
    }