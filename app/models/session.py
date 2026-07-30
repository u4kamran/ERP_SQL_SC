"""Session and token ORM models."""

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import AuditMixin, Base


class UserSession(Base, AuditMixin):
    __tablename__ = "UserSessions"
    __table_args__ = {"schema": "auth"}

    SessionId: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    UserId: Mapped[int] = mapped_column(Integer, ForeignKey("auth.Users.UserId"), nullable=False)
    RefreshTokenHash: Mapped[str] = mapped_column(String(255), nullable=False)
    IpAddress: Mapped[Optional[str]] = mapped_column(String(45))
    UserAgent: Mapped[Optional[str]] = mapped_column(String(500))
    Browser: Mapped[Optional[str]] = mapped_column(String(100))
    Device: Mapped[Optional[str]] = mapped_column(String(100))
    OperatingSystem: Mapped[Optional[str]] = mapped_column(String(100))
    IsRememberMe: Mapped[bool] = mapped_column(Boolean, default=False)
    ExpiresAt: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    LastActivityDate: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    IsRevoked: Mapped[bool] = mapped_column(Boolean, default=False)
    RevokedDate: Mapped[Optional[datetime]] = mapped_column(DateTime)
    RevokedReason: Mapped[Optional[str]] = mapped_column(String(200))

    user: Mapped["User"] = relationship(back_populates="sessions")
    refresh_tokens: Mapped[list["RefreshToken"]] = relationship(back_populates="session")


class RefreshToken(Base, AuditMixin):
    __tablename__ = "RefreshTokens"
    __table_args__ = {"schema": "auth"}

    RefreshTokenId: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    UserId: Mapped[int] = mapped_column(Integer, ForeignKey("auth.Users.UserId"), nullable=False)
    SessionId: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("auth.UserSessions.SessionId"), nullable=False
    )
    TokenHash: Mapped[str] = mapped_column(String(255), nullable=False)
    ExpiresAt: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    IsRevoked: Mapped[bool] = mapped_column(Boolean, default=False)
    RevokedDate: Mapped[Optional[datetime]] = mapped_column(DateTime)
    ReplacedByTokenId: Mapped[Optional[int]] = mapped_column(Integer)

    session: Mapped["UserSession"] = relationship(back_populates="refresh_tokens")


class RevokedToken(Base, AuditMixin):
    __tablename__ = "RevokedTokens"
    __table_args__ = {"schema": "auth"}

    RevokedTokenId: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    Jti: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    TokenType: Mapped[str] = mapped_column(String(20), nullable=False)
    UserId: Mapped[Optional[int]] = mapped_column(Integer)
    ExpiresAt: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    RevokedDate: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    RevokedReason: Mapped[Optional[str]] = mapped_column(String(200))


from app.models.user import User  # noqa: E402
