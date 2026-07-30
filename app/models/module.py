"""Module and Feature ORM models."""

from datetime import datetime
from typing import List, Optional

from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import AuditMixin, Base


class Module(Base, AuditMixin):
    __tablename__ = "Modules"
    __table_args__ = {"schema": "auth"}

    ModuleId: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    ModuleCode: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    ModuleName: Mapped[str] = mapped_column(String(100), nullable=False)
    Description: Mapped[Optional[str]] = mapped_column(String(500))
    DisplayOrder: Mapped[int] = mapped_column(Integer, default=0)
    IconClass: Mapped[Optional[str]] = mapped_column(String(100))

    features: Mapped[List["Feature"]] = relationship(back_populates="module")
    permissions: Mapped[List["Permission"]] = relationship(back_populates="module")


class Feature(Base, AuditMixin):
    __tablename__ = "Features"
    __table_args__ = {"schema": "auth"}

    FeatureId: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    ModuleId: Mapped[int] = mapped_column(
        Integer, ForeignKey("auth.Modules.ModuleId"), nullable=False
    )
    FeatureCode: Mapped[str] = mapped_column(String(50), nullable=False)
    FeatureName: Mapped[str] = mapped_column(String(100), nullable=False)
    Description: Mapped[Optional[str]] = mapped_column(String(500))
    DisplayOrder: Mapped[int] = mapped_column(Integer, default=0)

    module: Mapped["Module"] = relationship(back_populates="features")
    permissions: Mapped[List["Permission"]] = relationship(back_populates="feature")


from app.models.permission import Permission  # noqa: E402
