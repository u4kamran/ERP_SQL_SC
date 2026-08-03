"""Seed GL voucher entry permissions into auth database."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import select

from app.database.session import SessionLocal
from app.models.module import Module
from app.models.permission import Permission, RolePermission
from app.models.role import Role

PERMS = [
    ("gl.voucher.view", "View Voucher Entry", "Open voucher entry and lookups"),
    ("gl.voucher.create", "Create Vouchers", "Save new vouchers to GL0002/GL0003"),
    ("gl.voucher.edit", "Edit Vouchers", "Edit unposted vouchers"),
    ("gl.voucher.delete", "Delete Vouchers", "Delete unposted vouchers"),
]


def seed():
    db = SessionLocal()
    try:
        module = db.execute(select(Module).where(Module.ModuleCode == "GL")).scalar_one_or_none()
        if not module:
            module = Module(
                ModuleCode="GL",
                ModuleName="General Ledger",
                Description="Voucher and GL entry",
                DisplayOrder=15,
                IsActive=True,
            )
            db.add(module)
            db.flush()

        for code, name, desc in PERMS:
            existing = db.execute(select(Permission).where(Permission.PermissionCode == code)).scalar_one_or_none()
            if not existing:
                db.add(Permission(ModuleId=module.ModuleId, PermissionCode=code, PermissionName=name, Description=desc))

        db.flush()

        for role_code in ("SUPER_ADMIN", "ADMIN", "USER"):
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
        print("Voucher permissions seeded. Users must re-login to refresh JWT permissions.")
    except Exception as e:
        db.rollback()
        raise e
    finally:
        db.close()


if __name__ == "__main__":
    seed()
