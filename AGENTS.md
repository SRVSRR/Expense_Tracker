# AGENTS.md

## Purpose

This file tells a coding agent exactly what to build, in what order, and how
to know each step is done. Follow the phases in sequence. Do not start a
phase until the previous phase's "Definition of done" is satisfied. If
something here is ambiguous, stop and ask rather than guessing.

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
- Do not mark a checklist item complete based only on a manual smoke test;
  record the verification separately until the corresponding automated test or
  acceptance criteria are satisfied.
- The detailed P0 sequence and acceptance criteria live in
  `docs/P0_PLAN.md`; keep it aligned with this file and `TODO.md`.
- For P0, transaction `type` and `account_id` are intentionally immutable in
  transaction updates. Do not add partial support that can leave two account
  balances inconsistent; a future atomic transfer/type-change feature must be
  planned separately.

## Current status (as of 2026-09-06)

**Phases 1–6: COMPLETE (with API + caching + P0 test coverage)**

Completed:
- **Phase 1 (Foundation)**: Full CRUD for accounts, transactions, categories — all scoped to authenticated user via JWT
- **Phase 1 Auth**: JWT auth with bcrypt hashing, register/login/me endpoints
- **Phase 2 (Recurring transactions)**: CRUD `/api/recurring`, occurrence expansion, upcoming transactions
- **Phase 3 (Naive Forecasting)**: `/forecast/cashflow`, `/forecast/runway`, `/forecast/anomalies` — rolling 3-month average
- **Phase 4 (Rule-based categorization)**: `/api/categorize/suggest` with keyword matching + fallback
- **Phase 5 (ML categorization)**: `backend/app/ml/categorizer.py` — LightGBM classifier with TF-IDF features; model train via `/api/categorize/train`; confidence threshold 0.55 fallback; model info endpoint
- **Phase 6 upgrade (prediction caching)**: `/api/forecast/*` and `/api/budget/*` endpoints now read from `predictions` table with TTL caching (24h/12h/24h/7d); `invalidate_predictions()` called on transaction create/update/delete
- **P0 Test Infrastructure**: Isolated async integration-test fixtures with in-memory SQLite, auth helpers, 72 automated integration tests passing

Not done (ML upgrade):
- LightGBM regressors for income/expense forecasting.
- Feature engineering (seasonality, spend velocity, etc.).
- Prediction caching in `predictions` table via scheduled jobs.
- Confidence ranges in the chart.

**Prediction caching**: all forecast/budget endpoints read from `predictions` table with TTL; transaction create/update/delete invalidates cache

**P0 Complete**: All integration tests for auth/user isolation, CRUD + balance effects, forecast/budget/cache invalidation, category parent ownership validation, and transaction edit policy (`type`/`account_id` immutable) are passing.

## Tech stack (API-only)

| Layer | Choice | Notes |
|---|---|---|
| **API** | FastAPI (Python 3.13) | Run via `uvicorn main:app --reload` |
| **Database (dev)** | SQLite via `aiosqlite` | `backend/expense_tracker.db` |
| **Database (prod)** | PostgreSQL via Supabase | Swap `.env` `DATABASE_URL` |
| **Auth** | Local JWT (bcrypt + python-jose) | Not Supabase Auth yet |
| **ML** | LightGBM, scikit-learn, pandas | Installed but not yet integrated |
| **Backend venv** | `backend/venv/` | Activate: `source venv/bin/activate` |

### Important compatibility notes

- **bcrypt pinned to <5**: `passlib` is removed; we use `bcrypt` directly. Version 4.x works; 5.x broke passlib.
- **SQLite**: `alembic` now uses sync engine — `echo=False` in engine config; alembic `env.py` loads `.env` before anything else
- **CORS**: `allow_origins=["*"]` — adjust for production

## API endpoints (API-only)

All endpoints are scoped to the authenticated user via JWT bearer token.

