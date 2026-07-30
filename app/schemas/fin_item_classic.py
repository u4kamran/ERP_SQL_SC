"""Pydantic schemas for VB6-style Fin_Item form."""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


ITEM_NATURE_OPTIONS = [
    {"value": 0, "label": "Imported"},
    {"value": 1, "label": "Local"},
    {"value": 2, "label": "Manufactured"},
]


class FinItemClassicStats(BaseModel):
    record_count: int
    last_item_id: Optional[float] = None


class FinItemClassicDefaults(BaseModel):
    manual_id: int
    uom_id: int = 1
    uom_title: Optional[str] = None
    country_id: int = 1
    country_title: Optional[str] = None
    co_id: int = 1
    co_title: Optional[str] = None
    gl_sales_id: int = 30010001
    gl_pur_id: int = 30010001
    gl_cons_id: int = 30010001
    gl_disc_id: int = 30010001
    gl_stax_id: int = 30010001


class FinItemClassicLookup(BaseModel):
    id: int | float
    title: str
    manual_id: Optional[int] = None
    item_short: Optional[str] = None
    barcodeid: Optional[str] = None


class FinItemClassicTransactionRow(BaseModel):
    doc_no: Optional[str] = None
    doc_date: Optional[datetime] = None
    party_title: Optional[str] = None
    qty: Optional[float] = None
    rate: Optional[float] = None
    extra: Optional[str] = None


class FinItemClassicSave(BaseModel):
    item_id: float = Field(..., gt=0)
    item_title: str = Field(..., min_length=1, max_length=100)
    item_short: Optional[str] = Field(None, max_length=20)
    item_oem: Optional[str] = Field(None, max_length=20)
    manual_id: int = Field(..., gt=0)
    barcodeid: Optional[str] = Field("0", max_length=50)
    barcodeid_ws: Optional[str] = Field("0", max_length=50)
    visacard_rate: Optional[float] = 0
    uom_id: int = Field(..., gt=0)
    country_id: int = Field(..., gt=0)
    item_nature: int = Field(0, ge=0, le=2)
    min_level: Optional[float] = 0
    max_level: Optional[float] = 0
    ro_qty: Optional[float] = 0
    critical_level: Optional[float] = 0
    min_level1: Optional[float] = 0
    max_level1: Optional[float] = 0
    ro_qty1: Optional[float] = 0
    promotion: bool = False
    sales_rate: Optional[float] = 0
    cost_rate: Optional[float] = 0
    sales_price_wo_gst: Optional[float] = 0
    market_price: Optional[float] = 0
    ws_price: Optional[float] = 0
    gst_amount: Optional[float] = 0
    cost_wo_gst: Optional[float] = 0
    gl_sales_id: int = Field(..., gt=0)
    gl_pur_id: int = Field(..., gt=0)
    gl_cons_id: int = Field(..., gt=0)
    gl_disc_id: int = Field(..., gt=0)
    gl_stax_id: int = Field(..., gt=0)
    stax_reg: Optional[float] = 0
    stax_unreg: Optional[float] = 0
    remarks: Optional[str] = Field("Nil", max_length=50)
    co_id: int = Field(..., gt=0)
    ed_status: bool = False


class FinItemClassicDetail(BaseModel):
    item_id: float
    item_title: str
    item_short: Optional[str] = None
    item_oem: Optional[str] = None
    manual_id: int = 0
    barcodeid: Optional[str] = None
    barcodeid_ws: Optional[str] = None
    visacard_rate: Optional[float] = None
    uom_id: Optional[int] = None
    uom_title: Optional[str] = None
    country_id: Optional[int] = None
    country_title: Optional[str] = None
    item_nature: Optional[int] = 0
    min_level: Optional[float] = None
    max_level: Optional[float] = None
    ro_qty: Optional[float] = None
    critical_level: Optional[float] = None
    min_level1: Optional[float] = None
    max_level1: Optional[float] = None
    ro_qty1: Optional[float] = None
    promotion: bool = False
    sales_rate: Optional[float] = None
    cost_rate: Optional[float] = None
    sales_price_wo_gst: Optional[float] = None
    market_price: Optional[float] = None
    ws_price: Optional[float] = None
    gst_amount: Optional[float] = None
    cost_wo_gst: Optional[float] = None
    saved_cost_price: Optional[float] = None
    tp_rate: Optional[float] = None
    gl_sales_id: Optional[int] = None
    gl_pur_id: Optional[int] = None
    gl_cons_id: Optional[int] = None
    gl_disc_id: Optional[int] = None
    gl_stax_id: Optional[int] = None
    gl_sales_title: Optional[str] = None
    gl_pur_title: Optional[str] = None
    gl_cons_title: Optional[str] = None
    gl_disc_title: Optional[str] = None
    gl_stax_title: Optional[str] = None
    stax_reg: Optional[float] = None
    stax_unreg: Optional[float] = None
    oqty: Optional[float] = None
    cqty: Optional[float] = None
    oamt: Optional[float] = None
    camt: Optional[float] = None
    oqty1: Optional[float] = None
    cqty1: Optional[float] = None
    average_cost: Optional[float] = None
    profit_percent: Optional[float] = None
    remarks: Optional[str] = None
    co_id: Optional[int] = None
    co_title: Optional[str] = None
    ed_status: bool = False
    is_existing: bool = False
    status_label: str = "New"
    last_purchases: List[FinItemClassicTransactionRow] = []
    last_sales: List[FinItemClassicTransactionRow] = []


class FinItemClassicSaveResponse(BaseModel):
    message: str
    is_new: bool
    item_id: float


class FinItemClassicHistory(BaseModel):
    last_purchases: List[FinItemClassicTransactionRow] = []
    last_sales: List[FinItemClassicTransactionRow] = []
