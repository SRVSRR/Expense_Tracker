# Expense Tracker Delivery Checklist

Status: API foundation, Supabase Auth migration, P0, P1, and P2 are complete; P3 is in progress. The backend is deployed, but mobile integration is still the next client-side phase.

Detailed implementation sequence and acceptance criteria: [docs/P0_PLAN.md](docs/P0_PLAN.md).
Role-focused case studies: [docs/case-studies/](docs/case-studies/).

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
- **2026-09-07**: Auth Migration Phase 1 complete. Supabase JWT verification
	implemented in `app/utils/supabase_auth.py` with JWKS fetching/caching,
	RS256 signature verification, audience/issuer/expiry validation. 10 unit tests
	pass (mocked + real RSA key). All 72 existing integration tests still pass
	(82 total). Local JWT auth remains the live path; Supabase verifier is
	additive and isolated for Phase 2+ integration.
- **2026-09-07**: Auth Migration Phase 2 complete. Alembic migration `59062dbe3d50`
	adds `auth_user_id` (UUID) columns with FK to `auth.users.id` on 6 tables
	(`accounts`, `transactions`, `categories`, `recurring_rules`, `predictions`,
	`correction_logs`). Cross-schema FK validated against Supabase `auth` schema.
	Migration is reversible. Models updated with conditional `auth_user_id_column()`
	helper for test compatibility (SQLite). All 82 tests pass.
- **2026-09-07**: Auth Migration Phase 3 complete. `get_current_user` uses
	Supabase JWT (RS256 via JWKS) in production and local JWT (HS256) only when
	`TESTING=1`. Local `/register` and `/login` endpoints are removed. Test
	fixtures create users directly with local JWT tokens (simulating Supabase
	user IDs). All 82 tests pass.
- **2026-09-07**: Phase 3 integration tests updated for Supabase Auth compatibility.
	All 82 tests pass (72 P0 + 10 Supabase auth). Category seeding fixed for test
	users. All schemas updated to use `auth_user_id` instead of `user_id`.
- **2026-09-10**: Render deployment verified for the FastAPI backend with Supabase
	Auth as the production authentication provider. Render health-check path is
	`/health`; it verifies database connectivity with `SELECT 1`. Production
	configuration uses `SUPABASE_JWKS_URL` and `SUPABASE_ISSUER`; `AUTH_MODE` is
	not read by the application, and `TESTING=0` (or unset) selects Supabase JWT
	verification. The deployed API base URL should be recorded here once finalized:
	`https://expense-tracker-uwrp.onrender.com`.
- **2026-09-10**: Documentation consistency pass. Removed the stale duplicate
	P1–P3 checklist and corrected the remaining P1 statuses against the
	implementation. Repaired the uncommitted forecast OpenAPI example syntax and
	added missing `Transaction`, `CashflowForecastDay`, and `AnomalyItem` schema
	examples, and pointed root `MIGRATION.md` to `docs/MIGRATION.md`. Verified
	`backend/venv/bin/python -m pytest -q backend/tests`
	(82 passed) and `backend/venv/bin/python -m compileall -q backend/app backend/tests`.
- **2026-09-12**: Added five DS/DE case studies under `docs/case-studies/`,
	including a reading guide, and linked them from `README.md`. No application
	code was changed in this documentation pass.
- **2026-09-16**: P1 completed. Recurring rules reject past `expected_date`
	(422) and expand `biweekly`/`quarterly` occurrences; route-level failures
	use the shared `{code, message, details}` envelope with `with_retry` on
	analytics reads; the app factory now owns routers, CORS, logging
	middleware, `/`, `/health`, and a lifespan that runs migrations; all routes
	document OpenAPI error examples via the shared `app/utils/openapi.py`
	module. Verified `backend/venv/bin/python -m pytest -q backend/tests`
	(87 passed) and `backend/venv/bin/python -m compileall -q backend/app backend/tests`.
	A startup failure now fails loudly with a logged error if Alembic
	migrations fail. Circuit breaker and `with_db_transaction` in route
	business logic remain explicit debt.

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

## Auth Migration - Local JWT → Supabase Auth

Phased migration documented in [docs/MIGRATION.md](docs/MIGRATION.md). Scope: backend only; clients are unaffected until Phase 5 (mobile repo integration).

