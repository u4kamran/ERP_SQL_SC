"""Schemas for credit summary ledger (all transactions + daily credit sum)."""

from __future__ import annotations

from datetime import date
from typing import List, Optional

from pydantic import BaseModel

from app.schemas.gl_ledger_report import GlLedgerReportRequest

GlLedgerCreditSummaryRequest = GlLedgerReportRequest


class GlLedgerCreditTransactionRow(BaseModel):
    voucher_date: Optional[date] = None
    voucher_no: str = ""
    voucher_type: str = ""
    narration: str = ""
    book_id: Optional[int] = None
    reference: str = ""
    credit: float = 0
    daily_credit_sum: Optional[float] = None
    balance: float = 0


class GlLedgerCreditSummarySection(BaseModel):
    ac_id: int
    ac_id_display: str
    ac_title: str
    opening_balance: float = 0
    opening_credit: float = 0
    transactions: List[GlLedgerCreditTransactionRow] = []
    total_credit: float = 0
    transaction_count: int = 0


class GlLedgerCreditSummaryData(BaseModel):
    company_name: str
    report_title: str
    criteria: str
    date_range: str
    printed_on: str
    page_wise: bool = False
    accounts: List[GlLedgerCreditSummarySection] = []
    total_accounts: int = 0
