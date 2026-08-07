"""Pydantic schemas for dbo.CUST_SMS CRUD."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, field_validator


class CustSmsBase(BaseModel):
    cust_name: str = Field(..., min_length=1, max_length=150)
    mobile_no: str = Field(..., min_length=7, max_length=20)
    mobile_no_tmp: Optional[str] = Field(None, max_length=20)
    cust_address: Optional[str] = Field(None, max_length=2000)
    status: Optional[int] = None
    star_rating: Optional[str] = Field(None, max_length=50)
    star_rating_value: Optional[str] = Field(None, max_length=50)
    star_rating_visit: Optional[str] = Field(None, max_length=50)
    star_rating_visit_value: Optional[str] = Field(None, max_length=50)
    star_rating_tsales: Optional[str] = Field(None, max_length=50)
    star_rating_tsales_value: Optional[str] = Field(None, max_length=50)

    @field_validator("cust_name", "mobile_no", "mobile_no_tmp", "cust_address", mode="before")
    @classmethod
    def strip_text(cls, value):
        if value is None:
            return value
        if isinstance(value, str):
            cleaned = value.strip()
            return cleaned or None
        return value

    @field_validator("mobile_no")
    @classmethod
    def require_mobile(cls, value: str) -> str:
        if not value or not value.strip():
            raise ValueError("Mobile number is required.")
        return value.strip()


class CustSmsCreate(CustSmsBase):
    pass


class CustSmsUpdate(CustSmsBase):
    pass


class CustSmsResponse(BaseModel):
    cust_id: int
    cust_name: str = ""
    mobile_no: str = ""
    mobile_no_tmp: str = ""
    cust_address: str = ""
    status: int | None = None
    added_datetime: datetime | None = None
    star_rating: str = ""
    star_rating_value: str = ""
    star_rating_visit: str = ""
    star_rating_visit_value: str = ""
    star_rating_tsales: str = ""
    star_rating_tsales_value: str = ""


class CustSmsListResponse(BaseModel):
    items: list[CustSmsResponse] = Field(default_factory=list)
    total: int = 0
    skip: int = 0
    limit: int = 50
