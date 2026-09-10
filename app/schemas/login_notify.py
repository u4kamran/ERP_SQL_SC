"""Schemas for login-alert email setup."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class LoginNotifySettingsUpdate(BaseModel):
    enabled: bool | None = None
    notify_email: str | None = Field(None, max_length=255)
    notes: str | None = Field(None, max_length=300)


class LoginNotifyDashboard(BaseModel):
    settings: dict[str, Any] = Field(default_factory=dict)
    smtp_configured: bool = False
    smtp_hint: str = ""
    today: dict[str, Any] = Field(default_factory=dict)
    totals: dict[str, Any] = Field(default_factory=dict)
    recent: list[dict[str, Any]] = Field(default_factory=list)
