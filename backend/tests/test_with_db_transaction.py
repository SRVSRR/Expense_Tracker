"""Tests for atomic transaction handling with with_db_transaction / db_transaction."""

import pytest
from sqlalchemy import select

from app.models import Account, Transaction
from app.utils import generate_uuid


@pytest.mark.asyncio
async def test_with_db_transaction_rollback_on_error(db_session, auth_user):
    """Ensure balance + transaction atomically rollback when recurring rule fails."""
    from app.utils import with_db_transaction, db_transaction
    from app.db.database import AsyncSessionLocal

    # Create account directly
    account = Account(
        id=generate_uuid(),
        auth_user_id=auth_user["user_id"],
        name="Test Account",
        currency="USD",
        initial_balance=1000.0,
        current_balance=1000.0,
    )
    db_session.add(account)
    await db_session.commit()
    await db_session.refresh(account)

    account_id = account.id
    initial_balance = account.current_balance

    # Simulate atomic operation that fails after balance mutation
    async def failing_atomic():
        # Mutate balance
        account.current_balance -= 100.0
        db_session.add(account)
        # Add transaction
        tx = Transaction(
            id=generate_uuid(),
            auth_user_id=auth_user["user_id"],
            account_id=account_id,
            type="expense",
            amount=100.0,
            category="Food",
            description="Test",
            merchant="Test",
        )
        db_session.add(tx)
        await db_session.flush()
        # Simulate failure before commit (e.g., recurring rule FK error)
        raise RuntimeError("Simulated recurring rule failure")

    # Use with_db_transaction - should rollback both balance and transaction
    with pytest.raises(RuntimeError):
        await with_db_transaction(db_session, failing_atomic)

    # Need to expire and re-query to see DB state
    await db_session.rollback()
    result = await db_session.execute(select(Account).where(Account.id == account_id))
    refreshed = result.scalar_one()
    # Balance should be unchanged because transaction rolled back
    assert refreshed.current_balance == initial_balance

    # No transaction should exist
    result = await db_session.execute(
        select(Transaction).where(Transaction.auth_user_id == auth_user["user_id"])
    )
    txs = result.scalars().all()
    assert len(txs) == 0


@pytest.mark.asyncio
async def test_db_transaction_context_manager_success(db_session, auth_user):
    """Test db_transaction context manager commits on success."""
    from app.utils import db_transaction

    account = Account(
        id=generate_uuid(),
        auth_user_id=auth_user["user_id"],
        name="Context Test",
        currency="USD",
        initial_balance=500.0,
        current_balance=500.0,
    )
    db_session.add(account)
    await db_session.commit()

    async with db_transaction(db_session):
        account.current_balance += 250.0
        db_session.add(account)
        tx = Transaction(
            id=generate_uuid(),
            auth_user_id=auth_user["user_id"],
            account_id=account.id,
            type="income",
            amount=250.0,
            category="Salary",
            description="Bonus",
            merchant="Employer",
        )
        db_session.add(tx)

    # After commit, verify
    result = await db_session.execute(select(Account).where(Account.id == account.id))
    refreshed = result.scalar_one()
    assert refreshed.current_balance == 750.0

    result = await db_session.execute(
        select(Transaction).where(Transaction.auth_user_id == auth_user["user_id"])
    )
    assert len(result.scalars().all()) == 1


@pytest.mark.asyncio
async def test_db_transaction_context_manager_rollback(db_session, auth_user):
    """Test db_transaction rolls back on exception."""
    from app.utils import db_transaction

    account = Account(
        id=generate_uuid(),
        auth_user_id=auth_user["user_id"],
        name="Rollback Test",
        currency="USD",
        initial_balance=200.0,
        current_balance=200.0,
    )
    db_session.add(account)
    await db_session.commit()
    account_id = account.id

    with pytest.raises(ValueError):
        async with db_transaction(db_session):
            account.current_balance -= 50.0
            db_session.add(account)
            raise ValueError("boom")

    await db_session.rollback()
    result = await db_session.execute(select(Account).where(Account.id == account_id))
    refreshed = result.scalar_one()
    assert refreshed.current_balance == 200.0
