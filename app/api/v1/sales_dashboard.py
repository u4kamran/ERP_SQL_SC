"""Sales summary dashboard API."""

from datetime import datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import require_any_permission
from app.database.business_session import get_business_db
from app.schemas.sales_dashboard import (
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
