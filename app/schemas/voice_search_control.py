"""Schemas for voice search control panel."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class VoiceSearchSettingsUpdate(BaseModel):
    cloud_voice_enabled: bool | None = None
    guest_voice_enabled: bool | None = None
    whatsapp_voice_enabled: bool | None = None
    require_mobile: bool | None = None
    daily_limit_per_mobile: int | None = Field(None, ge=0, le=10000)
    minute_limit_per_ip: int | None = Field(None, ge=0, le=1000)
    daily_budget_usd: float | None = Field(None, ge=0, le=100000)
    max_clip_seconds: int | None = Field(None, ge=1, le=120)
    notes: str | None = Field(None, max_length=300)


class VoiceSearchDashboard(BaseModel):
    settings: dict[str, Any] = Field(default_factory=dict)
    today: dict[str, Any] = Field(default_factory=dict)
    top_mobiles: list[dict[str, Any]] = Field(default_factory=list)
    recent: list[dict[str, Any]] = Field(default_factory=list)
    totals: dict[str, Any] = Field(default_factory=dict)
