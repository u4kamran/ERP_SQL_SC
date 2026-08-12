"""Seed Purchase Order (Fin_InvM_Order) permissions into auth database."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import select

from app.database.session import SessionLocal
from app.models.module import Module
from app.models.permission import Permission, RolePermission
from app.models.role import Role

PERMS = [
    ("inventory.fin_inv_order.view", "View Purchase Order", "Open Purchase Order (Fin_InvM_Order)"),
    ("inventory.fin_inv_order.create", "Create Purchase Order", "Save new purchase orders"),
    ("inventory.fin_inv_order.edit", "Edit Purchase Order", "Edit unposted purchase orders"),
    ("inventory.fin_inv_order.delete", "Delete Purchase Order", "Delete unposted purchase orders"),
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
        print("Purchase Order permissions seeded. Users must re-login to refresh JWT permissions.")
    except Exception as e:
        db.rollback()
        raise e
    finally:
        db.close()


if __name__ == "__main__":
    seed()
