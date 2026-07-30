"""Schemas for SMS_DB_ email scheduler."""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class SmsEmailSchedulerConfig(BaseModel):
    enabled: bool = False
    recipients: str = ""
    body_keyword: str = "Total Sales"
    window_start: str = "08:00"
    window_end: str = "01:30"
    check_interval_minutes: int = Field(default=30, ge=5, le=120)
    email_subject: str = "Sales Summary Alert"
    last_emailed_id: int = 0


class SmsEmailSchedulerConfigUpdate(BaseModel):
    enabled: bool
    recipients: str
    body_keyword: str = "Total Sales"
    window_start: str = "08:00"
    window_end: str = "01:30"
    check_interval_minutes: int = Field(default=30, ge=5, le=120)
    email_subject: str = "Sales Summary Alert"


class SmsEmailSchedulerStatus(BaseModel):
    enabled: bool
    smtp_configured: bool
    within_window: bool
    scheduler_running: bool
    check_interval_minutes: int
    window_start: str
    window_end: str
    body_keyword: str
    recipients: List[str] = []
    last_emailed_id: int = 0
    last_check_at: Optional[str] = None
    last_email_at: Optional[str] = None
    last_email_record_id: Optional[int] = None
    last_error: Optional[str] = None
    next_check_at: Optional[str] = None
    last_check_message: Optional[str] = None
    latest_record_id: Optional[int] = None
    latest_record_preview: Optional[str] = None
    pending_send: bool = False


class SmsEmailSchedulerRunResult(BaseModel):
    success: bool
    message: str
    record_id: Optional[int] = None
    emailed: bool = False


class SmsDbRecord(BaseModel):
    id: int
    body: str
    sender: str
    recipient: str
    sent: datetime
    status: int
    subject: str
    added_at: datetime
