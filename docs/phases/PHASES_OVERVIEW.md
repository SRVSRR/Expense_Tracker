# Phase Documentation Overview

This directory contains detailed planning documents for each development phase.

## Phase Summary

| Phase | Name | Status | Description |
|-------|------|--------|-------------|
| **P0** | Foundation & Core API | ✅ Complete | Auth, CRUD, basic forecasting, categorization, tests |
| **Auth Migration** | Supabase Auth Migration | ✅ Complete | 4 phases: validator, FK schema, feature flag, cleanup |
| **P1** | Finish Documented Functionality | ✅ Complete | Recurring transactions, validation, error handling, factory alignment, route-level OpenAPI examples |
| **P2** | ML Upgrade | ✅ Complete | LightGBM forecasting with confidence intervals |
| **P3** | Production Hardening | ⏳ Planned | Rate limiting, logging, monitoring, CI/CD, deployment |

---

## Phase Files

| Phase | File | Status |
|-------|------|--------|
| P0 | `docs/P0_PLAN.md` | ✅ Complete |
| P1 | `docs/phases/P1_PHASE.md` | ✅ Complete |
| P2 | `docs/phases/P2_PHASE.md` | ✅ Complete |
| P3 | `docs/phases/P3_PHASE.md` | 📋 Planned |

---

## Phase Dependencies

```
P0 (Foundation) → Auth Migration → P2 (ML Upgrade) → P1 (Finish Features) → P3 (Production)
     ✅              ✅                ✅                 ✅            ⏳ Next
```

## Current Priority

**Active**: P3 — Production Hardening
- Production `SECRET_KEY` and environment-specific CORS origins
- Broader rate limiting and structured logging/monitoring, backups, CI
- Wire `with_db_transaction` into route business logic and implement a circuit breaker for external service calls (documented debt)

---

## Phase Completion Criteria

Each phase is complete when:
- [ ] All tasks checked in TODO.md
- [ ] All tests pass (95/95)
- [ ] Documentation updated
- [ ] AGENTS.md change log updated
- [ ] Code compiles and passes lint/typecheck