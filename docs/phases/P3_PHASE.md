# P3 Phase: Production Hardening

## Overview
Hardening the API for production deployment. Focus on reliability, observability, security, and deployment readiness.

## Status: In Progress (partial)

Parts are complete or underway independent of production hardening: Supabase Auth is the sole auth provider, the app-factory lifespan runs migrations at startup, per-endpoint rate limits are enforced with user-or-IP buckets, CORS is env-driven and fails fast in production, structured JSON logging with correlation IDs is active, error monitoring (Sentry) is optional via `SENTRY_DSN`, and daily `pg_dump` backups run via GitHub Actions (Free-tier, 7-day artifact/Dialog dashboard). Remaining P3 work (CI) is unscoped. Documented debt (atomic `with_db_transaction` + Supabase JWKS circuit breaker) is complete.

---

## Tasks

### 1. Production SECRET_KEY & CORS
**Status**: Complete — CORS is read from `CORS_ORIGINS` (comma-separated allowlist); wildcards are rejected and a missing value fails startup outside tests. `SECRET_KEY` remains a test-only convenience value because Supabase Auth signs production tokens.
**Priority**: Critical

**Requirements:**
- Generate strong production `SECRET_KEY` (32+ bytes)
- Configure environment-specific CORS origins
- Remove wildcard CORS in production

**Files:**
- `backend/.env.example` — `CORS_ORIGINS` documented
- `backend/app/factory.py` — `get_cors_origins()` reads `CORS_ORIGINS`, raises `RuntimeError` when unset or wildcard outside `TESTING=1`

**Acceptance:**
- Production uses unique SECRET_KEY — documented; SECRET_KEY only mints test tokens (Supabase signs production tokens)
- CORS origins configurable via `CORS_ORIGINS` env var — implemented
- No wildcard origins in production — enforced at startup (fail fast)

---

### 2. Rate Limiting
**Status**: Complete — per-endpoint tiers enforced via `slowapi` with user-or-IP buckets; `429` + `Retry-After` on excess; tiers documented in `/docs` and `ERROR_429` on all API routes.
**Priority**: High

**Requirements:**
- Configure rate limits per endpoint tier
- Auth endpoints: stricter limits
- API endpoints: generous but protective
- Return `429` with `Retry-After` header

**Current State:**
- `slowapi` installed; limiter wired in `app/factory.py` (`RateLimitExceeded` handler) with tiers in `app/utils/rate_limit.py`
- Buckets keyed by Bearer `sub` claim (bucketing only, enforced post-auth), falling back to client IP
- Tiers: auth `/me` 60/min, reads 120/min, writes 30/min, analytics 60/hour, train 2/hour (unchanged)
- Limits disabled under `TESTING=1` by design; tier contract + key function + 429 documentation covered by `tests/test_rate_limit.py`

**Remaining:**
- Tune limits based on load testing
- A future bulk-sync feature should get its own dedicated tier (all current writes are single-item; no bulk endpoints exist)

---

### 3. Structured Logging
**Status**: Complete — JSON logs with correlation IDs, redaction, and request metadata via `app/utils/logging.py` + `app/middleware/logging.py`; wired in `app/factory.py`.
**Priority**: High

**Requirements:**
- JSON-structured logs
- Correlation IDs for request tracing
- Log levels: DEBUG, INFO, WARNING, ERROR
- Include: request_id, user_id, method, path, status, latency
- Redact sensitive fields (tokens, passwords)

**Files:**
- `backend/app/utils/logging.py` — JSONFormatter, redaction helpers, context vars (`request_id_var`, `request_user_var`), `setup_logging()`
- `backend/app/middleware/logging.py` — `logging_middleware` (X-Request-ID generation/propagation, timing, user_id extraction from Bearer `sub`, redacted path, adds `X-Request-ID` to response, emits structured `request completed` log)
- `backend/app/factory.py` — calls `setup_logging()` at import and wires `logging_middleware` via `@app.middleware("http")`

**Output Format:**
```json
{
  "timestamp": "2026-09-07T10:30:00.123Z",
  "level": "INFO",
  "request_id": "req_abc123",
  "user_id": "user_123",
  "method": "POST",
  "path": "/api/transactions/",
  "status": 201,
  "latency_ms": 45,
  "service": "expense-tracker"
}
```

**Acceptance:**
- Every request emits a structured JSON log (`expense_tracker.request` logger, `request completed` with `request_id`, `user_id`, `method`, `path`, `status`, `latency_ms`, `service`) — verified via `TestClient` and `caplog`
- No secrets appear in logs: `Authorization` header values and sensitive query params (`password`, `token`, `secret`) are redacted; `X-Request-ID` header propagated
- Logs include `request_id`, `user_id`, `status`, `latency_ms`, `service` context — verified via 4 tests in `tests/test_factory.py` (107 total pass)

---

### 4. Error Monitoring
**Status**: Complete — Sentry optional via `SENTRY_DSN` (disabled in `TESTING=1` or when unset), initialized in `app/factory.py` lifespan, captures migrations failures and user context.
**Priority**: High

