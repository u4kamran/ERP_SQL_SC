"""Admin API for login-alert email setup."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.deps import CurrentUser, require_permission
from app.schemas.login_notify import LoginNotifyDashboard, LoginNotifySettingsUpdate
from app.services import login_notify_store as store
from app.services.email_service import EmailDeliveryError, EmailService
from app.services.login_notify_service import send_test_email

router = APIRouter()


def _dashboard(limit: int = 80) -> LoginNotifyDashboard:
    email = EmailService()
    data = store.dashboard(limit=limit)
    data["smtp_configured"] = email.is_configured()
    data["smtp_hint"] = email.configuration_hint()
    return LoginNotifyDashboard(**data)


@router.get("/dashboard", response_model=LoginNotifyDashboard)
def get_dashboard(
    limit: int = Query(80, ge=1, le=200),
    _user: CurrentUser = Depends(require_permission("auth.login_notify.view")),
) -> LoginNotifyDashboard:
    return _dashboard(limit=limit)


@router.put("/settings", response_model=LoginNotifyDashboard)
def update_settings(
    body: LoginNotifySettingsUpdate,
    _user: CurrentUser = Depends(require_permission("auth.login_notify.manage")),
) -> LoginNotifyDashboard:
    payload = {k: v for k, v in body.model_dump().items() if v is not None}
    try:
        store.update_settings(payload)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return _dashboard()


@router.post("/test", response_model=LoginNotifyDashboard)
def test_email(
    _user: CurrentUser = Depends(require_permission("auth.login_notify.manage")),
) -> LoginNotifyDashboard:
    try:
        send_test_email()
    except EmailDeliveryError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc
    return _dashboard()
