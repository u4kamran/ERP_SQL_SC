"""Pydantic schemas for VB6 Fin_InvM_Order Purchase Order parity."""

from __future__ import annotations

from datetime import date
from typing import List, Optional

from pydantic import BaseModel, Field, field_validator


class FinInvOrderLineIn(BaseModel):
    item_id: float
    barcode_id: str = ""
    manual_id: str = ""
    item_title: str = ""
    qty: float
    rate: float = 0.0
    amount: float = 0.0
    disc_per: float = 0.0
    disc_amt: float = 0.0
    net_amt: float = 0.0

    @field_validator("barcode_id", "manual_id", "item_title", mode="before")
    @classmethod
    def strip_text(cls, v):
        return (v or "").strip()


class FinInvOrderHeaderCharges(BaseModel):
    discount: float = 0.0
    claim: float = 0.0
    other_ded: float = 0.0
    loading: float = 0.0
    carriage: float = 0.0
    other_charges: float = 0.0


class FinInvOrderSaveRequest(BaseModel):
    inv_id: Optional[int] = None
    serial_no: Optional[int] = None
    doc_date: date
    supplier_id: int
    cust_order: str = ""
    cust_order_date: str = ""
    payment_type: int = Field(ge=0, le=2, default=1)
    stax_type: int = Field(ge=0, le=2, default=0)
    gp_id: str = ""
    gp_time: str = ""
    customer_title: str = ""
    address: str = ""
    stax_id: str = ""
    city_id: int = 0
    remarks: str = ""
    amount_rec: float = 0.0
    bal_amt: float = 0.0
    charges: FinInvOrderHeaderCharges = Field(default_factory=FinInvOrderHeaderCharges)
    lines: List[FinInvOrderLineIn] = Field(min_length=1)

    @field_validator(
        "cust_order",
        "cust_order_date",
        "gp_id",
        "gp_time",
        "customer_title",
        "address",
        "stax_id",
        "remarks",
        mode="before",
    )
    @classmethod
    def strip_optional(cls, v):
        return (v or "").strip()


class FinInvOrderLineOut(BaseModel):
    serial_order: int
    item_id: float
    barcode_id: str = ""
    manual_id: str = ""
    item_title: str = ""
    qty: float
    rate: float
    amount: float
    disc_per: float
    disc_amt: float
    net_amt: float


class FinInvOrderTotalsOut(BaseModel):
    qty: float = 0.0
    amount: float = 0.0
    disc_amt: float = 0.0
    net_amt: float = 0.0
    header_discount: float = 0.0
    header_charges: float = 0.0
    diff: float = 0.0
    net_invoice: float = 0.0


class FinInvOrderDocumentOut(BaseModel):
    inv_id: int
    serial_no: int
    fiscal: int
    doc_type_id: int
    doc_date: date
    supplier_id: int
    supplier_title: str = ""
    registration: str = ""
    cust_order: str = ""
    cust_order_date: str = ""
    payment_type: int = 1
    stax_type: int = 0
    gp_id: str = ""
    gp_time: str = ""
    customer_title: str = ""
    address: str = ""
    stax_id: str = ""
    city_id: int = 0
    city_title: str = ""
    remarks: str = ""
    amount_rec: float = 0.0
    bal_amt: float = 0.0
    sys_status: int = 0
    doc_abbr: str = "PO"
    charges: FinInvOrderHeaderCharges = Field(default_factory=FinInvOrderHeaderCharges)
    totals: FinInvOrderTotalsOut = Field(default_factory=FinInvOrderTotalsOut)
    lines: List[FinInvOrderLineOut] = []


class FinInvOrderSaveResponse(BaseModel):
    message: str
    inv_id: int
    serial_no: int
    doc_display: str


class FinInvOrderDeleteResponse(BaseModel):
    message: str
    inv_id: int


class FinInvOrderConfigOut(BaseModel):
    doc_type_id: int = 33
    doc_abbr: str = "PO"
    book_id: int = 133
    fiscal: int = 0
    max_entries: int = 2000
    fiscal_start: Optional[date] = None
    fiscal_end: Optional[date] = None
    company_name: str = ""
    book_ok: bool = True
    book_message: str = ""
    legacy_uid: int = 0


class FinInvOrderSupplierOut(BaseModel):
    supplier_id: int
    vendor_title: str = ""
    contact_person: str = ""
    address: str = ""
    stax_id: str = ""
    city_id: int = 0
    city_title: str = ""
    registration: str = ""
    tag_1: int = 0


class FinInvOrderItemOut(BaseModel):
    item_id: float
    manual_id: Optional[float] = None
    item_title: str = ""
    barcodeid: Optional[str] = None
    barcodeid_ws: Optional[str] = None
    cost_rate: float = 0.0
    sales_rate: float = 0.0
    stock_qty: float = 0.0
    visacard_rate: float = 0.0
    disc_p4: float = 0.0
    in_supplier_catalog: bool = False


class FinInvOrderSupplierItemOut(BaseModel):
    supplier_title: str = ""
    manual_id: str = ""
    item_title: str = ""
    tnot: float = 0.0
    stock_qty: float = 0.0
    cost_rate: float = 0.0
    sales_rate: float = 0.0
    item_id: float


class FinInvOrderLookupRow(BaseModel):
    id: str
    title: str
    extra: str = ""


class FinInvOrderHistoryRow(BaseModel):
    doc_id: str
    doc_date: Optional[date] = None
    party: str = ""
    qty: float = 0.0
    rate: float = 0.0
    extra: str = ""


class FinInvOrderPoHistoryRow(BaseModel):
    inv_id: int
    doc_date: Optional[date] = None
    supplier_id: int
    supplier_title: str = ""
    total_amt: float = 0.0


class FinInvOrderPrintLine(BaseModel):
    serial_order: int = 0
    item_title: str = ""
    qty: float = 0.0


class FinInvOrderPrintHeader(BaseModel):
    inv_id: int
    doc_date_display: str = ""
    supplier_title: str = ""
    cust_order: str = ""
    full_name: str = ""
    total_qty: float = 0.0
    company_name: str = ""
    company_address: str = ""
    company_phone: str = ""
    company_ntn: str = ""
    company_strn: str = ""
    print_note: str = ""


class FinInvOrderPrintOut(BaseModel):
    header: FinInvOrderPrintHeader
    lines: List[FinInvOrderPrintLine]


class FinInvOrderPrintRow(BaseModel):
    inv_id: int
    serial_order: int = 0
    item_id: float = 0.0
    item_title: str = ""
    qty: float = 0.0
    rate: float = 0.0
    sale_amt: float = 0.0
    total_amt: float = 0.0


class FinInvOrderAddSupplierItemRequest(BaseModel):
    manual_id: float


class FinInvOrderAddSupplierItemResponse(BaseModel):
    message: str
    item_id: float
