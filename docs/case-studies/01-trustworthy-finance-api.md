# Making a Personal-Finance API Trustworthy: Tests, Isolation, and Balance Accounting

**Reading time:** 7 minutes  
**Audience:** Data engineering, backend engineering, and hiring managers  
**Repository evidence:** `backend/tests/`, `backend/app/routes/transactions.py`, `backend/app/routes/categories.py`, `backend/app/services/prediction_cache.py`

## Problem

Personal-finance software fails in especially costly ways. A balance can drift by cents, one user can see another user’s accounts, or derived analytics can silently become stale after an edit. Those are not cosmetic bugs: they undermine trust in money movement, reporting, and forecasts.

This project needed an API-only backend that could be trusted with:

- Account balances that remain correct across transaction creation, edits, and deletes.
- Strict separation between users and their financial records.
- Forecast and budget outputs that stay consistent after the underlying data changes.
- An automated suite that proves all of the above without depending on production data.

The initial smoke tests were useful, but they were manual. They did not scale, could not run in CI, and could not reliably catch regressions. Manual checks also tend to verify the path the developer already expected, rather than the adversarial paths real users and bugs will find.

## Approach

I treated API trust as a testable engineering property rather than a manual checklist.

### 1. Isolated integration-test architecture

The test suite uses:

- In-memory SQLite through `aiosqlite`.
- A per-test database lifecycle: create schema, run test, drop schema.
- FastAPI dependency overrides so tests use the isolated database instead of production data.
- Separate authenticated clients for two users.
- Helpers for creating accounts directly and through the API.
- Local test JWTs that simulate Supabase user IDs without requiring live Supabase credentials.

Important files:

- `../../backend/tests/conftest.py`
- `../../backend/tests/test_auth_integration.py`
- `../../backend/tests/test_crud_integration.py`
- `../../backend/tests/test_forecast_budget_integration.py`
- `../../backend/tests/test_supabase_auth.py`
- `../../backend/tests/test_business_logic.py`

This design avoids the most common integration-test failure mode: tests contaminating each other through shared state. Every test begins from a clean schema and ends by tearing it down. It also avoids the second most common failure: accidentally testing or mutating a developer database.

### 2. Authentication and cross-user isolation

The auth tests verify both success and failure behavior:

- Protected endpoints reject missing tokens with `401`.
- Authenticated users can retrieve their own identity.
- One user cannot read, update, or delete another user’s:
  - Accounts
  - Transactions
  - Categories
  - Recurring rules
- User-scoped list endpoints return only the caller’s records.
- Filtered and paginated transaction queries remain scoped to the caller.

Critically, foreign-resource access returns `404` rather than `403`. That prevents leaking whether another user owns a particular resource ID. Category parent validation follows the same principle: a parent category belonging to another user is treated as missing.

### 3. Transaction accounting rules

Transactions mutate account balances, so updates and deletes require exact accounting behavior:

- Creating income increases the balance.
- Creating an expense decreases the balance.
- Editing an amount applies only the balance delta, exactly once.
- Editing metadata does not change the balance.
- Deleting a transaction reverses its original balance effect.
- Missing or foreign accounts return `404`.
- Non-positive transaction amounts are rejected.
- Transaction `type` and `account_id` are immutable during updates.

That last decision is deliberate. Changing a transaction’s type or account after creation could silently move money between accounts or alter its accounting meaning. The API rejects that dangerous operation instead of trying to implement it implicitly. A future transfer or type-change feature would need an explicit atomic reversal-and-apply operation, planned separately.

The balance logic lives in a small, directly testable function in `../../backend/app/routes/transactions.py`. Unit tests cover balance application and reversal, while integration tests cover the full request-to-balance behavior.

### 4. Derived-data invalidation

Forecasts and budgets are cached, but stale analytics are worse than slow analytics. Transaction, account, and recurring-rule mutations invalidate the affected user’s cached predictions. The cache layer is scoped by `auth_user_id`, so invalidation never deletes another user’s cached predictions.

The cache behavior is tested directly, including:

- Valid cached responses are reused.
- Expired or missing entries are recomputed.
- Transaction create, update, and delete invalidate predictions.
- Account and recurring-rule mutations invalidate predictions.
- Other users’ predictions remain intact.
- Budget and budget-analysis caches use a seven-day TTL, while runway uses twelve hours and cash-flow/anomaly use twenty-four hours.

## Stack

- FastAPI with async routes and dependencies
- SQLAlchemy with async sessions
- SQLite through `aiosqlite` for isolated tests
- PostgreSQL through Supabase for production
- `pytest`, `pytest-asyncio`, and `httpx.ASGITransport`
- JWT authentication backed by Supabase in production

## Results

- **82 automated tests pass.**
- Authentication, CRUD, balance accounting, forecast behavior, budget behavior, caching, invalidation, and user isolation are covered.
- Cross-user reads, updates, and deletes return `404`.
- Transaction edits preserve balance consistency.
- Cached analytics are invalidated by the mutations that affect them.
- Tests never touch production or developer database state.

A representative protected-endpoint flow is deliberately simple:

```sh
curl https://expense-tracker-uwrp.onrender.com/api/auth/me \
  -H 'Authorization: Bearer YOUR_ACCESS_TOKEN'
```

If the token is invalid, the API returns `401`. If a resource belongs to someone else, the API returns `404`.

### How to review this work

Start with `test_auth_integration.py` to see the adversarial cases, then read `test_crud_integration.py` for balance arithmetic and ownership checks. `test_forecast_budget_integration.py` shows that derived analytics are not merely cached for performance; their invalidation behavior is specified and tested. Finally, `test_business_logic.py` isolates the smallest accounting rules from HTTP behavior.

## Lessons

1. **Isolation is a feature.** The most valuable test was not any happy path; it was proving that user B receives `404` for user A’s data.
2. **Make dangerous edits impossible.** Immutability for transaction `type` and `account_id` avoids an entire class of balance bugs.
3. **Cache invalidation needs tests.** TTLs alone are not enough. Every mutation path must be tested against the cache.
4. **Test doubles should preserve production semantics.** Tests simulate Supabase user IDs with local JWTs while keeping the production verification path unchanged.
5. **Manual smoke tests do not scale.** A clean, isolated integration suite turns correctness from a one-time check into a repeatable guarantee.
6. **Small pure functions help.** Isolating balance arithmetic from request handling makes both the unit tests and the integration tests clearer.
