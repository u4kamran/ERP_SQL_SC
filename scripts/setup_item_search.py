"""Create item search alias/log tables and seed admin permissions."""

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
        "marketing.item_search.view",
        "View Item Search",
        "View product search settings, aliases, and empty-search report",
    ),
    (
        "marketing.item_search.manage",
        "Manage Item Search",
        "Change search settings and maintain item search aliases",
    ),
]


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
    sql_path = ROOT / "sql" / "30_create_item_search_tables.sql"
    sql = prepare_sql_for_database(sql_path.read_text(encoding="utf-8"), database)
    with _odbc_connect(database) as connection:
        cursor = connection.cursor()
        for batch in split_batches(sql):
            try:
                cursor.execute(batch)
            except Exception as exc:
                print(f"Batch warning: {exc}")
        cursor.execute(
            "SELECT name FROM sys.tables WHERE name IN (N'item_search_alias', N'item_search_log')"
        )
        found = [row[0] for row in cursor.fetchall()]
    print(f"item search tables in {database}: {', '.join(found)}")
    if "item_search_alias" not in found or "item_search_log" not in found:
        raise SystemExit("item search tables missing")


def seed_auth_db(auth_db: str) -> None:
    cfg = get_settings()
    url = (
        f"mssql+pyodbc://{quote_plus(cfg.db_user)}:{quote_plus(cfg.db_password)}"
        f"@{cfg.db_server}/{auth_db}?driver=ODBC+Driver+18+for+SQL+Server"
        f"&TrustServerCertificate=yes&Encrypt=no"
    )
    db = Session(create_engine(url))
    try:
        module = db.execute(select(Module).where(Module.ModuleCode == "REPORTS")).scalar_one_or_none()
        if not module:
            module = db.execute(select(Module).where(Module.ModuleCode == "AUTH")).scalar_one_or_none()
        if not module:
            print(f"{auth_db}: module not found")
            return
        for code, name, desc in PERMS:
            if not db.execute(select(Permission).where(Permission.PermissionCode == code)).scalar_one_or_none():
                db.add(Permission(ModuleId=module.ModuleId, PermissionCode=code, PermissionName=name, Description=desc))
        db.flush()
        for role_code in ("SUPER_ADMIN", "ADMIN"):
            role = db.execute(select(Role).where(Role.RoleCode == role_code)).scalar_one_or_none()
            if not role:
                continue
            for code, _, _ in PERMS:
                perm = db.execute(select(Permission).where(Permission.PermissionCode == code)).scalar_one()
                exists = db.execute(
                    select(RolePermission).where(
                        RolePermission.RoleId == role.RoleId,
                        RolePermission.PermissionId == perm.PermissionId,
                    )
                ).scalar_one_or_none()
                if not exists:
                    db.add(RolePermission(RoleId=role.RoleId, PermissionId=perm.PermissionId))
        db.commit()
        print(f"{auth_db}: item search permissions seeded.")
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--site", choices=["erp", "arp"], default="erp")
    args = parser.parse_args()
    create_tables()
    seed_auth_db("NSDS2626_AUTH" if args.site == "erp" else "NAHSL2627_AUTH")
    print("Users must re-login.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
