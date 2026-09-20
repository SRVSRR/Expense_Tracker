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
- **2026-09-17**: Fixed Render startup failure `No 'script_location' key
	found in configuration` — the app-factory lifespan pointed Alembic's
	`Config` at `backend/app/alembic.ini`, which does not exist; it now uses
	`BACKEND_DIR/alembic.ini` with a regression-guard test file
	(`tests/test_factory.py`, 3 tests). Verified 90 tests pass.
- **2026-09-18**: P3 item 1 complete — CORS now reads `CORS_ORIGINS`
	(comma-separated allowlist) via `get_cors_origins()` in `app/factory.py`;
	missing value or wildcard fails startup outside `TESTING=1`. Added 5 CORS
	tests in `tests/test_factory.py`. Verified 95 tests pass.
- **2026-09-18**: P3 item 2 complete — per-endpoint rate-limit tiers via
	`slowapi` (`app/utils/rate_limit.py`: auth 60/min, reads 120/min, writes
	30/min, analytics 60/hour, train 2/hour), keyed by Bearer `sub` with IP
	fallback and enforced post-auth; `ERROR_429` documented on all API routes
	and tiers listed in `/docs`. Added `tests/test_rate_limit.py` (8 tests).
	Verified 103 tests pass. No bulk endpoints exist, so WRITE 30/min only
	binds automation; slowapi buckets are per-route, so one dashboard load
	spends one hit per analytics bucket.
- **2026-09-19**: P3 item 3 complete — structured logging via `app/utils/logging.py`
	(JSONFormatter, redaction, request_id/user_id context) and `app/middleware/logging.py`
	(correlation ID `X-Request-ID`, timing, JSON `request completed` logs with
	`request_id`, `user_id`, `method`, `path`, `status`, `latency_ms`, `service`);
	redacts `Authorization` headers and sensitive query params. Added 4 logging
	tests in `tests/test_factory.py`. Verified 107 tests pass.
- **2026-09-19**: P3 item 4 + documented debt complete — `sentry-sdk[fastapi]`
	added, `app/utils/sentry.py` optional init via `SENTRY_DSN` (disabled in
	`TESTING=1`), lifespan captures migration failures and user context;
	`app/utils/circuit_breaker.py` protects Supabase JWKS fetch (3 failures →
	OPEN 60s, 503) and `with_db_transaction`/`db_transaction` now atomically
	wraps `create_transaction` (balance + recurring rule) with flush-aware
	cache invalidation. Added `tests/test_sentry.py` (3), `test_circuit_breaker.py`
	(5), `test_with_db_transaction.py` (3). Verified 119 tests pass.
- **2026-09-19**: P3 item 5 complete — Free-tier daily logical backups via
	GitHub Actions `.github/workflows/backup.yml` (02:00 UTC, masked
	`DATABASE_URL`, `pg_dump -Fc` + plain SQL, 7-day artifact, no S3) +
	`docs/ops/RESTORE.md` + `backend/scripts/verify_backup.py`; Dashboard
	snapshots remain view-only (no PITR on Free, Pro required). Verified no
	secrets in workflow/logs and `backend/venv/bin/python -m pytest -q` still
	119 passing.
- **2026-09-19**: Fix CI import-time `DATABASE_URL` check — `backend/app/db/database.py` now lazy (no import-time `raise`/`create_async_engine`); `get_database_url()`/`get_engine()` validate at `app/factory.py:66` lifespan (`TESTING=1` skips validation + migrations, otherwise fail-fast). Verified `DATABASE_URL="" TESTING=1 backend/venv/bin/python -m pytest backend/tests -q` → 119 passing (previously `RuntimeError` at `conftest.py:23` via `main:app` → `factory` → `database`).
- **2026-09-19**: P3 item 7/8 complete — CI via `.github/workflows/ci.yml`
	(3 jobs: `test` with `TESTING=1` + `compileall`, `lint` with `ruff` advisory,
	`security` with `pip-audit` + `bandit` advisory; `permissions: contents: read`,
	no secrets) + `.github/dependabot.yml` weekly. Verified `yaml OK` +
	`backend/venv/bin/python -m pytest -q` still 119 passing.
