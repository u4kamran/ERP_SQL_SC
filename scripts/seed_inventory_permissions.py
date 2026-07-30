"""Seed inventory FIN_ITEM permissions into auth database."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import select

from app.database.session import SessionLocal
from app.models.module import Module
from app.models.permission import Permission, RolePermission
from app.models.role import Role

PERMS = [
    ("inventory.fin_item.view", "View Items", "View FIN_ITEM inventory items"),
    ("inventory.fin_item.create", "Create Items", "Create FIN_ITEM records"),
    ("inventory.fin_item.update", "Update Items", "Update FIN_ITEM records"),
    ("inventory.fin_item.delete", "Delete Items", "Delete FIN_ITEM records"),
]


def seed():
    db = SessionLocal()
    try:
        module = db.execute(select(Module).where(Module.ModuleCode == "INVENTORY")).scalar_one_or_none()
        if not module:
            print("INVENTORY module not found. Run sql/05_seed_data.sql first.")
            return

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
        print("Inventory permissions seeded. Users must re-login to refresh JWT permissions.")
    except Exception as e:
        db.rollback()
        raise e
    finally:
        db.close()


if __name__ == "__main__":
    seed()