- [x] **Phase 1**: Backend token verification (Supabase JWT validator in `app/utils/supabase_auth.py`, 10 unit tests, 72 tests still pass)
- [x] **Phase 2**: Schema change for `auth.users` FK (Alembic migration `59062dbe3d50`, cross-schema FK to `auth.users.id` on 6 tables, UUID type, reversible)
- [x] **Phase 3**: Switch live auth dependency (Supabase JWT verification in `get_current_user`, local HS256 verification limited to `TESTING=1`, test fixtures updated, full 82-test pass)
- [x] **Phase 4**: Cleanup (dead code removal, security docs update, dependency trim)
- [x] **Phase 5**: Mobile integration guidance is ready. The mobile client should
	use `@supabase/supabase-js` for email/password, magic-link, or OAuth sign-in,
	attach the resulting Supabase access token as a Bearer token, and send API
	requests to `https://expense-tracker-uwrp.onrender.com` rather than localhost.
	The backend health check is
	`https://expense-tracker-uwrp.onrender.com/health`.

## P1 - Finish documented functionality

- [x] Define the recurring transaction request contract and automatically create a recurring rule when a transaction is marked recurring. Implemented conditionally: `TransactionCreate` carries the recurring fields, and `create_transaction` creates a `RecurringRule` only when `is_recurring` plus pattern, frequency, and expected date are supplied.
- [x] Validate recurring patterns and positive frequencies with Pydantic constraints. Implemented: `RecurringPattern` enum, `frequency >= 1`, and `expected_amount > 0`. Future-date validation for `expected_date` is now applied (past dates return 422), and `biweekly`/`quarterly` occurrence expansion is supported in `/api/recurring/upcoming`.
- [x] Add explicit error handling and rollback behavior around migration and database failures. Route-level 404s use the shared `{code, message, details}` exception envelope; `with_retry` protects read-heavy analytics computations against transient DB errors; startup logs and re-raises a clear error when Alembic migrations fail. `with_db_transaction` is not yet used in route business logic and no circuit breaker exists (both documented as explicit debt).
- [x] Reconcile the cache documentation with the implemented `budget_analysis` cache type. The application cache module documents and implements both 7-day budget cache types; `README.md` and `docs/INFRASTRUCTURE.md` are also updated in this pass.
- [x] Make the app factory and `main.py` use the same router and lifespan configuration. `backend/app/factory.py` now creates the full app (routers, CORS, request-logging middleware, `/`, `/health`, exception handlers, and the migration-running lifespan), and `main.py` is a thin entrypoint that only calls `create_app()`.
- [x] Add OpenAPI examples and response schemas for forecast, budget, recurring, and categorization endpoints. All routes document success and standard error responses (400/401/404/422/429/500) with examples via the shared `backend/app/utils/openapi.py` module; response schemas carry `json_schema_extra` examples.

## P2 - ML upgrade

- [x] Add separate LightGBM income and expense regressors.
- [x] Add seasonality, spend velocity, and other documented features.
- [x] Add request-driven prediction generation and cache writes. No scheduler is implemented.
- [x] Add confidence ranges to forecast responses.
- [x] Add model versioning and reproducible training metadata.

## P3 - Production hardening

- [x] Move authentication to Supabase Auth (completed).
- [ ] Use a strong production `SECRET_KEY` and environment-specific CORS origins.
- [ ] Add production rate limiting, structured logs, backups, and error monitoring. `slowapi` is installed and `/api/categorize/train` is limited; broader limits and monitoring remain.
- [ ] Run migrations as a release step. Startup currently runs `alembic upgrade head`; the basic `/health` endpoint checks database connectivity with `SELECT 1`.
- [x] Deploy the API and configure the `/health` endpoint for Render. Record the stable HTTPS URL `https://expense-tracker-uwrp.onrender.com` and the mobile client configuration.
- [ ] Add CI for tests, syntax checks, and dependency/security scanning.

## Definition of done

- All P0 items pass in CI.
- Every documented endpoint has an integration test for its happy path and auth/user-isolation behavior.
- The API starts from a clean database using migrations.
- A deployed environment can be configured from documented environment variables only.
