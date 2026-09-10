"""Sales dashboard scheduled email API."""

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr

from app.api.deps import CurrentUser, require_report_delivery
from app.scheduler.sales_dashboard_email_scheduler import get_sales_dashboard_email_runner
from app.schemas.sales_dashboard_email import (
    SalesDashboardEmailConfig,
    SalesDashboardEmailConfigUpdate,
    SalesDashboardEmailRunResult,
    SalesDashboardEmailStatus,
)
from app.services.sales_dashboard_email_service import SalesDashboardEmailService

router = APIRouter()

_SALES_VIEW = (
    "reports.sales_dashboard.view",
    "inventory.fin_item.view",
    "auth.admin.full",
)
_EMAIL_PERMS = require_report_delivery(
    *_SALES_VIEW,
    action_permissions=("reports.sales_dashboard.email",),
    denied_detail="You do not have permission to email this report.",
)


class SalesDashboardEmailTestRequest(BaseModel):
    to_email: EmailStr


@router.get("/config", response_model=SalesDashboardEmailConfig)
def get_config(current_user: CurrentUser = Depends(_EMAIL_PERMS)):
    return SalesDashboardEmailService().get_config()


@router.put("/config", response_model=SalesDashboardEmailConfig)
def save_config(
    payload: SalesDashboardEmailConfigUpdate,
    current_user: CurrentUser = Depends(_EMAIL_PERMS),
):
    try:
        return SalesDashboardEmailService().save_config(payload)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.get("/status", response_model=SalesDashboardEmailStatus)
def get_status(current_user: CurrentUser = Depends(_EMAIL_PERMS)):
    runner = get_sales_dashboard_email_runner()
    return SalesDashboardEmailService().get_status(scheduler_running=runner.is_running)


@router.post("/run-now", response_model=SalesDashboardEmailRunResult)
def run_now(current_user: CurrentUser = Depends(_EMAIL_PERMS)):
    return SalesDashboardEmailService().run_check(force=True)


@router.post("/test", response_model=SalesDashboardEmailRunResult)
def send_test(
    payload: SalesDashboardEmailTestRequest,
    current_user: CurrentUser = Depends(_EMAIL_PERMS),
):
    return SalesDashboardEmailService().send_test_email(str(payload.to_email))
