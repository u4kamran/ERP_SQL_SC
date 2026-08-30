"""Schemas for OTP / SMS master control."""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


class OtpSmsControlSettings(BaseModel):
    master_enabled: bool
    web_enabled: bool
    mobile_enabled: bool
    web_effective: bool
    mobile_effective: bool
    web_overridden_by_master: bool = False
    mobile_overridden_by_master: bool = False
    row_version: int
    updated_by_user_id: Optional[int] = None
    updated_by_username: Optional[str] = None
    updated_at: Optional[str] = None
    comment: Optional[str] = None
    config_ok: bool = True


class OtpSmsControlUpdate(BaseModel):
    master_enabled: bool
    web_enabled: bool
    mobile_enabled: bool
    row_version: int = Field(..., ge=1)
    comment: Optional[str] = Field(default=None, max_length=300)
