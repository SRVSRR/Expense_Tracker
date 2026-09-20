"""Database configuration and session management — lazy engine.

Importing this module no longer requires DATABASE_URL to be set and does
not create any connections. The engine is built on first use (get_engine)
or explicitly via init_engine(), and DATABASE_URL is validated at app
startup in the factory lifespan, preserving fail-fast in production while
allowing `import app.factory` and `pytest` collection with TESTING=1 and no
env file.
"""

from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
import os
from typing import Optional

from app.models import Base

_engine: Optional[AsyncEngine] = None
_SessionLocal: Optional[sessionmaker] = None


def get_database_url() -> str:
    """Resolve DATABASE_URL from env, or raise if missing outside TESTING."""
    url = os.getenv("DATABASE_URL")
    if url:
        return url
    # In tests we allow import without a real DB; conftest overrides get_db
    # with an in-memory SQLite engine. Fail-fast is enforced in factory lifespan.
    if os.getenv("TESTING") == "1":
        # Dummy URL so importing doesn't crash; real engine is never used in tests
        return "sqlite+aiosqlite:///:memory:"
    raise RuntimeError("DATABASE_URL must be set; local SQLite fallback is disabled")


def get_engine() -> AsyncEngine:
    """Get or create the async engine (lazy)."""
    global _engine, _SessionLocal
    if _engine is not None:
        return _engine
    url = get_database_url()
    connect_args: dict = {}
    if url.startswith("postgresql+asyncpg://"):
        # Supabase transaction pooling does not support session-scoped prepared statements.
        connect_args["statement_cache_size"] = 0
    _engine = create_async_engine(url, echo=False, connect_args=connect_args)
    _SessionLocal = sessionmaker(_engine, class_=AsyncSession, expire_on_commit=False)
    return _engine


def get_sessionmaker() -> sessionmaker:
    """Get or create the sessionmaker (ensures engine is initialized)."""
    global _SessionLocal
    if _SessionLocal is not None:
        return _SessionLocal
    get_engine()
    assert _SessionLocal is not None
    return _SessionLocal


# Backwards-compat proxies so `from app.db.database import engine` still works
# but importing the module no longer triggers DATABASE_URL validation or
# connection creation. The proxy delegates to the real engine on first use.


class _LazyEngineProxy:
    def __getattr__(self, name):
        return getattr(get_engine(), name)

    def __call__(self, *args, **kwargs):
        return get_engine()(*args, **kwargs)


class _LazySessionLocalProxy:
    def __call__(self, *args, **kwargs):
        return get_sessionmaker()(*args, **kwargs)

    def __getattr__(self, name):
        return getattr(get_sessionmaker(), name)


engine = _LazyEngineProxy()  # type: ignore
AsyncSessionLocal = _LazySessionLocalProxy()  # type: ignore


async def get_db():
    """Dependency for FastAPI to inject database session (lazy engine)."""
    SessionLocal = get_sessionmaker()
    async with SessionLocal() as session:
        yield session


async def init_db():
    """Initialize database tables (uses lazy engine)."""
    eng = get_engine()
    async with eng.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def dispose_engine():
    """Dispose the engine (called on shutdown)."""
    global _engine, _SessionLocal
    if _engine is not None:
        await _engine.dispose()
        _engine = None
        _SessionLocal = None
