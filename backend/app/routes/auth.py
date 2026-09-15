"""Authentication routes - Supabase Auth only"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.database import get_db
from app.models import User
from app.schemas import User as UserSchema
from app.utils import get_current_user
from app.utils.openapi import ERROR_401

router = APIRouter()


@router.get(
    "/me",
    response_model=UserSchema,
    summary="Get current user",
    description="Returns the authenticated user's profile. Registration and login are handled by Supabase Auth.",
    responses={
        200: {"description": "Current user profile"},
        401: ERROR_401,
    },
)
async def get_me(current_user: User = Depends(get_current_user)):
    return current_user