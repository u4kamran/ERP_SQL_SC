"""Create item image tables and seed admin permissions."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from urllib.parse import quote_plus

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from app.config.settings import get_settings, settings
from app.models.module import Module
from app.models.permission import Permission, RolePermission
from app.models.role import Role
from app.services.item_images import ensure_product_images_dir

PERMS = [
    (
        "inventory.item_images.view",
        "View Item Images",
        "View Item Image Manager, coverage, and candidates",
    ),
    (
        "inventory.item_images.manage",
        "Manage Item Images",
        "Search, approve, reject, upload, and configure item images",
    ),
    (
        "inventory.item_images.bulk",
        "Bulk Item Image Fetch",
        "Start, pause, resume, or cancel bulk image fetch jobs",
    ),
]

SITE_AUTH_DBS = {
    "erp": "NSDS2626_AUTH",
    "arp": "NAHSL2627_AUTH",
}


def split_batches(sql: str) -> list[str]:
    return [
        batch.strip()
        for batch in re.split(r"^\s*GO\s*$", sql, flags=re.MULTILINE | re.IGNORECASE)
        if batch.strip()
    ]


def prepare_sql_for_database(sql: str, database: str) -> str:
    rewritten = re.sub(
        r"(?im)^\s*USE\s+\[[^\]]+\]\s*;\s*$",
        f"USE [{database}];",
        sql,
        count=1,
    )
    if f"USE [{database}];" not in rewritten:
        rewritten = f"USE [{database}];\nGO\n\n{sql}"
    return rewritten


def _odbc_connect(database: str):
    import pyodbc

    server = settings.business_db_server or settings.db_server
    return pyodbc.connect(
        f"DRIVER={{{settings.db_driver}}};"
        f"SERVER={server};"
        f"DATABASE={database};"
        f"UID={settings.db_user};"
        f"PWD={settings.db_password};"
        f"TrustServerCertificate={settings.db_trust_server_certificate};"
        f"Encrypt={settings.db_encrypt};",
        autocommit=True,
    )


def create_tables() -> None:
    database = settings.business_db_name
    server = settings.business_db_server or settings.db_server
    sql_path = ROOT / "sql" / "31_create_item_images_tables.sql"
    sql = prepare_sql_for_database(sql_path.read_text(encoding="utf-8"), database)
    with _odbc_connect(database) as connection:
        cursor = connection.cursor()
        for batch in split_batches(sql):
            cursor.execute(batch)
        cursor.execute(
            """
            SELECT name FROM sys.tables
            WHERE name IN (
                N'item_images', N'item_image_status', N'item_image_candidates',
                N'item_image_jobs', N'item_image_job_items', N'item_image_audit',
                N'item_image_errors', N'item_image_settings'
            )
            ORDER BY name
            """
        )
        found = [row[0] for row in cursor.fetchall()]
    print(f"Item image tables ready in {database} on {server}: {', '.join(found)}")
    required = {
        "item_images",
        "item_image_status",
        "item_image_candidates",
        "item_image_jobs",
        "item_image_job_items",
        "item_image_audit",
        "item_image_errors",
        "item_image_settings",
    }
    missing = required - set(found)
    if missing:
        raise SystemExit(f"Missing tables: {', '.join(sorted(missing))}")
    ensure_product_images_dir()
    print(f"Product image folder: {ROOT / 'data' / 'ProductImages'}")
    pk_sql = ROOT / "sql" / "33_add_pk_provider_settings.sql"
    if pk_sql.exists():
        pk = prepare_sql_for_database(pk_sql.read_text(encoding="utf-8"), database)
        with _odbc_connect(database) as connection:
            cursor = connection.cursor()
            for batch in split_batches(pk):
                cursor.execute(batch)
            cursor.execute(
                """
                UPDATE dbo.item_image_settings
                SET naheed_enabled = 1,
                    metro_enabled = 1,
                    upcitemdb_enabled = 0,
                    open_food_facts_enabled = 0,
                    no_match_min = 30,
                    review_min = 75
                WHERE id = 1
                """
            )
    print("PK provider settings columns ready (Naheed on, min score 30)")


def _session_for_auth_db(auth_db: str) -> Session:
    get_settings.cache_clear()
    cfg = get_settings()
    url = (
        f"mssql+pyodbc://{quote_plus(cfg.db_user)}:{quote_plus(cfg.db_password)}"
        f"@{cfg.db_server}/{auth_db}?driver=ODBC+Driver+18+for+SQL+Server"
        f"&TrustServerCertificate=yes&Encrypt=no"
    )
    return Session(create_engine(url))


def seed_auth_db(auth_db: str) -> None:
    db = _session_for_auth_db(auth_db)
    try:
        module = db.execute(
            select(Module).where(Module.ModuleCode == "INVENTORY")
        ).scalar_one_or_none()
        if not module:
            module = db.execute(
                select(Module).where(Module.ModuleCode == "AUTH")
            ).scalar_one_or_none()
        if not module:
            print(f"{auth_db}: INVENTORY/AUTH module not found.")
            return

        for code, name, desc in PERMS:
            existing = db.execute(
                select(Permission).where(Permission.PermissionCode == code)
            ).scalar_one_or_none()
            if not existing:
                db.add(
                    Permission(
                        ModuleId=module.ModuleId,
                        PermissionCode=code,
                        PermissionName=name,
                        Description=desc,
                    )
                )
        db.flush()

        for role_code in ("SUPER_ADMIN", "ADMIN"):
            role = db.execute(select(Role).where(Role.RoleCode == role_code)).scalar_one_or_none()
            if not role:
                continue
            for code, _, _ in PERMS:
                perm = db.execute(
                    select(Permission).where(Permission.PermissionCode == code)
                ).scalar_one()
                exists = db.execute(
                    select(RolePermission).where(
                        RolePermission.RoleId == role.RoleId,
                        RolePermission.PermissionId == perm.PermissionId,
                    )
                ).scalar_one_or_none()
                if not exists:
                    db.add(
                        RolePermission(
                            RoleId=role.RoleId,
                            PermissionId=perm.PermissionId,
                        )
                    )
        db.commit()
        print(f"{auth_db}: Item image permissions seeded.")
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def main() -> int:
    parser = argparse.ArgumentParser(description="Setup Item Image Manager")
    parser.add_argument("--site", choices=sorted(SITE_AUTH_DBS), help="Seed one site auth DB")
    parser.add_argument("--all", action="store_true", help="Seed ERP and ARP auth databases")
    parser.add_argument("--skip-table", action="store_true", help="Skip business-DB table create")
    args = parser.parse_args()

    if not args.skip_table:
        create_tables()

    if args.all:
        dbs = list(SITE_AUTH_DBS.values())
    elif args.site:
        dbs = [SITE_AUTH_DBS[args.site]]
    else:
        dbs = [get_settings().db_name]

    for auth_db in dbs:
        seed_auth_db(auth_db)

    print("Users must re-login to pick up new permissions.")

    try:
        from app.database.session import SessionLocal
        from app.services.user_menu_rights_service import (
            ensure_user_menu_tables,
            sync_menus_from_site_links,
        )

        menu_db = SessionLocal()
        try:
            ensure_user_menu_tables(menu_db)
            count = sync_menus_from_site_links(menu_db)
            print(f"Menus synced ({count} rows).")
        finally:
            menu_db.close()
    except Exception as exc:
        print(f"Menu sync skipped: {exc}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