| Endpoint | Method | Description |
|---|---|---|
| `/api/auth` | POST /register, POST /login, GET /me | Auth registration, login, user info |
| `/api/accounts` | GET /, POST / | List + create accounts |
| `/api/accounts/{id}` | GET /, PUT /, DELETE / | Read/update/delete single account |
| `/api/transactions` | GET /, POST / | List + create transactions |
| `/api/transactions/{id}` | GET /, PUT /, DELETE / | Read/update/delete single transaction |
| `/api/categories` | GET /, POST / | List + create categories |
| `/api/forecast/cashflow` | GET | Rolling 3-month cashflow forecast (cached) |
| `/api/forecast/runway` | GET | Runway prediction based on burn rate (cached) |
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

### Authentication

All API endpoints require a valid JWT bearer token. The token is read from
`SecureStore` (iOS) or `AsyncStorage` (Android) and attached to requests via
the interceptor in `frontend/src/api/client.ts`. If the token is expired or
invalid, the 401 interceptor silently deletes the token from SecureStore and
the app should redirect to the login screen.

### Conventions

- **Python**: type hints throughout; keep Pydantic models accurate
- **SQLite**: `echo=False` in engine config; alembic uses sync engine
- **CORS**: `allow_origins=["*"]` — configure for production
- **API namespace**: `/accounts`, `/transactions`, `/forecast/cashflow`, etc.
- **All endpoints scoped**: never return another user's data
- **Predictions cached**: write to `predictions` table via scheduled jobs, read
  from cache in the API

## Build phases — implement strictly in this order

### Phase 1: Foundation (CRUD, no ML) ✅ DONE

Completed:
1. Scaffolded repo structure.
2. Set up SQLite dev database (Postgres-ready via `.env` swap).
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

### Phase 3: Naive forecasting ✅ DONE

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
- TTLs: cashflow 24h, runway 12h, anomaly 24h, budget 7d

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

## Incremental Commits (P0 Implementation)

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

## What to do next (priority order)

1. **Switch to Supabase** — When ready for production: swap auth to Supabase Auth, swap DB to Supabase Postgres
2. **Add OpenAPI/schema docs** — generate `/docs` and `/redoc` for API consumers
3. **ML upgrade** — Add LightGBM regressors for forecasting (P2)

## Conventions the agent must follow throughout

- **Python**: type hints throughout; keep Pydantic models accurate
- **SQLite**: `echo=False` in engine config; alembic uses sync engine with `.env` loading
- **CORS**: `allow_origins=["*"]` — adjust for production
- **API namespace**: `/accounts`, `/transactions`, `/forecast/cashflow`, etc.
- **All endpoints scoped**: never return another user's data
- **Predictions cached**: write to `predictions` table via scheduled jobs, read from cache in the API

## Repository structure (API-only)

```
/Expense_Tracker
  /backend                        FastAPI API app
    main.py                       App entrypoint (CORS, lifespan, routers)
    requirements.txt              Python deps (aiosqlite, fastapi, lightgbm, etc.)
    .env                          DATABASE_URL, SECRET_KEY
    expense_tracker.db            SQLite database (auto-created on first run)
    /app
      /db
        database.py               Async engine, session factory, init_db()
      /models
        __init__.py               SQLAlchemy ORM: User, Account, Transaction, Category, RecurringRule, Prediction
      /schemas
        __init__.py               Pydantic request/response schemas
      /routes
        __init__.py
        auth.py                   POST /register, POST /login, GET /me
        accounts.py               CRUD /accounts
        transactions.py           CRUD /transactions (with filtering, balance updates)
        categories.py             CRUD /categories
        forecast.py               GET /forecast/cashflow, /runway, /anomalies
        budget.py                 GET /budget/recommendations, /category-analysis
        recurring.py              CRUD /recurring + GET /recurring/upcoming
        categorize.py             POST /categorize/suggest, /categorize/corrections, /categorize/train
      /services
        categorize.py             Keyword-to-category mapping + suggest function
        seed.py                     Default category seeding on signup
      /ml
        __init__.py
        categorizer.py            LightGBM classifier with TF-IDF features
        saved_models/               Persisted models (auto-created on train)
      /utils
        __init__.py               JWT creation, password hashing, get_current_user dependency
    /migrations                   Alembic migration config + versions
    /alembic.ini                  Alembic configuration
  /AGENTS.md

Untracked:
  backend/app/services/prediction_cache.py