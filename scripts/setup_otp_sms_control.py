"""Create otp_sms_control table and seed admin permissions."""

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

PERMS = [
    (
        "auth.otp_sms_control.view",
        "View OTP SMS Control",
        "View master / web / mobile OTP SMS enablement",
    ),
    (
        "auth.otp_sms_control.manage",
        "Manage OTP SMS Control",
        "Enable or disable OTP SMS for web and mobile applications",
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


def create_control_table() -> None:
    database = settings.business_db_name
    server = settings.business_db_server or settings.db_server
    sql_path = ROOT / "sql" / "28_create_otp_sms_control.sql"
    sql = prepare_sql_for_database(sql_path.read_text(encoding="utf-8"), database)
    with _odbc_connect(database) as connection:
        cursor = connection.cursor()
        for batch in split_batches(sql):
            cursor.execute(batch)
        cursor.execute("SELECT name FROM sys.tables WHERE name = N'otp_sms_control'")
        found = [row[0] for row in cursor.fetchall()]
    print(f"otp_sms_control ready in {database} on {server}: {', '.join(found)}")
    if "otp_sms_control" not in found:
        raise SystemExit("otp_sms_control table missing")


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
        module = db.execute(select(Module).where(Module.ModuleCode == "AUTH")).scalar_one_or_none()
        if not module:
            module = db.execute(
                select(Module).where(Module.ModuleCode == "REPORTS")
            ).scalar_one_or_none()
        if not module:
            print(f"{auth_db}: AUTH/REPORTS module not found.")
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
        print(f"{auth_db}: OTP SMS control permissions seeded.")
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def main() -> int:
    parser = argparse.ArgumentParser(description="Setup OTP SMS master control")
    parser.add_argument("--site", choices=sorted(SITE_AUTH_DBS), help="Seed one site auth DB")
    parser.add_argument("--all", action="store_true", help="Seed ERP and ARP auth databases")
    parser.add_argument("--skip-table", action="store_true", help="Skip business-DB table create")
    args = parser.parse_args()

    if not args.skip_table:
        create_control_table()

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
