"""Supabase JWT verification using JWKS."""
import os
import httpx
from typing import Optional, Dict, Any
from jose import JWTError, jwt
from jose.utils import base64url_decode
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.database import get_db
from app.models import User

security = HTTPBearer()

_jwks_cache: Optional[Dict[str, Any]] = None


async def get_jwks() -> Dict[str, Any]:
    """Fetch and cache Supabase JWKS."""
    global _jwks_cache
    if _jwks_cache is None:
        supabase_jwks_url = os.getenv("SUPABASE_JWKS_URL")
        if not supabase_jwks_url:
            raise RuntimeError("SUPABASE_JWKS_URL not configured")
        async with httpx.AsyncClient() as client:
            resp = await client.get(supabase_jwks_url, timeout=10.0)
            resp.raise_for_status()
            _jwks_cache = resp.json()
    return _jwks_cache


def get_signing_key(token: str, jwks: Dict[str, Any]) -> str:
    """Extract the signing key from JWKS matching the token's kid."""
    unverified_header = jwt.get_unverified_header(token)
    kid = unverified_header.get("kid")
    if not kid:
        raise JWTError("Token missing kid header")

    for key in jwks.get("keys", []):
        if key.get("kid") == kid:
            # Reconstruct public key from JWK
            from jose.backends import RSAKey
            return RSAKey(key, algorithm="RS256")

    raise JWTError(f"Signing key not found for kid: {kid}")


async def verify_supabase_token(token: str) -> Dict[str, Any]:
    """Verify a Supabase-issued JWT using JWKS."""
    jwks = await get_jwks()
    signing_key = get_signing_key(token, jwks)

    supabase_issuer = os.getenv("SUPABASE_ISSUER")
    if not supabase_issuer:
        raise RuntimeError("SUPABASE_ISSUER not configured")

    payload = jwt.decode(
        token,
        signing_key,
        algorithms=["RS256"],
        audience="authenticated",
        issuer=supabase_issuer,
    )
    return payload


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> User:
    """Get current user from Supabase JWT."""
    token = credentials.credentials
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

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