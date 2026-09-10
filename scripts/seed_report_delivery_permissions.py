"""Seed per-report View / Email / WhatsApp permissions (each report has its own rights)."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from urllib.parse import quote_plus  # noqa: E402

from sqlalchemy import create_engine, select  # noqa: E402
from sqlalchemy.orm import Session  # noqa: E402

from app.config.settings import get_settings  # noqa: E402
from app.models.module import Module  # noqa: E402
from app.models.permission import Permission, RolePermission  # noqa: E402
from app.models.role import Role  # noqa: E402

# Each report gets its own View (+ Email / WhatsApp where the UI supports them).
REPORT_PERMS: list[tuple[str, str, str]] = [
    ("reports.gl_ledger.view", "View GL Ledger Report", "Open desktop GL Ledger report"),
    ("reports.gl_ledger.email", "Email GL Ledger Report", "Email PDF from desktop GL Ledger"),
    ("reports.gl_ledger.whatsapp", "WhatsApp GL Ledger Report", "Send PDF via WhatsApp from desktop GL Ledger"),
    ("reports.gl_ledger_detailed.view", "View Customer Ledger (Detailed)", "Open detailed customer ledger with invoice lines"),
    ("reports.gl_ledger_detailed.email", "Email Customer Ledger (Detailed)", "Email detailed customer ledger PDF"),
    ("reports.gl_ledger_detailed.whatsapp", "WhatsApp Customer Ledger (Detailed)", "WhatsApp detailed customer ledger PDF"),
    ("reports.gl_ledger_mobile.view", "View GL Ledger (Mobile)", "Open mobile GL Ledger report"),
    ("reports.gl_ledger_mobile.email", "Email GL Ledger (Mobile)", "Email PDF from mobile GL Ledger"),
    ("reports.gl_ledger_mobile.whatsapp", "WhatsApp GL Ledger (Mobile)", "Send PDF via WhatsApp from mobile GL Ledger"),
    ("reports.gl_credit_summary.view", "View Credit Summary Ledger", "Open Credit Summary Ledger report"),
    ("reports.gl_credit_summary.email", "Email Credit Summary Ledger", "Email PDF from Credit Summary Ledger"),
    ("reports.trial_balance_d2d.view", "View Trial Balance D2D", "Open Trial Balance Date to Date report"),
    ("reports.trial_balance_d2d.email", "Email Trial Balance D2D", "Email PDF from Trial Balance D2D"),
    ("reports.trial_balance_d2d.whatsapp", "WhatsApp Trial Balance D2D", "Send PDF via WhatsApp from Trial Balance D2D"),
    ("reports.trial_balance_d2d_mobile.view", "View Trial Balance D2D (Mobile)", "Open mobile Trial Balance D2D"),
    ("reports.trial_balance_d2d_mobile.email", "Email Trial Balance D2D (Mobile)", "Email PDF from mobile Trial Balance"),
    ("reports.trial_balance_d2d_mobile.whatsapp", "WhatsApp Trial Balance D2D (Mobile)", "Send PDF via WhatsApp from mobile Trial Balance"),
    ("reports.stock_balance_d2d.view", "View Stock Balance D2D", "Open Stock Balance Date to Date report"),
    ("reports.stock_balance_d2d.email", "Email Stock Balance D2D", "Email PDF from Stock Balance D2D"),
    ("reports.sales_dashboard.view", "View Sales Dashboard", "Open sales dashboard and KPI reports"),
    ("reports.sales_dashboard.email", "Email Sales Dashboard", "Configure and send Sales Dashboard emails"),
    ("reports.sms_email.manage", "Manage SMS Sales Email", "Configure and run SMS_DB_ sales email scheduler"),
]

# Grant all new per-report rights to roles that already had the old shared GL view
# (or sales view / sms manage) so existing users are not locked out.
LEGACY_MIRROR = {
    "reports.gl_ledger.view": [
        "reports.gl_ledger.view",
        "reports.gl_ledger.email",
        "reports.gl_ledger.whatsapp",
        "reports.gl_ledger_detailed.view",
        "reports.gl_ledger_detailed.email",
        "reports.gl_ledger_detailed.whatsapp",
        "reports.gl_ledger_mobile.view",
        "reports.gl_ledger_mobile.email",
        "reports.gl_ledger_mobile.whatsapp",
        "reports.gl_credit_summary.view",
        "reports.gl_credit_summary.email",
        "reports.trial_balance_d2d.view",
        "reports.trial_balance_d2d.email",
        "reports.trial_balance_d2d.whatsapp",
        "reports.trial_balance_d2d_mobile.view",
        "reports.trial_balance_d2d_mobile.email",
        "reports.trial_balance_d2d_mobile.whatsapp",
        "reports.stock_balance_d2d.view",
        "reports.stock_balance_d2d.email",
    ],
    "reports.sales_dashboard.view": [
        "reports.sales_dashboard.view",
        "reports.sales_dashboard.email",
    ],
    "reports.sms_email.manage": [
        "reports.sms_email.manage",
    ],
}

GRANT_ROLE_CODES = ("SUPER_ADMIN", "ADMIN", "REPORTS_ONLY")

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


def _ensure_permission(db: Session, module_id: int, code: str, name: str, desc: str) -> Permission:
    existing = db.execute(select(Permission).where(Permission.PermissionCode == code)).scalar_one_or_none()
    if existing:
        if existing.IsDeleted:
            existing.IsDeleted = False
            existing.IsActive = True
        return existing
    perm = Permission(
        ModuleId=module_id,
        PermissionCode=code,
        PermissionName=name,
        Description=desc,
    )
    db.add(perm)
    db.flush()
    return perm


def _role_has_permission(db: Session, role_id: int, permission_id: int) -> bool:
    row = db.execute(
        select(RolePermission).where(
            RolePermission.RoleId == role_id,
            RolePermission.PermissionId == permission_id,
            RolePermission.IsDeleted == False,  # noqa: E712
        )
    ).scalar_one_or_none()
    return row is not None


def _grant(db: Session, role_id: int, permission_id: int) -> None:
    existing = db.execute(
        select(RolePermission).where(
            RolePermission.RoleId == role_id,
            RolePermission.PermissionId == permission_id,
        )
    ).scalar_one_or_none()
    if existing:
        if existing.IsDeleted:
            existing.IsDeleted = False
        return
    db.add(RolePermission(RoleId=role_id, PermissionId=permission_id))


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

        by_code: dict[str, Permission] = {}
        for code, name, desc in REPORT_PERMS:
            by_code[code] = _ensure_permission(db, module.ModuleId, code, name, desc)
        db.flush()

        for role_code in GRANT_ROLE_CODES:
            role = db.execute(select(Role).where(Role.RoleCode == role_code)).scalar_one_or_none()
            if not role:
                continue
            for legacy_code, grant_codes in LEGACY_MIRROR.items():
                legacy = by_code.get(legacy_code) or db.execute(
                    select(Permission).where(Permission.PermissionCode == legacy_code)
                ).scalar_one_or_none()
                if not legacy or not _role_has_permission(db, role.RoleId, legacy.PermissionId):
                    # SUPER_ADMIN / ADMIN: still grant all report perms for convenience
                    if role_code not in ("SUPER_ADMIN", "ADMIN"):
                        continue
                for code in grant_codes:
                    perm = by_code.get(code)
                    if perm:
                        _grant(db, role.RoleId, perm.PermissionId)

            # Always ensure SUPER_ADMIN / ADMIN get every report perm
            if role_code in ("SUPER_ADMIN", "ADMIN"):
                for perm in by_code.values():
                    _grant(db, role.RoleId, perm.PermissionId)

        db.commit()
        print(f"{auth_db}: per-report permissions ready ({len(by_code)} codes).")
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def main() -> int:
    parser = argparse.ArgumentParser(description="Seed per-report View/Email/WhatsApp permissions")
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
