"""User ORM models."""

from datetime import datetime
from typing import List, Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import AuditMixin, Base


class User(Base, AuditMixin):
    __tablename__ = "Users"
    __table_args__ = {"schema": "auth"}

    UserId: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    Username: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    Email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    PasswordHash: Mapped[str] = mapped_column(String(255), nullable=False)
    FirstName: Mapped[Optional[str]] = mapped_column(String(100))
    LastName: Mapped[Optional[str]] = mapped_column(String(100))
    PhoneNumber: Mapped[Optional[str]] = mapped_column(String(30))
    ProfileImageUrl: Mapped[Optional[str]] = mapped_column(String(500))
    MustChangePassword: Mapped[bool] = mapped_column(Boolean, default=False)
    PasswordChangedDate: Mapped[Optional[datetime]] = mapped_column(DateTime)
    PasswordExpiryDate: Mapped[Optional[datetime]] = mapped_column(DateTime)
    FailedLoginAttempts: Mapped[int] = mapped_column(Integer, default=0)
    LockoutEndDate: Mapped[Optional[datetime]] = mapped_column(DateTime)
    LastLoginDate: Mapped[Optional[datetime]] = mapped_column(DateTime)
    LastLoginIp: Mapped[Optional[str]] = mapped_column(String(45))
    IsEmailVerified: Mapped[bool] = mapped_column(Boolean, default=False)

    user_roles: Mapped[List["UserRole"]] = relationship(back_populates="user")
    sessions: Mapped[List["UserSession"]] = relationship(back_populates="user")
    preferences: Mapped[List["UserPreference"]] = relationship(back_populates="user")
    password_history: Mapped[List["PasswordHistory"]] = relationship(back_populates="user")

    @property
    def full_name(self) -> str:
        parts = [p for p in [self.FirstName, self.LastName] if p]
        return " ".join(parts) if parts else self.Username

    @property
    def is_locked(self) -> bool:
        if self.LockoutEndDate is None:
            return False
        return self.LockoutEndDate > datetime.utcnow()


class PasswordHistory(Base, AuditMixin):
    __tablename__ = "PasswordHistory"
    __table_args__ = {"schema": "auth"}

    PasswordHistoryId: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    UserId: Mapped[int] = mapped_column(Integer, ForeignKey("auth.Users.UserId"), nullable=False)
    PasswordHash: Mapped[str] = mapped_column(String(255), nullable=False)

    user: Mapped["User"] = relationship(back_populates="password_history")


class PasswordResetToken(Base, AuditMixin):
    __tablename__ = "PasswordResetTokens"
    __table_args__ = {"schema": "auth"}

    PasswordResetTokenId: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    UserId: Mapped[int] = mapped_column(Integer, ForeignKey("auth.Users.UserId"), nullable=False)
    TokenHash: Mapped[str] = mapped_column(String(255), nullable=False)
    ExpiresAt: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    IsUsed: Mapped[bool] = mapped_column(Boolean, default=False)
    UsedDate: Mapped[Optional[datetime]] = mapped_column(DateTime)


class UserPreference(Base, AuditMixin):
    __tablename__ = "UserPreferences"
    __table_args__ = {"schema": "auth"}

    UserPreferenceId: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    UserId: Mapped[int] = mapped_column(Integer, ForeignKey("auth.Users.UserId"), nullable=False)
    PreferenceKey: Mapped[str] = mapped_column(String(100), nullable=False)
    PreferenceValue: Mapped[str] = mapped_column(String(500), nullable=False)

    user: Mapped["User"] = relationship(back_populates="preferences")


from app.models.role import UserRole  # noqa: E402
from app.models.session import UserSession  # noqa: E402
