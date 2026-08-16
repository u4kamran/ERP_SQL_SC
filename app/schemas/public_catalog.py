"""Public customer catalog + cart validation — safe fields only."""

from typing import Optional

from pydantic import BaseModel, Field


class PublicProduct(BaseModel):
    manual_id: int
    barcodeid: Optional[str] = None
    barcodeid_ws: Optional[str] = None
    item_title: str
    item_short: Optional[str] = None
    uom_title: Optional[str] = None
    co_title: Optional[str] = None
    sales_rate: Optional[float] = None
    sales_price_wo_gst: Optional[float] = None
    gst_amount: Optional[float] = None
    market_price: Optional[float] = None
    promotion: bool = False
    stock_qty: Optional[float] = None
    in_stock: bool = True
    image_url: Optional[str] = None


class PublicCatalogPage(BaseModel):
    items: list[PublicProduct] = Field(default_factory=list)
    page: int = 1
    page_size: int = 20
    has_more: bool = False
    total_hint: Optional[int] = None


class CartValidateLineIn(BaseModel):
    manual_id: int = Field(..., ge=1)
    qty: float = Field(..., gt=0, le=9999)


class CartValidateLineOut(BaseModel):
    manual_id: int
    qty: float
    item_title: str = ""
    item_short: Optional[str] = None
    barcodeid: Optional[str] = None
    uom_title: Optional[str] = None
    co_title: Optional[str] = None
    unit_price: float = 0.0
    sales_price_wo_gst: Optional[float] = None
    gst_amount: Optional[float] = None
    market_price: Optional[float] = None
    promotion: bool = False
    stock_qty: Optional[float] = None
    in_stock: bool = True
    line_total: float = 0.0
    ok: bool = True
    message: Optional[str] = None
    image_url: Optional[str] = None


class CartValidateRequest(BaseModel):
    lines: list[CartValidateLineIn] = Field(default_factory=list, max_length=100)


class CartValidateResponse(BaseModel):
    lines: list[CartValidateLineOut] = Field(default_factory=list)
    subtotal: float = 0.0
    estimated_total: float = 0.0
    changed: bool = False
    message: Optional[str] = None
