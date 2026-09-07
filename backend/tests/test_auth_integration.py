"""Integration tests for authentication and user isolation."""
import pytest
from httpx import AsyncClient


class TestRegistration:
    """Tests for user registration - Supabase Auth only (local endpoints removed)."""

    async def test_register_returns_404(self, client: AsyncClient):
        response = await client.post(
            "/api/auth/register",
            json={"email": "newuser@example.com", "password": "password123"},
        )
        assert response.status_code == 404

    async def test_duplicate_email_returns_404(self, client: AsyncClient, auth_user: dict):
        response = await client.post(
            "/api/auth/register",
            json={"email": auth_user["email"], "password": "differentpass"},
        )
        assert response.status_code == 404


class TestLogin:
    """Tests for user login - Supabase Auth only (local endpoint removed)."""

    async def test_login_returns_404(self, client: AsyncClient, auth_user: dict):
        response = await client.post(
            "/api/auth/login",
            json={"email": auth_user["email"], "password": "testpassword"},
        )
        assert response.status_code == 404

    async def test_wrong_password_returns_404(self, client: AsyncClient, auth_user: dict):
        response = await client.post(
            "/api/auth/login",
            json={"email": auth_user["email"], "password": "wrongpassword"},
        )
        assert response.status_code == 404


class TestProtectedEndpoints:
    """Tests for protected endpoint access."""

    async def test_protected_endpoint_without_token_returns_401(self, client: AsyncClient):
        response = await client.get("/api/auth/me")
        assert response.status_code == 401

    async def test_me_returns_authenticated_user(self, auth_client: AsyncClient, auth_user: dict):
        response = await auth_client.get("/api/auth/me")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == auth_user["user_id"]
        assert data["email"] == auth_user["email"]


class TestUserIsolation:
    """Tests for cross-user data isolation."""

    async def test_user_a_cannot_read_user_b_account(
        self, auth_client: AsyncClient, second_client: AsyncClient, create_account
    ):
        account = await create_account(name="User A Account")
        response = await second_client.get(f"/api/accounts/{account['id']}")
        assert response.status_code == 404

    async def test_user_a_cannot_update_user_b_account(
        self, auth_client: AsyncClient, second_client: AsyncClient, create_account
    ):
        account = await create_account(name="User A Account")
        response = await second_client.put(
            f"/api/accounts/{account['id']}",
            json={"name": "Hacked"},
        )
        assert response.status_code == 404

    async def test_user_a_cannot_delete_user_b_account(
        self, auth_client: AsyncClient, second_client: AsyncClient, create_account
    ):
        account = await create_account(name="User A Account")
        response = await second_client.delete(f"/api/accounts/{account['id']}")
        assert response.status_code == 404

    async def test_user_a_cannot_read_user_b_transaction(
        self, auth_client: AsyncClient, second_client: AsyncClient, create_account
    ):
        account = await create_account()
        # Create transaction via API as user A
        tx_resp = await auth_client.post(
            "/api/transactions/",
            json={
                "account_id": account["id"],
                "type": "expense",
                "amount": 10.0,
                "category": "Food",
                "description": "Test",
                "date": "2026-01-01T00:00:00",
            },
        )
        assert tx_resp.status_code == 201
        tx_id = tx_resp.json()["id"]
        
        # User B tries to read it
        response = await second_client.get(f"/api/transactions/{tx_id}")
        assert response.status_code == 404

    async def test_user_scoped_list_returns_only_own_accounts(
        self, auth_client: AsyncClient, second_client: AsyncClient, create_account
    ):
        await create_account(name="User A Account")
        await create_account(name="User A Account 2")

        response = await auth_client.get("/api/accounts/")
        assert response.status_code == 200
        accounts = response.json()
        assert len(accounts) == 2
        for acc in accounts:
            assert acc["name"].startswith("User A")

    async def test_user_scoped_list_transactions_only_own(
        self, auth_client: AsyncClient, second_client: AsyncClient, create_account
    ):
        account = await create_account(initial_balance=1000)
        # Create transaction via API
        resp = await auth_client.post(
            "/api/transactions/",
            json={
                "account_id": account["id"],
                "type": "expense",
                "amount": 50.0,
                "category": "Food",
                "description": "Lunch",
                "date": "2026-01-15T12:00:00",
            },
        )
        assert resp.status_code == 201

        response = await second_client.get("/api/transactions/")
        assert response.status_code == 200
        assert len(response.json()) == 0

        response = await auth_client.get("/api/transactions/")
        assert response.status_code == 200
        assert len(response.json()) == 1

    async def test_user_scoped_list_categories_only_own(
        self, auth_client: AsyncClient, second_client: AsyncClient
    ):
        resp = await auth_client.post(
            "/api/categories/",
            json={"name": "Custom Category", "type": "expense"},
        )
        assert resp.status_code == 201

        response = await second_client.get("/api/categories/")
        assert response.status_code == 200
        # Second user should only see default seeded categories
        names = [c["name"] for c in response.json()]
        assert "Custom Category" not in names

    async def test_user_scoped_list_recurring_only_own(
        self, auth_client: AsyncClient, second_client: AsyncClient, create_account
    ):
        account = await create_account()
        # Create a transaction first
        tx_resp = await auth_client.post(
            "/api/transactions/",
            json={
                "account_id": account["id"],
                "type": "expense",
                "amount": 10.0,
                "category": "Food",
                "description": "Recurring",
                "date": "2026-01-01T00:00:00",
            },
        )
        tx_id = tx_resp.json()["id"]

        # Create recurring rule
        rr_resp = await auth_client.post(
            "/api/recurring/",
            json={
                "transaction_id": tx_id,
                "pattern": "monthly",
                "frequency": 1,
                "expected_amount": 10.0,
                "expected_date": "2026-02-01T00:00:00",
            },
        )
        assert rr_resp.status_code == 201

        # Second user should not see it
        response = await second_client.get("/api/recurring/")
        assert response.status_code == 200
        assert len(response.json()) == 0