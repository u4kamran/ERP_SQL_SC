"""Sales dashboard business logic."""

from __future__ import annotations

import calendar
from datetime import datetime

from sqlalchemy.orm import Session

from app.repositories.sales_dashboard_repository import SalesDashboardRepository
from app.schemas.sales_dashboard import (
    DailySalesPoint,
    DailySalesTrend,
    SalesDashboardRequest,
    SalesDashboardSummary,
    SalesMetricComparison,
    SalesPeriodSummary,
    TopInvoiceRow,
    TopInvoicesResponse,
)


def shift_months(value: datetime, months: int) -> datetime:
    """Move a datetime by calendar months, clamping day to month end."""
    month_index = value.month - 1 + months
    year = value.year + month_index // 12
    month = month_index % 12 + 1
    day = min(value.day, calendar.monthrange(year, month)[1])
    return value.replace(year=year, month=month, day=day)


def _period_days(start_date: datetime, end_date: datetime) -> int:
    total_days = (end_date.date() - start_date.date()).days
    return max(total_days, 1)


def _build_period(
    repo: SalesDashboardRepository,
    start_date: datetime,
    end_date: datetime,
) -> SalesPeriodSummary:
    total_days = _period_days(start_date, end_date)
    data = repo.get_summary(start_date, end_date, total_days)
    return SalesPeriodSummary(
        start_date=start_date,
        end_date=end_date,
        total_days=total_days,
        **data,
    )


def _compare_values(current: float, previous: float) -> SalesMetricComparison:
    change = current - previous
    change_percent = (change / previous * 100) if previous else None
    return SalesMetricComparison(
        current=current,
        previous=previous,
        change=change,
        change_percent=change_percent,
    )


class SalesDashboardService:
    def __init__(self, db: Session):
        self.db = db

    def get_summary(self, params: SalesDashboardRequest) -> SalesDashboardSummary:
        repo = SalesDashboardRepository(self.db)

        current = _build_period(repo, params.start_date, params.end_date)

        prev_start = shift_months(params.start_date, -1)
        prev_end = shift_months(params.end_date, -1)
        previous = _build_period(repo, prev_start, prev_end)

        current_pp = current.profit_percent or 0.0
        previous_pp = previous.profit_percent or 0.0

        return SalesDashboardSummary(
            current=current,
            previous=previous,
            total_sale=_compare_values(current.total_sale, previous.total_sale),
            total_cost=_compare_values(current.total_cost, previous.total_cost),
            profit=_compare_values(current.profit, previous.profit),
            profit_percent=SalesMetricComparison(
                current=current_pp,
                previous=previous_pp,
                change=current_pp - previous_pp,
                change_percent=None,
            ),
            avg_sale_per_day=_compare_values(current.avg_sale_per_day, previous.avg_sale_per_day),
        )

    def get_daily_trend(self, params: SalesDashboardRequest) -> DailySalesTrend:
        repo = SalesDashboardRepository(self.db)
        current_rows = repo.get_daily_sales(params.start_date, params.end_date)
        prev_start = shift_months(params.start_date, -1)
        prev_end = shift_months(params.end_date, -1)
        previous_rows = repo.get_daily_sales(prev_start, prev_end)
        return DailySalesTrend(
            current=[DailySalesPoint(**row) for row in current_rows],
            previous=[DailySalesPoint(**row) for row in previous_rows],
        )

    def get_top_invoices(self, params: SalesDashboardRequest, limit: int = 10) -> TopInvoicesResponse:
        rows = SalesDashboardRepository(self.db).get_top_invoices(
            params.start_date, params.end_date, limit=limit
        )
        return TopInvoicesResponse(items=[TopInvoiceRow(**row) for row in rows])
