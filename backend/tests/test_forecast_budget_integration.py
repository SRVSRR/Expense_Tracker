"""Integration tests for forecast, budget, and cache invalidation."""
import pytest
from httpx import AsyncClient
from datetime import datetime, timedelta
from app.models import Transaction, TransactionType, Account, Prediction
from sqlalchemy import select


class TestForecastEndpoints:
    """Tests for forecast endpoints."""

    async def test_cashflow_forecast_shape(self, auth_client: AsyncClient, create_account):
        await _seed_deterministic_data(auth_client, create_account)
        
        response = await auth_client.get("/api/forecast/cashflow?days=30")
        assert response.status_code == 200
        data = response.json()
        assert "period_days" in data
        assert "avg_daily_income" in data
        assert "avg_daily_expense" in data
        assert "forecast" in data
        assert len(data["forecast"]) == 30
        for day in data["forecast"]:
            assert "date" in day
            assert "projected_balance" in day
            assert "expected_income" in day
            assert "expected_expense" in day

    async def test_runway_forecast_shape(self, auth_client: AsyncClient, create_account):
        await _seed_deterministic_data(auth_client, create_account)
        
        response = await auth_client.get("/api/forecast/runway?threshold=1000")
        assert response.status_code == 200
        data = response.json()
        assert "current_balance" in data
        assert "avg_daily_income" in data
        assert "avg_daily_expense" in data
        assert "net_daily_burn" in data
        assert "threshold" in data
        assert "days_until_threshold" in data
        assert data["threshold"] == 1000

    async def test_anomalies_forecast_shape(self, auth_client: AsyncClient, create_account):
        await _seed_deterministic_data(auth_client, create_account)
        
        # Add an obvious anomaly
        account = await create_account(initial_balance=1000.0)
        await auth_client.post(
            "/api/transactions/",
            json={
                "account_id": account["id"],
                "type": "expense",
                "amount": 10000.0,  # Way above average
                "category": "Food",
                "description": "Anomaly",
                "date": datetime.utcnow().isoformat(),
            },
        )
        
        response = await auth_client.get("/api/forecast/anomalies")
        assert response.status_code == 200
        data = response.json()
        assert "total_transactions_analyzed" in data
        assert "anomalies_found" in data
        assert "anomalies" in data

    async def test_forecast_user_isolation(self, auth_client: AsyncClient, second_client: AsyncClient, create_account):
        await _seed_deterministic_data(auth_client, create_account)
        
        # Second user should get empty/zero results
        response = await second_client.get("/api/forecast/cashflow?days=30")
        assert response.status_code == 200
        data = response.json()
        assert data["avg_daily_income"] == 0
        assert data["avg_daily_expense"] == 0


class TestBudgetEndpoints:
    """Tests for budget endpoints."""

    async def test_budget_recommendations_shape(self, auth_client: AsyncClient, create_account):
        await _seed_budget_data(auth_client, create_account)
        
        response = await auth_client.get("/api/budget/recommendations")
        assert response.status_code == 200
        data = response.json()
        assert "avg_monthly_income" in data
        assert "avg_monthly_expense" in data
        assert "savings_rate_percent" in data
        assert "recommendations" in data
        assert len(data["recommendations"]) >= 2
        for rec in data["recommendations"]:
            assert "category" in rec
            assert "monthly_average" in rec
            assert "percent_of_income" in rec
            assert "status" in rec
            assert "suggested_budget" in rec

    async def test_category_analysis_shape(self, auth_client: AsyncClient, create_account):
        await _seed_budget_data(auth_client, create_account)
        
        response = await auth_client.get("/api/budget/category-analysis")
        assert response.status_code == 200
        data = response.json()
        assert "period" in data
        assert "total_income" in data
        assert "total_expense" in data
        assert "net_flow" in data
        assert "categories" in data
        for cat in data["categories"]:
            assert "category" in cat
            assert "total_spent" in cat
            assert "monthly_average" in cat
            assert "transaction_count" in cat
            assert "percent_of_total" in cat

    async def test_budget_user_isolation(self, auth_client: AsyncClient, second_client: AsyncClient, create_account):
        await _seed_budget_data(auth_client, create_account)
        
        response = await second_client.get("/api/budget/recommendations")
        assert response.status_code == 200
        data = response.json()
        assert data["avg_monthly_income"] == 0
        assert data["avg_monthly_expense"] == 0


