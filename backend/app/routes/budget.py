"""Budget and recommendations routes — rule-based for v1"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from datetime import datetime, timedelta

from app.db.database import get_db
from app.models import Transaction, Account, User
from app.utils import get_current_user

router = APIRouter()


@router.get("/recommendations")
async def get_budget_recommendations(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Rule-based budget recommendations based on historical category spend vs income."""
    three_months_ago = datetime.utcnow() - timedelta(days=90)

    result = await db.execute(
        select(Transaction).where(
            Transaction.user_id == current_user.id,
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


@router.get("/category-analysis")
async def analyze_category_spending(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Analyze spending by category vs income over the last 3 months."""
    three_months_ago = datetime.utcnow() - timedelta(days=90)

    result = await db.execute(
        select(Transaction).where(
            Transaction.user_id == current_user.id,
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
