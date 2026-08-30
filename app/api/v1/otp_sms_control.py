"""Admin API for OTP / SMS master control."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.api.deps import CurrentUser, require_permission
from app.database.business_session import get_business_db
from app.database.session import get_db
from app.schemas.otp_sms_control import OtpSmsControlSettings, OtpSmsControlUpdate
from app.services.otp_sms_control_service import get_otp_control, update_otp_control
from app.utils import get_client_ip

router = APIRouter()


def _to_schema(payload: dict) -> OtpSmsControlSettings:
    return OtpSmsControlSettings(
        master_enabled=bool(payload["master_enabled"]),
        web_enabled=bool(payload["web_enabled"]),
        mobile_enabled=bool(payload["mobile_enabled"]),
        web_effective=bool(payload["web_effective"]),
        mobile_effective=bool(payload["mobile_effective"]),
        web_overridden_by_master=bool(payload.get("web_overridden_by_master")),
        mobile_overridden_by_master=bool(payload.get("mobile_overridden_by_master")),
        row_version=int(payload.get("row_version") or 1),
        updated_by_user_id=payload.get("updated_by_user_id"),
        updated_by_username=payload.get("updated_by_username"),
        updated_at=payload.get("updated_at"),
        comment=payload.get("comment"),
        config_ok=bool(payload.get("config_ok", True)),
    )


@router.get("/otp-settings", response_model=OtpSmsControlSettings)
def get_otp_settings(
    _user: CurrentUser = Depends(require_permission("auth.otp_sms_control.view")),
    _db: Session = Depends(get_business_db),
) -> OtpSmsControlSettings:
    return _to_schema(get_otp_control())


@router.put("/otp-settings", response_model=OtpSmsControlSettings)
def put_otp_settings(
    body: OtpSmsControlUpdate,
    request: Request,
    current_user: CurrentUser = Depends(require_permission("auth.otp_sms_control.manage")),
    business_db: Session = Depends(get_business_db),
    auth_db: Session = Depends(get_db),
) -> OtpSmsControlSettings:
    payload = update_otp_control(
        business_db,
        auth_db,
        master_enabled=body.master_enabled,
        web_enabled=body.web_enabled,
        mobile_enabled=body.mobile_enabled,
        expected_version=body.row_version,
        comment=body.comment,
        user_id=current_user.user_id,
        username=current_user.username,
        ip_address=get_client_ip(request),
        user_agent=request.headers.get("user-agent"),
    )
    return _to_schema(payload)
