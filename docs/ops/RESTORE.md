# Restore Runbook — Supabase Free Tier (pg_dump)

Supabase **Free plan has no Point-in-Time Recovery (PITR)** — Dashboard → Database → Backups shows daily physical snapshots (7-day retention, view-only, restore requires contacting Supabase or upgrading). For portable, owner-controlled restores we use **daily logical backups via `pg_dump`** (GitHub Actions artifact, 7-day retention). This runbook covers both paths.

## Prerequisites

- `DATABASE_URL` with Transaction pooler port `6543` and `postgresql://` driver (`docs/INFRASTRUCTURE.md:37`, `backend/app/db/database.py:17` auto-sets `statement_cache_size=0`)
  - Local: `backend/.env` (never committed, gitignored at `.gitignore:9`)
  - CI/Render: GitHub → Settings → Secrets and variables → Actions → `DATABASE_URL`; Render → Environment → `DATABASE_URL`
  - Supabase Dashboard → Project Settings → Database → Connection string → Transaction pooler (pooler host, port 6543). URL-encode special chars in password.
- Tools: `psql`, `pg_dump`/`pg_restore` (PostgreSQL client 14+), `alembic` (for migration re-apply), `curl`, `python` (for `backend/scripts/verify_backup.py`)
- Secrets safety: never log `DATABASE_URL`; workflow masks it via `::add-mask::` in `.github/workflows/backup.yml:1`; locally avoid `echo $DATABASE_URL` in shared terminals

## What gets backed up

- **GitHub Actions daily `pg_dump`** (` .github/workflows/backup.yml:1`): cron `0 2 * * *` UTC + `workflow_dispatch` manual trigger
  - Creates `backup-<TIMESTAMP>.dump` (`-Fc` custom, compressed) + `backup-<TIMESTAMP>.sql` (plain)
  - Uploads as artifact `pg-backup-<TIMESTAMP>` with `retention-days: 7` (matches Free retention, no S3 bucket)
  - Also runs `SELECT 1` + `SELECT pg_is_in_recovery()` smoke test before dump (no secrets in logs)
- **Supabase Dashboard daily snapshot**: view-only on Free; useful to confirm backup window but not directly downloadable for self-restore

## Before any risky migration — manual backup (recommended)

```sh
# From repo root, with backend/.env set
# 1. Verify connectivity (no secrets in output)
psql "$DATABASE_URL" -c "SELECT 1;"  # should return 1 row

# 2. Create timestamped dump (custom + plain)
TIMESTAMP=$(date -u +%Y%m%dT%H%M%SZ)
pg_dump "$DATABASE_URL" -Fc -f "backup-${TIMESTAMP}.dump"
pg_dump "$DATABASE_URL" -f "backup-${TIMESTAMP}.sql"
ls -lh backup-*.dump backup-*.sql

# 3. Optional: verify dump restores to a throwaway local DB
# createdb expense_tracker_verify && pg_restore -d postgres://localhost/expense_tracker_verify backup-*.dump && psql -d expense_tracker_verify -c "SELECT count(*) FROM accounts;"
```

Or trigger GitHub Actions → `backup` → Run workflow (manual) and download artifact.

## Restore — from GitHub Actions artifact or local dump

```sh
# 1. Download artifact (GitHub → Actions → backup → pg-backup-<TIMESTAMP> → Download) and unzip, or use local backup-*.dump

# 2. Restore to the Supabase pooler URL
# Custom format (preferred, compressed, parallel-safe):
pg_restore -d "$DATABASE_URL" --verbose --clean --if-exists --no-owner --no-acl backup-*.dump

# Or plain SQL:
# psql "$DATABASE_URL" < backup-*.sql

# 3. Re-apply migrations to ensure schema matches code (lifespan also runs this at boot)
cd backend
alembic upgrade head

# 4. Verify
curl -s https://expense-tracker-uwrp.onrender.com/health | jq  # expect {"status":"ok","database":"ok"}
curl -s https://expense-tracker-uwrp.onrender.com/openapi.json | head
# Bearer round-trip (replace <token> with supabase-js access token):
curl -s -H "Authorization: Bearer <token>" https://expense-tracker-uwrp.onrender.com/api/accounts/ | jq
psql "$DATABASE_URL" -c "SELECT count(*) FROM accounts; SELECT count(*) FROM transactions;"

# 5. If Render, redeploy is not needed — DB restore is live; lifespan will re-run migrations on next boot anyway
```

