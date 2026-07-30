"""User data access repository."""

from datetime import datetime
from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.models.permission import Permission, RolePermission
from app.models.role import Role, UserRole
from app.models.user import PasswordHistory, User


class UserRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, user_id: int) -> Optional[User]:
        return self.db.get(User, user_id)

    def get_by_username(self, username: str) -> Optional[User]:
        stmt = select(User).where(
            User.Username == username,
            User.IsDeleted == False,  # noqa: E712
        )
        return self.db.execute(stmt).scalar_one_or_none()

    def get_by_email(self, email: str) -> Optional[User]:
        stmt = select(User).where(
            User.Email == email,
            User.IsDeleted == False,  # noqa: E712
        )
        return self.db.execute(stmt).scalar_one_or_none()

    def get_user_roles(self, user_id: int) -> List[Role]:
        stmt = (
            select(Role)
            .join(UserRole, UserRole.RoleId == Role.RoleId)
            .where(
                UserRole.UserId == user_id,
                UserRole.IsActive == True,  # noqa: E712
                UserRole.IsDeleted == False,  # noqa: E712
                Role.IsActive == True,  # noqa: E712
            )
        )
        return list(self.db.execute(stmt).scalars().all())

    def get_user_permissions(self, user_id: int) -> List[str]:
        stmt = (
            select(Permission.PermissionCode)
            .join(RolePermission, RolePermission.PermissionId == Permission.PermissionId)
            .join(Role, Role.RoleId == RolePermission.RoleId)
            .join(UserRole, UserRole.RoleId == Role.RoleId)
            .where(
                UserRole.UserId == user_id,
                UserRole.IsActive == True,  # noqa: E712
                RolePermission.IsActive == True,  # noqa: E712
                Permission.IsActive == True,  # noqa: E712
            )
            .distinct()
        )
        return list(self.db.execute(stmt).scalars().all())

    def create(self, user: User) -> User:
        self.db.add(user)
        self.db.flush()
        return user

    def update(self, user: User) -> User:
        user.ModifiedDate = datetime.utcnow()
        self.db.flush()
        return user

    def set_roles(self, user_id: int, role_ids: List[int], modified_by: Optional[int] = None):
        """Replace user roles with the given role IDs."""
        existing = list(
            self.db.execute(select(UserRole).where(UserRole.UserId == user_id)).scalars().all()
        )
        target = set(role_ids)
        for ur in existing:
            if ur.RoleId in target:
                ur.IsActive = True
                ur.IsDeleted = False
                target.discard(ur.RoleId)
            else:
                ur.IsActive = False
                ur.IsDeleted = True
        for role_id in target:
            self.db.add(UserRole(UserId=user_id, RoleId=role_id, CreatedBy=modified_by))

    def assign_roles(self, user_id: int, role_ids: List[int], created_by: Optional[int] = None):
        self.set_roles(user_id, role_ids, created_by)

    def add_password_history(self, user_id: int, password_hash: str):
        self.db.add(PasswordHistory(UserId=user_id, PasswordHash=password_hash))

    def get_password_history(self, user_id: int, limit: int = 5) -> List[PasswordHistory]:
        stmt = (
            select(PasswordHistory)
            .where(PasswordHistory.UserId == user_id, PasswordHistory.IsDeleted == False)  # noqa: E712
            .order_by(PasswordHistory.CreatedDate.desc())
            .limit(limit)
        )
        return list(self.db.execute(stmt).scalars().all())

    def list_users(self, skip: int = 0, limit: int = 50) -> List[User]:
        stmt = (
            select(User)
            .where(User.IsDeleted == False)  # noqa: E712
            .order_by(User.Username)
            .offset(skip)
            .limit(limit)
        )
        return list(self.db.execute(stmt).scalars().all())
