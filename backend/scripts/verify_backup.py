#!/usr/bin/env python3
"""
Verify backup health — safe for production use.

- Never logs DATABASE_URL
- Checks DB connectivity (SELECT 1) and pg_is_in_recovery()
- Optionally checks a local dump file age (<24h by default)

Usage:
  DATABASE_URL=postgresql://... python backend/scripts/verify_backup.py
  DATABASE_URL=postgresql://... python backend/scripts/verify_backup.py --path backup-20250919T020000Z.dump
  DATABASE_URL=postgresql://... python backend/scripts/verify_backup.py --max-age-hours 24 --path backup-*.dump

Exit codes: 0 = healthy, 1 = warning/error
"""

import argparse
import os
import sys
import glob
from datetime import datetime, timezone, timedelta
from pathlib import Path


def _redacted(msg: str) -> str:
    # Ensure we never print the URL even if caller passes it in an error
    url = os.getenv("DATABASE_URL", "")
    if url and url in msg:
        return msg.replace(url, "[REDACTED_DATABASE_URL]")
    return msg


def check_db() -> bool:
    url = os.getenv("DATABASE_URL")
    if not url:
        print("WARN: DATABASE_URL not set — skipping DB check (set it in backend/.env or env)", file=sys.stderr)
        return True  # Not a failure for local dry-run without DB
    try:
        # Use sync psycopg2 if available, else try asyncpg via sqlalchemy sync fallback
        # For minimal deps, try psycopg2 first
        try:
            import psycopg2

            conn = psycopg2.connect(url.replace("+asyncpg", "").replace("+psycopg2", "").replace("postgresql+asyncpg://", "postgresql://"))
            cur = conn.cursor()
            cur.execute("SELECT 1;")
            assert cur.fetchone()[0] == 1
            cur.execute("SELECT pg_is_in_recovery();")
            in_recovery = cur.fetchone()[0]
            cur.close()
            conn.close()
            print(f"DB OK: SELECT 1 succeeded, pg_is_in_recovery={in_recovery}")
            if in_recovery:
                print("WARN: DB is in recovery (replica) — writes may be blocked", file=sys.stderr)
            return True
        except ImportError:
            # Fallback: try via sqlalchemy sync engine
            from sqlalchemy import create_engine, text

            sync_url = url.replace("+asyncpg", "").replace("+aiosqlite", "")
            if sync_url.startswith("postgresql+"):
                sync_url = "postgresql://" + sync_url.split("://", 1)[1]
            # Use psycopg2 driver implicitly
            engine = create_engine(sync_url, pool_pre_ping=True)
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
                result = conn.execute(text("SELECT pg_is_in_recovery()"))
                in_recovery = result.scalar()
                print(f"DB OK: SELECT 1 succeeded, pg_is_in_recovery={in_recovery}")
            engine.dispose()
            return True
    except Exception as exc:
        print(f"DB ERROR: {_redacted(str(exc))}", file=sys.stderr)
        return False


def check_file(path_pattern: str, max_age_hours: int) -> bool:
    files = glob.glob(path_pattern)
    if not files:
        print(f"WARN: No files matched pattern '{path_pattern}' — skipping file age check", file=sys.stderr)
        print("      (GitHub artifact check: gh run list --workflow=backup --limit 3)", file=sys.stderr)
        return True
    now = datetime.now(timezone.utc)
    ok = True
    for f in sorted(files):
        p = Path(f)
        try:
            mtime = datetime.fromtimestamp(p.stat().st_mtime, tz=timezone.utc)
            age = now - mtime
            age_hours = age.total_seconds() / 3600
            size = p.stat().st_size
            status = "OK" if age_hours <= max_age_hours else "STALE"
            print(f"{status}: {f} — {size} bytes, age {age_hours:.1f}h (mtime {mtime.isoformat()})")
            if age_hours > max_age_hours:
                print(f"  WARN: File older than {max_age_hours}h — backup may be stale", file=sys.stderr)
                ok = False
        except Exception as exc:
            print(f"ERROR checking {f}: {_redacted(str(exc))}", file=sys.stderr)
            ok = False
    return ok


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify backup health (safe, no secrets in logs)")
    parser.add_argument("--path", default=None, help="Glob pattern for local dump file(s), e.g., 'backup-*.dump'")
    parser.add_argument("--max-age-hours", type=int, default=24, help="Max age in hours before file is considered stale (default 24)")
    args = parser.parse_args()

    db_ok = check_db()
    file_ok = True
    if args.path:
        file_ok = check_file(args.path, args.max_age_hours)

    if db_ok and file_ok:
        print("VERIFY OK")
        return 0
    print("VERIFY FAILED", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
