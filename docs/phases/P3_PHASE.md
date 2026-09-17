# P3 Phase: Production Hardening

## Overview
Hardening the API for production deployment. Focus on reliability, observability, security, and deployment readiness.

## Status: In Progress (partial)

Parts are complete or underway independent of production hardening: Supabase Auth is the sole auth provider, the app-factory lifespan runs migrations at startup, `slowapi` limits ML training, and CORS is env-driven and fails fast in production. Remaining P3 work (broader rate limits, CI, monitoring, backups) is unscoped.

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
**Status**: Partially Done (slowapi added)  
**Priority**: High

**Requirements:**
- Configure rate limits per endpoint tier
- Auth endpoints: stricter limits
- API endpoints: generous but protective
- Return `429` with `Retry-After` header

**Current State:**
- `slowapi` installed
- Limiter configured in `main.py`
- Auth endpoints: 5/min (register), 10/min (login)
- Categorization train: 2/hour

**Remaining:**
- Tune limits based on load testing
- Add IP-based + user-based limiting
- Document limits in OpenAPI

---

### 3. Structured Logging
**Status**: Not Started  
**Priority**: High

**Requirements:**
- JSON-structured logs
- Correlation IDs for request tracing
- Log levels: DEBUG, INFO, WARNING, ERROR
- Include: request_id, user_id, method, path, status, latency
- Redact sensitive fields (tokens, passwords)

**Files:**
- `backend/app/utils/logging.py` (new)
- `backend/main.py` — Configure logging
- `backend/app/middleware/logging.py` (new middleware)

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
  "latency_ms": 45
}
```

---

### 4. Error Monitoring
**Status**: Not Started  
**Priority**: High

**Requirements:**
- Integrate Sentry (or similar)
- Capture unhandled exceptions with context
- Alert on error rate spikes
- Track error patterns

**Implementation:**
- Add `sentry-sdk` to requirements
- Initialize in `main.py` lifespan
- Add `sentry_sdk.init()` with DSN from env
- Capture user_id in scope

---

### 5. Backups & Point-in-Time Recovery
**Status**: Not Started  
**Priority**: High

**Requirements:**
- Automated daily Supabase backups
- Point-in-time recovery configured
- Backup verification script
- Documented restore procedure

**Implementation:**
- Configure in Supabase dashboard
- Document restore procedure in `docs/ops/RESTORE.md`
- Test restore quarterly

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
**Status**: Not Started  
**Priority**: High

**Requirements:**
- GitHub Actions workflow
- Run on PR and main branch
- Steps: lint, typecheck, test, build, security scan
- Deploy to staging on main, production on tag

**Pipeline Steps:**
```yaml
jobs:
  lint:
    - ruff check .
    - mypy backend/app
  test:
    - pytest tests/
  security:
    - pip-audit
    - bandit -r backend/app
  build:
    - docker build
  deploy-staging:
    - deploy to staging env
  deploy-prod:
    - on tag, deploy to production
```

**Files:**
- `.github/workflows/ci.yml` (new)
- `.github/workflows/cd.yml` (new)

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
- P1: In Progress
- P2 (ML Upgrade): Complete ✅

## Timeline Estimate
| Task | Estimate |
|------|----------|
| 1. SECRET_KEY/CORS | 0.5 day ✅ done (2026-09-18) |
| 2. Rate Limiting | 1 day |
| 3. Structured Logging | 1-2 days |
| 4. Error Monitoring | 1 day |
| 5. Backups/PITR | 1 day |
| 6. Health Checks | 0.5 day |
| 7. CI/CD Pipeline | 2-3 days |
| 8. Security Scanning | 0.5 day |
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