# AGENTS.md

## Purpose

This file tells a coding agent exactly what to build, in what order, and how
to know each step is done. Follow the phases in sequence. Do not start a
phase until the previous phase's "Definition of done" is satisfied. If
something here is ambiguous, stop and ask rather than guessing.

## Ask before acting; do not improvise

- Whenever the agent is unsure about intent, scope, or the right choice, it
  MUST stop and ask the user a focused question instead of guessing or
  improvising on its own. Do not assume what the user wants.
- Do not make changes the user did not ask for, even if they seem obviously
  beneficial. Unrequested "improvements", refactors, or scope expansion are
  unwanted without explicit approval.
- Before each change, the agent should be able to state what the user asked
  for and how the planned change maps to it. If it cannot, ask first.
- Confirm the implementation/delivery style (e.g. preset/whatever) with the
  user only when genuinely ambiguous; otherwise keep questions limited to
  real decision points.

## Project summary

A full-stack personal finance API with manual-entry income + expense tracking
as the core differentiator. API-only, no frontend code in this repo. Separate
mobile and desktop repos will consume this API.

The API is the core product. Prioritize API correctness, performance, and
correctness over frontend UI concerns.

## Documentation consistency

- After every substantive implementation change or verification, update both
  `TODO.md` and `AGENTS.md` so status, decisions, and remaining technical debt
  stay synchronized.
- Every major change anywhere in the project must be committed incrementally;
  this rule applies to all phases and file types, not only P0. Keep each commit
  focused on one coherent change and include the corresponding documentation
  and verification updates.
- Do not create a commit unless the user explicitly requests implementation or
  a commit; when implementation is requested, do not leave the completed major
  change uncommitted.
- Do not mark a checklist item complete based only on a manual smoke test;
  record the verification separately until the corresponding automated test or
  acceptance criteria are satisfied.
- The detailed P0 sequence and acceptance criteria live in
  `docs/P0_PLAN.md`; keep it aligned with this file and `TODO.md`.
- For P0, transaction `type` and `account_id` are intentionally immutable in
  transaction updates. Do not add partial support that can leave two account
  balances inconsistent; a future atomic transfer/type-change feature must be
  planned separately.
- Supabase Transaction pooler uses port 6543. For `postgresql+asyncpg://`
  URLs, the database engine must disable prepared-statement caching with
  `statement_cache_size=0`; never commit the password-bearing URL.
- If tests fail during collection because LightGBM cannot load macOS
  `libomp.dylib`, treat that as an environment prerequisite issue separate from
  database configuration and record it in `TODO.md`.
- A valid pooler URL with `password authentication failed` indicates a secret
  or URL-encoding problem, not an engine configuration problem; never log or
  copy the password into project files.
- The Supabase Transaction pooler connection was verified on 2026-09-06 with a
  password-safe `SELECT 1` check and `statement_cache_size=0`.
- The application now uses Supabase PostgreSQL exclusively; local SQLite is
  retained only for isolated automated tests and no local runtime database is
  created.
- Registration was verified on 2026-09-06 with a live `201 Created` response;
  user responses must continue to exclude password fields and password hashes.

## Current status (as of 2026-09-18)

**Phases 1–6: COMPLETE (with API + caching + P0 test coverage)**

