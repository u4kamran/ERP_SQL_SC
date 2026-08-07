"""Typed request and response schemas for delivery management."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, Field, field_validator


DeliveryStatus = Literal[
    "Pending",
    "Assigned",
    "On The Way",
    "Arrived",
    "Delivered",
    "Cancelled",
    "Failed Delivery",
    "Returned",
]


class DeliveryRiderCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    phone: str | None = Field(None, max_length=30)

    @field_validator("name", "phone", mode="before")
    @classmethod
    def strip_text(cls, value):
        if isinstance(value, str):
            return value.strip() or None
        return value


class DeliveryRiderUpdate(DeliveryRiderCreate):
    is_active: bool = True


class DeliveryRiderResponse(BaseModel):
    id: int
    name: str
    phone: str | None = None
    is_active: bool
    created_at: datetime
    updated_at: datetime
    latitude: Decimal | None = None
    longitude: Decimal | None = None
    location_accuracy: Decimal | None = None
    location_updated_at: datetime | None = None


class DeliveryOrderResponse(BaseModel):
    id: int
    source_serial_no: int
    invoice_id: int | None = None
    invoice_date: datetime | None = None
    customer_id: int | None = None
    cust_sms_id: int | None = None
    customer_title: str
    customer_mobile_no: str
    customer_alternate_mobile: str | None = None
    address: str
    city_id: int | None = None
    sale_amount: Decimal | None = None
    balance_amount: Decimal | None = None
    total_amount: Decimal | None = None
    payment_type: int | None = None
    rider_id: int | None = None
    rider_name: str | None = None
    status: DeliveryStatus
    created_at: datetime
    updated_at: datetime
    delivered_at: datetime | None = None
    delivered_latitude: Decimal | None = None
    delivered_longitude: Decimal | None = None
    delivered_accuracy: Decimal | None = None
    customer_latitude: Decimal | None = None
    customer_longitude: Decimal | None = None
    customer_location_updated_at: datetime | None = None
    rider_latitude: Decimal | None = None
    rider_longitude: Decimal | None = None
    rider_location_updated_at: datetime | None = None
    remarks: str | None = None


class DeliveryOrderListResponse(BaseModel):
    items: list[DeliveryOrderResponse] = Field(default_factory=list)
    total: int = 0
    skip: int = 0
    limit: int = 50


class DeliverySummaryResponse(BaseModel):
    total_orders: int = 0
    unassigned_orders: int = 0
    active_riders: int = 0
    delivered_today: int = 0
    status_counts: dict[str, int] = Field(default_factory=dict)


class DeliverySyncResponse(BaseModel):
    lookback_hours: int
    limit: int
    scanned: int
    created: int
    refreshed: int
    skipped: int


class DeliveryAssignRequest(BaseModel):
    rider_id: int = Field(..., gt=0)


class DeliveryBulkDeliverRequest(BaseModel):
    rider_id: int | None = Field(None, gt=0)


class DeliveryBulkActionResponse(BaseModel):
    updated: int
    message: str


class DeliveryStatusUpdateRequest(BaseModel):
    status: DeliveryStatus
    latitude: Decimal | None = Field(None, ge=-90, le=90)
    longitude: Decimal | None = Field(None, ge=-180, le=180)
    accuracy: Decimal | None = Field(None, ge=0)
    remarks: str | None = Field(None, max_length=1000)

    @field_validator("remarks", mode="before")
    @classmethod
    def strip_remarks(cls, value):
        if isinstance(value, str):
            return value.strip() or None
        return value


class DeliveryRegistrationInvoice(BaseModel):
    source_serial_no: int
    invoice_id: int
    invoice_date: datetime | None = None
    gp_time: str = ""
    customer_title: str = ""
    current_mobile: str = ""
    address: str = ""
    total_amount: Decimal | None = None
    payment_type: int | None = None


class DeliveryCustomerLookup(BaseModel):
    exists: bool
    cust_sms_id: int | None = None
    name: str = ""
    mobile: str = ""
    alternate_mobile: str = ""
    address: str = ""


class DeliveryRegistrationRequest(BaseModel):
    source_serial_no: int = Field(..., gt=0)
    mobile: str = Field(..., min_length=7, max_length=30)
    name: str = Field(..., min_length=1, max_length=150)
    address: str = Field(..., min_length=1, max_length=250)

    @field_validator("mobile", "name", "address", mode="before")
    @classmethod
    def strip_registration_text(cls, value):
        if isinstance(value, str):
            return value.strip()
        return value


class DeliveryRegistrationResponse(BaseModel):
    delivery_order_id: int
    invoice_id: int
    customer_created: bool
    cust_sms_id: int
    message: str
