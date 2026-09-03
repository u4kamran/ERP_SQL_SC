"""Sync Menus catalog + grant Customer Ledger (Detailed) to users who already have GL Ledger menu.

Safe for ARP (NAHSL2627_AUTH) and ERP (NSDS2626_AUTH). No business-DB writes.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path
from urllib.parse import quote_plus

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from sqlalchemy import create_engine, select, text  # noqa: E402
from sqlalchemy.orm import Session  # noqa: E402

from app.config.settings import get_settings  # noqa: E402
from app.models.menu import Menu, UserMenuRight  # noqa: E402
from app.services.user_menu_rights_service import sync_menus_from_site_links  # noqa: E402

SITE_AUTH = {"erp": "NSDS2626_AUTH", "arp": "NAHSL2627_AUTH"}
NEW_PATH = "/admin/gl-ledger-detailed"
LEGACY_PATH = "/admin/gl-ledger-report"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--site", choices=("erp", "arp"), required=True)
    args = parser.parse_args()
    auth_db = SITE_AUTH[args.site]

    get_settings.cache_clear()
    settings = get_settings()
    url = (
        f"mssql+pyodbc://{quote_plus(settings.db_user)}:{quote_plus(settings.db_password)}"
        f"@{settings.db_server}/{auth_db}?driver=ODBC+Driver+18+for+SQL+Server"
        f"&TrustServerCertificate=yes&Encrypt=no"
    )
    engine = create_engine(url)
    db = Session(engine)
    try:
        count = sync_menus_from_site_links(db)
        print(f"{auth_db}: menus synced ({count} rows touched)")

        new_menu = db.execute(select(Menu).where(Menu.Path == NEW_PATH)).scalar_one_or_none()
        legacy = db.execute(select(Menu).where(Menu.Path == LEGACY_PATH)).scalar_one_or_none()
        if not new_menu:
            print("ERROR: new menu row missing after sync")
            return 1
        print(f"  new menu id={new_menu.MenuId} code={new_menu.MenuCode}")

        granted = 0
        if legacy:
            # Users who can open existing GL Ledger also get the detailed ledger menu.
            rights = db.execute(
                select(UserMenuRight).where(
                    UserMenuRight.MenuId == legacy.MenuId,
                    UserMenuRight.CanAccess == True,  # noqa: E712
                    UserMenuRight.IsDeleted == False,  # noqa: E712
                )
            ).scalars().all()
            for right in rights:
                existing = db.execute(
                    select(UserMenuRight).where(
                        UserMenuRight.UserId == right.UserId,
                        UserMenuRight.MenuId == new_menu.MenuId,
                    )
                ).scalar_one_or_none()
                if existing is None:
                    db.add(
                        UserMenuRight(
                            UserId=right.UserId,
                            MenuId=new_menu.MenuId,
                            CanAccess=True,
                            CreatedBy=right.CreatedBy,
                        )
                    )
                    granted += 1
                elif not existing.CanAccess or existing.IsDeleted:
                    existing.CanAccess = True
                    existing.IsDeleted = False
                    existing.IsActive = True
                    granted += 1
            db.commit()
        print(f"  user menu grants updated: {granted}")
        print("Users with JWT caches should re-login (or refresh) to see the menu.")
        return 0
    finally:
        db.close()
        engine.dispose()


if __name__ == "__main__":
    raise SystemExit(main())