Completed:
- **Phase 1 (Foundation)**: Full CRUD for accounts, transactions, categories — all scoped to authenticated user via JWT
- **Phase 1 Auth**: Local JWT auth originally included bcrypt-backed register/login/me endpoints; local register/login were later removed during the Supabase Auth cleanup
- **Phase 2 (Recurring transactions)**: CRUD `/api/recurring`, occurrence expansion, upcoming transactions
- **Phase 3 (Naive Forecasting)**: `/forecast/cashflow`, `/forecast/runway`, `/forecast/anomalies` — rolling 3-month average
- **Phase 4 (Rule-based categorization)**: `/api/categorize/suggest` with keyword matching + fallback
- **Phase 5 (ML categorization)**: `backend/app/ml/categorizer.py` — LightGBM classifier with TF-IDF features; model train via `/api/categorize/train`; confidence threshold 0.55 fallback; model info endpoint
- **Phase 6 upgrade (prediction caching)**: `/api/forecast/*` and `/api/budget/*` endpoints now read from `predictions` table with TTL caching (24h/12h/24h/7d); `invalidate_predictions()` called on transaction create/update/delete
- **P0 Test Infrastructure**: Isolated async integration-test fixtures with in-memory SQLite, auth helpers, and 82 automated tests passing
- **Auth Migration Phase 1**: Supabase JWT verification implemented in `app/utils/supabase_auth.py` (JWKS fetching/caching, RS256 verification, audience/issuer/expiry validation); 10 unit tests pass; all 72 existing integration tests still pass (82 total); local JWT auth remains live path — Supabase verifier is additive and isolated for Phase 2+ integration
- **Auth Migration Phase 2**: Schema change for `auth.users` FK — Alembic migration `59062dbe3d50` adds `auth_user_id` (UUID) columns with FK to `auth.users.id` on 6 tables (`accounts`, `transactions`, `categories`, `recurring_rules`, `predictions`, `correction_logs`). Cross-schema FK validated against Supabase `auth` schema. Migration is reversible. Models updated with conditional `auth_user_id_column()` helper for test compatibility (SQLite). All 82 tests pass.
- **Auth Migration Phase 3**: `get_current_user` uses Supabase JWT verification in production and local HS256 JWTs only when `TESTING=1`. `AUTH_MODE` is not read by the application. Test fixtures create users directly with local JWT tokens (simulating Supabase user IDs). All 82 tests pass.
- **Auth Migration Phase 4 (CLEANUP COMPLETE)**: Local `/register` and `/login` endpoints removed. Local `users` table dropped via Alembic migration `b3028a70b346` (reversible, drops `user_id` columns and FKs to `public.users`). Local JWT creation (`create_access_token`), bcrypt password hashing, and `SECRET_KEY` retained for test fixtures only. `get_current_user` now exclusively uses Supabase JWT (RS256 via JWKS). All 82 tests pass.

**ML Upgrade (P2): COMPLETE**
- LightGBM regressors for income/expense forecasting — `backend/app/ml/forecasting.py`
- Feature engineering: seasonality (sin/cos encoding), spend velocity, rolling windows, lag features, expanding windows, cyclical encoding
- Separate income/expense regressors with time-series cross-validation
- Confidence intervals (80% default) via residual standard deviation
- Model versioning (`MODEL_VERSION = "1.0.0"`), training metadata, feature importance
- Confidence intervals (80% default) in forecast responses
- `backend/app/routes/forecast.py` updated to use ML forecasting
- `backend/app/ml/forecasting.py` — `ForecastRegressor` + `ForecastManager` classes
- `backend/app/schemas/__init__.py` — `CashflowForecastDay`, `CashflowForecast`, `RunwayForecast`, `AnomaliesResponse` with confidence intervals

**Prediction caching**: all forecast/budget endpoints read from `predictions` table with TTL; transaction create/update/delete invalidates cache

**P0 Complete**: All integration tests for auth/user isolation, CRUD + balance effects, forecast/budget/cache invalidation, category parent ownership validation, and transaction edit policy (`type`/`account_id` immutable) are passing.

**Auth Migration**: Phases 1-4 complete. `get_current_user` uses Supabase RS256/JWKS verification in production and local HS256 only for tests; local auth routes and the local `users` table are removed. All 82 tests pass.

**P1 (Finish documented functionality): COMPLETE**
- Recurring rules reject past `expected_date` (422) via Pydantic future-date validation; `biweekly` and `quarterly` occurrence expansion are supported in `/api/recurring/upcoming`
- Route-level failures use the shared `{code, message, details}` exception envelope (`NotFoundError` etc.); `with_retry` protects read-heavy analytics computations against transient DB errors; startup logs and re-raises a clear error if Alembic migrations fail
- The app factory (`app/factory.py`) owns routers, CORS, request-logging middleware, `/`, `/health`, and the lifespan that runs migrations; `main.py` is a thin entrypoint
- All routes document standard error responses with examples via the shared `app/utils/openapi.py` module
- All 87 tests pass. Remaining explicit debt: `with_db_transaction` not yet used in route business logic, and no circuit breaker is implemented.

