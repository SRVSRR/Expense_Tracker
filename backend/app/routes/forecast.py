"""Forecasting routes (AI/ML features) — naive implementations for v1"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from datetime import datetime, timedelta

from app.db.database import get_db
from app.models import Transaction, Account
from app.utils import get_current_user
from app.services.prediction_cache import get_cached_prediction, store_prediction
from app.schemas import (
    CashflowForecast,
    RunwayForecast,
    AnomaliesResponse,
)

router = APIRouter()


async def _compute_cashflow(db: AsyncSession, user_id: str, days: int) -> dict:
    """Compute naive cashflow forecast (rolling 3-month average)."""
    three_months_ago = datetime.utcnow() - timedelta(days=90)

    result = await db.execute(
        select(Transaction).where(
            Transaction.auth_user_id == user_id,
            Transaction.date >= three_months_ago,
        )
    )
    transactions = result.scalars().all()

    daily_income = {}
    daily_expense = {}
    for tx in transactions:
        day = tx.date.date()
        if tx.type.value == "income":
            daily_income[day] = daily_income.get(day, 0) + tx.amount
        else:
            daily_expense[day] = daily_expense.get(day, 0) + tx.amount

    num_days = max(len(daily_income), len(daily_expense), 1)
    avg_daily_income = sum(daily_income.values()) / num_days if daily_income else 0
    avg_daily_expense = sum(daily_expense.values()) / num_days if daily_expense else 0

    today = datetime.utcnow().date()
    account_result = await db.execute(
        select(func.sum(Account.current_balance)).where(Account.auth_user_id == user_id)
    )
    running_balance = account_result.scalar() or 0.0

    forecast = []
    for i in range(1, days + 1):
        forecast_date = today + timedelta(days=i)
        running_balance += avg_daily_income - avg_daily_expense
        forecast.append({
            "date": forecast_date.isoformat(),
            "projected_balance": round(running_balance, 2),
            "expected_income": round(avg_daily_income, 2),
            "expected_expense": round(avg_daily_expense, 2),
        })

    return {
        "period_days": days,
        "avg_daily_income": round(avg_daily_income, 2),
        "avg_daily_expense": round(avg_daily_expense, 2),
        "forecast": forecast,
    }


async def _compute_runway(db: AsyncSession, user_id: str, threshold: float) -> dict:
    """Compute naive runway prediction."""
    three_months_ago = datetime.utcnow() - timedelta(days=90)

    result = await db.execute(
        select(Transaction).where(
            Transaction.auth_user_id == user_id,
            Transaction.date >= three_months_ago,
        )
    )
    transactions = result.scalars().all()

    daily_expense = {}
    daily_income = {}
    for tx in transactions:
        day = tx.date.date()
        if tx.type.value == "expense":
            daily_expense[day] = daily_expense.get(day, 0) + tx.amount
        else:
            daily_income[day] = daily_income.get(day, 0) + tx.amount

    num_days = max(len(daily_expense), len(daily_income), 1)
    avg_daily_expense = sum(daily_expense.values()) / num_days if daily_expense else 0
    avg_daily_income = sum(daily_income.values()) / num_days if daily_income else 0
    net_daily_burn = avg_daily_expense - avg_daily_income

    account_result = await db.execute(
        select(func.sum(Account.current_balance)).where(Account.auth_user_id == user_id)
    )
    current_balance = account_result.scalar() or 0.0

    if net_daily_burn <= 0:
        days_remaining = None
    else:
        days_remaining = max(0, int((current_balance - threshold) / net_daily_burn))

    return {
        "current_balance": round(current_balance, 2),
        "avg_daily_income": round(avg_daily_income, 2),
        "avg_daily_expense": round(avg_daily_expense, 2),
        "net_daily_burn": round(net_daily_burn, 2),
        "threshold": threshold,
        "days_until_threshold": days_remaining,
    }


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


@router.get(
    "/cashflow",
    response_model=CashflowForecast,
    summary="Cash flow forecast",
    description="Returns a rolling 3-month average cash flow forecast for the specified number of days. Cached for 24 hours.",
    responses={
        200: {"description": "Successful response with forecast data"},
        401: {"description": "Unauthorized - invalid or missing token"},
    },
)
async def get_cashflow_forecast(
    days: int = Query(default=30, ge=7, le=365, description="Number of days to forecast"),
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user),
):
    """Cash flow forecast — cached in predictions table (24h TTL)."""
    cached = await get_cached_prediction(db, current_user.id, "cashflow")
    if cached and cached.get("period_days") == days:
        return cached

    data = await _compute_cashflow(db, current_user.id, days)
    await store_prediction(db, current_user.id, "cashflow", data)
    return data


@router.get(
    "/runway",
    response_model=RunwayForecast,
    summary="Runway prediction",
    description="Computes days until balance hits a threshold based on net daily burn rate. Cached for 12 hours.",
    responses={
        200: {"description": "Successful response with runway data"},
        401: {"description": "Unauthorized - invalid or missing token"},
    },
)
async def get_runway_forecast(
    threshold: float = Query(default=0.0, description="Balance threshold (default 0)"),
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user),
):
    """Runway prediction — cached in predictions table (12h TTL)."""
    cached = await get_cached_prediction(db, current_user.id, "runway")
    if cached and cached.get("threshold") == threshold:
        return cached

    data = await _compute_runway(db, current_user.id, threshold)
    await store_prediction(db, current_user.id, "runway", data)
    return data


@router.get(
    "/anomalies",
    response_model=AnomaliesResponse,
    summary="Anomaly detection",
    description="Detects per-category expense outliers (>2x category average). Cached for 24 hours.",
    responses={
        200: {"description": "Successful response with anomaly data"},
        401: {"description": "Unauthorized - invalid or missing token"},
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