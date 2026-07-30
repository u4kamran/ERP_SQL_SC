"""
SQLAlchemy declarative base and shared mixins.

Every authentication table includes:
- CreatedDate, CreatedBy, ModifiedDate, ModifiedBy
- IsActive, IsDeleted

Note: RowVersion exists in the database (SQL Server ROWVERSION) but is NOT
mapped in ORM — SQL Server auto-manages it and rejects explicit INSERT values.
"""

from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, Integer
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


def utc_now() -> datetime:
    """Return naive UTC datetime for SQL Server DATETIME columns."""
    return datetime.utcnow()


class Base(DeclarativeBase):
    """Root declarative base for all ORM models."""

    pass


class TimestampMixin:
    """Standard audit timestamp columns."""

    CreatedDate: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=utc_now
    )
    CreatedBy: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    ModifiedDate: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    ModifiedBy: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)


class AuditMixin(TimestampMixin):
    """Full audit mixin with soft-delete and row versioning."""

    IsActive: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="1")
    IsDeleted: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="0")
