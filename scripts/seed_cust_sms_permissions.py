"""Seed CUST_SMS CRUD permissions."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import select

from app.database.session import SessionLocal
from app.models.module import Module
from app.models.permission import Permission, RolePermission
from app.models.role import Role

PERMS = [
    (
        "marketing.cust_sms.view",
        "View CUST_SMS",
        "View Customer SMS (CUST_SMS) master records",
    ),
    (
        "marketing.cust_sms.create",
        "Create CUST_SMS",
        "Create Customer SMS (CUST_SMS) records",
    ),
    (
        "marketing.cust_sms.update",
        "Update CUST_SMS",
        "Update Customer SMS (CUST_SMS) records",
    ),
    (
        "marketing.cust_sms.delete",
        "Delete CUST_SMS",
        "Delete Customer SMS (CUST_SMS) records",
    ),
]


def seed():
    db = SessionLocal()
    try:
        module = db.execute(
            select(Module).where(Module.ModuleCode == "REPORTS")
        ).scalar_one_or_none()
        if not module:
            module = db.execute(
                select(Module).where(Module.ModuleCode == "AUTH")
            ).scalar_one_or_none()
        if not module:
            print("REPORTS/AUTH module not found. Run sql/05_seed_data.sql first.")
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

        for role_code in ("SUPER_ADMIN", "ADMIN", "USER"):
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
                    db.add(RolePermission(RoleId=role.RoleId, PermissionId=perm.PermissionId))

        db.commit()
        print("CUST_SMS permissions seeded. Users must re-login.")
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed()
