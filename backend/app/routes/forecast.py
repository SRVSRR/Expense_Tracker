"""Forecasting routes (AI/ML features) — naive implementations for v1"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from datetime import datetime, timedelta
from typing import Optional

from app.db.database import get_db
from app.models import Transaction, Account, User
from app.utils import get_current_user

router = APIRouter()


@router.get("/cashflow")
async def get_cashflow_forecast(
    days: int = Query(default=30, ge=7, le=365),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Naive cash flow forecast: rolling 3-month average applied forward."""
    three_months_ago = datetime.utcnow() - timedelta(days=90)

    result = await db.execute(
        select(Transaction).where(
            Transaction.user_id == current_user.id,
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

    forecast = []
    today = datetime.utcnow().date()
    account_result = await db.execute(
        select(func.sum(Account.current_balance)).where(Account.user_id == current_user.id)
    )
    running_balance = account_result.scalar() or 0.0

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


@router.get("/runway")
async def get_runway_forecast(
    threshold: float = Query(default=0.0, description="Balance threshold"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Predict days until balance hits threshold based on current spending trend."""
    three_months_ago = datetime.utcnow() - timedelta(days=90)

    result = await db.execute(
        select(Transaction).where(
            Transaction.user_id == current_user.id,
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
        select(func.sum(Account.current_balance)).where(Account.user_id == current_user.id)
    )
    current_balance = account_result.scalar() or 0.0

    if net_daily_burn <= 0:
        days_remaining = None  # Not spending more than earning
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


@router.get("/anomalies")
async def detect_anomalies(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Simple anomaly detection: flag transactions > 2x category average (IQR method)."""
    result = await db.execute(
        select(Transaction).where(Transaction.user_id == current_user.id)
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
