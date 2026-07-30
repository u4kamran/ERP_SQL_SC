"""Assign SUPER_ADMIN role to legacy super-user accounts (sa, admin, etc.)."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import select

from app.database.session import SessionLocal
from app.models.role import Role, UserRole
from app.models.user import User

SUPER_USERNAMES = {"sa", "admin", "administrator"}


def main() -> None:
    db = SessionLocal()
    try:
        super_role = db.execute(
            select(Role).where(Role.RoleCode == "SUPER_ADMIN")
        ).scalar_one()
        admin_role = db.execute(
            select(Role).where(Role.RoleCode == "ADMIN")
        ).scalar_one_or_none()

        users = db.execute(select(User).where(User.IsDeleted == False)).scalars().all()  # noqa: E712
        updated = 0

        for user in users:
            if user.Username.lower() not in SUPER_USERNAMES:
                continue

            has_super = db.execute(
                select(UserRole).where(
                    UserRole.UserId == user.UserId,
                    UserRole.RoleId == super_role.RoleId,
                )
            ).scalar_one_or_none()

            if not has_super:
                db.add(
                    UserRole(
                        UserId=user.UserId,
                        RoleId=super_role.RoleId,
                        CreatedBy=user.UserId,
                    )
                )
                updated += 1
                print(f"ASSIGN SUPER_ADMIN -> {user.Username} (UserId {user.UserId})")

            if admin_role:
                admin_link = db.execute(
                    select(UserRole).where(
                        UserRole.UserId == user.UserId,
                        UserRole.RoleId == admin_role.RoleId,
                    )
                ).scalar_one_or_none()
                if admin_link:
                    db.delete(admin_link)
                    print(f"REMOVE ADMIN       -> {user.Username}")

        db.commit()
        print(f"Done. Updated {updated} user(s).")
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
