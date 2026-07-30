"""Schemas for General Ledger report."""

from __future__ import annotations

from datetime import date
from typing import List, Optional

from pydantic import BaseModel, EmailStr, Field, field_validator


class GlLedgerReportRequest(BaseModel):
    start_ac_id: int = Field(..., ge=1)
    end_ac_id: int = Field(..., ge=1)
    date_from: date
    date_to: date
    suppress_zero_bal: bool = False
    complete_report: bool = False
    page_wise: bool = False

    @field_validator("end_ac_id")
    @classmethod
    def end_after_start(cls, end_ac_id: int, info):
        start = info.data.get("start_ac_id")
        if start is not None and end_ac_id < start:
            raise ValueError("Ending ID must be greater than or equal to Starting ID.")
        return end_ac_id


class GlLedgerEmailRequest(GlLedgerReportRequest):
    to_email: str = Field(..., min_length=3, max_length=500)
    subject: Optional[str] = Field(None, max_length=200)
    message: Optional[str] = Field(None, max_length=2000)

    @field_validator("to_email")
    @classmethod
    def validate_recipients(cls, value: str) -> str:
        from email_validator import EmailNotValidError, validate_email

        parts = [part.strip() for part in value.replace(";", ",").split(",") if part.strip()]
        if not parts:
            raise ValueError("Enter at least one email address.")
        normalized: list[str] = []
        for part in parts:
            try:
                normalized.append(validate_email(part, check_deliverability=False).normalized)
            except EmailNotValidError as exc:
                raise ValueError(f"Invalid email address: {part}") from exc
        return ", ".join(normalized)


class GlLedgerEmailResponse(BaseModel):
    message: str
    success: bool = True
    recipients: List[str] = []


class GlLedgerEmailStatus(BaseModel):
    configured: bool = False
    from_email: str = ""
    hint: str = ""


class GlLedgerWhatsAppRequest(GlLedgerReportRequest):
    to_phone: str = Field(..., min_length=7, max_length=20)
    message: Optional[str] = Field(None, max_length=1000)


class GlLedgerWhatsAppResponse(BaseModel):
    message: str
    success: bool = True
    to_phone: str = ""


class GlLedgerWhatsAppStatus(BaseModel):
    configured: bool = False
    hint: str = ""


class GlWhatsAppContactLookup(BaseModel):
    contact_id: str
    name: str
    phone_display: str
    phone_raw: str = ""
    ac_id: Optional[int] = None
    source: str = ""
    has_mobile: bool = True


class GlLedgerMobilePdfResponse(BaseModel):
    view_url: str
    filename: str
    expires_in_minutes: int = 15


class GlAccountLookup(BaseModel):
    ac_id: int
    ac_title: str
    ac_id_display: str


class GlLedgerTransactionRow(BaseModel):
    voucher_date: Optional[date] = None
    voucher_no: str = ""
    voucher_type: str = ""
    narration: str = ""
    book_id: Optional[int] = None
    reference: str = ""
    debit: float = 0
    credit: float = 0
    balance: float = 0


class GlLedgerAccountSection(BaseModel):
    ac_id: int
    ac_id_display: str
    ac_title: str
    opening_balance: float = 0
    opening_debit: float = 0
    opening_credit: float = 0
    transactions: List[GlLedgerTransactionRow] = []
    total_debit: float = 0
    total_credit: float = 0
    transaction_count: int = 0


class GlLedgerReportData(BaseModel):
    company_name: str
    report_title: str
    criteria: str
    date_range: str
    printed_on: str
    page_wise: bool = False
    accounts: List[GlLedgerAccountSection] = []
    total_accounts: int = 0