**Requirements:**
- Integrate Sentry (or similar)
- Capture unhandled exceptions with context
- Alert on error rate spikes
- Track error patterns

**Implementation:**
- Added `sentry-sdk[fastapi]` to `requirements.txt`
- `app/utils/sentry.py` — `init_sentry()` (reads `SENTRY_DSN`, `ENVIRONMENT`, `SENTRY_TRACES_SAMPLE_RATE`, respects `TESTING=1`), `capture_user_context()`, `is_sentry_enabled()`
- `app/factory.py` lifespan calls `init_sentry()` before migrations, captures migration failures via `sentry_sdk.capture_exception`
- `app/middleware/logging.py` and `app/utils/__init__.py:get_current_user` attach Bearer `sub` to Sentry scope (non-auth, best-effort)
- `.env.example` documents `SENTRY_DSN`, `ENVIRONMENT`, `SENTRY_TRACES_SAMPLE_RATE`

**Acceptance:**
- Sentry disabled when `SENTRY_DSN` not set or `TESTING=1` — no crash, 3 tests in `tests/test_sentry.py`
- When enabled, unhandled exceptions and migration failures are reported with `user_id` scope

---

### Debt: Atomic transactions & Circuit breaker (documented debt)
**Status**: Complete — `with_db_transaction`/`db_transaction` wired for atomic balance + recurring rule; circuit breaker protects Supabase JWKS fetch with 503 on outage.
**Priority**: High

**Requirements:**
- Wire `with_db_transaction` into route business logic (balance + recurring rule atomic)
- Circuit breaker for external service calls (Supabase JWKS)

**Files:**
- `backend/app/utils/__init__.py` — `db_transaction` context manager + fixed `with_db_transaction` (nested transaction support)
- `backend/app/services/prediction_cache.py` — `store_prediction`/`invalidate_predictions` now `flush` when `in_transaction()` else `commit`
- `backend/app/routes/transactions.py` — `create_transaction` wrapped in `async with db_transaction(db)` for atomic balance + recurring rule
- `backend/app/utils/circuit_breaker.py` — `CircuitBreaker` (CLOSED/OPEN/HALF_OPEN, 3 failures → OPEN 60s), `supabase_jwks_breaker`, `circuit_breaker` decorator
- `backend/app/utils/supabase_auth.py` — `_fetch_jwks` wrapped with breaker, `_jwks_lock` for thundering-herd, `_clear_jwks_cache()` for tests, raises `ExternalServiceError` (503)

**Acceptance:**
- Balance + transaction + recurring rule atomically commit or rollback — 3 tests in `tests/test_with_db_transaction.py`
- JWKS fetch fast-fails with `503 EXTERNAL_SERVICE_UNAVAILABLE` when breaker OPEN, recovers after timeout — 5 tests in `tests/test_circuit_breaker.py`

---

### 5. Backups & Point-in-Time Recovery
**Status**: Complete — Free-tier daily `pg_dump` via GitHub Actions + Dashboard snapshots as view-only fallback; PITR not available on Free (Pro required).
**Priority**: High

**Requirements:**
- Automated daily Supabase backups
- Point-in-time recovery configured
- Backup verification script
- Documented restore procedure

**Implementation (Free plan):**
- `.github/workflows/backup.yml` — daily cron `0 2 * * *` + `workflow_dispatch`, masks `DATABASE_URL` via `::add-mask::`, smoke-tests `SELECT 1`/`pg_is_in_recovery()`, runs `pg_dump -Fc` + plain SQL, uploads artifact `pg-backup-<TIMESTAMP>` with `retention-days: 7` (no S3)
- `backend/scripts/verify_backup.py` — `SELECT 1` + `pg_is_in_recovery()` + optional local dump age check (`--path backup-*.dump --max-age-hours 24`), never logs `DATABASE_URL`
- `docs/ops/RESTORE.md` — full runbook: manual `pg_dump`/`pg_restore`/`psql` + `alembic upgrade head` + `curl /health` + Bearer round-trip, troubleshooting (`password authentication failed` → secret/encoding, `CORS_ORIGINS is not set`, `429`, `503` breaker), retention/limits (Free: daily snapshot 7-day view-only, artifact 7-day private, local dumps gitignored)
- Supabase Dashboard → Database → Backups remains view-only on Free; Pro PITR slider is documented as upgrade path when needed

**Acceptance:**
- Workflow exists and is masked/permission-scoped (`permissions: contents: read`, `if: secrets.DATABASE_URL != ''`)
- `docs/ops/RESTORE.md` linked from `docs/INFRASTRUCTURE.md` and `TODO.md:182`
- Verify: `DATABASE_URL=... python backend/scripts/verify_backup.py` + `gh run list --workflow=backup` shows green run + artifact; `backend/venv/bin/python -m pytest -q` still 119 passing

---

### 6. Database Health Check
**Status**: Partial (health endpoint exists)  
**Priority**: Medium