**P3 (Production hardening): IN PROGRESS — item 1 (SECRET_KEY/CORS) COMPLETE**
- CORS is `CORS_ORIGINS`-driven with fail-fast: wildcards and unset values raise at startup outside `TESTING=1`
- `SECRET_KEY` is documented as test-only convenience; Supabase Auth signs production tokens
- 5 CORS tests added; 95 tests pass. Remaining P3 items: broader rate limiting, CI, monitoring/backups.

**Deployment and mobile handoff**: The FastAPI backend is deployed on Render with
Supabase Auth as the production provider. Render uses `/health` as the health-check
path; the endpoint verifies database connectivity with `SELECT 1`. The mobile
client must use `@supabase/supabase-js`, send Supabase access tokens as Bearer
 tokens, and target `https://expense-tracker-uwrp.onrender.com` rather than
 localhost. Render health checks use `/health`.

## Tech stack (API-only)

| Layer | Choice | Notes |
|---|---|---|
| **API** | FastAPI (Python 3.13) | Run via `uvicorn main:app --reload` |
| **Database (runtime)** | PostgreSQL via Supabase Transaction pooler | Port 6543; `statement_cache_size=0` |
| **Database (tests)** | In-memory SQLite via `aiosqlite` | Isolated fixtures only; never production data |
| **Auth** | Supabase Auth (RS256 via JWKS) | Local JWT (bcrypt + python-jose) retained for test fixtures only; Supabase Auth is sole provider |
| **ML** | LightGBM, scikit-learn, pandas | Integrated for categorization and cash-flow/runway forecasting |
| **Backend venv** | `backend/venv/` | Activate: `source venv/bin/activate` |

### Important compatibility notes

- **bcrypt pinned to <5**: `passlib` is removed; we use `bcrypt` directly. Version 4.x works; 5.x broke passlib.
- **PostgreSQL**: Supabase Transaction pooler uses port 6543; asyncpg prepared-statement caching is disabled
- **CORS**: loaded from `CORS_ORIGINS` env var; wildcards rejected and missing value fails startup outside tests

## API endpoints (API-only)

All endpoints are scoped to the authenticated user via JWT bearer token.

| Endpoint | Method | Description |
|---|---|---|
| `/api/auth` | GET /me | User info (Supabase Auth handles registration/login) |
| `/api/accounts` | GET /, POST / | List + create accounts |
| `/api/accounts/{id}` | GET /, PUT /, DELETE / | Read/update/delete single account |
| `/api/transactions` | GET /, POST / | List + create transactions |
| `/api/transactions/{id}` | GET /, PUT /, DELETE / | Read/update/delete single transaction |
| `/api/categories` | GET /, POST / | List + create categories |
| `/api/forecast/cashflow` | GET | LightGBM cash-flow forecast with 80% confidence intervals (cached) |
| `/api/forecast/runway` | GET | Runway prediction from ML-projected burn rate (cached) |
| `/api/forecast/anomalies` | GET | Per-category 2x-average outlier detection (cached) |
| `/api/budget/recommendations` | GET | Rule-based budget recommendations (cached, 7d TTL) |
| `/api/budget/category-analysis` | GET | Spending analysis by category (cached, 7d TTL) |
| `/api/categorize/suggest` | POST | Keyword-based category suggestion with ML fallback |
| `/api/categorize/corrections` | POST | Log user corrections for ML training |
| `/api/categorize/train` | POST | Train LightGBM model on correction_logs |
| `/api/categorize/model-info` | GET | Return model training status |

### Prediction caching TTL

| Type | TTL |
|---|---|
| `cashflow` | 24 hours |
| `runway` | 12 hours |
| `anomaly` | 24 hours |
| `budget` | 7 days |
| `budget_analysis` | 7 days |

### Authentication

All API endpoints require a valid JWT bearer token issued by Supabase Auth (RS256).
Mobile and desktop clients should store the token in secure platform storage and
attach it to requests as a Bearer token. If the token is expired or invalid,
the client should delete the stored token and redirect to the Supabase Auth login flow.
Registration and login are handled entirely by Supabase Auth (email/password, OAuth providers).
The backend only verifies the Supabase-issued JWT via JWKS.

### Conventions

