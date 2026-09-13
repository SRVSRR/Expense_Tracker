# Shipping Analytics Safely: Caching, Budgets, Deployment, and Handoff

**Reading time:** 8 minutes  
**Audience:** Data engineering, platform engineering, and hiring managers  
**Repository evidence:** `backend/app/services/prediction_cache.py`, `backend/app/routes/budget.py`, `backend/main.py`, `docs/INFRASTRUCTURE.md`

## Problem

A correct API is not automatically a production-ready platform. Analytics endpoints can become expensive, repeated requests can recompute the same results, stale outputs can mislead users, deployments can fail silently, and mobile clients can integrate against the wrong environment.

This project needed:

- Fast repeated access to forecasts and budgets.
- Guarantees that edits invalidate stale analytics.
- A deployment with health checks and clear client configuration.
- Documentation that mobile developers can actually use.

Without those properties, every new feature would increase operational risk rather than product value.

## Approach

### 1. Cache derived analytics by user and type

Forecast and budget outputs are cached in the `predictions` table with explicit TTLs:

| Prediction type | TTL |
|---|---|
| `cashflow` | 24 hours |
| `runway` | 12 hours |
| `anomaly` | 24 hours |
| `budget` | 7 days |
| `budget_analysis` | 7 days |

Each cached row stores the requesting user, prediction type, serialized result, generation time, and expiry. Retrieval always returns the newest unexpired entry for that user and type.

This separation matters because forecasts change faster than long-run budget aggregates. A single cache TTL would either recompute stable budget outputs too often or serve volatile cash-flow outputs for too long.

Relevant code:

- `../../backend/app/services/prediction_cache.py`

### 2. Invalidate on every relevant mutation

A cache is only trustworthy if writes and deletes invalidate it correctly. The API invalidates the affected user’s predictions when:

- Transactions are created, updated, or deleted.
- Accounts are created, updated, or deleted.
- Recurring rules are created or deleted.

Account changes matter because balances affect forecasts. Recurring-rule changes matter because expected future transactions affect projections. Invalidation is scoped by user, so one user’s mutation never clears another user’s cached analytics.

That behavior is covered directly by integration tests. Cache tests check valid reuse, expiry and recomputation, mutation-driven invalidation, account and recurring-rule invalidation, and cross-user cache isolation.

### 3. Keep budget analytics explainable

Budget endpoints use transparent rule-based calculations over the prior three months:

- Average monthly income and expenses.
- Savings rate.
- Category-level monthly averages.
- Category share of income or total spending.
- Suggested budgets for high-spend categories.

Examples:

- Categories above 30% of income are flagged as high and receive a reduced suggested budget.
- Categories between 20% and 30% are flagged as moderate.
- Everything else remains on track.

This makes budget recommendations auditable without requiring users to trust an opaque model. Category analysis separately reports totals, monthly averages, transaction counts, and shares of total spending.

Relevant code:

- `../../backend/app/routes/budget.py`

### 4. Deploy with verifiable health and configuration

The production API runs on Render with Supabase PostgreSQL and Supabase Auth. The `/health` endpoint performs a database connectivity check, not merely a process liveness check. Render uses that path for deployment health verification.

Production configuration uses:

- Supabase Transaction pooler URL
- Supabase JWKS URL
- Supabase JWT issuer
- Test-only local JWT secrets isolated from production

For Supabase’s Transaction pooler, the database engine disables asyncpg prepared-statement caching. That setting matters because pooled transaction-mode connections do not support session-scoped prepared statements.

The deployment also retains a clear migration story: startup runs Alembic migrations, while production release practice should treat migrations as an explicit release step.

Relevant documentation:

- `../../docs/INFRASTRUCTURE.md`
- `../../README.md`

### 5. Make mobile integration unambiguous

The mobile handoff avoids localhost ambiguity:

- API base URL: `https://expense-tracker-uwrp.onrender.com`
- Auth header: `Authorization: Bearer <Supabase access token>`
- Health check: `https://expense-tracker-uwrp.onrender.com/health`
- Auth library: `@supabase/supabase-js`
- Token storage: platform secure storage

Mobile devices cannot reach a development machine’s `127.0.0.1`; the case-study documentation explicitly calls out LAN addresses or tunnels for local device testing. Clients are instructed to clear stored tokens on `401` and return to Supabase Auth, rather than retrying indefinitely with an invalid credential.

## Stack

- FastAPI with async SQLAlchemy sessions
- PostgreSQL via Supabase Transaction pooler
- `asyncpg` with disabled prepared-statement caching for pooled connections
- Alembic migrations
- Render deployment with health checks
- OpenAPI, Swagger UI, and ReDoc
- Supabase Auth and `@supabase/supabase-js` for clients

## Results

- Repeated forecast and budget requests can be served from valid cached predictions.
- Data mutations invalidate the affected user’s analytics.
- Cache behavior is isolated across users.
- `/health` verifies database connectivity for deployment checks.
- Mobile developers receive one stable API URL, one auth contract, and one health endpoint.
- Request-driven cache writes are explicitly documented; no hidden scheduler is implied.
- Full test coverage remains in place for cache reads, TTL behavior, mutation invalidation, and cross-user isolation.

### 6. Define failure drills explicitly

Production readiness can be reviewed as a set of failure drills:

- Revoke or expire a token and confirm protected endpoints return `401`.
- Edit a transaction and confirm cached forecasts are recomputed rather than reused.
- Delete an account and confirm balances, forecasts, and budget outputs change consistently.
- Request another user’s resource and confirm the API returns `404`, not data.
- Take the database offline in staging and confirm `/health` reports the dependency failure.

Those checks convert deployment documentation from a narrative into repeatable operational behavior. They also give a hiring reviewer a practical way to validate the platform claims without deploying production infrastructure.

## Lessons

1. **Invalidation is part of the feature.** A cache without tested mutation paths is a future stale-data bug.
2. **Health checks should test dependencies.** A process can be alive while its database is unreachable.
3. **Scope everything by user.** User isolation applies to primary records and derived caches alike.
4. **Deployment docs are product docs.** A stable URL, health path, auth contract, and token-handling rules prevent most integration mistakes.
5. **Document what is not built.** Request-driven caching, permissive development CORS, and missing schedulers should be explicit technical debt rather than surprises.
6. **Keep analytics explainable where possible.** Rule-based budgets complement ML forecasts by giving users an auditable answer alongside a probabilistic one.
