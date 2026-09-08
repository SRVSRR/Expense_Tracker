# Auth Migration: Local JWT → Supabase Auth

## Overview
Phased migration from local JWT authentication to Supabase Auth. This document tracks the complete migration plan and progress.

## Why Supabase Auth?
- Native OAuth support (Google, GitHub, Apple, etc.)
- Built-in email/password with verification flows
- Row Level Security (RLS) integration
- Managed token rotation and refresh
- Social login without custom implementation
- Session management and revocation
- Audit logs and security features

## Migration Strategy: Phased Approach

Each phase is additive and reversible. Local JWT remains functional until Phase 4.

---

## Phase 1: Backend Token Verification (✅ Complete)

**Goal**: Add Supabase JWT verification capability alongside local JWT.

**Deliverables:**
- `backend/app/utils/supabase_auth.py` — JWKS fetching/caching, RS256 verification
- `backend/app/utils/supabase_auth.py` — Audience/issuer/expiry validation
- `backend/tests/test_supabase_auth.py` — 10 unit tests (mocked + real RSA)
- Feature flag `AUTH_MODE` to toggle between local/Supabase

**Verification:**
- 10 unit tests pass (mocked JWKS + real RSA key)
- All 72 existing integration tests still pass (82 total)
- Local JWT auth remains live path; Supabase verifier additive

**Files Created:**
- `backend/app/utils/supabase_auth.py`
- `backend/tests/test_supabase_auth.py`

---

## Phase 2: Schema Change for `auth.users` FK (✅ Complete)

**Goal**: Add foreign key to Supabase `auth.users.id` on all user-scoped tables.

**Deliverables:**
- Alembic migration `59062dbe3d50` adds `auth_user_id` (UUID) columns
- Cross-schema FK to `auth.users.id` on 6 tables:
  - `accounts`
  - `transactions`
  - `categories`
  - `recurring_rules`
  - `predictions`
  - `correction_logs`
- Models updated with conditional `auth_user_id_column()` helper
- Migration is reversible

**Verification:**
- Migration applies cleanly to Supabase PostgreSQL
- Cross-schema FK validated against `auth.users`
- All 82 tests pass

**Files:**
- `backend/alembic/versions/59062dbe3d50_add_auth_users_fk.py`
- `backend/app/models/__init__.py` — conditional `auth_user_id_column()`

---

## Phase 3: Switch Live Auth Dependency (✅ Complete)

**Goal**: Make Supabase JWT the default auth path; disable local register/login.

**Deliverables:**
- Feature flag `AUTH_MODE` (`local` | `supabase`)
- `get_current_user` supports both Supabase RS256 and local HS256
- Local `/register` and `/login` return 400 when `AUTH_MODE=supabase`
- Test fixtures updated to simulate Supabase user IDs via local JWT
- All 82 tests pass with `AUTH_MODE=local`

**Files Modified:**
- `backend/app/utils/__init__.py` — `AUTH_MODE` flag, dual verification
- `backend/app/routes/auth.py` — Disabled register/login in supabase mode
- `backend/app/utils/__init__.py` — `is_supabase_auth_mode()`
- `backend/tests/conftest.py` — Test fixtures use local JWT simulating Supabase IDs

---

## Phase 4: Cleanup (✅ Complete)

**Goal**: Remove dead local auth code; Supabase Auth is sole provider.

**Deliverables:**
- Removed `/api/auth/register` and `/api/auth/login` endpoints
- Dropped local `public.users` table via Alembic migration `b3028a70b346`
  - Dropped `user_id` columns and FKs from 6 tables
  - Reversible migration
- `get_current_user` exclusively uses Supabase JWT (RS256 via JWKS)
- Local JWT creation (`create_access_token`), bcrypt, `SECRET_KEY` retained for tests only
- `get_current_user` exclusively uses `verify_supabase_token`

**Migration:**
- `backend/alembic/versions/b3028a70b346_drop_local_users_table.py`

**Files Removed/Modified:**
- `backend/app/routes/auth.py` — Only `/me` remains
- `backend/app/models/__init__.py` — `User` model: `password_hash` only in `TESTING` mode
- `backend/app/utils/__init__.py` — Removed `AUTH_MODE`, `is_supabase_auth_mode()`
- `backend/tests/test_auth_integration.py` — Register/login tests expect 404
- `backend/app/utils/__init__.py` — Removed local JWT verification path

---

## Phase 5: Mobile Integration (📋 Planned)

**Goal**: Document mobile client integration with Supabase Auth.

**Scope:**
- Mobile repo uses `@supabase/supabase-js` directly
- No custom auth screens in mobile app
- Backend only verifies Supabase JWT
- Update mobile repo auth phase tasks

**Timeline**: When mobile repo Phase 1 begins.

---

## Rollback Plan

### Before Phase 4 (Before Cleanup)
- Re-enable local `/register` and `/login` endpoints
- Revert `AUTH_MODE` to `local`
- Re-enable local `users` table (migration downgrade)

### After Phase 4 (After Cleanup)
- Restore local auth code from git history
- Recreate `public.users` table (migration downgrade)
- Re-enable local JWT verification in `get_current_user`

---

## Verification Checklist (All Phases)

- [x] Phase 1: Supabase JWT validator works (10 unit tests)
- [x] Phase 2: FK schema migration applies/reverts cleanly
- [x] Phase 3: `AUTH_MODE=supabase` disables local auth; `AUTH_MODE=local` works
- [x] Phase 4: No local auth code remains; all 82 tests pass
- [ ] Phase 5: Mobile integration guide written (when mobile repo starts)

---

## Configuration

### Environment Variables

```env
# Supabase Auth (required for production)
SUPABASE_JWKS_URL=https://<project-ref>.supabase.co/auth/v1/.well-known/jwks.json
SUPABASE_ISSUER=https://<project-ref>.supabase.co/auth/v1

# Local development (testing only)
AUTH_MODE=local
SECRET_KEY=test-secret-key-for-testing-only
ACCESS_TOKEN_EXPIRE_MINUTES=1440
```

### Supabase Project Setup
1. Create Supabase project
2. Enable Email/Password auth
3. Enable OAuth providers (Google, GitHub, Apple)
4. Configure redirect URLs
5. Copy JWKS URL and Issuer to env

---

## Rollback Commands

```bash
# Revert to Phase 3 (before cleanup)
alembic downgrade b3028a70b346

# Revert to Phase 2 (before feature flag)
alembic downgrade 59062dbe3d50

# Full rollback to local JWT
# 1. Revert code to pre-Phase 1 commit
# 2. alembic downgrade base
# 3. Set AUTH_MODE=local
```

---

## Testing Strategy

| Phase | Tests |
|-------|-------|
| Phase 1 | 10 unit tests for JWKS/RS256 verification |
| Phase 2 | Migration up/down on Supabase + SQLite |
| Phase 3 | Integration tests with `AUTH_MODE=supabase` |
| Phase 4 | Full suite (82 tests) with Supabase-only auth |

---

## Documentation Links

- [P0 Plan](P0_PLAN.md) — Foundation test plan
- [Phase 1](phases/P1_PHASE.md) — Recurring transactions, validation, docs
- [Phase 2](phases/P2_PHASE.md) — ML forecasting upgrade (complete)
- [Phase 3](phases/P3_PHASE.md) — Production hardening
- [SECURITY.md](../SECURITY.md) — Security policy
- [INFRASTRUCTURE.md](../INFRASTRUCTURE.md) — Deployment guide