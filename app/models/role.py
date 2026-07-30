"""Role ORM models."""

from typing import List, Optional

from sqlalchemy import Boolean, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import AuditMixin, Base


class Role(Base, AuditMixin):
    __tablename__ = "Roles"
    __table_args__ = {"schema": "auth"}

    RoleId: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    RoleCode: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    RoleName: Mapped[str] = mapped_column(String(100), nullable=False)
    Description: Mapped[Optional[str]] = mapped_column(String(500))
    IsSystemRole: Mapped[bool] = mapped_column(Boolean, default=False)

    role_permissions: Mapped[List["RolePermission"]] = relationship(back_populates="role")
    user_roles: Mapped[List["UserRole"]] = relationship(back_populates="role")


class UserRole(Base, AuditMixin):
    __tablename__ = "UserRoles"
    __table_args__ = {"schema": "auth"}

    UserRoleId: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    UserId: Mapped[int] = mapped_column(Integer, ForeignKey("auth.Users.UserId"), nullable=False)
    RoleId: Mapped[int] = mapped_column(Integer, ForeignKey("auth.Roles.RoleId"), nullable=False)

    user: Mapped["User"] = relationship(back_populates="user_roles")
    role: Mapped["Role"] = relationship(back_populates="user_roles")


from app.models.permission import RolePermission  # noqa: E402
from app.models.user import User  # noqa: E402
