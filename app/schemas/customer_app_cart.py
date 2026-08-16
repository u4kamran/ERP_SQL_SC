"""Schemas for Customer App Cart (saved basket — not a sales invoice)."""

from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field


CartStatus = Literal[
    "SAVED",
    "UNDER_REVIEW",
    "CONTACTED",
    "CONFIRMED",
    "CONVERTED",
    "CANCELLED",
    "EXPIRED",
]


class CustomerLookupRequest(BaseModel):
    mobile: str = Field(..., min_length=10, max_length=20)


class CustomerLookupResponse(BaseModel):
    exists: bool
    cust_id: Optional[int] = None
    cust_name: Optional[str] = None
    mobile_no: Optional[str] = None
    cust_address: Optional[str] = None
    message: str


class CustomerRegisterRequest(BaseModel):
    cust_name: str = Field(..., min_length=2, max_length=150)
    mobile: str = Field(..., min_length=10, max_length=20)
    cust_address: Optional[str] = Field(None, max_length=250)


class CustomerRegisterResponse(BaseModel):
    created: bool
    cust_id: int
    cust_name: str
    mobile_no: str
    cust_address: Optional[str] = None
    message: str


class SaveCartLineIn(BaseModel):
    manual_id: int = Field(..., ge=1)
    qty: float = Field(..., gt=0, le=9999)


class SaveCartRequest(BaseModel):
    mobile: str = Field(..., min_length=10, max_length=20)
    cust_name: str = Field(..., min_length=2, max_length=150)
    cust_address: Optional[str] = Field(None, max_length=250)
    idempotency_key: str = Field(..., min_length=8, max_length=64)
    lines: list[SaveCartLineIn] = Field(..., min_length=1, max_length=100)


class CartLineOut(BaseModel):
    line_no: int
    manual_id: int
    item_title: str
    barcode: Optional[str] = None
    uom_title: Optional[str] = None
    qty: float
    unit_price: float
    discount_amount: float = 0.0
    tax_amount: float = 0.0
    line_total: float


class CartSummaryOut(BaseModel):
    id: int
    cart_ref: str
    cust_sms_id: int
    customer_name: str
    customer_mobile_no: str
    customer_address: Optional[str] = None
    status: str
    source: str
    total_items: int
    estimated_subtotal: float
    estimated_discount: float = 0.0
    estimated_tax: float = 0.0
    estimated_total: float
    converted_doc_ref: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class CartDetailOut(CartSummaryOut):
    lines: list[CartLineOut] = Field(default_factory=list)
    history: list[dict] = Field(default_factory=list)


class SaveCartResponse(BaseModel):
    cart: CartDetailOut
    customer_created: bool
    message: str


class CartListPage(BaseModel):
    items: list[CartSummaryOut] = Field(default_factory=list)
    page: int = 1
    page_size: int = 20
    total: int = 0
    has_more: bool = False


class StaffStatusUpdateRequest(BaseModel):
    status: CartStatus
    remarks: Optional[str] = Field(None, max_length=1000)
