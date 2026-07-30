"""
Sync local SQL Server databases to an online SQL Server (backup -> copy -> restore).

Usage:
  python -m scripts.run_db_sync --status
  python -m scripts.run_db_sync --dry-run
  python -m scripts.run_db_sync
  python -m scripts.run_db_sync --loop          # repeat every SYNC_INTERVAL_MINUTES
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.config.settings import settings
from app.logging.logger import logger
from app.services.db_sync_service import DatabaseSyncError, DatabaseSyncService
from app.services.db_sync_store import load_state, record_run


def print_status() -> None:
    svc = DatabaseSyncService()
    print("Database sync status")
    print("--------------------")
    print(f"  Enabled:     {settings.sync_enabled}")
    print(f"  Configured:  {svc.is_configured()}")
    print(f"  Hint:        {svc.configuration_hint()}")
    print(f"  Local server: {settings.db_server}")
    print(f"  Remote server: {settings.sync_remote_server or '(not set)'}")
    print(f"  Auth DB:     {settings.db_name} (sync={settings.sync_auth_db})")
    print(f"  Business DB: {settings.business_db_name} (sync={settings.sync_business_db})")
    print(f"  Backup dir:  {settings.sync_backup_dir}")
    print(f"  Remote share:{settings.sync_remote_backup_share or '(not set)'}")
    print(f"  Interval:    {settings.sync_interval_minutes} minutes")
    state = load_state()
    if state:
        print(f"  Last run:    {state.get('last_run', '—')}")
        print(f"  Last status: {state.get('last_status', '—')}")
        print(f"  Last message:{state.get('last_message', '—')}")


def run_once(*, dry_run: bool) -> int:
    svc = DatabaseSyncService()
    try:
        result = svc.run(dry_run=dry_run)
        if not dry_run:
            removed = svc.cleanup_old_backups()
            if removed:
                logger.info("Removed %s old local backup(s).", removed)
        print(result.get("message") or result)
        return 0
    except DatabaseSyncError as exc:
        print(f"ERROR: {exc}")
        if not dry_run:
            record_run(status="error", message=str(exc))
        return 1
    except Exception as exc:
        logger.exception("Database sync failed")
        print(f"ERROR: {exc}")
        if not dry_run:
            record_run(status="error", message=str(exc))
        return 1


def main() -> None:
    parser = argparse.ArgumentParser(description="Sync local SQL Server to online SQL Server")
    parser.add_argument("--status", action="store_true", help="Show configuration and last run")
    parser.add_argument("--dry-run", action="store_true", help="Validate settings without copying data")
    parser.add_argument(
        "--loop",
        action="store_true",
        help="Run repeatedly every SYNC_INTERVAL_MINUTES (use with Task Scheduler or background)",
    )
    args = parser.parse_args()

    if args.status:
        print_status()
        return

    if args.loop:
        interval = max(15, settings.sync_interval_minutes) * 60
        print(f"DB sync loop started — every {interval // 60} minutes. Ctrl+C to stop.")
        while True:
            run_once(dry_run=args.dry_run)
            time.sleep(interval)
        return

    raise SystemExit(run_once(dry_run=args.dry_run))


if __name__ == "__main__":
    main()
