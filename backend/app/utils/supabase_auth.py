"""Supabase JWT verification using JWKS."""
import asyncio
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
from app.utils.circuit_breaker import circuit_breaker, supabase_jwks_breaker
from app.utils.exceptions import ExternalServiceError

security = HTTPBearer()

_jwks_cache: Optional[Dict[str, Any]] = None
_jwks_lock = asyncio.Lock()


@circuit_breaker(supabase_jwks_breaker)
async def _fetch_jwks(url: str) -> Dict[str, Any]:
    """Fetch JWKS from Supabase with circuit-breaker protection.
    
    Called only on cache miss. Failures count toward breaker threshold and
    are wrapped as ExternalServiceError (503) for the global handler.
    """
    async with httpx.AsyncClient() as client:
        resp = await client.get(url, timeout=10.0)
        resp.raise_for_status()
        return resp.json()


async def get_jwks() -> Dict[str, Any]:
    """Fetch and cache Supabase JWKS with breaker and thundering-herd protection."""
    global _jwks_cache
    if _jwks_cache is not None:
        return _jwks_cache

    async with _jwks_lock:
        # Double-check after acquiring lock
        if _jwks_cache is not None:
            return _jwks_cache

        supabase_jwks_url = os.getenv("SUPABASE_JWKS_URL")
        if not supabase_jwks_url:
            raise RuntimeError("SUPABASE_JWKS_URL not configured")
        try:
            _jwks_cache = await _fetch_jwks(supabase_jwks_url)
        except ExternalServiceError:
            raise
        except httpx.HTTPError as exc:
            # Fallback wrap if breaker didn't catch (should be 503)
            raise ExternalServiceError(service="supabase", message=str(exc)) from exc
    return _jwks_cache


def _clear_jwks_cache() -> None:
    """Clear JWKS cache and reset breaker (for tests)."""
    global _jwks_cache
    _jwks_cache = None
    supabase_jwks_breaker.reset()


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