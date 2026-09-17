"""Budget and recommendations routes — rule-based for v1"""
from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from datetime import datetime, timedelta

from app.db.database import get_db
from app.models import Transaction, Account
from app.utils import get_current_user, with_retry
from app.services.prediction_cache import get_cached_prediction, store_prediction
from app.utils.openapi import ERROR_401, ERROR_429, ERROR_500
from app.utils.rate_limit import ANALYTICS_LIMIT, limiter
from app.schemas import BudgetRecommendations, CategoryAnalysis

router = APIRouter()


@with_retry(max_retries=3, base_delay=0.5, max_delay=5.0)
async def _compute_recommendations(db: AsyncSession, user_id: str) -> dict:
    """Compute rule-based budget recommendations."""
    three_months_ago = datetime.utcnow() - timedelta(days=90)

    result = await db.execute(
        select(Transaction).where(
            Transaction.auth_user_id == user_id,
            Transaction.date >= three_months_ago,
        )
    )
    transactions = result.scalars().all()

    total_income = 0
    category_expenses = {}
    for tx in transactions:
        if tx.type.value == "income":
            total_income += tx.amount
        else:
            cat = tx.category
            category_expenses[cat] = category_expenses.get(cat, 0) + tx.amount

    total_expense = sum(category_expenses.values())
    avg_monthly_income = total_income / 3 if total_income > 0 else 0
    avg_monthly_expense = total_expense / 3 if total_expense > 0 else 0

    recommendations = []
    for cat, amount in category_expenses.items():
        monthly_avg = amount / 3
        pct_of_income = (monthly_avg / avg_monthly_income * 100) if avg_monthly_income > 0 else 0

        status_label = "on_track"
        suggested_budget = monthly_avg

        if pct_of_income > 30:
            status_label = "high"
            suggested_budget = monthly_avg * 0.8
        elif pct_of_income > 20:
            status_label = "moderate"
            suggested_budget = monthly_avg * 0.9

        recommendations.append({
            "category": cat,
            "monthly_average": round(monthly_avg, 2),
            "percent_of_income": round(pct_of_income, 1),
            "status": status_label,
            "suggested_budget": round(suggested_budget, 2),
        })

    savings_rate = 0
    if avg_monthly_income > 0:
        savings_rate = round((1 - avg_monthly_expense / avg_monthly_income) * 100, 1)

    return {
        "avg_monthly_income": round(avg_monthly_income, 2),
        "avg_monthly_expense": round(avg_monthly_expense, 2),
        "savings_rate_percent": savings_rate,
        "recommendations": sorted(recommendations, key=lambda x: x["percent_of_income"], reverse=True),
    }


@with_retry(max_retries=3, base_delay=0.5, max_delay=5.0)
async def _compute_category_analysis(db: AsyncSession, user_id: str) -> dict:
    """Compute spending analysis by category."""
    three_months_ago = datetime.utcnow() - timedelta(days=90)

    result = await db.execute(
        select(Transaction).where(
            Transaction.auth_user_id == user_id,
            Transaction.date >= three_months_ago,
        )
    )
    transactions = result.scalars().all()

    category_data = {}
    total_income = 0
    total_expense = 0

    for tx in transactions:
        if tx.type.value == "income":
            total_income += tx.amount
        else:
            cat = tx.category
            if cat not in category_data:
                category_data[cat] = {"total": 0, "count": 0, "transactions": []}
            category_data[cat]["total"] += tx.amount
            category_data[cat]["count"] += 1
            category_data[cat]["transactions"].append({
                "amount": tx.amount,
                "date": tx.date.isoformat(),
                "description": tx.description,
            })
            total_expense += tx.amount

    analysis = []
    for cat, data in category_data.items():
        analysis.append({
            "category": cat,
            "total_spent": round(data["total"], 2),
            "monthly_average": round(data["total"] / 3, 2),
            "transaction_count": data["count"],
            "percent_of_total": round(data["total"] / max(total_expense, 1) * 100, 1),
        })

    return {
        "period": "last_3_months",
        "total_income": round(total_income, 2),
        "total_expense": round(total_expense, 2),
        "net_flow": round(total_income - total_expense, 2),
        "categories": sorted(analysis, key=lambda x: x["total_spent"], reverse=True),
    }


@router.get(
    "/recommendations",
    response_model=BudgetRecommendations,
    summary="Budget recommendations",
    description="Returns rule-based budget caps per category based on historical averages and income percentage. Cached for 7 days.",
    responses={
        200: {"description": "Successful response with budget recommendations"},
        401: ERROR_401,
        429: ERROR_429,
        500: ERROR_500,
    },
)
@limiter.limit(ANALYTICS_LIMIT)
async def get_budget_recommendations(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user),
):
    """Budget recommendations — cached in predictions table (7-day TTL)."""
    cached = await get_cached_prediction(db, current_user.id, "budget")
    if cached:
        return cached

    data = await _compute_recommendations(db, current_user.id)
    await store_prediction(db, current_user.id, "budget", data)
    return data


@router.get(
    "/category-analysis",
    response_model=CategoryAnalysis,
    summary="Category spending analysis",
    description="Returns full spending breakdown by category for the last 3 months. Cached for 7 days.",
    responses={
        200: {"description": "Successful response with category analysis"},
        401: ERROR_401,
        429: ERROR_429,
        500: ERROR_500,
    },
)
@limiter.limit(ANALYTICS_LIMIT)
async def analyze_category_spending(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user),
):
    """Category spending analysis — cached (7-day TTL, same cache key as budget)."""
    cached = await get_cached_prediction(db, current_user.id, "budget_analysis")
    if cached:
        return cached

    data = await _compute_category_analysis(db, current_user.id)
    await store_prediction(db, current_user.id, "budget_analysis", data, ttl_hours=168)
    return data