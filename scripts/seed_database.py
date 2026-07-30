"""
Database seed script.

Creates default admin user with proper BCrypt password hash.
Run after SQL scripts: python -m scripts.seed_database
"""

import sys
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import select

from app.config.settings import settings
from app.database.session import SessionLocal
from app.models.role import Role, UserRole
from app.models.user import User
from app.security.password import hash_password


def seed_admin():
    db = SessionLocal()
    try:
        admin = db.execute(select(User).where(User.Username == settings.default_admin_username)).scalar_one_or_none()

        password_hash = hash_password(settings.default_admin_password)

        if admin:
            admin.PasswordHash = password_hash
            admin.MustChangePassword = True
            admin.ModifiedDate = datetime.utcnow()
            print(f"Updated admin password hash for user: {settings.default_admin_username}")
        else:
            admin = User(
                Username=settings.default_admin_username,
                Email=settings.default_admin_email,
                PasswordHash=password_hash,
                FirstName="System",
                LastName="Administrator",
                MustChangePassword=True,
                PasswordExpiryDate=datetime.utcnow() + timedelta(days=settings.password_expiry_days),
                IsEmailVerified=True,
                IsActive=True,
            )
            db.add(admin)
            db.flush()

            super_admin_role = db.execute(
                select(Role).where(Role.RoleCode == "SUPER_ADMIN")
            ).scalar_one_or_none()

            if super_admin_role:
                db.add(UserRole(UserId=admin.UserId, RoleId=super_admin_role.RoleId, CreatedBy=admin.UserId))

            print(f"Created admin user: {settings.default_admin_username}")

        db.commit()
        print(f"Default password: {settings.default_admin_password}")
        print("IMPORTANT: Change password on first login!")
    except Exception as e:
        db.rollback()
        print(f"Seed failed: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_admin()
