"""Schemas for Trial Balance Date to Date report."""

from __future__ import annotations

from typing import List, Literal, Optional

from pydantic import BaseModel, Field

from app.schemas.gl_ledger_report import GlLedgerEmailRequest, GlLedgerReportRequest


class TrialBalanceD2DRequest(GlLedgerReportRequest):
    short_format: bool = False
    sort_by: Literal["ac_id", "ac_title"] = "ac_id"
    sort_order: Literal["asc", "desc"] = "asc"


class TrialBalanceD2DEmailRequest(GlLedgerEmailRequest):
    short_format: bool = False
    sort_by: Literal["ac_id", "ac_title"] = "ac_id"
    sort_order: Literal["asc", "desc"] = "asc"


class TrialBalanceD2DWhatsAppRequest(TrialBalanceD2DRequest):
    to_phone: str = Field(..., min_length=7, max_length=20)
    message: Optional[str] = Field(None, max_length=1000)


class TrialBalanceD2DRow(BaseModel):
    ac_id: int
    ac_id_display: str
    ac_title: str
    opening_balance: float = 0
    period_debit: float = 0
    period_credit: float = 0
    net_balance: float = 0
    closing_balance: float = 0


class TrialBalanceD2DTotals(BaseModel):
    opening_debit: float = 0
    opening_credit: float = 0
    opening_credit_signed: float = 0  # VB6 TOBalCr — sum of negative openings
    period_debit: float = 0
    period_credit: float = 0
    net_debit: float = 0
    net_credit: float = 0
    closing_debit: float = 0
    closing_credit: float = 0
    diff_opening: float = 0
    diff_closing: float = 0


class TrialBalanceD2DData(BaseModel):
    company_name: str
    report_title: str
    criteria: str
    date_range: str
    printed_on: str
    short_format: bool = False
    rows: List[TrialBalanceD2DRow] = []
    total_rows: int = 0
    totals: TrialBalanceD2DTotals = Field(default_factory=TrialBalanceD2DTotals)
