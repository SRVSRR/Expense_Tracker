# Expense Tracker Delivery Checklist

Status: API foundation exists; correctness and operational work is in progress.

Detailed implementation sequence and acceptance criteria: [docs/P0_PLAN.md](docs/P0_PLAN.md).

## Project change policy

- Every major implementation, configuration, documentation, or security change
	must be committed incrementally throughout the entire project.
- Keep commits focused on one coherent change and record the affected files and
	verification in `AGENTS.md` and this file.

## Verification log

- **2026-09-05**: Live authenticated smoke test passed for account creation
	with an initial balance, income and expense transactions, transaction type
	filtering, amount update, deletion reversal, and resulting account balances.
	This does not replace the pending automated integration-test work below.

- **2026-09-06**: Full P0 test suite passes (72 tests). All integration tests for auth,
	user isolation, CRUD operations, balance effects, forecast/budget endpoints,
	cache invalidation, and category parent ownership validation are green.
- **2026-09-06**: Supabase Transaction pooler support documented and configured;
	PostgreSQL asyncpg connections disable prepared-statement caching for port 6543.
- **2026-09-06**: Syntax and database-configuration checks pass. Full pytest
	collection is currently blocked by the environment's missing macOS
	`libomp.dylib` required by LightGBM; this is unrelated to pooler configuration.
- **2026-09-06**: Local Supabase Transaction pooler URL format is valid, but the
	connectivity check received `password authentication failed`; replace or reset
	the database password and URL-encode special characters before retrying.
- **2026-09-06**: Retried the local Supabase Transaction pooler connection after
	updating credentials; `SELECT 1` succeeded with prepared-statement caching disabled.
- **2026-09-06**: Removed the stale local SQLite runtime configuration and confirmed
	no `backend/expense_tracker.db` exists; Supabase is now the only runtime database.
- **2026-09-06**: Live registration request succeeded with `201 Created`; the
	response returned user metadata without exposing the password or password hash.

## P0 - Make the current API trustworthy

- [x] Keep account balances consistent when transactions are created, updated, or deleted.
- [x] Reject recurring rules that reference another user's transaction.
- [x] Invalidate derived predictions after account and recurring-rule mutations.
- [x] Add integration tests for registration, login, auth failures, and user isolation.
- [x] Add integration tests for account, transaction, category, and recurring CRUD.
- [x] Add integration tests for forecast, budget, and cache invalidation behavior.
- [x] Validate category ownership when creating or updating `parent_id`.
- [x] Enforce the documented transaction edit policy: `type` and `account_id` remain immutable during transaction updates; amount and metadata edits remain supported.

### P0 implementation sequence

1. Add isolated async integration-test fixtures and authentication helpers.
2. Cover registration, login, auth failures, and cross-user isolation.
3. Cover account, transaction, category, and recurring CRUD plus balance effects.
4. Add category parent ownership validation and negative tests.
5. Cover forecast, budget, prediction caching, and invalidation behavior.
6. Run the full suite and update this verification log with the result.

## P1 - Finish documented functionality

- [ ] Define the recurring transaction request contract and automatically create a recurring rule when a transaction is marked recurring.
- [ ] Validate recurring patterns and positive frequencies with Pydantic constraints.
- [ ] Add explicit error handling and rollback behavior around migration and database failures.
- [ ] Reconcile the cache documentation with the implemented `budget_analysis` cache type.
- [ ] Make the app factory and `main.py` use the same router and lifespan configuration.
- [ ] Add OpenAPI examples and response schemas for forecast, budget, recurring, and categorization endpoints.

## P2 - ML upgrade

- [ ] Add separate LightGBM income and expense regressors.
- [ ] Add seasonality, spend velocity, and other documented features.
- [ ] Add scheduled prediction generation and cache writes.
- [ ] Add confidence ranges to forecast responses.
- [ ] Add model versioning and reproducible training metadata.

## P3 - Production hardening

- [ ] Move authentication to Supabase Auth or document the decision to retain local JWT.
- [ ] Use a strong production `SECRET_KEY` and environment-specific CORS origins.
- [ ] Add rate limiting, structured logs, backups, and error monitoring.
- [ ] Run migrations as a release step and add a health check that verifies database connectivity.
- [ ] Deploy the API and configure a stable HTTPS URL for mobile and desktop clients.
- [ ] Add CI for tests, syntax checks, and dependency/security scanning.

## Definition of done

- All P0 items pass in CI.
- Every documented endpoint has an integration test for its happy path and auth/user-isolation behavior.
- The API starts from a clean database using migrations.
- A deployed environment can be configured from documented environment variables only.
