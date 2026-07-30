"""Pydantic schemas for FIN_ITEM CRUD."""

from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class FinItemBase(BaseModel):
    item_title: Optional[str] = Field(None, max_length=100)
    item_short: Optional[str] = Field(None, max_length=20)
    ac_level: Optional[int] = None
    ed_status: Optional[int] = 0
    item_oem: Optional[str] = Field(None, max_length=20)
    barcodeid: Optional[str] = Field(None, max_length=50)
    uom_id: Optional[int] = 1
    country_id: Optional[int] = 1
    item_nature: Optional[int] = 0
    min_level: Optional[float] = 0
    max_level: Optional[float] = 0
    ro_qty: Optional[float] = 0
    critical_level: Optional[float] = 0
    visacard_rate: Optional[float] = 0
    sales_rate: Optional[float] = 0
    cost_rate: Optional[float] = 0
    disc_p1: Optional[float] = 0
    disc_p2: Optional[float] = 0
    disc_p3: Optional[float] = 0
    disc_p4: Optional[float] = 0
    gl_sales_id: Optional[int] = 0
    gl_pur_id: Optional[int] = 0
    gl_cons_id: Optional[int] = 0
    gl_disc_id: Optional[int] = 0
    gl_stax_id: Optional[int] = 0
    stax_reg: Optional[float] = 0
    stax_unreg: Optional[float] = 0
    remarks: Optional[str] = Field(None, max_length=50)
    co_id: Optional[int] = 0
    min_level1: Optional[float] = 0
    max_level1: Optional[float] = 0
    ro_qty1: Optional[float] = 0
    critical_level1: Optional[float] = 0
    barcodeid_ws: Optional[str] = Field(None, max_length=50)


class FinItemCreate(FinItemBase):
    item_title: str = Field(..., min_length=1, max_length=100)


class FinItemUpdate(FinItemBase):
    pass


class FinItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    item_id: float = Field(validation_alias="ITEM_ID")
    manualid: int
    item_title: Optional[str] = Field(None, validation_alias="ITEM_TITLE")
    item_short: Optional[str] = Field(None, validation_alias="ITEM_SHORT")
    ac_level: Optional[int] = Field(None, validation_alias="AC_LEVEL")
    ed_status: Optional[int] = Field(None, validation_alias="ED_STATUS")
    item_oem: Optional[str] = Field(None, validation_alias="ITEM_OEM")
    barcodeid: Optional[str] = None
    uom_id: Optional[int] = Field(None, validation_alias="UOM_ID")
    country_id: Optional[int] = Field(None, validation_alias="COUNTRY_ID")
    tnot: Optional[int] = Field(None, validation_alias="TNOT")
    oqty: Optional[float] = Field(None, validation_alias="OQTY")
    oamt: Optional[float] = Field(None, validation_alias="OAMT")
    cqty: Optional[float] = Field(None, validation_alias="CQTY")
    camt: Optional[float] = Field(None, validation_alias="CAMT")
    avg_cost: Optional[float] = None
    mr_cost: Optional[float] = Field(None, validation_alias="Mr_Cost")
    item_nature: Optional[int] = Field(None, validation_alias="ITEM_NATURE")
    min_level: Optional[float] = Field(None, validation_alias="MIN_LEVEL")
    max_level: Optional[float] = Field(None, validation_alias="MAX_LEVEL")
    ro_qty: Optional[float] = Field(None, validation_alias="RO_QTY")
    critical_level: Optional[float] = Field(None, validation_alias="CRITICAL_LEVEL")
    visacard_rate: Optional[float] = Field(None, validation_alias="VISACARD_RATE")
    sales_rate: Optional[float] = Field(None, validation_alias="SALES_RATE")
    cost_rate: Optional[float] = Field(None, validation_alias="COST_RATE")
    disc_p1: Optional[float] = Field(None, validation_alias="DISC_P1")
    disc_p2: Optional[float] = Field(None, validation_alias="DISC_P2")
    disc_p3: Optional[float] = Field(None, validation_alias="DISC_P3")
    disc_p4: Optional[float] = Field(None, validation_alias="DISC_P4")
    gl_sales_id: Optional[int] = Field(None, validation_alias="GL_SALES_ID")
    gl_pur_id: Optional[int] = Field(None, validation_alias="GL_PUR_ID")
    gl_cons_id: Optional[int] = Field(None, validation_alias="GL_CONS_ID")
    gl_disc_id: Optional[int] = Field(None, validation_alias="GL_DISC_ID")
    gl_stax_id: Optional[int] = Field(None, validation_alias="GL_STAX_ID")
    stax_reg: Optional[float] = Field(None, validation_alias="STAX_REG")
    stax_unreg: Optional[float] = Field(None, validation_alias="STAX_UNREG")
    remarks: Optional[str] = Field(None, validation_alias="REMARKS")
    cprocess_id: Optional[int] = None
    qtycdebit: Optional[float] = None
    qtyccredit: Optional[float] = None
    amtcdebit: Optional[float] = None
    amtccredit: Optional[float] = None
    qtytcbal: Optional[float] = Field(None, validation_alias="QTYTCBAL")
    amttcbal: Optional[float] = None
    qtynetbal: Optional[float] = None
    amtnetbal: Optional[float] = None
    qtynetclosing: Optional[float] = None
    amtnetclosing: Optional[float] = None
    co_id: Optional[int] = None
    oqty1: Optional[float] = Field(None, validation_alias="OQTY1")
    oamt1: Optional[float] = Field(None, validation_alias="OAMT1")
    cqty1: Optional[float] = Field(None, validation_alias="CQTY1")
    camt1: Optional[float] = Field(None, validation_alias="CAMT1")
    tnot1: Optional[int] = Field(None, validation_alias="TNOT1")
    min_level1: Optional[float] = Field(None, validation_alias="MIN_LEVEL1")
    max_level1: Optional[float] = Field(None, validation_alias="MAX_LEVEL1")
    ro_qty1: Optional[float] = Field(None, validation_alias="RO_QTY1")
    critical_level1: Optional[float] = Field(None, validation_alias="CRITICAL_LEVEL1")
    barcodeid_ws: Optional[str] = Field(None, validation_alias="BARCODEID_WS")


class FinItemListResponse(BaseModel):
    items: list[FinItemResponse]
    total: int
    skip: int
    limit: int
