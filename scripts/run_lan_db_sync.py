"""
LAN database sync — Machine 1 (main) -> Machine 2 (SQL backup).

Uses local network only (192.168.x.x). No cloud, no internet cost.

Setup:
  Machine 1 (MAIN): ERP + source SQL Server — run this script here.
  Machine 2 (BACKUP): SQL Server + shared folder D:\\SQLBackup

On Machine 2 (shaheenac — SQL Server 2008):
  1. SQL Server 2008 with Mixed Mode + sa login
  2. Create D:\\DB_2626 and D:\\DB_2626\\data
  3. Share D:\\DB_2626 as \\\\shaheenac\\DB_2626
  4. SQL Server service account needs read/write on both folders

On Machine 1 — add to .env (see .env.lan.example):
  SYNC_ENABLED=true
  SYNC_LAN_ONLY=true
  SYNC_REMOTE_SERVER=192.168.1.20
  SYNC_REMOTE_BACKUP_SHARE=\\\\192.168.1.20\\SQLBackup
  SYNC_REMOTE_RESTORE_DIR=D:\\SQLBackup

Usage:
  python -m scripts.run_lan_db_sync --status
  python -m scripts.run_lan_db_sync --dry-run
  python -m scripts.run_lan_db_sync
  python -m scripts.run_lan_db_sync --loop
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.logging.logger import logger
from app.services.db_sync_service import DatabaseSyncError
from app.services.db_sync_store import load_state, record_run
from app.services.lan_db_sync_service import LanDatabaseSyncService


def print_status() -> None:
    svc = LanDatabaseSyncService()
    report = svc.status_report()
    print("LAN database sync (Machine 1 -> Machine 2)")
    print("=" * 45)
    for key, value in report.items():
        print(f"  {key}: {value}")
    state = load_state()
    if state:
        print(f"  last_run: {state.get('last_run', '—')}")
        print(f"  last_status: {state.get('last_status', '—')}")
        print(f"  last_message: {state.get('last_message', '—')}")


def run_once(*, dry_run: bool) -> int:
    svc = LanDatabaseSyncService()
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
        logger.exception("LAN database sync failed")
        print(f"ERROR: {exc}")
        if not dry_run:
            record_run(status="error", message=str(exc))
        return 1


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Sync SQL Server to backup PC over LAN (no internet)"
    )
    parser.add_argument("--status", action="store_true", help="Show LAN sync config")
    parser.add_argument("--dry-run", action="store_true", help="Validate without copying data")
    parser.add_argument(
        "--loop",
        action="store_true",
        help="Repeat every SYNC_INTERVAL_MINUTES (e.g. nightly = 1440)",
    )
    args = parser.parse_args()

    if args.status:
        print_status()
        return

    if args.loop:
        from app.config.settings import settings

        interval = max(15, settings.sync_interval_minutes) * 60
        print(f"LAN sync loop — every {interval // 60} min. Ctrl+C to stop.")
        while True:
            run_once(dry_run=args.dry_run)
            time.sleep(interval)
        return

    raise SystemExit(run_once(dry_run=args.dry_run))


if __name__ == "__main__":
    main()
