"""Sales dashboard business logic."""

from __future__ import annotations

from datetime import datetime

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.repositories.sales_dashboard_repository import SalesDashboardRepository
from app.schemas.sales_dashboard import (
    CumulativeSalesResponse,
    CumulativeSalesRow,
    DailySalesPoint,
    DailySalesTrend,
    DayWiseSalesResponse,
    DayWiseSalesRow,
    SalesDashboardRequest,
    SalesDashboardSummary,
    SalesMetricComparison,
    SalesPeriodSummary,
    TopInvoiceRow,
    TopInvoicesResponse,
)
from app.utils.business_day import align_previous_trend_dates, count_business_days, shift_business_period

def _build_period(
    repo: SalesDashboardRepository,
    start_date: datetime,
    end_date: datetime,
) -> SalesPeriodSummary:
    total_days = count_business_days(start_date, end_date)
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

        prev_start, prev_end = shift_business_period(params.start_date, params.end_date, -1)
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
        prev_start, prev_end = shift_business_period(params.start_date, params.end_date, -1)
        previous_rows = align_previous_trend_dates(
            repo.get_daily_sales(prev_start, prev_end),
            months=1,
        )
        return DailySalesTrend(
            current=[DailySalesPoint(**row) for row in current_rows],
            previous=[DailySalesPoint(**row) for row in previous_rows],
        )

    def get_top_invoices(self, params: SalesDashboardRequest, limit: int = 10) -> TopInvoicesResponse:
        rows = SalesDashboardRepository(self.db).get_top_invoices(
            params.start_date, params.end_date, limit=limit
        )
        return TopInvoicesResponse(items=[TopInvoiceRow(**row) for row in rows])

    def get_day_wise_sales(self, params: SalesDashboardRequest) -> DayWiseSalesResponse:
        rows = SalesDashboardRepository(self.db).get_day_wise_sales(
            params.start_date, params.end_date
        )
        from app.config.settings import settings
        note = (
            f"Business day: {settings.business_day_start_hour:02d}:00"
            f" → next day {settings.business_day_end_hour:02d}:00"
        )
        return DayWiseSalesResponse(
            items=[DayWiseSalesRow(**row) for row in rows],
            business_hours_note=note,
        )

    def get_cumulative_sales(self, params: SalesDashboardRequest) -> CumulativeSalesResponse:
        repo = SalesDashboardRepository(self.db)
        try:
            rows = repo.get_cumulative_sales(params.start_date, params.end_date)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

        from app.config.settings import settings
        note = (
            f"Business day: {settings.business_day_start_hour:02d}:00"
            f" → next day {settings.business_day_end_hour:02d}:00"
        )
        return CumulativeSalesResponse(
            start_date=params.start_date,
            end_date=params.end_date,
            items=[CumulativeSalesRow(**row) for row in rows],
            business_hours_note=note,
        )

    def build_cumulative_sales_pdf(self, params: SalesDashboardRequest) -> tuple[bytes, str]:
        from app.reports.cumulative_sales_pdf import build_cumulative_sales_pdf

        report = self.get_cumulative_sales(params)
        period_label = (
            f"{params.start_date.strftime('%d %b %Y %H:%M')} -> "
            f"{params.end_date.strftime('%d %b %Y %H:%M')}"
        )
        pdf_bytes = build_cumulative_sales_pdf(
            report.items,
            period_label=period_label,
            business_hours_note=report.business_hours_note,
        )
        filename = (
            f"cumulative-sales-"
            f"{params.start_date.strftime('%Y%m%d')}-"
            f"{params.end_date.strftime('%Y%m%d')}.pdf"
        )
        return pdf_bytes, filename

    def build_day_wise_pdf(self, params: SalesDashboardRequest) -> tuple[bytes, str]:
        from app.reports.day_wise_sales_pdf import build_day_wise_sales_pdf

        report = self.get_day_wise_sales(params)
        period_label = (
            f"{params.start_date.strftime('%d %b %Y %H:%M')} -> "
            f"{params.end_date.strftime('%d %b %Y %H:%M')}"
        )
        pdf_bytes = build_day_wise_sales_pdf(
            report.items,
            period_label=period_label,
            business_hours_note=report.business_hours_note,
        )
        filename = (
            f"day-wise-sales-"
            f"{params.start_date.strftime('%Y%m%d')}-"
            f"{params.end_date.strftime('%Y%m%d')}.pdf"
        )
        return pdf_bytes, filename

    def build_full_dashboard_pdf(
        self, params: SalesDashboardRequest, *, include_cumulative: bool = False
    ) -> tuple[bytes, str]:
        from app.config.settings import settings
        from app.reports.sales_dashboard_full_pdf import build_full_sales_dashboard_pdf
        from app.utils.business_day import shift_business_period

        summary = self.get_summary(params)
        top_invoices = self.get_top_invoices(params, limit=10)
        day_wise = self.get_day_wise_sales(params)
        cumulative = self.get_cumulative_sales(params) if include_cumulative else None

        prev_start, prev_end = shift_business_period(params.start_date, params.end_date, -1)
        period_label = (
            f"Current: {params.start_date.strftime('%d %b %Y %H:%M')} -> "
            f"{params.end_date.strftime('%d %b %Y %H:%M')}"
        )
        compare_label = (
            f"Compared with: {prev_start.strftime('%d %b %Y %H:%M')} -> "
            f"{prev_end.strftime('%d %b %Y %H:%M')}"
        )
        pdf_bytes = build_full_sales_dashboard_pdf(
            summary,
            top_invoices,
            day_wise,
            cumulative,
            period_label=period_label,
            compare_label=compare_label,
            app_name=settings.app_name,
        )
        filename = (
            f"sales-dashboard-"
            f"{params.start_date.strftime('%Y%m%d')}-"
            f"{params.end_date.strftime('%Y%m%d')}.pdf"
        )
        return pdf_bytes, filename
