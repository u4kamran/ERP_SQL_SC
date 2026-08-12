"""Pydantic schemas for VB6 Fin_PurM / Fin_PurD Purchase Receipt parity."""

from __future__ import annotations

from datetime import date
from typing import List, Optional

from pydantic import BaseModel, Field, field_validator


class FinPurLineIn(BaseModel):
    item_id: float
    item_title: str = ""
    qty: float
    rate: float = 0.0
    pur_amt: float = 0.0
    stax_rate: float = 0.0
    stax_amt: float = 0.0
    disc_per: float = 0.0
    disc_amt: float = 0.0
    disc_per_oi: float = 0.0
    disc_amt_oi: float = 0.0
    total_amt: float = 0.0
    remarks: str = ""
    exp_date: Optional[date] = None

    @field_validator("remarks", "item_title", mode="before")
    @classmethod
    def strip_text(cls, v):
        return (v or "").strip()


class FinPurHeaderCharges(BaseModel):
    """Hidden H* buckets on Fin_PurM (after Fin_PurDed mapping)."""

    discount: float = 0.0
    claim: float = 0.0
    other_ded: float = 0.0
    loading: float = 0.0
    carriage: float = 0.0
    other_charges: float = 0.0


class FinPurSaveRequest(BaseModel):
    prod_id: Optional[int] = None
    serial_no: Optional[int] = None
    doc_date: date
    supplier_id: int
    remarks: str = "Nil"
    payment_type: int = Field(ge=0, le=2, default=0)
    stax_type: int = Field(ge=0, le=1, default=0, description="0=Registered, 1=UN-Registered")
    gp_id: str = ""
    gp_time: str = ""
    vendor_title: str = ""
    address: str = ""
    stax_id: str = ""
    city_id: int = 0
    charges: FinPurHeaderCharges = Field(default_factory=FinPurHeaderCharges)
    lines: List[FinPurLineIn] = Field(min_length=1)

    @field_validator("remarks", "gp_id", "gp_time", "vendor_title", "address", "stax_id", mode="before")
    @classmethod
    def strip_optional(cls, v):
        return (v or "").strip()


class FinPurLineOut(BaseModel):
    serial_order: int
    item_id: float
    item_title: str = ""
    qty: float
    rate: float
    pur_amt: float
    stax_rate: float
    stax_amt: float
    disc_per: float
    disc_amt: float
    disc_per_oi: float
    disc_amt_oi: float
    total_amt: float
    remarks: str = ""
    exp_date: Optional[date] = None


class FinPurTotalsOut(BaseModel):
    qty: float = 0.0
    amount: float = 0.0
    sales_tax: float = 0.0
    discount: float = 0.0
    stax_excl_amt: float = 0.0
    off_inv_disc: float = 0.0
    included: float = 0.0
    net_amount: float = 0.0
    header_discount: float = 0.0
    header_charges: float = 0.0
    diff: float = 0.0


class FinPurDocumentOut(BaseModel):
    prod_id: int
    serial_no: int
    fiscal: int
    doc_type_id: int
    doc_date: date
    supplier_id: int
    supplier_title: str = ""
    registration: str = ""
    remarks: str = ""
    payment_type: int = 0
    stax_type: int = 0
    gp_id: str = ""
    gp_time: str = ""
    vendor_title: str = ""
    address: str = ""
    stax_id: str = ""
    city_id: int = 0
    city_title: str = ""
    sys_status: int = 0
    doc_abbr: str = "PUR"
    charges: FinPurHeaderCharges = Field(default_factory=FinPurHeaderCharges)
    totals: FinPurTotalsOut = Field(default_factory=FinPurTotalsOut)
    lines: List[FinPurLineOut] = []


class FinPurSaveResponse(BaseModel):
    message: str
    prod_id: int
    serial_no: int
    doc_display: str
    needs_resave: bool = False


class FinPurDeleteResponse(BaseModel):
    message: str
    prod_id: int


class FinPurConfigOut(BaseModel):
    doc_type_id: int = 2
    doc_abbr: str = "PUR"
    book_id: int = 102
    fiscal: int = 0
    max_entries: int = 500
    stax_type_mode: int = 1
    fiscal_start: Optional[date] = None
    fiscal_end: Optional[date] = None
    company_name: str = ""
    book_ok: bool = True
    book_message: str = ""
    reg_stax_rate: float = 0.0
    unreg_stax_rate: float = 0.0
    legacy_uid: int = 0
    is_sa: bool = False


class FinPurSupplierOut(BaseModel):
    supplier_id: int
    vendor_title: str
    address: str = ""
    stax_id: str = ""
    city_id: int = 0
    city_title: str = ""
    registration: str = ""
    tag_1: int = 0
    sales_tax_rate: float = 0.0


class FinPurItemOut(BaseModel):
    item_id: float
    manual_id: Optional[float] = None
    item_title: str
    barcodeid: Optional[str] = None
    barcodeid_ws: Optional[str] = None
    co_id: Optional[int] = None
    co_title: str = ""
    uom_id: Optional[int] = None
    uom_abbr: str = ""
    sales_rate: float = 0.0
    stock_qty: float = 0.0
    mrp: float = 0.0
    tp_rate: float = 0.0
    stax_reg: float = 0.0
    ed_status: int = 0


class FinPurLookupRow(BaseModel):
    id: str
    title: str
    extra: str = ""
