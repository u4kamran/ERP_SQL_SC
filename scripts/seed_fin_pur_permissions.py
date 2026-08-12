"""Seed Purchase Receipt (Fin_Pur) permissions into auth database."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import select

from app.database.session import SessionLocal
from app.models.module import Module
from app.models.permission import Permission, RolePermission
from app.models.role import Role

PERMS = [
    ("inventory.fin_pur.view", "View Purchase Receipt", "Open Purchase Receipt (Fin_PurM)"),
    ("inventory.fin_pur.create", "Create Purchase Receipt", "Save new GRN / purchase documents"),
    ("inventory.fin_pur.edit", "Edit Purchase Receipt", "Edit unposted purchase documents"),
    ("inventory.fin_pur.delete", "Delete Purchase Receipt", "Delete unposted purchase documents"),
]


def seed():
    db = SessionLocal()
    try:
        module = db.execute(select(Module).where(Module.ModuleCode == "INVENTORY")).scalar_one_or_none()
        if not module:
            module = Module(
                ModuleCode="INVENTORY",
                ModuleName="Inventory",
                Description="Inventory and purchase",
                DisplayOrder=20,
                IsActive=True,
            )
            db.add(module)
            db.flush()

        for code, name, desc in PERMS:
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
        print("Purchase Receipt permissions seeded. Users must re-login to refresh JWT permissions.")
    except Exception as e:
        db.rollback()
        raise e
    finally:
        db.close()


if __name__ == "__main__":
    seed()
