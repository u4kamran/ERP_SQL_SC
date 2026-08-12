"""Create User Menu Rights tables and sync menu catalog from site_links."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database.session import SessionLocal
from app.services.user_menu_rights_service import (
    ensure_user_menu_tables,
    sync_menus_from_site_links,
)


def main() -> int:
    db = SessionLocal()
    try:
        ensure_user_menu_tables(db)
        count = sync_menus_from_site_links(db, actor_user_id=None)
        print(f"User menu rights ready. Synced {count} menu rows.")
        return 0
    except Exception as exc:  # noqa: BLE001
        print(f"ERROR: {exc}")
        return 1
    finally:
        db.close()


if __name__ == "__main__":
    raise SystemExit(main())