- **Python**: type hints throughout; keep Pydantic models accurate
- **SQLite**: `echo=False` in engine config; Alembic migrations use a sync engine
- **CORS**: loaded from `CORS_ORIGINS` env var; wildcards rejected and missing value fails startup outside tests
- **API namespace**: `/accounts`, `/transactions`, `/forecast/cashflow`, etc.
- **All endpoints scoped**: never return another user's data
- **Predictions cached**: write to `predictions` table via scheduled jobs, read
  from cache in the API

## Build phases — implement strictly in this order

### Phase 1: Foundation (CRUD, no ML) ✅ DONE

Completed:
1. Scaffolded repo structure.
2. Configure Supabase PostgreSQL through the Transaction pooler.
3. Implemented all 6 tables via SQLAlchemy ORM.
4. FastAPI: Full CRUD for accounts, transactions, categories — all scoped to authenticated user.
5. JWT auth: register, login, get-me endpoints with bcrypt password hashing.

### Phase 2: Recurring transactions (manual) ✅ DONE

Completed:
- Add-transaction form has a "recurring" checkbox toggle.
- Frequency selector (weekly, bi-weekly, monthly, quarterly, yearly).
- Next-date input for expected recurrence date.
- Backend CRUD for `recurring_rules`: POST /, GET /, GET /upcoming, DELETE /{id}.
- Upcoming transactions auto-generated from rules with occurrence expansion.
- Recurring rule created automatically when transaction is marked recurring.

### Phase 3: Naive forecasting ✅ DONE (later superseded by P2 LightGBM forecasting)

Completed:
- Backend `/forecast/cashflow`: Rolling 3-month average (naive model).
- Backend `/forecast/runway`: Computes days until balance hits threshold using net daily burn rate.
- Backend `/forecast/anomalies`: Per-category 2x-average outlier flagging.

### Phase 4: Rule-based categorization ✅ DONE

Completed:
- Keyword-matching function: maps merchant/description substrings to 14 categories.
- Backend POST `/api/categorize/suggest` returns suggested category + confidence level.
- POST `/api/categorize/corrections` stores corrections for ML training.
- POST `/api/categorize/train` trains model on correction_logs data.
- GET `/api/categorize/model-info` returns training status.
- Confidence threshold 0.55 — falls back to rules when ML confidence is low.

### Phase 5: ML categorization ✅ DONE

Completed:
- `backend/app/ml/categorizer.py`: LightGBM classifier with TF-IDF features.
- Model saved/loaded from disk (`backend/app/ml/saved_models/`).
- Minimum 30 correction samples required to train.
- Confidence threshold 0.55 — falls back to rules when ML confidence is low.
- POST `/api/categorize/train` — trains model on all correction_logs data.
- GET `/api/categorize/model-info` — returns training status.

### Phase 6: Prediction caching ✅ DONE

Completed:
- Backend forecast/budget endpoints read from `predictions` table with TTL
- Transaction create/update/delete calls `invalidate_predictions()`
- TTLs: cashflow 24h, runway 12h, anomaly 24h, budget/budget_analysis 7d

### Phase 7: Runway prediction ✅ DONE

Completed:
- Backend `/forecast/runway`: Computes days until balance hits threshold using net daily burn rate.

### Phase 8: Anomaly detection ✅ DONE

Completed:
- Backend `/forecast/anomalies`: Per-category 2x-average outlier flagging.

### Phase 9: Budget recommendations ✅ DONE

Completed:
- Backend `/budget/recommendations`: Rule-based budget caps per category based on historical average + income percentage.
- Backend `/budget/category-analysis`: Full spending breakdown by category.

### Phase 10: Auto-recurrence detection — NOT STARTED

Deferred until further notice.

## Incremental Change Log

Every major project change must be added here with its date, commit identifier
or focused commit description, files affected, and verification performed. The
entries below begin with the P0 implementation history and remain applicable to
future phases.

