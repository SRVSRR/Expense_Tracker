# P0 Implementation Plan

## Goal

Make the existing API trustworthy through automated coverage, complete ownership validation, and an explicit transaction-edit policy. P0 is complete only when the tests run against an isolated database and verify both happy paths and user isolation.

## Scope and decisions

- Keep the existing async FastAPI and SQLAlchemy architecture.
- Use an isolated temporary SQLite database for integration tests. Do not use the developer database or the running server for automated tests.
- Keep transaction `type` and `account_id` immutable during `PUT /api/transactions/{transaction_id}` for now. The current API updates amount and metadata only. This avoids silently moving a transaction between accounts or changing its accounting effect. A future feature may support those edits with an atomic reversal-and-apply operation, but that is outside this P0 implementation.
- Reject a category `parent_id` unless the referenced parent category belongs to the authenticated user. A missing or foreign parent should return `404` and leave no category row behind.
- Preserve the existing user-scoping rule on every business endpoint.

## Work sequence

### 1. Test infrastructure

**Files:** `backend/tests/conftest.py`, `backend/tests/` test modules, possibly `backend/requirements.txt` only if an existing test dependency is missing.

- Build an async test database fixture using a temporary SQLite URL.
- Override `app.get_db` for the test client and create/drop the schema per test session or test function as appropriate.
- Provide helpers/fixtures for registering users, obtaining JWTs, creating accounts, and authenticated request headers.
- Ensure tests do not depend on `backend/expense_tracker.db`, `.env`, a running Uvicorn process, or test data left by another test.
- Keep the existing unit tests and run them with the integration tests.

### 2. Authentication and isolation coverage

**Files:** `backend/tests/test_auth_integration.py` and/or the shared integration test module.

Test cases:

- Registration returns `201` and a user payload without a password hash.
- Duplicate email registration returns `400`.
- Login returns a bearer token for valid credentials.
- Wrong password returns `401`.
- Protected endpoint without a token returns `401`.
- `/api/auth/me` returns the authenticated user.
- User A cannot read, update, or delete User B's account, transaction, category, or recurring rule; expect `404` for resource lookups/mutations.
- User-scoped list endpoints return only the current user's records.

### 3. Account, transaction, category, and recurring CRUD coverage

**Files:** `backend/tests/test_crud_integration.py` and focused modules if the test file becomes too large.

Accounts:

- Create an account with `initial_balance`; assert both `initial_balance` and `current_balance`.
- List, retrieve, update allowed fields, and delete an account.
- Verify account ownership checks.

Transactions:

- Create income and expense transactions; assert balance changes from the opening balance.
- List, retrieve, filter by account/type/category/date, and paginate.
- Update amount; assert the balance delta is applied exactly once.
- Update metadata; assert the balance is unchanged.
- Delete income and expense transactions; assert each balance effect is reversed.
- Reject non-positive amounts with `422`.
- Verify missing/foreign account and transaction handling.
- Assert `type` and `account_id` are not accepted as editable fields in the current contract; document this as the deliberate P0 policy.

Categories:

- Verify registration seeds default categories.
- Create, list, retrieve, update, and delete a user-owned category.
- Create with a same-user `parent_id` successfully.
- Create and update with a foreign `parent_id` return `404` and do not persist the invalid relationship.
- Verify category resource ownership.

Recurring rules:

- Create, list, and delete a rule linked to the current user's transaction.
- Reject a rule linked to another user's transaction with `404`.
- Verify upcoming occurrence expansion for supported patterns and ownership filtering.
- Verify recurring-rule ownership on list/delete.

### 4. Forecast, budget, and cache coverage

**Files:** `backend/tests/test_forecast_budget_integration.py` and/or service-level tests.

- Seed deterministic income and expense data for one user.
- Verify each forecast endpoint returns the expected response shape and only uses that user's data.
- Verify runway and anomaly responses for known inputs.
- Verify budget recommendations and category analysis for known inputs.
- Store a prediction, confirm the endpoint can read it while valid, and confirm expired/missing entries are recomputed or handled as implemented.
- Confirm transaction create, update, and delete invalidate the current user's cached predictions.
- Confirm account and recurring-rule mutations invalidate the current user's cached predictions.
- Confirm invalidation never deletes another user's predictions.

### 5. Documentation and acceptance update

**Files:** `README.md`, `TODO.md`, `AGENTS.md`.

- Link this plan from the testing and delivery sections of `README.md`.
- Track each P0 workstream and its test coverage in `TODO.md`.
- Keep `AGENTS.md` aligned with the transaction-edit decision, test commands, and completion gates.
- After implementation, record the test command and result in the `TODO.md` verification log.

## Implementation order

1. Add isolated integration-test fixtures and prove one auth test can run without the development database.
2. Add auth and user-isolation tests.
3. Add account and transaction CRUD/balance tests.
4. Add category parent ownership validation and its tests.
5. Add category and recurring CRUD tests.
6. Add forecast, budget, and cache tests.
7. Update documentation and run the full validation commands.

## Validation commands

From the repository root:

```sh
.venv/bin/python -m pytest -q backend/tests
.venv/bin/python -m compileall -q backend/app backend/tests
```

The P0 gate must also pass against a clean temporary test database, with no Uvicorn process required:

```sh
.venv/bin/python -m pytest -q backend/tests -m integration
```

If the project does not add a pytest marker, use the full test command and keep the integration tests included in the default suite.

## Definition of done

- All P0 checklist items are either implemented and covered by automated tests or have an explicit documented decision.
- The full backend test suite passes from a clean checkout/environment.
- Tests cover successful behavior, validation failures, authentication failures, and cross-user isolation.
- No test writes to the developer SQLite database.
- Documentation agrees on the transaction edit policy and remaining P1 work.
