"""Seed Login Alert email permissions (ERP and/or ARP auth DB)."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from urllib.parse import quote_plus

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from app.config.settings import get_settings
from app.models.module import Module
from app.models.permission import Permission, RolePermission
from app.models.role import Role

PERMS = [
    (
        "auth.login_notify.view",
        "View Login Alerts",
        "View login email alert settings and send log",
    ),
    (
        "auth.login_notify.manage",
        "Manage Login Alerts",
        "Change login notify address and send test emails",
    ),
]

SITE_AUTH_DBS = {
    "erp": "NSDS2626_AUTH",
    "arp": "NAHSL2627_AUTH",
}


def _session_for_auth_db(auth_db: str) -> Session:
    get_settings.cache_clear()
    settings = get_settings()
    url = (
        f"mssql+pyodbc://{quote_plus(settings.db_user)}:{quote_plus(settings.db_password)}"
        f"@{settings.db_server}/{auth_db}?driver=ODBC+Driver+18+for+SQL+Server"
        f"&TrustServerCertificate=yes&Encrypt=no"
    )
    return Session(create_engine(url))


def seed_auth_db(auth_db: str) -> None:
    db = _session_for_auth_db(auth_db)
    try:
        module = db.execute(
            select(Module).where(Module.ModuleCode == "AUTH")
        ).scalar_one_or_none()
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
            role = db.execute(
                select(Role).where(Role.RoleCode == role_code)
            ).scalar_one_or_none()
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
        print(f"{auth_db}: login notify permissions seeded.")
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def main() -> int:
    parser = argparse.ArgumentParser(description="Seed login-alert permissions")
    parser.add_argument("--site", choices=sorted(SITE_AUTH_DBS), help="Seed one site auth DB")
    parser.add_argument("--all", action="store_true", help="Seed ERP and ARP auth databases")
    args = parser.parse_args()

    if args.all:
        dbs = list(SITE_AUTH_DBS.values())
    elif args.site:
        dbs = [SITE_AUTH_DBS[args.site]]
    else:
        dbs = [get_settings().db_name]

    for auth_db in dbs:
        seed_auth_db(auth_db)

    print("Users must re-login.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
