"""Authentication routes"""
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import os

from app.db.database import get_db
from app.models import User
from app.schemas import UserCreate, UserLogin, User as UserSchema
from app.utils import (
    generate_uuid,
    get_password_hash,
    verify_password,
    create_access_token,
    get_current_user,
    is_supabase_auth_mode,
)
from app.services.seed import seed_categories
from app.utils.rate_limit import limiter

router = APIRouter()


@router.post("/register", response_model=UserSchema, status_code=status.HTTP_201_CREATED)
@limiter.limit("5/minute")
async def register(request: Request, user_data: UserCreate, db: AsyncSession = Depends(get_db)):
    # Local registration disabled in Supabase Auth mode
    if is_supabase_auth_mode():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Local registration is disabled. Use Supabase Auth for registration.",
        )

    result = await db.execute(select(User).where(User.email == user_data.email))
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )

    user = User(
        id=generate_uuid(),
        email=user_data.email,
    )
    user.password_hash = get_password_hash(user_data.password)
    db.add(user)
    await db.commit()
    await db.refresh(user)

    # Seed default categories for the new user
    await seed_categories(user.id, db)

    return user


@router.post("/login")
@limiter.limit("10/minute")
async def login(request: Request, user_data: UserLogin, db: AsyncSession = Depends(get_db)):
    # Local login disabled in Supabase Auth mode
    if is_supabase_auth_mode():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Local login is disabled. Use Supabase Auth for login.",
        )

    result = await db.execute(select(User).where(User.email == user_data.email))
    user = result.scalar_one_or_none()
    if not user or not verify_password(user_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    access_token = create_access_token(data={"sub": user.id})
    return {"access_token": access_token, "token_type": "bearer", "user_id": user.id}


@router.get("/me", response_model=UserSchema)
async def get_me(current_user: User = Depends(get_current_user)):
    return current_user
