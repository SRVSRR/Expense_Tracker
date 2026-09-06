# MIGRATION.md — Local JWT → Supabase Auth

## Purpose
This is a scoped, phased task list for migrating auth from the backend's current local JWT implementation to Supabase Auth. This touches the most security-sensitive part of the app and affects every future client repo, so execute phases in strict order, do not skip verification steps, and do not delete old code until its replacement is proven working.

Google OAuth is already configured in Supabase (Client ID/Secret, redirect URI, provider enabled). This doc covers the backend-side migration only.

## Why this migration (context for the agent)
Local JWT works and is fully tested (72 passing tests, including cross-user isolation), but the product needs social login (Google now, Apple likely later for App Store compliance) and cross-platform session handling for the upcoming mobile client. Supabase Auth provides both natively; building social login on top of local JWT would be substantially more work than migrating auth once, now, before mobile code exists.

## Decision (locked in — do not revisit mid-migration)

- **Auth provider:** Supabase Auth (was: local JWT)
- **User table pattern:** foreign-key directly to `auth.users.id` from `accounts`, `transactions`, etc. Do not create a mirrored `public.users` table — one source of truth for user identity, fewer sync bugs.
- **Existing test/dev data in Supabase:** disposable. Wipe and start fresh rather than backfilling old local-JWT test users into `auth.users`.

## Phase 1: Backend token verification (no client changes yet)
Goal: the backend can verify a Supabase-issued JWT, while local register/login endpoints still exist and still work. Nothing is removed yet — this phase is additive only, so the existing test suite must still pass unmodified at the end of it.

Tasks:

1. Get the Supabase project's JWT secret (or JWKS URL, depending on Supabase's current recommended verification method) from **Project Settings → API** in the Supabase dashboard.
2. Add this as a new backend config value (e.g. `SUPABASE_JWT_SECRET` or `SUPABASE_JWKS_URL`) in `.env` / `.env.example`— do not remove the existing `SECRET_KEY` yet.
3. Write a new token verification function (e.g. `app/auth/supabase_jwt.py`) that validates a Supabase-issued JWT and extracts the user id from its `sub` claim.
4. Add a test that constructs (or mocks) a Supabase-shaped JWT and confirms the new verifier accepts it and rejects tampered/expired tokens.
5. Do NOT wire this into the main `get_current_user` dependency yet — keep it isolated and tested standalone first.

**Definition of done:** new Supabase JWT verification exists, is unit tested, and the existing 72 tests still pass untouched (local JWT auth is still the live path).

## Phase 2: Schema change for `auth.users` FK
Goal: `accounts`, `transactions`, `categories`, `recurring_rules` reference `auth.users.id` instead of (or in addition to, temporarily) the local`users` table.

Tasks:

1. Write an Alembic migration adding the FK relationship to `auth.users.id` for the relevant tables. Confirm Supabase's `auth.users` table is queryable via the same Postgres connection (it lives in the `auth` schema, not `public`, so cross-schema FK syntax applies).
2. Do NOT drop the local `users` table yet — keep it until Phase 4 confirms nothing depends on it.
3. Run the migration against the Supabase dev project (the same one already verified end-to-end) and confirm it applies cleanly with `alembic upgrade head` / `alembic current`.

**Definition of done:** new FK columns exist pointing at `auth.users.id`; migration is reversible; old `users` table and its FKs are untouched and still functional.

## Phase 3: Switch the live auth dependency
Goal: `get_current_user` (or equivalent dependency) now verifies Supabase JWTs by default. Local register/login endpoints are disabled but not yet deleted, in case a rollback is needed.

Tasks:

1. Swap the main auth dependency to use the Phase 1 Supabase verifier.
2. Comment out or feature-flag the local `/api/auth/register` and `/api/auth/login` routes rather than deleting them outright — this is the rollback point if something breaks.
3. Update every route that reads `current_user.id` to use the `auth.users` id consistently (should be transparent if Phase 2's FK migration was done correctly).
4. Update the 72-test suite's fixtures: wherever tests currently create a user via the local register endpoint, switch to creating a user via Supabase's admin API (service role key, test-only) or a test double that produces a validly-shaped Supabase JWT.
5. Re-run the full suite. Every previously-passing test — including all 19 cross-user isolation tests — must still pass under the new auth.

**Definition of done:** all 72 tests pass using Supabase-based test user creation/auth; manual curl verification (register via Supabase, hit a protected endpoint) succeeds against the real Supabase project.

## Phase 4: Cleanup
Goal: remove dead code now that Supabase Auth is confirmed as the sole, stable auth path.

Tasks:

1. Delete the local `/api/auth/register` and `/api/auth/login` route code (kept disabled since Phase 3).
2. Remove bcrypt password hashing code, the local `users` table (drop via a new Alembic migration — back up first), and any now-unused `SECRET_KEY`-based JWT creation logic. Keep `SECRET_KEY` only if something else in the app still uses it (double check before removing).
3. Update `SECURITY.md`: replace all local-JWT-specific claims (HS256 details, bcrypt cost factor, local token expiry config) with accurate Supabase Auth equivalents. Re-check the email-enumeration note from the earlier security review — confirm whether Supabase's own signup flow has the same enumeration behavior or handles it differently, and document whichever is actually true.
4. Update `AGENTS.md`: remove "auth strategy" from the open decisions list (it's now resolved) and update the "Current state" section to describe Supabase Auth instead of local JWT.
5. Run `pip-audit` / dependency check — bcrypt and local-JWT-only dependencies (e.g. `python-jose` if used only for local signing) can likely be removed from `requirements.txt` if nothing else needs them.

**Definition of done:** no dead auth code remains; `SECURITY.md` and `AGENTS.md` accurately describe the Supabase Auth setup; full test suite still passes; dependency list is trimmed.

## Phase 5: Mobile-side integration (when mobile repo work begins)
Not part of this backend migration, but noted here so the connection isn't lost: the mobile repo's Phase 1 (auth screens) should use `@supabase/supabase-js` directly rather than hand-building login/register screens against custom backend endpoints, since those endpoints will no longer exist after Phase 4. Update the mobile repo's auth phase tasks accordingly before mobile development starts.

## Rollback plan (if Phase 3 or 4 surfaces a serious issue)

- Before Phase 4 cleanup, rollback is simple: re-enable the commented-out local auth routes and revert the `get_current_user` dependency swap. This is exactly why Phase 3 keeps old code disabled rather than deleted.
- After Phase 4 cleanup, rollback requires restoring the deleted code from git history and re-running the dropped-table migration in reverse — more costly, which is why Phase 4 should only start once Phase 3's full test suite and manual verification are both green.

## Verification checklist (run at the end of Phase 3, before starting Phase 4)

- [ ] Register a new user via Supabase Auth (email/password) — confirm appears in `auth.users`
- [ ] Sign in via Google OAuth through Supabase — confirm a valid session token is issued
- [ ] Hit a protected backend endpoint (e.g. create an account) using the Supabase-issued token — confirm it succeeds
- [ ] Attempt the same request with an expired or tampered token — confirm 401
- [ ] Attempt to access another user's resource — confirm 404 (cross-user isolation still holds under new auth)
- [ ] Full 72-test suite passes
- [ ] Manual smoke test of forecast/budget endpoints under a Supabase-authed user