- **2026-09-19**: Dependabot — merged 8 PRs: `aiosqlite 0.22.1`, `alembic 1.20.0`,
	`scikit-learn 1.9.1`, `httpx 0.28.1`, `python-multipart 0.0.32`, `checkout@v7`,
	`setup-python@v7`, `upload-artifact@v7`. Verified `backend/venv/bin/pip install` with new versions + `TESTING=1 pytest` still 119 passing, `compileall OK`, actions workflows valid.

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
- [x] Add explicit error handling and rollback behavior around migration and database failures. Route-level 404s use the shared `{code, message, details}` exception envelope; `with_retry` protects read-heavy analytics computations against transient DB errors; startup logs and re-raises a clear error when Alembic migrations fail. `with_db_transaction`/`db_transaction` now atomically wraps `create_transaction` (balance + recurring rule) and Supabase JWKS fetch is protected by a circuit breaker (documented debt complete in P3).
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
- [x] Use a strong production `SECRET_KEY` and environment-specific CORS origins. `SECRET_KEY` is test-only (Supabase signs production tokens). CORS now loads from `CORS_ORIGINS` (comma-separated allowlist) with startup fail-fast and wildcard rejection outside tests.
- [x] Add production rate limiting. Per-endpoint tiers enforced via `slowapi` (auth 60/min, reads 120/min, writes 30/min, analytics 60/hour, train 2/hour), keyed by Bearer `sub` with IP fallback; `429` + `Retry-After` on excess.
- [x] Add structured JSON logging with correlation IDs. Every request emits a JSON log with `request_id`, `user_id`, `method`, `path`, `status`, `latency_ms`, `service`; `X-Request-ID` is propagated; query params and headers are redacted; no secrets leak.
- [x] Add error monitoring (Sentry, optional via `SENTRY_DSN`, captures user context and migration failures) and documented debt: `with_db_transaction`/`db_transaction` atomic for `create_transaction` (balance + recurring rule) and circuit breaker for Supabase JWKS (3 failures → OPEN 60s, 503 `EXTERNAL_SERVICE_UNAVAILABLE`).
- [x] Configure daily logical backups on Free tier (GitHub Actions `pg_dump` via `.github/workflows/backup.yml`, 02:00 UTC, masked `DATABASE_URL`, 7-day artifact) + Dashboard daily snapshots (view-only) + `docs/ops/RESTORE.md` runbook + `backend/scripts/verify_backup.py` (`SELECT 1`/`pg_is_in_recovery()`/dump-age); note Free has no PITR (Pro required for PITR slider).
- [ ] Run migrations as a release step. Startup currently runs `alembic upgrade head`; the basic `/health` endpoint checks database connectivity with `SELECT 1`.
- [x] Deploy the API and configure the `/health` endpoint for Render. Record the stable HTTPS URL `https://expense-tracker-uwrp.onrender.com` and the mobile client configuration.
- [x] Add CI for tests, syntax checks, and dependency/security scanning. `ci.yml` runs on PR/push to `main` (test: `TESTING=1 pytest` + `compileall`; lint: `ruff check/format` advisory; security: `pip-audit` + `bandit` advisory) with `pip` cache and no secrets; Dependabot weekly for `pip` + `github-actions`.

## External Application Dependencies

Switch these external apps/secrets only when the roadmap requires it (e.g., rotating credentials, new Supabase project, enabling Sentry for P3 monitoring, or pointing mobile/Render to a new environment). Check the box when the switch is done and re-verify `/health` + `SELECT 1` + a Bearer-token request.

### Supabase (Auth + PostgreSQL — required at runtime)
- [ ] Supabase project exists (`<project-ref>.supabase.co`). Supabase is the sole runtime DB/Auth provider; local SQLite is test-only (`backend/tests/conftest.py:14` sets `TESTING=1`).
- [ ] `DATABASE_URL` — Transaction pooler on **port 6543** with `postgresql+asyncpg://` driver (`docs/INFRASTRUCTURE.md:37`, `backend/app/db/database.py:17` auto-sets `statement_cache_size=0`). Source: Supabase Dashboard → Project Settings → Database → Connection string → Transaction pooler. Must be stored in local `backend/.env` and in Render → Environment (never committed). URL-encode special chars in password; a `password authentication failed` is a secret/encoding problem, not an engine config problem.
- [ ] `SUPABASE_JWKS_URL` = `https://<project-ref>.supabase.co/auth/v1/.well-known/jwks.json` and `SUPABASE_ISSUER` = `https://<project-ref>.supabase.co/auth/v1`. Source: Supabase Dashboard → Project Settings → API. Verified via `app/utils/supabase_auth.py:20` (JWKS fetch/caching, RS256, circuit breaker `app/utils/circuit_breaker.py:1`). Missing value fails startup with `RuntimeError`.
- [ ] Supabase `auth.users` schema accessible; Alembic migration `59062dbe3d50` creates `auth_user_id` UUID FKs to `auth.users.id` on 6 tables. `DATABASE_URL` must use a role with cross-schema FK grants.

### Render (hosting — required for deploy)
- [ ] Service configured: Build `pip install -r backend/requirements.txt`, Start `cd backend && uvicorn main:app --host 0.0.0.0 --port $PORT`, Health path `/health` (`backend/app/factory.py:221` does `SELECT 1`). See `docs/INFRASTRUCTURE.md:55`.
- [ ] Env vars set on Render → Environment: `DATABASE_URL`, `SUPABASE_JWKS_URL`, `SUPABASE_ISSUER`, `SECRET_KEY` (test-only, `backend/.env.example:3`), `CORS_ORIGINS` (comma-separated allowlist, fail-fast outside `TESTING=1`, `backend/app/factory.py:36`), `TESTING=0`, `ACCESS_TOKEN_EXPIRE_MINUTES`, plus optional `SENTRY_DSN`/`ENVIRONMENT` below.
- [ ] Client base URL recorded: `https://expense-tracker-uwrp.onrender.com` (`TODO.md:65`). Mobile repo must use `@supabase/supabase-js` token as Bearer and target this URL, not localhost. Re-verify after any env change: `curl https://expense-tracker-uwrp.onrender.com/health` → `{"status":"ok","database":"ok"}` and `https://expense-tracker-uwrp.onrender.com/openapi.json` + a Bearer-token account/transaction round-trip.

### Sentry (error monitoring — optional)
- [ ] Sentry project created only when enabling P3 Item 4 production monitoring (otherwise disabled). When disabled or `TESTING=1`, `app/utils/sentry.py:1` no-ops and lifespan does not crash.
- [ ] When enabling: `SENTRY_DSN` from Sentry → Project Settings → Client Keys (DSN), `ENVIRONMENT` (defaults to `production`), `SENTRY_TRACES_SAMPLE_RATE` (default `0.1`). Add to `backend/.env.example:15` template and to Render env, then redeploy. Verify by triggering a non-401 error (e.g., bad `account_id`) and checking Sentry Issues include `user_id` scope (`app/middleware/logging.py:1` + `app/utils/__init__.py:94`).

## Definition of done

- All P0 items pass in CI.
- Every documented endpoint has an integration test for its happy path and auth/user-isolation behavior.
- The API starts from a clean database using migrations.
- A deployed environment can be configured from documented environment variables only.
