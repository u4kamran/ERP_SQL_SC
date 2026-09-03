"""Schemas for Detailed Customer Ledger (parallel to GL Ledger — does not alter it)."""

from __future__ import annotations

from datetime import date
from typing import List, Optional

from pydantic import BaseModel, Field, field_validator

from app.schemas.gl_ledger_report import (
    GlLedgerEmailRequest,
    GlLedgerEmailResponse,
    GlLedgerEmailStatus,
    GlLedgerMobilePdfResponse,
    GlLedgerWhatsAppRequest,
    GlLedgerWhatsAppResponse,
    GlLedgerWhatsAppStatus,
    GlWhatsAppContactLookup,
    GlAccountLookup,
)


class GlLedgerDetailedReportRequest(BaseModel):
    start_ac_id: int = Field(..., ge=1)
    end_ac_id: int = Field(..., ge=1)
    date_from: date
    date_to: date
    suppress_zero_bal: bool = False
    complete_report: bool = False
    page_wise: bool = False
    include_invoice_detail: bool = True

    @field_validator("end_ac_id")
    @classmethod
    def end_after_start(cls, end_ac_id: int, info):
        start = info.data.get("start_ac_id")
        if start is not None and end_ac_id < start:
            raise ValueError("Ending ID must be greater than or equal to Starting ID.")
        return end_ac_id


class GlLedgerDetailedEmailRequest(GlLedgerDetailedReportRequest):
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


class GlLedgerDetailedWhatsAppRequest(GlLedgerDetailedReportRequest):
    to_phone: str = Field(..., min_length=7, max_length=20)
    message: Optional[str] = Field(None, max_length=1000)


class GlLedgerInvoiceDetailLine(BaseModel):
    item_title: str = ""
    gate_pass: str = ""
    bill_no: str = ""
    qty: Optional[float] = None
    rate: Optional[float] = None
    value: Optional[float] = None
    gst: Optional[float] = None
    gst_display: str = "-"


class GlLedgerDetailedTransactionRow(BaseModel):
    voucher_date: Optional[date] = None
    voucher_no: str = ""
    voucher_type: str = ""
    narration: str = ""
    book_id: Optional[int] = None
    reference: str = ""
    serial_no: Optional[int] = None
    debit: float = 0
    credit: float = 0
    balance: float = 0
    line_details: List[GlLedgerInvoiceDetailLine] = []


class GlLedgerDetailedAccountSection(BaseModel):
    ac_id: int
    ac_id_display: str
    ac_title: str
    opening_balance: float = 0
    opening_debit: float = 0
    opening_credit: float = 0
    transactions: List[GlLedgerDetailedTransactionRow] = []
    total_debit: float = 0
    total_credit: float = 0
    transaction_count: int = 0
    total_qty: float = 0
    total_value: float = 0
    total_gst: float = 0


class GlLedgerDetailedReportData(BaseModel):
    company_name: str
    report_title: str
    criteria: str
    date_range: str
    printed_on: str
    page_wise: bool = False
    include_invoice_detail: bool = True
    accounts: List[GlLedgerDetailedAccountSection] = []
    total_accounts: int = 0


# Re-export shared response types used by the API layer
__all__ = [
    "GlLedgerDetailedReportRequest",
    "GlLedgerDetailedEmailRequest",
    "GlLedgerDetailedWhatsAppRequest",
    "GlLedgerInvoiceDetailLine",
    "GlLedgerDetailedTransactionRow",
    "GlLedgerDetailedAccountSection",
    "GlLedgerDetailedReportData",
    "GlLedgerEmailResponse",
    "GlLedgerEmailStatus",
    "GlLedgerMobilePdfResponse",
    "GlLedgerWhatsAppResponse",
    "GlLedgerWhatsAppStatus",
    "GlWhatsAppContactLookup",
    "GlAccountLookup",
    "GlLedgerEmailRequest",
    "GlLedgerWhatsAppRequest",
]
