"""Audit and login history ORM models."""

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import BigInteger, DateTime, ForeignKey, Integer, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import AuditMixin, Base


class LoginHistory(Base, AuditMixin):
    __tablename__ = "LoginHistory"
    __table_args__ = {"schema": "auth"}

    LoginHistoryId: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    UserId: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("auth.Users.UserId"))
    Username: Mapped[str] = mapped_column(String(100), nullable=False)
    LoginStatus: Mapped[str] = mapped_column(String(20), nullable=False)
    FailureReason: Mapped[Optional[str]] = mapped_column(String(200))
    IpAddress: Mapped[Optional[str]] = mapped_column(String(45))
    UserAgent: Mapped[Optional[str]] = mapped_column(String(500))
    Browser: Mapped[Optional[str]] = mapped_column(String(100))
    Device: Mapped[Optional[str]] = mapped_column(String(100))
    OperatingSystem: Mapped[Optional[str]] = mapped_column(String(100))
    SessionId: Mapped[Optional[uuid.UUID]] = mapped_column(Uuid)


class AuditLog(Base, AuditMixin):
    __tablename__ = "AuditLogs"
    __table_args__ = {"schema": "auth"}

    AuditLogId: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    UserId: Mapped[Optional[int]] = mapped_column(Integer)
    Username: Mapped[Optional[str]] = mapped_column(String(100))
    Action: Mapped[str] = mapped_column(String(100), nullable=False)
    EntityType: Mapped[Optional[str]] = mapped_column(String(100))
    EntityId: Mapped[Optional[str]] = mapped_column(String(100))
    OldValues: Mapped[Optional[str]] = mapped_column(Text)
    NewValues: Mapped[Optional[str]] = mapped_column(Text)
    IpAddress: Mapped[Optional[str]] = mapped_column(String(45))
    UserAgent: Mapped[Optional[str]] = mapped_column(String(500))
    Status: Mapped[str] = mapped_column(String(20), default="SUCCESS")
    ErrorMessage: Mapped[Optional[str]] = mapped_column(String(500))
