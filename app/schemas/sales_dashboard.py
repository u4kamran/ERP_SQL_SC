"""Schemas for sales summary dashboard."""

from datetime import datetime

from pydantic import BaseModel, Field


class SalesDashboardRequest(BaseModel):
    start_date: datetime = Field(default_factory=lambda: datetime(2026, 7, 1, 6, 0, 0))
    end_date: datetime = Field(default_factory=lambda: datetime(2026, 7, 29, 7, 0, 0))


class SalesPeriodSummary(BaseModel):
    start_date: datetime
    end_date: datetime
    total_days: int
    total_sale: float = 0
    total_cost: float = 0
    profit: float = 0
    profit_percent: float | None = None
    avg_sale_per_day: float = 0


class SalesMetricComparison(BaseModel):
    current: float
    previous: float
    change: float
    change_percent: float | None = None


class SalesDashboardSummary(BaseModel):
    current: SalesPeriodSummary
    previous: SalesPeriodSummary
    total_sale: SalesMetricComparison
    total_cost: SalesMetricComparison
    profit: SalesMetricComparison
    profit_percent: SalesMetricComparison
    avg_sale_per_day: SalesMetricComparison


class DailySalesPoint(BaseModel):
    sale_date: str
    total_sale: float = 0
    total_cost: float = 0
    profit: float = 0


class DailySalesTrend(BaseModel):
    current: list[DailySalesPoint] = []
    previous: list[DailySalesPoint] = []


class TopInvoiceRow(BaseModel):
    inv_id: int
    total_sale: float = 0
    total_qty: float = 0
    total_discount: float = 0


class TopInvoicesResponse(BaseModel):
    items: list[TopInvoiceRow] = []


class DayWiseSalesRow(BaseModel):
    business_date: str
    day_label: str
    total_sale: float = 0
    total_cost: float = 0
    profit: float = 0
    invoice_count: int = 0


class DayWiseSalesResponse(BaseModel):
    items: list[DayWiseSalesRow] = []
    business_hours_note: str = "Business day: 08:00 → next day 05:00"
