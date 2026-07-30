"""Public guest price lookup — safe fields only (no cost/GL data)."""

from typing import Optional

from pydantic import BaseModel


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
