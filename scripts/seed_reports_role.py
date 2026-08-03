"""Seed reports permissions and REPORTS_ONLY role."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from sqlalchemy import create_engine, select, text  # noqa: E402
from sqlalchemy.orm import Session  # noqa: E402
from urllib.parse import quote_plus  # noqa: E402

from app.config.settings import get_settings  # noqa: E402
from app.models.module import Module  # noqa: E402
from app.models.permission import Permission, RolePermission  # noqa: E402
from app.models.role import Role  # noqa: E402

REPORT_PERMS = [
    ("reports.sales_dashboard.view", "View Sales Dashboard", "Open sales dashboard and KPI reports"),
    ("reports.gl_ledger.view", "View GL Ledger Report", "Generate General Ledger PDF report"),
]

PROFILE_PERMS = (
    "auth.profile.view",
    "auth.profile.update",
    "auth.profile.change_password",
)

REPORTS_ONLY_PERMS = tuple(code for code, _, _ in REPORT_PERMS) + PROFILE_PERMS

SITE_AUTH_DBS = {
    "erp": "NSDS2626_AUTH",
    "arp": "NAHSL2627_AUTH",
}


def _session_for_auth_db(auth_db: str) -> Session:
    get_settings.cache_clear()
    settings = get_settings()
    server = settings.db_server
    url = (
        f"mssql+pyodbc://{quote_plus(settings.db_user)}:{quote_plus(settings.db_password)}"
        f"@{server}/{auth_db}?driver=ODBC+Driver+18+for+SQL+Server"
        f"&TrustServerCertificate=yes&Encrypt=no"
    )
    engine = create_engine(url)
    return Session(engine)


def seed_auth_db(auth_db: str) -> None:
    db = _session_for_auth_db(auth_db)
    try:
        module = db.execute(select(Module).where(Module.ModuleCode == "REPORTS")).scalar_one_or_none()
        if not module:
            module = Module(
                ModuleCode="REPORTS",
                ModuleName="Reports",
                Description="Reporting and analytics",
                DisplayOrder=12,
                IsActive=True,
            )
            db.add(module)
            db.flush()

        for code, name, desc in REPORT_PERMS:
            existing = db.execute(select(Permission).where(Permission.PermissionCode == code)).scalar_one_or_none()
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
            for code, _, _ in REPORT_PERMS:
                perm = db.execute(select(Permission).where(Permission.PermissionCode == code)).scalar_one()
                exists = db.execute(
                    select(RolePermission).where(
                        RolePermission.RoleId == role.RoleId,
                        RolePermission.PermissionId == perm.PermissionId,
                    )
                ).scalar_one_or_none()
                if not exists:
                    db.add(RolePermission(RoleId=role.RoleId, PermissionId=perm.PermissionId))

        role = db.execute(select(Role).where(Role.RoleCode == "REPORTS_ONLY")).scalar_one_or_none()
        if not role:
            role = Role(
                RoleCode="REPORTS_ONLY",
                RoleName="Reports Only",
                Description="View sales and GL reports only",
                IsSystemRole=True,
            )
            db.add(role)
            db.flush()

        for code in REPORTS_ONLY_PERMS:
            perm = db.execute(select(Permission).where(Permission.PermissionCode == code)).scalar_one_or_none()
            if not perm:
                raise RuntimeError(f"Missing permission {code} in {auth_db}")
            exists = db.execute(
                select(RolePermission).where(
                    RolePermission.RoleId == role.RoleId,
                    RolePermission.PermissionId == perm.PermissionId,
                )
            ).scalar_one_or_none()
            if not exists:
                db.add(RolePermission(RoleId=role.RoleId, PermissionId=perm.PermissionId))

        db.commit()
        print(f"{auth_db}: REPORTS_ONLY role ready.")
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def main() -> int:
    parser = argparse.ArgumentParser(description="Seed REPORTS_ONLY role")
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

    print("Users must re-login to refresh JWT permissions.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
