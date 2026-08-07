"""Idempotently seed the delivery module and admin permissions."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import select

from app.database.session import SessionLocal
from app.models.module import Module
from app.models.permission import Permission, RolePermission
from app.models.role import Role


PERMISSIONS = [
    (
        "delivery.orders.view",
        "View Delivery Orders",
        "View delivery orders, summary, and riders",
    ),
    (
        "delivery.orders.sync",
        "Sync Delivery Orders",
        "Import recent delivery orders from invoices",
    ),
    (
        "delivery.orders.assign",
        "Assign Delivery Orders",
        "Assign delivery orders to active riders",
    ),
    (
        "delivery.orders.update",
        "Update Delivery Status",
        "Update delivery order status and proof of delivery",
    ),
    (
        "delivery.riders.manage",
        "Manage Delivery Riders",
        "Create and manage delivery riders",
    ),
]


def seed() -> None:
    db = SessionLocal()
    try:
        module = db.execute(
            select(Module).where(Module.ModuleCode == "DELIVERY")
        ).scalar_one_or_none()
        if not module:
            module = Module(
                ModuleCode="DELIVERY",
                ModuleName="Delivery Management",
                Description="Delivery order, rider, and status management",
                DisplayOrder=13,
                IconClass="bi-truck",
            )
            db.add(module)
            db.flush()

        for code, name, description in PERMISSIONS:
            permission = db.execute(
                select(Permission).where(Permission.PermissionCode == code)
            ).scalar_one_or_none()
            if not permission:
                db.add(
                    Permission(
                        ModuleId=module.ModuleId,
                        PermissionCode=code,
                        PermissionName=name,
                        Description=description,
                    )
                )

        db.flush()

        for role_code in ("SUPER_ADMIN", "ADMIN"):
            role = db.execute(
                select(Role).where(Role.RoleCode == role_code)
            ).scalar_one_or_none()
            if not role:
                continue
            for code, _, _ in PERMISSIONS:
                permission = db.execute(
                    select(Permission).where(Permission.PermissionCode == code)
                ).scalar_one()
                mapping = db.execute(
                    select(RolePermission).where(
                        RolePermission.RoleId == role.RoleId,
                        RolePermission.PermissionId == permission.PermissionId,
                    )
                ).scalar_one_or_none()
                if not mapping:
                    db.add(
                        RolePermission(
                            RoleId=role.RoleId,
                            PermissionId=permission.PermissionId,
                        )
                    )

        db.commit()
        print("Delivery permissions seeded for SUPER_ADMIN and ADMIN. Users must re-login.")
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed()
