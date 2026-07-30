"""Permission ORM models."""

from typing import List, Optional

from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import AuditMixin, Base


class Permission(Base, AuditMixin):
    __tablename__ = "Permissions"
    __table_args__ = {"schema": "auth"}

    PermissionId: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    ModuleId: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("auth.Modules.ModuleId"), nullable=True
    )
    FeatureId: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("auth.Features.FeatureId"), nullable=True
    )
    PermissionCode: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    PermissionName: Mapped[str] = mapped_column(String(150), nullable=False)
    Description: Mapped[Optional[str]] = mapped_column(String(500))

    module: Mapped[Optional["Module"]] = relationship(back_populates="permissions")
    feature: Mapped[Optional["Feature"]] = relationship(back_populates="permissions")
    role_permissions: Mapped[List["RolePermission"]] = relationship(back_populates="permission")


class RolePermission(Base, AuditMixin):
    __tablename__ = "RolePermissions"
    __table_args__ = {"schema": "auth"}

    RolePermissionId: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    RoleId: Mapped[int] = mapped_column(Integer, ForeignKey("auth.Roles.RoleId"), nullable=False)
    PermissionId: Mapped[int] = mapped_column(
        Integer, ForeignKey("auth.Permissions.PermissionId"), nullable=False
    )

    role: Mapped["Role"] = relationship(back_populates="role_permissions")
    permission: Mapped["Permission"] = relationship(back_populates="role_permissions")


from app.models.module import Feature, Module  # noqa: E402
from app.models.role import Role  # noqa: E402
