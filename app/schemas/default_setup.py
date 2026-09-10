"""Schemas for Default Setup (business day configuration)."""

from pydantic import BaseModel, Field


class BusinessDayConfigResponse(BaseModel):
    business_day_start_time: str = Field(description="24-hour HH:MM, e.g. 08:00")
    business_day_end_time: str = Field(description="24-hour HH:MM on next calendar day, e.g. 05:00")
    business_hours_note: str = ""
    updated_at: str | None = None
    updated_by_username: str | None = None


class BusinessDayConfigUpdate(BaseModel):
    business_day_start_time: str = Field(min_length=4, max_length=5, examples=["08:00"])
    business_day_end_time: str = Field(min_length=4, max_length=5, examples=["05:00"])
