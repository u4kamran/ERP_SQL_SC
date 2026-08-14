"""Seed Voice Search Control panel permissions."""

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
        "marketing.voice_control.view",
        "View Voice Search Control",
        "View voice limits, budget, and misuse audit log",
    ),
    (
        "marketing.voice_control.manage",
        "Manage Voice Search Control",
        "Change voice enable flags, limits, and daily budget",
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
            print("REPORTS/AUTH module not found.")
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
        print("Voice control permissions seeded. Users must re-login.")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
