"""Schemas for WhatsApp / offline chat orders (sales prices only, no cost)."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, field_validator


class OrderCartItem(BaseModel):
    manual_id: int
    item_title: str
    item_short: str = ""
    barcodeid: str = ""
    uom_title: str = ""
    unit_price: float = 0.0
    price_wo_gst: float | None = None
    gst_amount: float = 0.0
    qty: float = 1.0
    line_total: float = 0.0
    line_gst: float = 0.0
    line_wo_gst: float = 0.0


class ChatOrder(BaseModel):
    order_id: str
    order_no: str
    conversation_id: str = ""
    channel: Literal["whatsapp", "offline"] = "offline"
    phone: str = ""
    customer_name: str = ""
    customer_mobile: str = ""
    customer_address: str = ""
    latitude: float | None = None
    longitude: float | None = None
    maps_url: str = ""
    notes: str = ""
    status: Literal[
        "pending",
        "confirmed",
        "preparing",
        "ready",
        "completed",
        "cancelled",
    ] = "pending"
    items: list[OrderCartItem] = Field(default_factory=list)
    item_count: int = 0
    subtotal_wo_gst: float = 0.0
    gst_total: float = 0.0
    order_total: float = 0.0
    created_at: datetime
    updated_at: datetime
    receipt_text: str = ""


class ChatOrderSummary(BaseModel):
    order_id: str
    order_no: str
    channel: Literal["whatsapp", "offline"]
    phone: str = ""
    customer_name: str = ""
    customer_mobile: str = ""
    status: str
    item_count: int = 0
    order_total: float = 0.0
    created_at: datetime
    updated_at: datetime


class ChatOrderStatusUpdate(BaseModel):
    status: Literal[
        "pending",
        "confirmed",
        "preparing",
        "ready",
        "completed",
        "cancelled",
    ]


class ChatOrderNoteUpdate(BaseModel):
    notes: str = Field("", max_length=500)

    @field_validator("notes", mode="before")
    @classmethod
    def strip_notes(cls, value):
        return value.strip() if isinstance(value, str) else value
