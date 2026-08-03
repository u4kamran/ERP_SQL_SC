"""Schemas for scheduled sales dashboard email reports."""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


class SalesDashboardEmailConfig(BaseModel):
    enabled: bool = False
    recipients: str = ""
    interval_minutes: int = 30
    email_subject: str = "Sales Dashboard — Month-over-Month"
    date_preset: str = "this-month"


class SalesDashboardEmailConfigUpdate(BaseModel):
    enabled: bool = False
    recipients: str = ""
    interval_minutes: int = Field(default=30, ge=15, le=1440)
    email_subject: str = "Sales Dashboard — Month-over-Month"
    date_preset: str = "this-month"


class SalesDashboardEmailStatus(BaseModel):
    enabled: bool
    smtp_configured: bool
    scheduler_running: bool
    interval_minutes: int
    date_preset: str
    recipients: list[str]
    last_email_at: Optional[str] = None
    last_error: Optional[str] = None
    next_check_at: Optional[str] = None
    last_check_message: Optional[str] = None


class SalesDashboardEmailRunResult(BaseModel):
    success: bool
    message: str
    emailed: bool = False
