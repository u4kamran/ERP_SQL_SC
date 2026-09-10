"""Schemas for Stock Balance Date to Date report (VB6 RptStD2D / RptStD2DAmtBrand)."""

from __future__ import annotations

from datetime import date
from typing import List, Literal, Optional

from pydantic import BaseModel, Field, field_validator

from app.schemas.gl_ledger_report import GlLedgerEmailResponse, GlLedgerEmailStatus


class StockBalanceD2DRequest(BaseModel):
    start_item_id: int = Field(..., ge=1)
    end_item_id: int = Field(..., ge=1)
    date_from: date
    date_to: date
    suppress_zero_bal: bool = False
    complete_report: bool = False
    show_manual_id: bool = True
    store_ledger: bool = False
    print_amount: bool = False
    sort_by: Literal["ac_id", "ac_title"] = "ac_id"
    sort_order: Literal["asc", "desc"] = "asc"

    @field_validator("end_item_id")
    @classmethod
    def end_after_start(cls, end_item_id: int, info):
        start = info.data.get("start_item_id")
        if start is not None and end_item_id < start:
            raise ValueError("Ending ID must be greater than or equal to Starting ID.")
        return end_item_id


class StockBalanceD2DEmailRequest(StockBalanceD2DRequest):
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


class StockBalanceD2DRow(BaseModel):
    item_id: int
    item_id_display: str
    item_title: str
    brand: str = "Nil"
    # Qty-mode (RptStD2D): opening / stock in / stock out / net / closing
    opening_balance: float = 0
    stock_in: float = 0
    stock_out: float = 0
    net_balance: float = 0
    closing_balance: float = 0
    # Amt-mode (RptStD2DAmtBrand): opening+closing qty/amt + period nets
    opening_qty: float = 0
    opening_amt: float = 0
    period_qty: float = 0
    period_amt: float = 0
    closing_qty: float = 0
    closing_amt: float = 0


class StockBalanceD2DTotals(BaseModel):
    # Qty-mode totals
    opening_balance: float = 0
    stock_in: float = 0
    stock_out: float = 0
    net_stock_in: float = 0
    net_stock_out: float = 0
    closing_balance: float = 0
    # Amt-mode totals
    opening_qty: float = 0
    opening_amt: float = 0
    period_qty: float = 0
    period_amt: float = 0
    closing_qty: float = 0
    closing_amt: float = 0


class StockBalanceD2DData(BaseModel):
    company_name: str
    report_title: str
    criteria: str
    date_range: str
    printed_on: str
    print_amount: bool = False
    rows: List[StockBalanceD2DRow] = []
    total_rows: int = 0
    totals: StockBalanceD2DTotals = Field(default_factory=StockBalanceD2DTotals)


class StockItemLookup(BaseModel):
    item_id: int
    item_id_display: str
    item_title: str
    manualid: Optional[int] = None


__all__ = [
    "StockBalanceD2DRequest",
    "StockBalanceD2DEmailRequest",
    "StockBalanceD2DRow",
    "StockBalanceD2DTotals",
    "StockBalanceD2DData",
    "StockItemLookup",
    "GlLedgerEmailResponse",
    "GlLedgerEmailStatus",
]
