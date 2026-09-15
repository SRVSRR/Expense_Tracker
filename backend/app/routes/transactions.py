"""Transaction management routes"""
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime
from typing import Optional

from app.db.database import get_db
from app.models import Transaction, TransactionType, Account, RecurringRule
from app.schemas import (
    TransactionCreate,
    TransactionUpdate,
    Transaction as TransactionSchema,
    RecurringRuleCreate,
    RecurringPattern,
)
from app.utils import generate_uuid, get_current_user
from app.utils.exceptions import NotFoundError
from app.utils.openapi import ERROR_401, ERROR_404, ERROR_422, ERROR_500
from app.services.prediction_cache import invalidate_predictions

router = APIRouter()


def apply_transaction_balance(
    account: Account,
    transaction_type: TransactionType,
    amount: float,
    multiplier: int = 1,
) -> None:
    """Apply or reverse a transaction amount on its account balance."""
    signed_amount = amount * multiplier
    if transaction_type.value == "expense":
        account.current_balance -= signed_amount
    else:
        account.current_balance += signed_amount


@router.post(
    "/",
    response_model=TransactionSchema,
    status_code=status.HTTP_201_CREATED,
    summary="Create transaction",
    responses={
        201: {"description": "Transaction created successfully"},
        401: ERROR_401,
        404: ERROR_404,
        422: ERROR_422,
        500: ERROR_500,
    },
)
async def create_transaction(
    tx_data: TransactionCreate,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user),
):
    result = await db.execute(
        select(Account).where(
            Account.id == tx_data.account_id, Account.auth_user_id == current_user.id
        )
    )
    account = result.scalar_one_or_none()
    if not account:
        raise NotFoundError(resource="Account", identifier=tx_data.account_id)

    transaction = Transaction(
        id=generate_uuid(),
        auth_user_id=current_user.id,
        account_id=tx_data.account_id,
        type=tx_data.type,
        amount=tx_data.amount,
        category=tx_data.category,
        description=tx_data.description,
        merchant=tx_data.merchant,
        date=tx_data.date,
        is_recurring=tx_data.is_recurring,
    )
    db.add(transaction)

    apply_transaction_balance(account, tx_data.type, tx_data.amount)

    # Auto-create recurring rule if transaction is marked as recurring with required fields
    if tx_data.is_recurring and tx_data.recurring_pattern and tx_data.recurring_frequency and tx_data.recurring_expected_date:
        recurring_rule = RecurringRule(
            id=generate_uuid(),
            auth_user_id=current_user.id,
            transaction_id=transaction.id,
            pattern=tx_data.recurring_pattern,
            frequency=tx_data.recurring_frequency,
            expected_amount=tx_data.amount,
            expected_date=tx_data.recurring_expected_date,
        )
        db.add(recurring_rule)

    await db.commit()
    await db.refresh(transaction)
    await invalidate_predictions(db, current_user.id)
    return transaction


@router.get(
    "/",
    response_model=list[TransactionSchema],
    summary="List transactions",
    responses={
        200: {"description": "List of transactions"},
        401: ERROR_401,
        422: ERROR_422,
        500: ERROR_500,
    },
)
async def list_transactions(
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user),
    account_id: Optional[str] = None,
    type: Optional[str] = None,
    category: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    limit: int = Query(default=50, le=200),
    offset: int = Query(default=0, ge=0),
):
    query = select(Transaction).where(Transaction.auth_user_id == current_user.id)

    if account_id:
        query = query.where(Transaction.account_id == account_id)
    if type:
        query = query.where(Transaction.type == type)
    if category:
        query = query.where(Transaction.category == category)
    if start_date:
        query = query.where(Transaction.date >= start_date)
    if end_date:
        query = query.where(Transaction.date <= end_date)

    query = query.order_by(Transaction.date.desc()).offset(offset).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()


@router.get(
    "/{transaction_id}",
    response_model=TransactionSchema,
    summary="Get transaction",
    responses={
        200: {"description": "Transaction details"},
        401: ERROR_401,
        404: ERROR_404,
        500: ERROR_500,
    },
)
async def get_transaction(
    transaction_id: str,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user),
):
    result = await db.execute(
        select(Transaction).where(
            Transaction.id == transaction_id,
            Transaction.auth_user_id == current_user.id,
        )
    )
    transaction = result.scalar_one_or_none()
    if not transaction:
        raise NotFoundError(resource="Transaction", identifier=transaction_id)
    return transaction


@router.put(
    "/{transaction_id}",
    response_model=TransactionSchema,
    summary="Update transaction",
    responses={
        200: {"description": "Transaction updated successfully"},
        401: ERROR_401,
        404: ERROR_404,
        422: ERROR_422,
        500: ERROR_500,
    },
)
async def update_transaction(
    transaction_id: str,
    tx_data: TransactionUpdate,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user),
):
    result = await db.execute(
        select(Transaction).where(
            Transaction.id == transaction_id,
            Transaction.auth_user_id == current_user.id,
        )
    )
    transaction = result.scalar_one_or_none()
    if not transaction:
        raise NotFoundError(resource="Transaction", identifier=transaction_id)

    update_data = tx_data.model_dump(exclude_unset=True)
    if "amount" in update_data:
        account_result = await db.execute(
            select(Account).where(
                Account.id == transaction.account_id,
                Account.auth_user_id == current_user.id,
            )
        )
        account = account_result.scalar_one_or_none()
        if account is None:
            raise NotFoundError(resource="Account", identifier=transaction.account_id)
        balance_delta = update_data["amount"] - transaction.amount
        apply_transaction_balance(account, transaction.type, balance_delta)
    for field, value in update_data.items():
        setattr(transaction, field, value)

    await db.commit()
    await db.refresh(transaction)
    await invalidate_predictions(db, current_user.id)
    return transaction


@router.delete(
    "/{transaction_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete transaction",
    responses={
        204: {"description": "Transaction deleted successfully"},
        401: ERROR_401,
        404: ERROR_404,
        500: ERROR_500,
    },
)
async def delete_transaction(
    transaction_id: str,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user),
):
    result = await db.execute(
        select(Transaction).where(
            Transaction.id == transaction_id,
            Transaction.auth_user_id == current_user.id,
        )
    )
    transaction = result.scalar_one_or_none()
    if not transaction:
        raise NotFoundError(resource="Transaction", identifier=transaction_id)

    account_result = await db.execute(
        select(Account).where(
            Account.id == transaction.account_id,
            Account.auth_user_id == current_user.id,
        )
    )
    account = account_result.scalar_one_or_none()
    if account is None:
        raise NotFoundError(resource="Account", identifier=transaction.account_id)

    apply_transaction_balance(account, transaction.type, transaction.amount, multiplier=-1)
    await db.delete(transaction)
    await db.commit()
    await invalidate_predictions(db, current_user.id)