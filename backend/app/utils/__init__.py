"""Utility functions"""
from datetime import datetime, timedelta
from typing import Optional, Callable, TypeVar, Any
from functools import wraps
import asyncio

from jose import JWTError, jwt
import bcrypt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError, OperationalError
import os
import uuid

from app.db.database import get_db
from app.models import User
from app.utils.supabase_auth import verify_supabase_token

security = HTTPBearer()

# For tests - local JWT creation (HS256)
SECRET_KEY = os.getenv("SECRET_KEY", "your-super-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "1440"))

# TESTING mode for local JWT verification in tests
TESTING = os.getenv("TESTING") == "1"


T = TypeVar("T")


def generate_uuid() -> str:
    return str(uuid.uuid4())


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))


def get_password_hash(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a local JWT token (for testing only)."""
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def with_retry(
    max_retries: int = 3,
    base_delay: float = 0.5,
    max_delay: float = 5.0,
    exceptions: tuple = (OperationalError,),
):
    """Decorator for retrying async database operations with exponential backoff."""
    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            last_exception = None
            for attempt in range(max_retries + 1):
                try:
                    return await func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt < max_retries:
                        delay = min(base_delay * (2 ** attempt), max_delay)
                        await asyncio.sleep(delay)
                    else:
                        raise
            raise last_exception
        return wrapper
    return decorator


async def with_db_transaction(db: AsyncSession, func: Callable[..., T]) -> T:
    """
    Execute a function within a database transaction with automatic rollback on error.
    """
    async with db.begin():
        try:
            result = await func()
            return result
        except Exception:
            # The transaction will be rolled back automatically when exiting the context
            raise


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> User:
    token = credentials.credentials
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if TESTING:
        # Local JWT verification for tests (HS256)
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            user_id: str = payload.get("sub")
            if user_id is None:
                raise credentials_exception
        except JWTError:
            raise credentials_exception
    else:
        # Supabase JWT verification (RS256 via JWKS)
        try:
            payload = await verify_supabase_token(token)
            user_id: str = payload.get("sub")
            if user_id is None:
                raise credentials_exception
        except JWTError:
            raise credentials_exception

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None:
        raise credentials_exception
    return user