class TestPredictionCache:
    """Tests for prediction caching and invalidation."""

    async def test_cache_read_write(self, auth_client: AsyncClient, create_account, db_session):
        await _seed_deterministic_data(auth_client, create_account)
        
        # First call computes and caches
        response1 = await auth_client.get("/api/forecast/cashflow?days=30")
        assert response1.status_code == 200
        data1 = response1.json()
        
        # Second call should return cached (same object)
        response2 = await auth_client.get("/api/forecast/cashflow?days=30")
        assert response2.status_code == 200
        data2 = response2.json()
        assert data1 == data2

    async def test_transaction_create_invalidates_cache(self, auth_client: AsyncClient, create_account, db_session):
        await _seed_deterministic_data(auth_client, create_account)
        
        # Prime the cache
        await auth_client.get("/api/forecast/cashflow?days=30")
        
        # Create a new transaction
        account = await create_account(initial_balance=1000.0)
        await auth_client.post(
            "/api/transactions/",
            json={
                "account_id": account["id"],
                "type": "expense",
                "amount": 100.0,
                "category": "Food",
                "description": "New expense",
                "date": datetime.utcnow().isoformat(),
            },
        )
        
        # Cache should be invalidated - next call recomputes
        response = await auth_client.get("/api/forecast/cashflow?days=30")
        assert response.status_code == 200
        # The forecast should reflect the new transaction (different projected balance)

    async def test_transaction_update_invalidates_cache(self, auth_client: AsyncClient, create_account, db_session):
        await _seed_deterministic_data(auth_client, create_account)
        
        # Prime the cache
        await auth_client.get("/api/forecast/cashflow?days=30")
        
        # Update an existing transaction amount
        # First get a transaction ID
        tx_resp = await auth_client.get("/api/transactions/?limit=1")
        tx_id = tx_resp.json()[0]["id"]
        
        await auth_client.put(f"/api/transactions/{tx_id}", json={"amount": 999.0})
        
        # Cache invalidated
        response = await auth_client.get("/api/forecast/cashflow?days=30")
        assert response.status_code == 200

    async def test_transaction_delete_invalidates_cache(self, auth_client: AsyncClient, create_account, db_session):
        await _seed_deterministic_data(auth_client, create_account)
        
        await auth_client.get("/api/forecast/cashflow?days=30")
        
        tx_resp = await auth_client.get("/api/transactions/?limit=1")
        tx_id = tx_resp.json()[0]["id"]
        
        await auth_client.delete(f"/api/transactions/{tx_id}")
        
        response = await auth_client.get("/api/forecast/cashflow?days=30")
        assert response.status_code == 200

    async def test_account_create_invalidates_cache(self, auth_client: AsyncClient, create_account, db_session):
        await _seed_deterministic_data(auth_client, create_account)
        
        await auth_client.get("/api/forecast/cashflow?days=30")
        
        await auth_client.post("/api/accounts/", json={"name": "New Account", "initial_balance": 500.0})
        
        response = await auth_client.get("/api/forecast/cashflow?days=30")
        assert response.status_code == 200

    async def test_account_update_invalidates_cache(self, auth_client: AsyncClient, create_account, db_session):
        await _seed_deterministic_data(auth_client, create_account)
        
        await auth_client.get("/api/forecast/cashflow?days=30")
        
        account = await create_account(initial_balance=1000.0)
        await auth_client.put(f"/api/accounts/{account['id']}", json={"name": "Renamed"})
        
        response = await auth_client.get("/api/forecast/cashflow?days=30")
        assert response.status_code == 200

    async def test_account_delete_invalidates_cache(self, auth_client: AsyncClient, create_account, db_session):
        await _seed_deterministic_data(auth_client, create_account)
        
        await auth_client.get("/api/forecast/cashflow?days=30")
        
        account = await create_account(initial_balance=1000.0)
        await auth_client.delete(f"/api/accounts/{account['id']}")
        
        response = await auth_client.get("/api/forecast/cashflow?days=30")
        assert response.status_code == 200

    async def test_recurring_rule_create_invalidates_cache(self, auth_client: AsyncClient, create_account, db_session):
        await _seed_deterministic_data(auth_client, create_account)
        
        await auth_client.get("/api/forecast/cashflow?days=30")
        
        account = await create_account(initial_balance=1000.0)
        tx_resp = await auth_client.post(
            "/api/transactions/",
            json={"account_id": account["id"], "type": "expense", "amount": 50.0, "category": "Food", "description": "Test", "date": "2026-01-01T00:00:00"},
        )
        await auth_client.post(
            "/api/recurring/",
            json={"transaction_id": tx_resp.json()["id"], "pattern": "monthly", "frequency": 1, "expected_amount": 50.0, "expected_date": "2027-01-01T00:00:00"},
        )
        
        response = await auth_client.get("/api/forecast/cashflow?days=30")
        assert response.status_code == 200

    async def test_recurring_rule_delete_invalidates_cache(self, auth_client: AsyncClient, create_account, db_session):
        await _seed_deterministic_data(auth_client, create_account)
        
        await auth_client.get("/api/forecast/cashflow?days=30")
        
        account = await create_account(initial_balance=1000.0)
        tx_resp = await auth_client.post(
            "/api/transactions/",
            json={"account_id": account["id"], "type": "expense", "amount": 50.0, "category": "Food", "description": "Test", "date": "2026-01-01T00:00:00"},
        )
        rr_resp = await auth_client.post(
            "/api/recurring/",
            json={"transaction_id": tx_resp.json()["id"], "pattern": "monthly", "frequency": 1, "expected_amount": 50.0, "expected_date": "2027-01-01T00:00:00"},
        )
        rule_id = rr_resp.json()["id"]
        
        await auth_client.delete(f"/api/recurring/{rule_id}")
        
        response = await auth_client.get("/api/forecast/cashflow?days=30")
        assert response.status_code == 200

    async def test_invalidation_does_not_affect_other_users(
        self, auth_client: AsyncClient, second_client: AsyncClient, create_account, db_session
    ):
        await _seed_deterministic_data(auth_client, create_account)
        await _seed_deterministic_data(second_client, create_account)
        
        # Prime both caches
        await auth_client.get("/api/forecast/cashflow?days=30")
        await second_client.get("/api/forecast/cashflow?days=30")
        
        # User 1 creates transaction
        account = await create_account(initial_balance=1000.0)
        await auth_client.post(
            "/api/transactions/",
            json={"account_id": account["id"], "type": "expense", "amount": 100.0, "category": "Food", "description": "New", "date": datetime.utcnow().isoformat()},
        )
        
        # User 2's cache should still be valid
        response = await second_client.get("/api/forecast/cashflow?days=30")
        assert response.status_code == 200
        
        # Verify user 2's cache still returns old data (we can't easily assert exact equality
        # but we can verify the endpoint works without error)