**If using Supabase Dashboard snapshot (Free):** Open Dashboard → Database → Backups → view snapshot list (no self-service restore button on Free). To restore a Dashboard snapshot you must either upgrade to Pro for self-service PITR or contact Supabase support. Prefer the `pg_dump` artifact for owner-controlled restores on Free.

## Verify backups (ops check)

```sh
# Local check: DB connectivity + artifact age (if you have a local backup file)
backend/venv/bin/python backend/scripts/verify_backup.py        # checks SELECT 1 + pg_is_in_recovery()
backend/venv/bin/python backend/scripts/verify_backup.py --path backup-*.dump  # also checks file age <24h

# GitHub check: Actions → backup → latest run green + artifact exists + retention 7 days
# gh CLI (optional, needs GH_TOKEN):
# gh run list --workflow=backup --limit 3
# gh run view <run-id> --log | grep -E "Backup created|artifact"
```

Run verification: before every deploy, weekly via cron, and quarterly test restore to a throwaway DB (`createdb` → `pg_restore` → `SELECT count(*)`).

## Troubleshooting

- `password authentication failed` → secret or URL-encoding problem, not engine config (`AGENTS.md:40`). Reset password in Supabase Dashboard → Database → Connection string, URL-encode `! @ # $ %` etc, update `backend/.env` and Render/GitHub Secrets, retry `psql "$DATABASE_URL" -c "SELECT 1;"`.
- `No 'script_location' key found in configuration` → `alembic.ini` path misconfigured; lifespan uses `BACKEND_DIR/alembic.ini` (`backend/app/factory.py:35`). Fixed in `59ac235`.
- `CORS_ORIGINS is not set` → set on Render/local `.env` (`backend/app/factory.py:36`, `docs/INFRASTRUCTURE.md:62`); `TESTING=1` bypasses for tests.
- `429 Too Many Requests` → per-endpoint tiers (`backend/app/utils/rate_limit.py:1`, `backend/app/factory.py:118` table); check `Retry-After` header.
- `543 PGRST` or `503 EXTERNAL_SERVICE_UNAVAILABLE` from JWKS → `app/utils/circuit_breaker.py:1` (3 failures → OPEN 60s); wait 60s, check `SUPABASE_JWKS_URL`/`SUPABASE_ISSUER` in env, verify Supabase project is not paused (Free pauses after 7 days inactivity).

## Retention & limits (Free)

- **Supabase Free:** daily snapshot, 7-day retention, no PITR slider, no self-service snapshot download/restore; pausing after 7 days inactivity may affect availability.
- **GitHub Actions artifact:** 7-day retention (`retention-days: 7` in workflow), private to repo; download before expiry if longer retention needed (promote to S3/GDrive when you outgrow Free).
- **Local `pg_dump` files:** gitignored (`backend/*.dump`, `backend/*.sql` should not be committed); store `backend/backups/` locally if you keep them beyond artifact window — also gitignored.

## When to switch

- Need **PITR slider or longer retention** → upgrade Supabase to Pro (enables PITR) and update this runbook to use Dashboard → Database → Backups → Point-in-time.
- Need **long-term archival** → add S3 bucket + `aws s3 cp backup-*.dump s3://...` step to workflow (add `AWS_ACCESS_KEY_ID`/`AWS_SECRET_ACCESS_KEY` secrets, never logged).
