"""Test configuration and fixtures for integration tests."""
import sys
from pathlib import Path
from typing import AsyncGenerator
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

backend_directory = Path(__file__).parents[1]
if str(backend_directory) not in sys.path:
    sys.path.insert(0, str(backend_directory))

from main import app
from app.db.database import get_db, Base
from app.models import User
from app.utils import generate_uuid, get_password_hash, create_access_token


TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

test_engine = create_async_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)


async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
    async with TestingSessionLocal() as session:
        yield session


@pytest_asyncio.fixture(scope="function")
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Create a fresh database session for each test."""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async with TestingSessionLocal() as session:
        yield session
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture(scope="function")
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Create an AsyncClient with the test database overridden."""
    app.dependency_overrides[get_db] = lambda: db_session
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test", follow_redirects=True) as ac:
        yield ac
    app.dependency_overrides.clear()


# Enable asyncio mode for pytest-asyncio
pytestmark = pytest.mark.asyncio


@pytest.fixture
def auth_headers() -> dict:
    """Helper to create auth headers from a token."""
    def _make(token: str) -> dict:
        return {"Authorization": f"Bearer {token}"}
    return _make


@pytest_asyncio.fixture
async def register_user(client: AsyncClient) -> dict:
    """Register a new user and return user data + token."""
    async def _register(email: str = "test@example.com", password: str = "password123"):
        response = await client.post(
            "/api/auth/register",
            json={"email": email, "password": password},
        )
        assert response.status_code == 201, f"Registration failed: {response.text}"
        user_data = response.json()
        # Login to get token
        login_response = await client.post(
            "/api/auth/login",
            json={"email": email, "password": password},
        )
        assert login_response.status_code == 200
        token = login_response.json()["access_token"]
        return {"user": user_data, "token": token, "email": email, "password": password}
    return _register


@pytest_asyncio.fixture
async def create_user_direct(db_session: AsyncSession) -> callable:
    """Create a user directly in the database (bypassing API)."""
    async def _create(email: str = "test@example.com", password: str = "password123"):
        user = User(
            id=generate_uuid(),
            email=email,
            password_hash=get_password_hash(password),
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)
        token = create_access_token(data={"sub": user.id})
        return {"user": user, "token": token, "email": email, "password": password}
    return _create


@pytest_asyncio.fixture
async def auth_user(client: AsyncClient, register_user) -> dict:
    """Create and authenticate a user via API."""
    return await register_user()


@pytest_asyncio.fixture
async def second_user(client: AsyncClient, register_user) -> dict:
    """Create a second authenticated user."""
    return await register_user(email="other@example.com", password="password123")


@pytest_asyncio.fixture
async def auth_client(db_session: AsyncSession, auth_user: dict) -> AsyncGenerator[AsyncClient, None]:
    """Return a client with auth headers pre-set."""
    app.dependency_overrides[get_db] = lambda: db_session
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test", follow_redirects=True, headers={"Authorization": f"Bearer {auth_user['token']}"}) as ac:
        yield ac
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def second_client(db_session: AsyncSession, second_user: dict) -> AsyncGenerator[AsyncClient, None]:
    """Return a client authenticated as the second user."""
    app.dependency_overrides[get_db] = lambda: db_session
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test", follow_redirects=True, headers={"Authorization": f"Bearer {second_user['token']}"}) as ac:
        yield ac
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def create_account(auth_client: AsyncClient) -> callable:
    """Create an account for the authenticated user via API."""
    async def _create(name: str = "Test Account", initial_balance: float = 100.0):
        response = await auth_client.post(
            "/api/accounts/",
            json={"name": name, "initial_balance": initial_balance},
        )
        assert response.status_code == 201, f"Account creation failed: {response.text}"
        return response.json()
    return _create


@pytest_asyncio.fixture
async def create_account_second(second_client: AsyncClient) -> callable:
    """Create an account for the second authenticated user via API."""
    async def _create(name: str = "Test Account", initial_balance: float = 100.0):
        response = await second_client.post(
            "/api/accounts/",
            json={"name": name, "initial_balance": initial_balance},
        )
        assert response.status_code == 201, f"Account creation failed: {response.text}"
        return response.json()
    return _create


@pytest_asyncio.fixture
async def create_account_direct(db_session: AsyncSession, auth_user: dict) -> callable:
    """Create an account directly in the database for the authenticated user."""
    from app.models import Account
    async def _create(name: str = "Test Account", initial_balance: float = 100.0):
        account = Account(
            id=generate_uuid(),
            user_id=auth_user["user"]["id"],
            name=name,
            currency="USD",
            initial_balance=initial_balance,
            current_balance=initial_balance,
        )
        db_session.add(account)
        await db_session.commit()
        await db_session.refresh(account)
        return account
    return _create