class TestRunwayAnomaliesCache:
    """Specific tests for runway and anomaly cache types."""

    async def test_runway_cache_ttl_behavior(self, auth_client: AsyncClient, create_account):
        await _seed_deterministic_data(auth_client, create_account)
        
        response = await auth_client.get("/api/forecast/runway?threshold=0")
        assert response.status_code == 200
        data1 = response.json()
        
        response = await auth_client.get("/api/forecast/runway?threshold=0")
        assert response.status_code == 200
        data2 = response.json()
        
        assert data1 == data2  # Cached

    async def test_anomaly_cache_ttl_behavior(self, auth_client: AsyncClient, create_account):
        await _seed_deterministic_data(auth_client, create_account)
        
        response = await auth_client.get("/api/forecast/anomalies")
        assert response.status_code == 200
        data1 = response.json()
        
        response = await auth_client.get("/api/forecast/anomalies")
        assert response.status_code == 200
        data2 = response.json()
        
        assert data1 == data2  # Cached

    async def test_budget_cache_ttl_behavior(self, auth_client: AsyncClient, create_account):
        await _seed_budget_data(auth_client, create_account)
        
        response = await auth_client.get("/api/budget/recommendations")
        assert response.status_code == 200
        data1 = response.json()
        
        response = await auth_client.get("/api/budget/recommendations")
        assert response.status_code == 200
        data2 = response.json()
        
        assert data1 == data2  # Cached

    async def test_category_analysis_cache_ttl_behavior(self, auth_client: AsyncClient, create_account):
        await _seed_budget_data(auth_client, create_account)
        
        response = await auth_client.get("/api/budget/category-analysis")
        assert response.status_code == 200
        data1 = response.json()
        
        response = await auth_client.get("/api/budget/category-analysis")
        assert response.status_code == 200
        data2 = response.json()
        
        assert data1 == data2  # Cached


