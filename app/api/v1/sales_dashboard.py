"""Sales summary dashboard API."""

from datetime import datetime

from fastapi import APIRouter, Depends, Query
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.api.deps import require_any_permission
from app.database.business_session import get_business_db
from app.schemas.sales_dashboard import (
    CumulativeSalesResponse,
    DailySalesTrend,
    DayWiseSalesResponse,
    SalesDashboardRequest,
    SalesDashboardSummary,
    TopInvoicesResponse,
)
from app.services.sales_dashboard_service import SalesDashboardService
from app.utils.business_day import default_report_range

router = APIRouter()

_VIEW_PERMS = require_any_permission(
    "reports.sales_dashboard.view",
    "inventory.fin_item.view",
    "auth.admin.full",
)

_default_start, _default_end = default_report_range()


@router.get("/summary", response_model=SalesDashboardSummary)
def get_sales_summary(
    start_date: datetime = Query(default=_default_start),
    end_date: datetime = Query(default=_default_end),
    _user=Depends(_VIEW_PERMS),
    db: Session = Depends(get_business_db),
) -> SalesDashboardSummary:
    params = SalesDashboardRequest(start_date=start_date, end_date=end_date)
    return SalesDashboardService(db).get_summary(params)


@router.get("/daily-trend", response_model=DailySalesTrend)
def get_daily_trend(
    start_date: datetime = Query(default=_default_start),
    end_date: datetime = Query(default=_default_end),
    _user=Depends(_VIEW_PERMS),
    db: Session = Depends(get_business_db),
) -> DailySalesTrend:
    params = SalesDashboardRequest(start_date=start_date, end_date=end_date)
    return SalesDashboardService(db).get_daily_trend(params)


@router.get("/day-wise", response_model=DayWiseSalesResponse)
def get_day_wise_sales(
    start_date: datetime = Query(default=_default_start),
    end_date: datetime = Query(default=_default_end),
    _user=Depends(_VIEW_PERMS),
    db: Session = Depends(get_business_db),
) -> DayWiseSalesResponse:
    params = SalesDashboardRequest(start_date=start_date, end_date=end_date)
    return SalesDashboardService(db).get_day_wise_sales(params)


@router.get("/day-wise/pdf")
def get_day_wise_sales_pdf(
    start_date: datetime = Query(default=_default_start),
    end_date: datetime = Query(default=_default_end),
    _user=Depends(_VIEW_PERMS),
    db: Session = Depends(get_business_db),
) -> Response:
    params = SalesDashboardRequest(start_date=start_date, end_date=end_date)
    pdf_bytes, filename = SalesDashboardService(db).build_day_wise_pdf(params)
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/cumulative", response_model=CumulativeSalesResponse)
def get_cumulative_sales(
    start_date: datetime = Query(default=_default_start),
    end_date: datetime = Query(default=_default_end),
    _user=Depends(_VIEW_PERMS),
    db: Session = Depends(get_business_db),
) -> CumulativeSalesResponse:
    params = SalesDashboardRequest(start_date=start_date, end_date=end_date)
    return SalesDashboardService(db).get_cumulative_sales(params)


@router.get("/cumulative/pdf")
def get_cumulative_sales_pdf(
    start_date: datetime = Query(default=_default_start),
    end_date: datetime = Query(default=_default_end),
    _user=Depends(_VIEW_PERMS),
    db: Session = Depends(get_business_db),
) -> Response:
    params = SalesDashboardRequest(start_date=start_date, end_date=end_date)
    pdf_bytes, filename = SalesDashboardService(db).build_cumulative_sales_pdf(params)
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/dashboard/pdf")
def get_sales_dashboard_pdf(
    start_date: datetime = Query(default=_default_start),
    end_date: datetime = Query(default=_default_end),
    include_cumulative: bool = Query(default=False),
    _user=Depends(_VIEW_PERMS),
    db: Session = Depends(get_business_db),
) -> Response:
    """Full dashboard PDF: summary, MoM, top invoices, day-wise, optional cumulative."""
    params = SalesDashboardRequest(start_date=start_date, end_date=end_date)
    pdf_bytes, filename = SalesDashboardService(db).build_full_dashboard_pdf(
        params, include_cumulative=include_cumulative
    )
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/pdf")
def get_sales_dashboard_pdf_legacy(
    start_date: datetime = Query(default=_default_start),
    end_date: datetime = Query(default=_default_end),
    include_cumulative: bool = Query(default=False),
    _user=Depends(_VIEW_PERMS),
    db: Session = Depends(get_business_db),
) -> Response:
    """Alias for /dashboard/pdf."""
    params = SalesDashboardRequest(start_date=start_date, end_date=end_date)
    pdf_bytes, filename = SalesDashboardService(db).build_full_dashboard_pdf(
        params, include_cumulative=include_cumulative
    )
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/top-invoices", response_model=TopInvoicesResponse)
def get_top_invoices(
    start_date: datetime = Query(default=_default_start),
    end_date: datetime = Query(default=_default_end),
    limit: int = Query(default=10, ge=1, le=50),
    _user=Depends(_VIEW_PERMS),
    db: Session = Depends(get_business_db),
) -> TopInvoicesResponse:
    params = SalesDashboardRequest(start_date=start_date, end_date=end_date)
    return SalesDashboardService(db).get_top_invoices(params, limit=limit)
