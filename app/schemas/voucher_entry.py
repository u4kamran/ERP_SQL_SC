"""Pydantic schemas for web voucher entry (VB6 GL0002/GL0003 parity)."""

from __future__ import annotations

from datetime import date, datetime
from typing import List, Optional

from pydantic import BaseModel, Field, field_validator


class VoucherLineIn(BaseModel):
    ac_id: int
    narration: str = ""
    debit: float = 0.0
    credit: float = 0.0
    reference: str = ""

    @field_validator("narration", mode="before")
    @classmethod
    def strip_narration(cls, v):
        return (v or "").strip()


class VoucherSaveRequest(BaseModel):
    book_id: int
    v_mode: int = Field(ge=1, le=3, description="1=JV, 2=Payment, 3=Receipt")
    fiscal: int = Field(ge=0, le=12)
    voucher_date: date
    remarks: str = ""
    lines: List[VoucherLineIn] = Field(min_length=1)
    voucher_id: Optional[int] = None
    serial_no: Optional[float] = None


class VoucherLineOut(BaseModel):
    serial_order: int
    ac_id: int
    ac_title: Optional[str] = None
    narration: str
    debit: float
    credit: float
    reference: str = ""


class VoucherHeaderOut(BaseModel):
    serial_no: float
    voucher_id: int
    book_id: int
    v_mode: int
    fiscal: int
    voucher_date: date
    remarks: str
    amount: float
    book_type: int
    sys_status: int
    voucher_abbr: Optional[str] = None
    book_title: Optional[str] = None
    lines: List[VoucherLineOut] = []


class VoucherSaveResponse(BaseModel):
    message: str
    serial_no: float
    voucher_id: int
    voucher_display: str


class VoucherBookOut(BaseModel):
    book_id: int
    book_title: str
    voucher_abbr: str
    book_type: int
    ac_id: Optional[int] = None
    v_numbering: int
    v_combination: int
    bb_od: Optional[int] = None
    title_jv: Optional[str] = None
    book_balance: Optional[float] = None


class VoucherConfigOut(BaseModel):
    max_entries: int
    fiscal_start: Optional[date] = None
    fiscal_end: Optional[date] = None
    legacy_uid: int


class VoucherAccountLookup(BaseModel):
    ac_id: int
    ac_title: str
    cbal: Optional[float] = None


class VoucherNarrationLookup(BaseModel):
    id: str
    narration: str
    source: str


class VoucherNextNumberOut(BaseModel):
    voucher_id: int
    voucher_display: str


class VoucherDeleteResponse(BaseModel):
    message: str
    voucher_id: int