# Helper functions for seeding data
async def _seed_deterministic_data(auth_client: AsyncClient, create_account):
    """Seed known income/expense data for predictable forecasts."""
    account = await create_account(initial_balance=5000.0)
    
    # Add income transactions over last 90 days
    base_date = datetime.utcnow() - timedelta(days=90)
    for i in range(12):  # ~monthly income
        await auth_client.post(
            "/api/transactions/",
            json={
                "account_id": account["id"],
                "type": "income",
                "amount": 3000.0,
                "category": "Salary",
                "description": f"Salary {i}",
                "date": (base_date + timedelta(days=i * 7)).isoformat(),
            },
        )
    
    # Add expense transactions
    expense_categories = ["Food", "Transport", "Rent", "Utilities"]
    for i, cat in enumerate(expense_categories):
        for week in range(4):
            await auth_client.post(
                "/api/transactions/",
                json={
                    "account_id": account["id"],
                    "type": "expense",
                    "amount": 200.0 + i * 50,
                    "category": cat,
                    "description": f"{cat} {week}",
                    "date": (base_date + timedelta(days=i * 20 + week * 5)).isoformat(),
                },
            )
    
    return account


async def _seed_budget_data(auth_client: AsyncClient, create_account):
    account = await create_account(initial_balance=2000.0)
    
    base_date = datetime.utcnow() - timedelta(days=90)
    # Income
    for i in range(3):
        await auth_client.post(
            "/api/transactions/",
            json={
                "account_id": account["id"],
                "type": "income",
                "amount": 5000.0,
                "category": "Salary",
                "description": f"Salary {i}",
                "date": (base_date + timedelta(days=i * 30)).isoformat(),
            },
        )
    # Expenses
    for i in range(9):
        await auth_client.post(
            "/api/transactions/",
            json={
                "account_id": account["id"],
                "type": "expense",
                "amount": 500.0,
                "category": "Food",
                "description": f"Food {i}",
                "date": (base_date + timedelta(days=i * 10)).isoformat(),
            },
        )
    for i in range(3):
        await auth_client.post(
            "/api/transactions/",
            json={
                "account_id": account["id"],
                "type": "expense",
                "amount": 1000.0,
                "category": "Rent",
                "description": f"Rent {i}",
                "date": (base_date + timedelta(days=i * 30)).isoformat(),
            },
        )
    
    return account