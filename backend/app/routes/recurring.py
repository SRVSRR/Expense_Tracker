"""Recurring rules routes"""
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime, timedelta
from typing import List

from app.db.database import get_db
from app.models import RecurringRule, Transaction, Account
from app.schemas import (
    RecurringRuleCreate,
    RecurringRule as RecurringRuleSchema,
    RecurringUpcomingItem,
)
from app.utils import generate_uuid, get_current_user
from app.services.prediction_cache import invalidate_predictions

router = APIRouter()


@router.post(
    "/",
    response_model=RecurringRuleSchema,
    status_code=status.HTTP_201_CREATED,
    summary="Create recurring rule",
    description="Creates a recurring rule linked to a transaction. The transaction must belong to the current user.",
    responses={
        201: {"description": "Recurring rule created successfully"},
        401: {"description": "Unauthorized - invalid or missing token"},
        404: {"description": "Transaction not found or not owned by user"},
    },
)
async def create_recurring_rule(
    data: RecurringRuleCreate,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user),
):
    if data.transaction_id:
        transaction_result = await db.execute(
            select(Transaction).where(
                Transaction.id == data.transaction_id,
                Transaction.auth_user_id == current_user.id,
            )
        )
        if transaction_result.scalar_one_or_none() is None:
            raise HTTPException(status_code=404, detail="Transaction not found")

    rule = RecurringRule(
        id=generate_uuid(),
        auth_user_id=current_user.id,
        transaction_id=data.transaction_id,
        pattern=data.pattern,
        frequency=data.frequency,
        expected_amount=data.expected_amount,
        expected_date=data.expected_date,
    )
    db.add(rule)
    await db.commit()
    await db.refresh(rule)
    await invalidate_predictions(db, current_user.id)
    return rule


@router.get(
    "/",
    response_model=List[RecurringRuleSchema],
    summary="List recurring rules",
    description="Returns all recurring rules for the current user, ordered by expected date.",
    responses={
        200: {"description": "List of recurring rules"},
        401: {"description": "Unauthorized - invalid or missing token"},
    },
)
async def list_recurring_rules(
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user),
):
    result = await db.execute(
        select(RecurringRule)
        .where(RecurringRule.auth_user_id == current_user.id)
        .order_by(RecurringRule.expected_date.asc())
    )
    return result.scalars().all()


@router.get(
    "/upcoming",
    response_model=List[RecurringUpcomingItem],
    summary="Upcoming recurring transactions",
    description="Returns expanded upcoming occurrences for all recurring rules within the specified day range.",
    responses={
        200: {"description": "List of upcoming transaction occurrences"},
        401: {"description": "Unauthorized - invalid or missing token"},
    },
)
async def get_upcoming_transactions(
    days: int = Query(default=30, ge=1, le=365, description="Number of days to look ahead"),
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user),
):
    now = datetime.utcnow()
    end = now + timedelta(days=days)

    result = await db.execute(
        select(RecurringRule)
        .where(
            RecurringRule.auth_user_id == current_user.id,
            RecurringRule.expected_date >= now,
            RecurringRule.expected_date <= end,
        )
        .order_by(RecurringRule.expected_date.asc())
    )
    rules = result.scalars().all()

    upcoming = []
    for rule in rules:
        occurrences = _generate_occurrences(rule, now, end)
        for occ_date in occurrences:
            upcoming.append({
                "id": f"{rule.id}_{occ_date.isoformat()}",
                "rule_id": rule.id,
                "pattern": rule.pattern,
                "frequency": rule.frequency,
                "expected_amount": rule.expected_amount,
                "expected_date": occ_date.isoformat(),
                "transaction_id": rule.transaction_id,
            })

    upcoming.sort(key=lambda x: x["expected_date"])
    return upcoming


def _generate_occurrences(rule, start: datetime, end: datetime) -> List[datetime]:
    """Generate all expected dates for a recurring rule within a date range."""
    occurrences = []
    current = rule.expected_date
    pattern = rule.pattern
    freq = rule.frequency

    # If the expected_date is in the future and within range, include it
    if start <= current <= end:
        occurrences.append(current)

    # Generate future occurrences from the expected_date
    while current <= end:
        if pattern == "daily":
            current += timedelta(days=freq)
        elif pattern == "weekly":
            current += timedelta(weeks=freq)
        elif pattern == "biweekly":
            current += timedelta(weeks=2 * freq)
        elif pattern == "monthly":
            current = _add_months(current, freq)
        elif pattern == "quarterly":
            current = _add_months(current, 3 * freq)
        elif pattern == "yearly":
            current = current.replace(year=current.year + freq)
        else:
            break

        if start <= current <= end:
            occurrences.append(current)

    return occurrences


def _add_months(dt: datetime, months: int) -> datetime:
    """Add a number of months to a datetime, clamping the day to the target month."""
    month = dt.month + months
    year = dt.year + (month - 1) // 12
    month = (month - 1) % 12 + 1
    day = min(dt.day, _days_in_month(year, month))
    return dt.replace(year=year, month=month, day=day)


def _days_in_month(year: int, month: int) -> int:
    import calendar
    return calendar.monthrange(year, month)[1]


@router.delete("/{rule_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_recurring_rule(
    rule_id: str,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user),
):
    result = await db.execute(
        select(RecurringRule).where(
            RecurringRule.id == rule_id,
            RecurringRule.auth_user_id == current_user.id,
        )
    )
    rule = result.scalar_one_or_none()
    if not rule:
        raise HTTPException(status_code=404, detail="Recurring rule not found")

    await db.delete(rule)
    await db.commit()
    await invalidate_predictions(db, current_user.id)