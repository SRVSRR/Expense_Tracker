"""Account management routes"""
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.database import get_db
from app.models import Account
from app.schemas import AccountCreate, AccountUpdate, Account as AccountSchema
from app.utils import generate_uuid, get_current_user
from app.utils.exceptions import NotFoundError
from app.utils.openapi import ERROR_401, ERROR_404, ERROR_422, ERROR_500
from app.services.prediction_cache import invalidate_predictions

router = APIRouter()


@router.post(
    "/",
    response_model=AccountSchema,
    status_code=status.HTTP_201_CREATED,
    summary="Create account",
    responses={
        201: {"description": "Account created successfully"},
        401: ERROR_401,
        422: ERROR_422,
        500: ERROR_500,
    },
)
async def create_account(
    account_data: AccountCreate,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user),
):
    account = Account(
        id=generate_uuid(),
        auth_user_id=current_user.id,
        name=account_data.name,
        currency=account_data.currency,
        initial_balance=account_data.initial_balance,
        current_balance=account_data.initial_balance,
    )
    db.add(account)
    await db.commit()
    await db.refresh(account)
    await invalidate_predictions(db, current_user.id)
    return account


@router.get(
    "/",
    response_model=list[AccountSchema],
    summary="List accounts",
    responses={
        200: {"description": "List of accounts"},
        401: ERROR_401,
        500: ERROR_500,
    },
)
async def list_accounts(
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user),
):
    result = await db.execute(
        select(Account).where(Account.auth_user_id == current_user.id)
    )
    return result.scalars().all()


@router.get(
    "/{account_id}",
    response_model=AccountSchema,
    summary="Get account",
    responses={
        200: {"description": "Account details"},
        401: ERROR_401,
        404: ERROR_404,
        500: ERROR_500,
    },
)
async def get_account(
    account_id: str,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user),
):
    result = await db.execute(
        select(Account).where(
            Account.id == account_id, Account.auth_user_id == current_user.id
        )
    )
    account = result.scalar_one_or_none()
    if not account:
        raise NotFoundError(resource="Account", identifier=account_id)
    return account


@router.put(
    "/{account_id}",
    response_model=AccountSchema,
    summary="Update account",
    responses={
        200: {"description": "Account updated successfully"},
        401: ERROR_401,
        404: ERROR_404,
        422: ERROR_422,
        500: ERROR_500,
    },
)
async def update_account(
    account_id: str,
    account_data: AccountUpdate,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user),
):
    result = await db.execute(
        select(Account).where(
            Account.id == account_id, Account.auth_user_id == current_user.id
        )
    )
    account = result.scalar_one_or_none()
    if not account:
        raise NotFoundError(resource="Account", identifier=account_id)

    update_data = account_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(account, field, value)

    await db.commit()
    await db.refresh(account)
    await invalidate_predictions(db, current_user.id)
    return account


@router.delete(
    "/{account_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete account",
    responses={
        204: {"description": "Account deleted successfully"},
        401: ERROR_401,
        404: ERROR_404,
        500: ERROR_500,
    },
)
async def delete_account(
    account_id: str,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user),
):
    result = await db.execute(
        select(Account).where(
            Account.id == account_id, Account.auth_user_id == current_user.id
        )
    )
    account = result.scalar_one_or_none()
    if not account:
        raise NotFoundError(resource="Account", identifier=account_id)

    await db.delete(account)
    await db.commit()
    await invalidate_predictions(db, current_user.id)
