"""Integration tests for account, transaction, category, and recurring CRUD."""
import pytest
from httpx import AsyncClient
from datetime import datetime, timedelta


class TestAccountCRUD:
    """Tests for account CRUD operations."""

    async def test_error_response_envelope(self, auth_client: AsyncClient):
        response = await auth_client.get("/api/accounts/missing-account")
        assert response.status_code == 404
        body = response.json()
        assert body["error"]["code"] == "NOT_FOUND"
        assert "message" in body["error"]
        assert isinstance(body["error"]["details"], dict)

    async def test_create_account_with_initial_balance(self, auth_client: AsyncClient):
        response = await auth_client.post(
            "/api/accounts",
            json={"name": "Checking", "initial_balance": 500.0},
        )
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Checking"
        assert data["initial_balance"] == 500.0
        assert data["current_balance"] == 500.0
        assert data["currency"] == "USD"
        assert "id" in data

    async def test_list_accounts(self, auth_client: AsyncClient, create_account):
        await create_account(name="Account 1", initial_balance=100.0)
        await create_account(name="Account 2", initial_balance=200.0)

        response = await auth_client.get("/api/accounts")
        assert response.status_code == 200
        accounts = response.json()
        assert len(accounts) == 2

    async def test_get_account(self, auth_client: AsyncClient, create_account):
        account = await create_account(name="Savings", initial_balance=1000.0)
        response = await auth_client.get(f"/api/accounts/{account['id']}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == account["id"]
        assert data["name"] == "Savings"

    async def test_update_account_allowed_fields(self, auth_client: AsyncClient, create_account):
        account = await create_account(name="Old Name", initial_balance=100.0)
        response = await auth_client.put(
            f"/api/accounts/{account['id']}",
            json={"name": "New Name", "currency": "EUR"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "New Name"
        assert data["currency"] == "EUR"
        assert data["current_balance"] == 100.0

    async def test_delete_account(self, auth_client: AsyncClient, create_account):
        account = await create_account(name="To Delete", initial_balance=100.0)
        response = await auth_client.delete(f"/api/accounts/{account['id']}")
        assert response.status_code == 204

        response = await auth_client.get(f"/api/accounts/{account['id']}")
        assert response.status_code == 404

    async def test_account_ownership_check(self, auth_client: AsyncClient, second_client: AsyncClient, create_account):
        account = await create_account(name="Private", initial_balance=100.0)
        response = await second_client.get(f"/api/accounts/{account['id']}")
        assert response.status_code == 404


class TestTransactionCRUD:
    """Tests for transaction CRUD and balance effects."""

    async def test_create_income_transaction(self, auth_client: AsyncClient, create_account):
        account = await create_account(initial_balance=100.0)
        response = await auth_client.post(
            "/api/transactions/",
            json={
                "account_id": account["id"],
                "type": "income",
                "amount": 500.0,
                "category": "Salary",
                "description": "Monthly pay",
                "date": "2026-01-15T12:00:00",
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["type"] == "income"
        assert data["amount"] == 500.0

        # Verify balance updated
        acc_resp = await auth_client.get(f"/api/accounts/{account['id']}")
        assert acc_resp.json()["current_balance"] == 600.0

    async def test_create_expense_transaction(self, auth_client: AsyncClient, create_account):
        account = await create_account(initial_balance=500.0)
        response = await auth_client.post(
            "/api/transactions/",
            json={
                "account_id": account["id"],
                "type": "expense",
                "amount": 50.0,
                "category": "Food",
                "description": "Groceries",
                "date": "2026-01-15T12:00:00",
            },
        )
        assert response.status_code == 201

        acc_resp = await auth_client.get(f"/api/accounts/{account['id']}")
        assert acc_resp.json()["current_balance"] == 450.0

    async def test_reject_non_positive_amount(self, auth_client: AsyncClient, create_account):
        account = await create_account(initial_balance=100.0)
        response = await auth_client.post(
            "/api/transactions/",
            json={
                "account_id": account["id"],
                "type": "expense",
                "amount": 0,
                "category": "Food",
                "description": "Free",
                "date": "2026-01-15T12:00:00",
            },
        )
        assert response.status_code == 422

        response = await auth_client.post(
            "/api/transactions/",
            json={
                "account_id": account["id"],
                "type": "expense",
                "amount": -10.0,
                "category": "Food",
                "description": "Negative",
                "date": "2026-01-15T12:00:00",
            },
        )
        assert response.status_code == 422

    async def test_list_transactions_with_filters(self, auth_client: AsyncClient, create_account):
        account = await create_account(initial_balance=1000.0)
        # Create various transactions
        await auth_client.post(
            "/api/transactions/",
            json={"account_id": account["id"], "type": "income", "amount": 1000.0, "category": "Salary", "description": "Pay", "date": "2026-01-01T12:00:00"},
        )
        await auth_client.post(
            "/api/transactions/",
            json={"account_id": account["id"], "type": "expense", "amount": 50.0, "category": "Food", "description": "Lunch", "date": "2026-01-15T12:00:00"},
        )
        await auth_client.post(
            "/api/transactions/",
            json={"account_id": account["id"], "type": "expense", "amount": 30.0, "category": "Transport", "description": "Bus", "date": "2026-01-20T12:00:00"},
        )

        # Filter by type
        resp = await auth_client.get("/api/transactions/", params={"type": "expense"})
        assert resp.status_code == 200
        assert len(resp.json()) == 2

        # Filter by category
        resp = await auth_client.get("/api/transactions/", params={"category": "Food"})
        assert resp.status_code == 200
        assert len(resp.json()) == 1

        # Filter by date range
        resp = await auth_client.get("/api/transactions/", params={"start_date": "2026-01-10T00:00:00"})
        assert resp.status_code == 200
        assert len(resp.json()) == 2

        # Pagination
        resp = await auth_client.get("/api/transactions/", params={"limit": 2, "offset": 0})
        assert resp.status_code == 200
        assert len(resp.json()) == 2
        resp = await auth_client.get("/api/transactions/", params={"limit": 2, "offset": 2})
        assert resp.status_code == 200
        assert len(resp.json()) == 1

    async def test_get_transaction(self, auth_client: AsyncClient, create_account):
        account = await create_account(initial_balance=100.0)
        create_resp = await auth_client.post(
            "/api/transactions/",
            json={"account_id": account["id"], "type": "expense", "amount": 25.0, "category": "Food", "description": "Test", "date": "2026-01-15T12:00:00"},
        )
        tx_id = create_resp.json()["id"]

        response = await auth_client.get(f"/api/transactions/{tx_id}")
        assert response.status_code == 200
        assert response.json()["id"] == tx_id

    async def test_update_transaction_amount_adjusts_balance(self, auth_client: AsyncClient, create_account):
        account = await create_account(initial_balance=100.0)
        create_resp = await auth_client.post(
            "/api/transactions/",
            json={"account_id": account["id"], "type": "expense", "amount": 20.0, "category": "Food", "description": "Test", "date": "2026-01-15T12:00:00"},
        )
        tx_id = create_resp.json()["id"]

        # Balance should be 80.0
        acc_resp = await auth_client.get(f"/api/accounts/{account['id']}")
        assert acc_resp.json()["current_balance"] == 80.0

        # Update amount from 20 to 30 (delta = +10 expense)
        response = await auth_client.put(
            f"/api/transactions/{tx_id}",
            json={"amount": 30.0},
        )
        assert response.status_code == 200
        assert response.json()["amount"] == 30.0

        # Balance should be 70.0 (100 - 30)
        acc_resp = await auth_client.get(f"/api/accounts/{account['id']}")
        assert acc_resp.json()["current_balance"] == 70.0

    async def test_update_transaction_metadata_no_balance_change(self, auth_client: AsyncClient, create_account):
        account = await create_account(initial_balance=100.0)
        create_resp = await auth_client.post(
            "/api/transactions/",
            json={"account_id": account["id"], "type": "expense", "amount": 20.0, "category": "Food", "description": "Original", "date": "2026-01-15T12:00:00"},
        )
        tx_id = create_resp.json()["id"]

        response = await auth_client.put(
            f"/api/transactions/{tx_id}",
            json={"description": "Updated", "category": "Shopping"},
        )
        assert response.status_code == 200
        assert response.json()["description"] == "Updated"
        assert response.json()["category"] == "Shopping"

        # Balance unchanged
        acc_resp = await auth_client.get(f"/api/accounts/{account['id']}")
        assert acc_resp.json()["current_balance"] == 80.0

    async def test_type_and_account_id_immutable_in_update(self, auth_client: AsyncClient, create_account):
        """Verify that type and account_id are not accepted in PUT /transactions/{id}."""
        account = await create_account(initial_balance=100.0)
        other_account = await create_account(name="Other", initial_balance=0.0)
        create_resp = await auth_client.post(
            "/api/transactions/",
            json={"account_id": account["id"], "type": "expense", "amount": 20.0, "category": "Food", "description": "Test", "date": "2026-01-15T12:00:00"},
        )
        tx_id = create_resp.json()["id"]

        # Attempt to change type - should be ignored or rejected
        response = await auth_client.put(
            f"/api/transactions/{tx_id}",
            json={"type": "income"},
        )
        # Current implementation ignores unknown fields, so it should succeed but not change type
        assert response.status_code == 200
        assert response.json()["type"] == "expense"

        # Attempt to change account_id - should be ignored
        response = await auth_client.put(
            f"/api/transactions/{tx_id}",
            json={"account_id": other_account["id"]},
        )
        assert response.status_code == 200
        assert response.json()["account_id"] == account["id"]

    async def test_delete_income_transaction_reverses_balance(self, auth_client: AsyncClient, create_account):
        account = await create_account(initial_balance=100.0)
        create_resp = await auth_client.post(
            "/api/transactions/",
            json={"account_id": account["id"], "type": "income", "amount": 200.0, "category": "Salary", "description": "Pay", "date": "2026-01-15T12:00:00"},
        )
        tx_id = create_resp.json()["id"]

        # Balance should be 300.0
        acc_resp = await auth_client.get(f"/api/accounts/{account['id']}")
        assert acc_resp.json()["current_balance"] == 300.0

        response = await auth_client.delete(f"/api/transactions/{tx_id}")
        assert response.status_code == 204

        # Balance should revert to 100.0
        acc_resp = await auth_client.get(f"/api/accounts/{account['id']}")
        assert acc_resp.json()["current_balance"] == 100.0

    async def test_delete_expense_transaction_reverses_balance(self, auth_client: AsyncClient, create_account):
        account = await create_account(initial_balance=100.0)
        create_resp = await auth_client.post(
            "/api/transactions/",
            json={"account_id": account["id"], "type": "expense", "amount": 30.0, "category": "Food", "description": "Test", "date": "2026-01-15T12:00:00"},
        )
        tx_id = create_resp.json()["id"]

        acc_resp = await auth_client.get(f"/api/accounts/{account['id']}")
        assert acc_resp.json()["current_balance"] == 70.0

        response = await auth_client.delete(f"/api/transactions/{tx_id}")
        assert response.status_code == 204

        acc_resp = await auth_client.get(f"/api/accounts/{account['id']}")
        assert acc_resp.json()["current_balance"] == 100.0

    async def test_missing_account_returns_404(self, auth_client: AsyncClient):
        response = await auth_client.post(
            "/api/transactions/",
            json={"account_id": "nonexistent", "type": "expense", "amount": 10.0, "category": "Food", "description": "Test", "date": "2026-01-15T12:00:00"},
        )
        assert response.status_code == 404

    async def test_foreign_account_returns_404(self, auth_client: AsyncClient, second_client: AsyncClient, create_account):
        account = await create_account(initial_balance=100.0)
        response = await second_client.post(
            "/api/transactions/",
            json={"account_id": account["id"], "type": "expense", "amount": 10.0, "category": "Food", "description": "Test", "date": "2026-01-15T12:00:00"},
        )
        assert response.status_code == 404


class TestCategoryCRUD:
    """Tests for category CRUD operations."""

    async def test_default_categories_seeded_on_registration(self, auth_client: AsyncClient):
        response = await auth_client.get("/api/categories")
        assert response.status_code == 200
        categories = response.json()
        # Should have default categories
        names = [c["name"] for c in categories]
        assert "Food & Dining" in names
        assert "Income" in names
        assert len(categories) >= 14

    async def test_create_category(self, auth_client: AsyncClient):
        response = await auth_client.post(
            "/api/categories",
            json={"name": "Custom Expense", "type": "expense", "color": "#FF0000", "icon": "💰"},
        )
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Custom Expense"
        assert data["type"] == "expense"
        assert data["color"] == "#FF0000"
        assert data["icon"] == "💰"

    async def test_create_category_with_same_user_parent(self, auth_client: AsyncClient):
        parent_resp = await auth_client.post(
            "/api/categories",
            json={"name": "Parent", "type": "expense"},
        )
        parent_id = parent_resp.json()["id"]

        child_resp = await auth_client.post(
            "/api/categories",
            json={"name": "Child", "type": "expense", "parent_id": parent_id},
        )
        assert child_resp.status_code == 201
        assert child_resp.json()["parent_id"] == parent_id

    async def test_create_category_with_foreign_parent_returns_404(
        self, auth_client: AsyncClient, second_client: AsyncClient
    ):
        parent_resp = await second_client.post(
            "/api/categories",
            json={"name": "Other Parent", "type": "expense"},
        )
        foreign_parent_id = parent_resp.json()["id"]

        response = await auth_client.post(
            "/api/categories",
            json={"name": "Child", "type": "expense", "parent_id": foreign_parent_id},
        )
        assert response.status_code == 404

    async def test_update_category_with_foreign_parent_returns_404(
        self, auth_client: AsyncClient, second_client: AsyncClient
    ):
        parent_resp = await second_client.post(
            "/api/categories",
            json={"name": "Other Parent", "type": "expense"},
        )
        foreign_parent_id = parent_resp.json()["id"]

        child_resp = await auth_client.post(
            "/api/categories",
            json={"name": "Child", "type": "expense"},
        )
        child_id = child_resp.json()["id"]

        response = await auth_client.put(
            f"/api/categories/{child_id}",
            json={"name": "Child", "type": "expense", "parent_id": foreign_parent_id},
        )
        assert response.status_code == 404

    async def test_list_categories(self, auth_client: AsyncClient):
        await auth_client.post("/api/categories", json={"name": "Cat1", "type": "expense"})
        await auth_client.post("/api/categories", json={"name": "Cat2", "type": "income"})

        response = await auth_client.get("/api/categories")
        assert response.status_code == 200
        categories = response.json()
        names = [c["name"] for c in categories]
        assert "Cat1" in names
        assert "Cat2" in names

    async def test_get_category(self, auth_client: AsyncClient):
        create_resp = await auth_client.post(
            "/api/categories",
            json={"name": "Test Category", "type": "expense"},
        )
        cat_id = create_resp.json()["id"]

        response = await auth_client.get(f"/api/categories/{cat_id}")
        assert response.status_code == 200
        assert response.json()["id"] == cat_id

    async def test_update_category(self, auth_client: AsyncClient):
        create_resp = await auth_client.post(
            "/api/categories",
            json={"name": "Original", "type": "expense"},
        )
        cat_id = create_resp.json()["id"]

        response = await auth_client.put(
            f"/api/categories/{cat_id}",
            json={"name": "Updated", "type": "expense", "color": "#00FF00"},
        )
        assert response.status_code == 200
        assert response.json()["name"] == "Updated"
        assert response.json()["color"] == "#00FF00"

    async def test_delete_category(self, auth_client: AsyncClient):
        create_resp = await auth_client.post(
            "/api/categories",
            json={"name": "To Delete", "type": "expense"},
        )
        cat_id = create_resp.json()["id"]

        response = await auth_client.delete(f"/api/categories/{cat_id}")
        assert response.status_code == 204

        response = await auth_client.get(f"/api/categories/{cat_id}")
        assert response.status_code == 404

    async def test_category_ownership_check(self, auth_client: AsyncClient, second_client: AsyncClient):
        create_resp = await auth_client.post(
            "/api/categories",
            json={"name": "Private", "type": "expense"},
        )
        cat_id = create_resp.json()["id"]

        response = await second_client.get(f"/api/categories/{cat_id}")
        assert response.status_code == 404

        response = await second_client.put(
            f"/api/categories/{cat_id}",
            json={"name": "Hacked", "type": "expense"},
        )
        assert response.status_code == 404

        response = await second_client.delete(f"/api/categories/{cat_id}")
        assert response.status_code == 404


class TestRecurringCRUD:
    """Tests for recurring rule CRUD operations."""

    async def test_create_recurring_rule_linked_to_own_transaction(self, auth_client: AsyncClient, create_account):
        account = await create_account(initial_balance=100.0)
        tx_resp = await auth_client.post(
            "/api/transactions/",
            json={"account_id": account["id"], "type": "expense", "amount": 10.0, "category": "Food", "description": "Recurring", "date": "2026-01-01T00:00:00"},
        )
        tx_id = tx_resp.json()["id"]

        response = await auth_client.post(
            "/api/recurring/",
            json={
                "transaction_id": tx_id,
                "pattern": "monthly",
                "frequency": 1,
                "expected_amount": 10.0,
                "expected_date": "2027-01-01T00:00:00",
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["transaction_id"] == tx_id
        assert data["pattern"] == "monthly"

    async def test_reject_recurring_rule_linked_to_foreign_transaction(
        self, auth_client: AsyncClient, second_client: AsyncClient, create_account, create_account_second
    ):
        account = await create_account_second(initial_balance=100.0)
        tx_resp = await second_client.post(
            "/api/transactions/",
            json={"account_id": account["id"], "type": "expense", "amount": 10.0, "category": "Food", "description": "Recurring", "date": "2026-01-01T00:00:00"},
        )
        tx_id = tx_resp.json()["id"]

        response = await auth_client.post(
            "/api/recurring/",
            json={
                "transaction_id": tx_id,
                "pattern": "monthly",
                "frequency": 1,
                "expected_amount": 10.0,
                "expected_date": "2027-01-01T00:00:00",
            },
        )
        assert response.status_code == 404

    async def test_list_recurring_rules(self, auth_client: AsyncClient, create_account):
        account = await create_account(initial_balance=100.0)
        tx_resp = await auth_client.post(
            "/api/transactions/",
            json={"account_id": account["id"], "type": "expense", "amount": 10.0, "category": "Food", "description": "Recurring 1", "date": "2026-01-01T00:00:00"},
        )
        tx_id = tx_resp.json()["id"]

        await auth_client.post(
            "/api/recurring/",
            json={"transaction_id": tx_id, "pattern": "monthly", "frequency": 1, "expected_amount": 10.0, "expected_date": "2027-01-01T00:00:00"},
        )

        response = await auth_client.get("/api/recurring/")
        assert response.status_code == 200
        assert len(response.json()) == 1

    async def test_delete_recurring_rule(self, auth_client: AsyncClient, create_account):
        account = await create_account(initial_balance=100.0)
        tx_resp = await auth_client.post(
            "/api/transactions/",
            json={"account_id": account["id"], "type": "expense", "amount": 10.0, "category": "Food", "description": "Recurring", "date": "2026-01-01T00:00:00"},
        )
        tx_id = tx_resp.json()["id"]

        rr_resp = await auth_client.post(
            "/api/recurring/",
            json={"transaction_id": tx_id, "pattern": "monthly", "frequency": 1, "expected_amount": 10.0, "expected_date": "2027-01-01T00:00:00"},
        )
        rule_id = rr_resp.json()["id"]

        response = await auth_client.delete(f"/api/recurring/{rule_id}")
        assert response.status_code == 204

        response = await auth_client.get("/api/recurring/")
        assert len(response.json()) == 0

    async def test_recurring_rule_ownership_on_list(self, auth_client: AsyncClient, second_client: AsyncClient, create_account):
        account = await create_account(initial_balance=100.0)
        tx_resp = await auth_client.post(
            "/api/transactions/",
            json={"account_id": account["id"], "type": "expense", "amount": 10.0, "category": "Food", "description": "Recurring", "date": "2026-01-01T00:00:00"},
        )
        tx_id = tx_resp.json()["id"]

        await auth_client.post(
            "/api/recurring/",
            json={"transaction_id": tx_id, "pattern": "monthly", "frequency": 1, "expected_amount": 10.0, "expected_date": "2027-01-01T00:00:00"},
        )

        response = await second_client.get("/api/recurring/")
        assert response.status_code == 200
        assert len(response.json()) == 0

    async def test_recurring_rule_ownership_on_delete(self, auth_client: AsyncClient, second_client: AsyncClient, create_account):
        account = await create_account(initial_balance=100.0)
        tx_resp = await auth_client.post(
            "/api/transactions/",
            json={"account_id": account["id"], "type": "expense", "amount": 10.0, "category": "Food", "description": "Recurring", "date": "2026-01-01T00:00:00"},
        )
        tx_id = tx_resp.json()["id"]

        rr_resp = await auth_client.post(
            "/api/recurring/",
            json={"transaction_id": tx_id, "pattern": "monthly", "frequency": 1, "expected_amount": 10.0, "expected_date": "2027-01-01T00:00:00"},
        )
        rule_id = rr_resp.json()["id"]

        response = await second_client.delete(f"/api/recurring/{rule_id}")
        assert response.status_code == 404

    async def test_create_recurring_rule_rejects_past_expected_date(self, auth_client: AsyncClient, create_account):
        account = await create_account(initial_balance=100.0)
        tx_resp = await auth_client.post(
            "/api/transactions/",
            json={"account_id": account["id"], "type": "expense", "amount": 10.0, "category": "Food", "description": "Recurring", "date": "2026-01-01T00:00:00"},
        )
        tx_id = tx_resp.json()["id"]

        response = await auth_client.post(
            "/api/recurring/",
            json={
                "transaction_id": tx_id,
                "pattern": "monthly",
                "frequency": 1,
                "expected_amount": 10.0,
                "expected_date": "2026-02-01T00:00:00",
            },
        )
        assert response.status_code == 422

    async def test_create_transaction_rejects_past_recurring_expected_date(self, auth_client: AsyncClient, create_account):
        account = await create_account(initial_balance=100.0)
        response = await auth_client.post(
            "/api/transactions/",
            json={
                "account_id": account["id"],
                "type": "expense",
                "amount": 10.0,
                "category": "Food",
                "description": "Recurring",
                "date": "2026-01-01T00:00:00",
                "is_recurring": 1,
                "recurring_pattern": "monthly",
                "recurring_frequency": 1,
                "recurring_expected_date": "2026-02-01T00:00:00",
            },
        )
        assert response.status_code == 422

    async def test_upcoming_occurrences_expansion(self, auth_client: AsyncClient, create_account):
        from datetime import datetime, timedelta
        account = await create_account(initial_balance=100.0)
        tx_resp = await auth_client.post(
            "/api/transactions/",
            json={"account_id": account["id"], "type": "expense", "amount": 100.0, "category": "Rent", "description": "Monthly rent", "date": "2026-01-01T00:00:00"},
        )
        tx_id = tx_resp.json()["id"]

        future_date = (datetime.utcnow() + timedelta(days=5)).isoformat()
        await auth_client.post(
            "/api/recurring/",
            json={
                "transaction_id": tx_id,
                "pattern": "monthly",
                "frequency": 1,
                "expected_amount": 100.0,
                "expected_date": future_date,
            },
        )

        response = await auth_client.get("/api/recurring/upcoming?days=120")
        assert response.status_code == 200
        upcoming = response.json()
        assert len(upcoming) >= 1
        assert all("expected_date" in u for u in upcoming)
        assert all("expected_amount" in u for u in upcoming)

    async def test_upcoming_biweekly_expansion(self, auth_client: AsyncClient, create_account):
        account = await create_account(initial_balance=100.0)
        tx_resp = await auth_client.post(
            "/api/transactions/",
            json={"account_id": account["id"], "type": "expense", "amount": 20.0, "category": "Food", "description": "Biweekly", "date": "2026-01-01T00:00:00"},
        )
        tx_id = tx_resp.json()["id"]

        future_date = (datetime.utcnow() + timedelta(days=1)).isoformat()
        await auth_client.post(
            "/api/recurring/",
            json={
                "transaction_id": tx_id,
                "pattern": "biweekly",
                "frequency": 1,
                "expected_amount": 20.0,
                "expected_date": future_date,
            },
        )

        response = await auth_client.get("/api/recurring/upcoming?days=60")
        assert response.status_code == 200
        upcoming = response.json()
        assert len(upcoming) >= 3
        dates = [datetime.fromisoformat(u["expected_date"].replace("Z", "")) for u in upcoming]
        for first, second in zip(dates, dates[1:]):
            assert (second - first).days == 14

    async def test_upcoming_quarterly_expansion(self, auth_client: AsyncClient, create_account):
        account = await create_account(initial_balance=100.0)
        tx_resp = await auth_client.post(
            "/api/transactions/",
            json={"account_id": account["id"], "type": "expense", "amount": 300.0, "category": "Insurance", "description": "Quarterly", "date": "2026-01-01T00:00:00"},
        )
        tx_id = tx_resp.json()["id"]

        future_date = (datetime.utcnow() + timedelta(days=1)).isoformat()
        await auth_client.post(
            "/api/recurring/",
            json={
                "transaction_id": tx_id,
                "pattern": "quarterly",
                "frequency": 1,
                "expected_amount": 300.0,
                "expected_date": future_date,
            },
        )

        response = await auth_client.get("/api/recurring/upcoming?days=365")
        assert response.status_code == 200
        upcoming = response.json()
        assert len(upcoming) >= 3
        dates = [datetime.fromisoformat(u["expected_date"].replace("Z", "")) for u in upcoming]
        for first, second in zip(dates, dates[1:]):
            month_diff = (second.year - first.year) * 12 + (second.month - first.month)
            assert month_diff == 3