# Migrating Production Auth Without Breaking the Product

**Reading time:** 8 minutes  
**Audience:** Backend engineering, platform engineering, and hiring managers  
**Repository evidence:** `docs/MIGRATION.md`, `backend/app/utils/supabase_auth.py`, `backend/alembic/versions/`, `backend/tests/test_supabase_auth.py`

## Problem

The API originally used local JWT authentication with bcrypt-backed passwords. That was sufficient for early development, but it had three growing limitations:

1. No native social login support.
2. No managed session handling for mobile clients.
3. Growing responsibility for password security, token rotation, OAuth flows, and account recovery.

Building Google and Apple login on top of local JWT would have been substantially more work than migrating once to Supabase Auth—especially before mobile clients existed. But authentication is also the most dangerous part of the system to change. A bad migration could lock out users, leak accounts across users, or silently break every protected endpoint.

The migration therefore needed both forward progress and a credible way back. It is especially relevant to backend and data-engineering roles because it combines identity security, schema evolution, automated testing, operational configuration, and downstream client impact.

## Approach

I used a four-phase migration designed to preserve rollback options until the new system was proven.

### Phase 1: Additive Supabase JWT verification

First, I added Supabase JWT verification without changing the live auth path:

- Fetch and cache Supabase JWKS.
- Verify RS256 signatures.
- Validate audience, issuer, and expiry.
- Extract the user identity from the JWT `sub` claim.

Relevant files:

- `../../backend/app/utils/supabase_auth.py`
- `../../backend/tests/test_supabase_auth.py`

The new verifier was tested with mocked JWKS responses and real RSA keys. It accepts valid tokens and rejects tampered, expired, wrong-audience, and wrong-issuer tokens. The existing 72 integration tests still passed untouched.

This mattered because auth changes should first be provable in isolation, before they affect every route.

### Phase 2: Reference Supabase identities in the schema

Next, I added `auth_user_id` columns with foreign keys to Supabase `auth.users.id` on six tables:

- `accounts`
- `transactions`
- `categories`
- `recurring_rules`
- `predictions`
- `correction_logs`

The key production issue was a type mismatch: Supabase’s `auth.users.id` is a UUID, while the existing local identifiers were strings. The migration therefore uses UUID columns in PostgreSQL.

For tests, SQLite does not support the same UUID or cross-schema behavior cleanly, so models use a conditional helper:

- Production: UUID column with a foreign key to `auth.users.id`.
- Tests: ordinary string column for isolated SQLite fixtures.

The migration is reversible. That constraint was intentional: auth migrations should never be one-way until the replacement has proven stable.

Relevant migration:

- `../../backend/alembic/versions/59062dbe3d50_add_auth_users_fk.py`

### Phase 3: Switch the live dependency safely

The main `get_current_user` dependency was then switched to Supabase verification. During the transition, a feature flag preserved rollback:

- Production used Supabase RS256 verification.
- Tests used local HS256 tokens simulating Supabase user IDs.
- Local register/login paths were disabled rather than deleted immediately.

Test fixtures were updated so integration tests continued to simulate distinct Supabase user IDs without needing live Supabase credentials for every test run. Every route continued to scope queries by the authenticated user ID, so cross-user isolation remained intact.

### Phase 4: Remove the old auth path

Only after the full suite passed did I remove the dead code:

- Deleted local `/api/auth/register` and `/api/auth/login`.
- Dropped the local `public.users` table and old `user_id` references through a reversible migration.
- Retained bcrypt, local JWT creation, and `SECRET_KEY` only for isolated test fixtures.
- Made Supabase JWT verification the sole production auth path.

Only `/api/auth/me` remains as a backend auth endpoint. Registration, login, password management, and OAuth live in Supabase Auth.

Relevant migration:

- `../../backend/alembic/versions/b3028a70b346_drop_local_users_table.py`

## Stack

- Supabase Auth with RS256 JWTs
- JWKS-based signature verification
- PostgreSQL with cross-schema foreign keys
- Alembic reversible migrations
- FastAPI authentication dependencies
- `pytest` with async fixtures and isolated databases

## Results

- Supabase Auth is the sole production authentication provider.
- Production tokens are RS256 and verified through Supabase JWKS.
- All business records reference Supabase user IDs.
- Local auth code was removed without breaking the suite.
- **82 automated tests pass**, including authentication and cross-user isolation coverage.
- Rollback remained possible through git history and reversible migrations.
- Passwords and bearer tokens were never written into project files; URL-encoding and secret-handling issues were treated as configuration problems rather than engine problems.

A reviewer can trace each phase to concrete evidence: the JWKS verifier and RSA tests, the two Alembic revisions, the Supabase-only `/api/auth/me` route, and the integration fixtures that preserve distinct user identities. That traceability is what makes the migration reviewable rather than merely plausible.

### What a reviewer should verify

The migration can be checked without trusting the narrative:

- Confirm that production verification uses Supabase JWKS, audience, issuer, and expiry—not a shared local secret.
- Confirm that all six tables carry Supabase user identifiers and that local identifiers are gone from the production schema.
- Confirm that `/api/auth/register` and `/api/auth/login` return `404` because those backend paths no longer exist.
- Confirm that protected endpoints still return `401` for invalid tokens and `404` for another user’s resources.
- Confirm that password, token, JWKS, issuer, and database-URL values never appear in logs, tests, or committed files.

Those checks cover the migration’s most consequential failure modes: broken login, broken authorization, leaked identity, leaked secrets, and irreversible schema damage.

A representative mobile flow is now:

1. Sign in with Supabase Auth in the mobile app.
2. Store the Supabase access token securely.
3. Call the API with:

```sh
curl https://expense-tracker-uwrp.onrender.com/api/auth/me \
  -H 'Authorization: Bearer YOUR_SUPABASE_ACCESS_TOKEN'
```

## Lessons

1. **Migrate auth additively.** Never replace the live path before the replacement is independently tested.
2. **Keep rollback cheap.** Reversible migrations and feature flags turn a risky migration into a sequence of safe steps.
3. **Watch identity types.** UUID versus string identity mismatches are easy to overlook and expensive to fix later.
4. **Test doubles must not weaken production.** Tests simulate Supabase identities locally while production still verifies real RS256 tokens.
5. **Remove dead auth code deliberately.** Old registration and password paths are security liabilities once replaced.
6. **Document secrets handling explicitly.** Never log passwords, tokens, database URLs, or JWKS secrets while troubleshooting authentication.