**Current:**
- `/health` endpoint checks DB connectivity

**Enhancements:**
- Check migration status
- Check connection pool health
- Check replication lag (if applicable)
- Return detailed status for monitoring

**Files:**
- `backend/app/routes/health.py` (new) or extend `main.py`

---

### 7. CI/CD Pipeline
**Status**: Complete — `ci.yml` runs on PR + push to `main` with test, lint, and security jobs; no secrets required.
**Priority**: High

**Requirements:**
- GitHub Actions workflow
- Run on PR and main branch
- Steps: lint, typecheck, test, build, security scan
- Deploy to staging on main, production on tag

**Implementation (this repo):**
- `.github/workflows/ci.yml` — 3 jobs on `ubuntu-latest` with `python 3.13`:
  - `test`: `pip install -r backend/requirements.txt`, `python -m compileall -q`, `TESTING=1 python -m pytest backend/tests -q` (in-memory SQLite, no `DATABASE_URL`/`SUPABASE_*` needed, 119 tests)
  - `lint`: `pip install ruff`, `ruff check` + `ruff format --check` (advisory, `continue-on-error` via `|| echo ::warning::`), `compileall`
  - `security`: `pip install pip-audit bandit`, `pip-audit` + `bandit -r backend/app -ll` (advisory)
  - `permissions: contents: read`, no secrets, `actions/setup-python@v7` with `cache: pip`, `timeout-minutes: 10-20`, `workflow_dispatch` for manual runs
  - Render still auto-deploys on push to `main` (`docs/INFRASTRUCTURE.md:59`); `cd.yml` staging/prod tags deferred as overkill for Render Free — `ci.yml` is the gate

**Files:**
- `.github/workflows/ci.yml` (added)
- `.github/dependabot.yml` (weekly `pip` + `github-actions` updates)

**Acceptance:**
- PR/push triggers CI and gates `main` (branch protection can require `ci` status)
- `TESTING=1` ensures no external DB/Auth needed in CI
- Verify: `python -m compileall -q` + `TESTING=1 python -m pytest backend/tests -q` locally still 119 passing; push to trigger `ci` on GitHub → green

---

### 8. Dependency & Security Scanning
**Status**: Not Started  
**Priority**: Medium

**Requirements:**
- `pip-audit` in CI
- `bandit` for security linting
- `safety` check for known vulnerabilities
- Dependabot alerts enabled

**Files:**
- Add to CI pipeline
- `requirements.txt` pinned versions
- `requirements-dev.txt` for dev deps

---

### 9. Structured Deployment
**Status**: Not Started  
**Priority**: High

**Requirements:**
- Dockerfile optimized (multi-stage)
- Docker Compose for local/staging
- Kubernetes manifests or similar for prod
- Health checks in container
- Graceful shutdown handling

**Files:**
- `Dockerfile` (optimize)
- `docker-compose.yml` (update)
- `k8s/` manifests (new)

---

### 10. HTTPS & TLS
**Status**: Not Started  
**Priority**: Critical

**Requirements:**
- TLS 1.2+ enforced
- HSTS headers
- Certificate auto-renewal (Let's Encrypt or managed cert)
- Redirect HTTP → HTTPS

**Implementation:**
- Reverse proxy (nginx/Traefik) handles TLS
- App runs HTTP internally
- Configure in load balancer / ingress

---

### 11. API Versioning Strategy
**Status**: Not Started  
**Priority**: Medium

**Requirements:**
- URL versioning: `/api/v1/...`
- Deprecation policy documented
- Backward compatibility for 6 months

**Implementation:**
- Add version prefix to all routes
- Update OpenAPI version
- Document in `docs/API_VERSIONING.md`

---

## Dependencies
- P0: Complete ✅
- P1: Complete ✅
- P2 (ML Upgrade): Complete ✅

## Timeline Estimate
| Task | Estimate |
|------|----------|
| 1. SECRET_KEY/CORS | 0.5 day ✅ done (2026-09-18) |
| 2. Rate Limiting | 1 day ✅ done (2026-09-18) |
| 3. Structured Logging | 1-2 days ✅ done (2026-09-19) |
| 4. Error Monitoring | 1 day ✅ done (2026-09-19) |
| 5. Backups/PITR | 1 day ✅ done (2026-09-19, Free-tier pg_dump) |
| 6. Health Checks | 0.5 day |
| 7. CI/CD Pipeline | 2-3 days ✅ done (2026-09-19, ci.yml) |
| 8. Security Scanning | 0.5 day ✅ done via ci.yml security job |
| 9. Deployment | 2-3 days |
| 10. HTTPS/TLS | 1 day |
| 11. API Versioning | 1 day |
| **Total** | **11-14 days** |

## Definition of Done
- [ ] All P3 tasks complete
- [ ] CI/CD pipeline passes
- [ ] Staging deployment works
- [ ] Production deployment documented
- [ ] Monitoring/alerting configured
- [ ] Runbooks for common operations