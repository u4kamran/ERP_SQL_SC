"""Public guest price lookup — safe fields only (no cost/GL data)."""

from typing import Literal, Optional

from pydantic import BaseModel, Field


class GuestPriceLookupResponse(BaseModel):
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


class GuestPriceSearchMatch(GuestPriceLookupResponse):
    score: float = 0.0
    match_reason: str = ""
    stock_qty: Optional[float] = None
    in_stock: bool = True
    stock_label: str = "in_stock"
    suggested_qty: Optional[float] = None


class GuestPriceSearchResponse(BaseModel):
    query: str
    cleaned_query: str = ""
    match_type: Literal["exact", "single", "multiple", "none"]
    items: list[GuestPriceSearchMatch] = Field(default_factory=list)
    message: str = ""
    suggested_qty: Optional[float] = None
    empty_hint: Optional[str] = None
