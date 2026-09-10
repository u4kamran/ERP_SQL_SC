"""SMS_DB_ email scheduler API."""

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr

from app.api.deps import CurrentUser, require_any_permission
from app.scheduler.sms_email_scheduler import get_scheduler_runner
from app.schemas.sms_email_scheduler import (
    SmsEmailSchedulerConfig,
    SmsEmailSchedulerConfigUpdate,
    SmsEmailSchedulerRunResult,
    SmsEmailSchedulerStatus,
)
from app.services.sms_email_scheduler_service import SmsEmailSchedulerService

router = APIRouter()

_SMS_EMAIL_PERMS = require_any_permission(
    "reports.sms_email.manage",
    "auth.admin.full",
)


class SmsEmailTestRequest(BaseModel):
    to_email: EmailStr


@router.get("/config", response_model=SmsEmailSchedulerConfig)
def get_config(
    current_user: CurrentUser = Depends(_SMS_EMAIL_PERMS),
):
    return SmsEmailSchedulerService().get_config()


@router.put("/config", response_model=SmsEmailSchedulerConfig)
def save_config(
    payload: SmsEmailSchedulerConfigUpdate,
    current_user: CurrentUser = Depends(_SMS_EMAIL_PERMS),
):
    try:
        return SmsEmailSchedulerService().save_config(payload)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.get("/status", response_model=SmsEmailSchedulerStatus)
def get_status(
    current_user: CurrentUser = Depends(_SMS_EMAIL_PERMS),
):
    runner = get_scheduler_runner()
    return SmsEmailSchedulerService().get_status(scheduler_running=runner.is_running)


@router.post("/run-now", response_model=SmsEmailSchedulerRunResult)
def run_now(
    current_user: CurrentUser = Depends(_SMS_EMAIL_PERMS),
):
    return SmsEmailSchedulerService().run_check(force=True)


@router.post("/test", response_model=SmsEmailSchedulerRunResult)
def send_test(
    payload: SmsEmailTestRequest,
    current_user: CurrentUser = Depends(_SMS_EMAIL_PERMS),
):
    return SmsEmailSchedulerService().send_test_email(str(payload.to_email))