| Date | Commit | Description |
|---|---|---|
| 2026-09-06 | Test infrastructure | Added `backend/tests/conftest.py` with async fixtures: in-memory SQLite, `db_session`, `client` with ASGITransport, `register_user`, `auth_user`/`second_user`, `auth_client`/`second_client`, `create_account`/`create_account_second`/`create_account_direct` |
| 2026-09-06 | Auth & isolation tests | Created `backend/tests/test_auth_integration.py` with 14 tests: registration (201/duplicate 400), login (token/wrong password 401), protected endpoints (401/me), user isolation (accounts, transactions, categories, recurring rules all return 404 for foreign users, scoped lists return only own data) |
| 2026-09-06 | CRUD tests | Created `backend/tests/test_crud_integration.py` with 35 tests: accounts (create/list/get/update/delete/ownership), transactions (income/expense create, filters, get, amount update adjusts balance, metadata no balance change, type/account_id immutable, delete reverses balance, 404 missing/foreign account), categories (defaults seeded, create/list/get/update/delete, parent_id same-user OK, foreign parent_id 404 create/update, ownership), recurring rules (create linked to own tx, reject foreign tx, list/delete, ownership, upcoming expansion) |
| 2026-09-06 | Forecast/budget/cache tests | Created `backend/tests/test_forecast_budget_integration.py` with 23 tests: forecast endpoints (cashflow/runway/anomalies shape + isolation), budget endpoints (recommendations/category-analysis shape + isolation), cache (read/write, TTL behavior for cashflow/runway/anomaly/budget), invalidation (tx create/update/delete, account create/update/delete, recurring create/delete all invalidate), cross-user cache isolation |
| 2026-09-06 | Category parent_id validation | Modified `backend/app/routes/categories.py`: added parent_id ownership check in `create_category` and `update_category` — returns 404 if parent belongs to another user |
| 2026-09-06 | RecurringRule schema fix | Added `transaction_id: Optional[str] = None` to `RecurringRule` response schema in `backend/app/schemas/__init__.py` |
| 2026-09-06 | Route trailing slashes | Updated test endpoints to use trailing slashes (`/api/accounts/`, `/api/transactions/`, `/api/categories/`, `/api/recurring/`) to avoid 307 redirects |
| 2026-09-06 | Documentation | Updated `TODO.md` (all P0 items ✅, verification log) and `AGENTS.md` (current status, what's next) |
| 2026-09-07 | Auth Migration Phase 1 | Added `app/utils/supabase_auth.py` with JWKS fetching/caching, RS256 signature verification, audience/issuer/expiry validation; 10 unit tests in `tests/test_supabase_auth.py` (mocked JWKS + real RSA key validation); all 72 existing integration tests still pass (82 total); local JWT auth remains live path — Supabase verifier is additive and isolated for Phase 2+ integration |
| 2026-09-07 | Auth Migration Phase 2 | Alembic migration `59062dbe3d50` adds `auth_user_id` (UUID) columns with FK to `auth.users.id` on 6 tables (`accounts`, `transactions`, `categories`, `recurring_rules`, `predictions`, `correction_logs`). Cross-schema FK validated against Supabase `auth` schema. Migration is reversible. Models updated with conditional `auth_user_id_column()` helper for test compatibility (SQLite). All 82 tests pass. |
| 2026-09-07 | Auth Migration Phase 3 | `get_current_user` uses Supabase JWT verification in production and local HS256 JWTs only when `TESTING=1`; `AUTH_MODE` is not read by the application. Test fixtures use local JWTs to simulate Supabase user IDs. All 82 tests pass. |
| 2026-09-07 | Auth Migration Phase 4 (CLEANUP) | Local `/register` and `/login` endpoints removed. Local `users` table dropped via Alembic migration `b3028a70b346` (reversible, drops `user_id` columns and FKs to `public.users`). Local JWT creation (`create_access_token`), bcrypt password hashing, and `SECRET_KEY` retained for test fixtures only. `get_current_user` now exclusively uses Supabase JWT (RS256 via JWKS). All 82 tests pass. |
| 2026-09-10 | Render deployment and mobile handoff | Deployed the FastAPI backend with Supabase Auth at `https://expense-tracker-uwrp.onrender.com`. Configured `/health` for Render database-connectivity checks. Documented mobile use of `@supabase/supabase-js` and Bearer access tokens. |
| 2026-09-07 | OpenAPI/schema docs | Comprehensive OpenAPI schema with metadata, tags, servers, security schemes, and detailed descriptions. Swagger UI at `/docs`, ReDoc at `/redoc`. |
| 2026-09-07 | ML Upgrade (P2) | Added `backend/app/ml/forecasting.py` with `ForecastRegressor` + `ForecastManager` — separate LightGBM income/expense regressors, feature engineering (seasonality, velocity, rolling windows, lag features, expanding windows, cyclical encoding), time-series CV, confidence intervals (80%), model versioning. Updated `backend/app/routes/forecast.py` to use ML forecasting. Added `CashflowForecastDay`, `CashflowForecast`, `RunwayForecast`, `AnomaliesResponse` with confidence intervals in `backend/app/schemas/__init__.py`. All 82 tests pass. |
| 2026-09-07 | P1 Progress | Added `RecurringPattern` enum (daily/weekly/biweekly/monthly/quarterly/yearly) and Pydantic validation to `TransactionCreate` and `RecurringRuleBase`. Transaction creation auto-creates `RecurringRule` when `is_recurring=1` with required fields. Added `RecurringRule` schema with `auth_user_id`. All 82 tests pass. |
| 2026-09-07 | Error Handling & App Factory | Added `app/utils/exceptions.py` with custom exceptions (ValidationError, NotFoundError, ConflictError, DatabaseError, MigrationError, ExternalServiceError) and SQLAlchemy error handlers. Created `app/factory.py` with `create_app()` factory function; `main.py` now uses factory. Added `with_retry` decorator for DB operations and `with_db_transaction` context manager. Helpers are not yet used consistently across routes/migrations, and no circuit breaker exists. All 82 tests pass. |
| 2026-09-10 | Documentation consistency | Repaired forecast route-example syntax, added missing `Transaction`, `CashflowForecastDay`, and `AnomalyItem` OpenAPI schema examples, removed the stale duplicate P1–P3 checklist, corrected P1/P2/P3 checklist states, reconciled `budget_analysis` cache documentation, and pointed root `MIGRATION.md` to `docs/MIGRATION.md`. Verified `backend/venv/bin/python -m pytest -q backend/tests` (82 passed) and `backend/venv/bin/python -m compileall -q backend/app backend/tests`. |
| 2026-09-12 | DS/DE case studies | Added five role-focused case studies and a reading guide under `docs/case-studies/`, and linked them from `README.md`. File-reference checks only; no application-code changes. |
| 2026-09-16 | P1 recurring validation + expansion (`f13057e`) | Pydantic future-date validation rejects past `expected_date` (422) for recurring rules and recurring transaction creation; `biweekly`/`quarterly` occurrence expansion in `/api/recurring/upcoming`. Added 4 tests. 86 tests pass. |
| 2026-09-16 | P1 error handling + retry (`32a87c4`) | Routes raise shared `NotFoundError` (envelope `{code, message, details}`) instead of bare 404; `with_retry` applied to anomalies/recommendations/category-analysis computations. Added envelope test. 87 tests pass. |
| 2026-09-16 | P1 app factory alignment (`5381f22`) | Rewrote `app/factory.py` to own routers, CORS, logging middleware, `/`, `/health`, exception handlers, and a lifespan that runs migrations (previously lifespan was never wired, so migrations did not run at startup). `main.py` is a thin entrypoint. 87 tests pass. |
| 2026-09-16 | P1 OpenAPI route examples (`38834b7`) | Added shared `app/utils/openapi.py` error blocks (400/401/404/422/429/500) and `responses=`/summaries/descriptions on all accounts, transactions, categories, recurring, budget, categorize, and auth route decorators; forecast refactored to the shared module. 87 tests pass. |
| 2026-09-16 | P1 docs sync | Marked P1 complete in `TODO.md`, `AGENTS.md`, and `docs/phases/P1_PHASE.md`; reconciled factory/lifespan description in `docs/INFRASTRUCTURE.md`; corrected P3 phase status. Merely a documentation pass; no application-code changes. |
| 2026-09-17 | Fix Render startup: Alembic ini path | `backend/app/factory.py` resolved `alembic.ini` relative to `backend/app/` (where it does not exist), so startup failed with `No 'script_location' key found in configuration`. Lifespan now uses backend-dir `ALEMBIC_INI`; added `tests/test_factory.py` (3 tests) guarding ini path, `script_location` resolution, and lifespan wiring. 90 tests pass. |
| 2026-09-17 | Docs + agent guidance update | `docs/INFRASTRUCTURE.md` step 5 now documents that migrations run automatically at boot (lifespan → `alembic upgrade head`, `backend/alembic.ini`, `env.py` sync-driver handling) instead of a manual command. `AGENTS.md` gained an "Ask before acting; do not improvise" section requiring the agent to stop and ask the user whenever intent/scope is unclear. Documentation-only; no application-code changes. |
| 2026-09-18 | P3 item 1: SECRET_KEY/CORS hardening | Added `get_cors_origins()` to `backend/app/factory.py` — CORS loads from `CORS_ORIGINS` (comma-separated allowlist); wildcard sequences and unset values raise `RuntimeError` at startup unless `TESTING=1`. Added 5 CORS tests in `tests/test_factory.py`; updated `.env.example`, `README.md`, `SECURITY.md`, `docs/INFRASTRUCTURE.md`, `docs/phases/P3_PHASE.md` (item 1 complete), and `TODO.md`. 95 tests pass. |

## What to do next (priority order)

1. **P3: Production hardening** — Broader rate limiting (item 2), CI, monitoring/backups. Item 1 (SECRET_KEY/CORS) is complete: CORS is `CORS_ORIGINS`-driven with fail-fast, `SECRET_KEY` is documented as test-only.
2. **Mobile integration** — Configure the mobile repository with the final Render API URL (`https://expense-tracker-uwrp.onrender.com`) and Supabase project settings
3. **Documented technical debt** — Wire `with_db_transaction` into route business logic (startup/transaction rollbacks) and implement a circuit breaker for external service calls

## Conventions the agent must follow throughout

- **Python**: type hints throughout; keep Pydantic models accurate
- **Database**: Supabase PostgreSQL at runtime; in-memory SQLite is test-only
- **CORS**: loaded from `CORS_ORIGINS` env var; wildcards rejected and missing value fails startup outside tests
- **API namespace**: `/accounts`, `/transactions`, `/forecast/cashflow`, etc.
- **All endpoints scoped**: never return another user's data
- **Predictions cached**: write to `predictions` table via scheduled jobs, read from cache in the API

## Repository structure (API-only)

```
/Expense_Tracker
  /backend                        FastAPI API app
    main.py                       Thin entrypoint: load_dotenv + create_app()
    requirements.txt              Python deps (aiosqlite, fastapi, lightgbm, etc.)
    .env                          DATABASE_URL, SECRET_KEY, CORS_ORIGINS
    /app
      factory.py                App factory: routers, CORS, middleware, /health, lifespan(migrations)
      /db
        database.py               Async engine, session factory, init_db()
      /models
        __init__.py               SQLAlchemy ORM: auth-users lookup, Account, Transaction, Category, RecurringRule, Prediction, CorrectionLog
      /schemas
        __init__.py               Pydantic request/response schemas
      /routes
        __init__.py
        auth.py                   GET /me
        accounts.py               CRUD /accounts
        transactions.py           CRUD /transactions (with filtering, balance updates, conditional recurring-rule creation)
        categories.py             CRUD /categories
        forecast.py               GET /forecast/cashflow, /runway, /anomalies
        budget.py                 GET /budget/recommendations, /category-analysis
        recurring.py              CRUD /recurring + GET /recurring/upcoming
        categorize.py             POST /categorize/suggest, /categorize/corrections, /categorize/train
      /services
        categorize.py             Keyword-to-category mapping + suggest function
        seed.py                   Default category seeding
        prediction_cache.py       Prediction cache with TTL and invalidation
      /ml
        __init__.py
        categorizer.py            LightGBM classifier with TF-IDF features
        forecasting.py            LightGBM income/expense forecast regressors
        saved_models/             Persisted models (auto-created on train)
      /utils
        __init__.py               Supabase auth verification, test JWT helpers, retry/transaction helpers
        exceptions.py             Application and database error handlers
        rate_limit.py             Rate-limit configuration
        supabase_auth.py          Supabase JWKS verification
        openapi.py                Shared OpenAPI error response blocks
    /migrations                   Alembic migration config + versions
    /alembic.ini                  Alembic configuration
  /docs/case-studies              DS/DE case studies and reading guide
  /AGENTS.md