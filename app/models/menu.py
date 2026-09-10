"""ORM models for application menus and per-user menu rights."""

from typing import List, Optional

from sqlalchemy import Boolean, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import AuditMixin, Base


class Menu(Base, AuditMixin):
    __tablename__ = "Menus"
    __table_args__ = {"schema": "auth"}

    MenuId: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    MenuCode: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)
    MenuName: Mapped[str] = mapped_column(String(150), nullable=False)
    MenuGroup: Mapped[str] = mapped_column(String(100), nullable=False)
    ParentMenuCode: Mapped[Optional[str]] = mapped_column(String(120))
    Path: Mapped[Optional[str]] = mapped_column(String(255))
    IconClass: Mapped[Optional[str]] = mapped_column(String(100))
    PermissionCode: Mapped[Optional[str]] = mapped_column(String(100))
    Description: Mapped[Optional[str]] = mapped_column(String(500))
    DisplayOrder: Mapped[int] = mapped_column(Integer, default=0)
    IsGroup: Mapped[bool] = mapped_column(Boolean, default=False)

    user_rights: Mapped[List["UserMenuRight"]] = relationship(back_populates="menu")


class UserMenuRight(Base, AuditMixin):
    __tablename__ = "UserMenuRights"
    __table_args__ = {"schema": "auth"}

    UserMenuRightId: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    UserId: Mapped[int] = mapped_column(Integer, ForeignKey("auth.Users.UserId"), nullable=False)
    MenuId: Mapped[int] = mapped_column(Integer, ForeignKey("auth.Menus.MenuId"), nullable=False)
    CanAccess: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    menu: Mapped["Menu"] = relationship(back_populates="user_rights")
