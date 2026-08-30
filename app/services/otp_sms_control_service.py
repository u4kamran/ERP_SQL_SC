"""Authoritative OTP / SMS enablement: master AND channel.

Web OTP  = guest web chat / public WhatsApp OTP (`MobileOtpService`)
Mobile OTP = customer shopping app (`CustomerAppOtpService`)
"""

from __future__ import annotations

import json
import logging
import threading
import time
from datetime import datetime
from typing import Any, Literal, Optional

from fastapi import HTTPException, status
from sqlalchemy.exc import DBAPIError, ProgrammingError, SQLAlchemyError
from sqlalchemy.orm import Session

from app.config.settings import settings
from app.database.business_session import BusinessSessionLocal
from app.repositories.audit_repository import AuditRepository
from app.repositories.otp_sms_control_repository import OtpSmsControlRepository

logger = logging.getLogger("ahsteellab")

CHANNEL_WEB = "web"
CHANNEL_MOBILE = "mobile"
OtpChannel = Literal["web", "mobile"]

_CACHE_TTL_SECONDS = 5.0
_cache_lock = threading.Lock()
_cache: tuple[float, dict[str, Any]] | None = None

CONFIG_UNAVAILABLE_DETAIL = "Unable to determine OTP configuration. Please try again."


def _bool_env(name: str, default: bool = True) -> bool:
    return bool(getattr(settings, name, default))


def _seed_defaults() -> dict[str, bool]:
    """Preserve current production OTP behavior when inserting the first row."""
    return {
        "master_otp_enabled": True,
        "web_otp_enabled": _bool_env("guest_mobile_otp_required", True),
        "mobile_otp_enabled": _bool_env("customer_app_otp_required", True),
    }


def effective_allowed(*, master_enabled: bool, channel_enabled: bool) -> bool:
    return bool(master_enabled) and bool(channel_enabled)


def _public_payload(row: dict[str, Any], *, config_ok: bool) -> dict[str, Any]:
    master = bool(row.get("master_otp_enabled"))
    web = bool(row.get("web_otp_enabled"))
    mobile = bool(row.get("mobile_otp_enabled"))
    updated_at = row.get("updated_at")
    if isinstance(updated_at, datetime):
        updated_at_iso = updated_at.isoformat(sep=" ", timespec="seconds")
    else:
        updated_at_iso = str(updated_at) if updated_at else None
    return {
        "config_ok": config_ok,
        "master_enabled": master,
        "web_enabled": web,
        "mobile_enabled": mobile,
        "web_effective": effective_allowed(master_enabled=master, channel_enabled=web),
        "mobile_effective": effective_allowed(master_enabled=master, channel_enabled=mobile),
        "web_overridden_by_master": (not master) and web,
        "mobile_overridden_by_master": (not master) and mobile,
        "row_version": int(row.get("row_version") or 1),
        "updated_by_user_id": row.get("updated_by_user_id"),
        "updated_by_username": row.get("updated_by_username"),
        "updated_at": updated_at_iso,
        "comment": row.get("comment"),
    }


def _fail_closed_payload() -> dict[str, Any]:
    """If configuration cannot be loaded, do not weaken authentication."""
    return _public_payload(
        {
            "master_otp_enabled": True,
            "web_otp_enabled": True,
            "mobile_otp_enabled": True,
            "row_version": 0,
            "updated_by_user_id": None,
            "updated_by_username": None,
            "updated_at": None,
            "comment": None,
        },
        config_ok=False,
    )


def invalidate_otp_control_cache() -> None:
    global _cache
    with _cache_lock:
        _cache = None


def _store_cache(payload: dict[str, Any]) -> None:
    global _cache
    with _cache_lock:
        _cache = (time.monotonic(), payload)


def _read_cache() -> dict[str, Any] | None:
    with _cache_lock:
        if _cache is None:
            return None
        stored_at, payload = _cache
        if (time.monotonic() - stored_at) > _CACHE_TTL_SECONDS:
            return None
        return dict(payload)


def _load_from_db(db: Session, *, may_commit: bool) -> dict[str, Any]:
    repo = OtpSmsControlRepository(db)
    try:
        row = repo.get_row()
        if row is None:
            try:
                row = repo.ensure_row(**_seed_defaults())
                if may_commit:
                    db.commit()
                else:
                    db.flush()
            except SQLAlchemyError:
                db.rollback()
                row = repo.get_row()
                if row is None:
                    raise
        return _public_payload(row, config_ok=True)
    except ProgrammingError:
        db.rollback()
        logger.warning("otp_sms_control table is missing; OTP stays required until setup.")
        return _fail_closed_payload()
    except DBAPIError:
        db.rollback()
        logger.exception("Failed to load otp_sms_control")
        return _fail_closed_payload()


def get_otp_control(db: Optional[Session] = None) -> dict[str, Any]:
    """Read master/channel flags. `db` is unused; reads use a dedicated session."""
    cached = _read_cache()
    if cached is not None:
        return cached

    session = BusinessSessionLocal()
    try:
        payload = _load_from_db(session, may_commit=True)
        if payload.get("config_ok"):
            _store_cache(payload)
        return payload
    finally:
        session.close()


def require_otp_control(db: Optional[Session] = None) -> dict[str, Any]:
    payload = get_otp_control(db)
    if not payload.get("config_ok"):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=CONFIG_UNAVAILABLE_DETAIL,
        )
    return payload


def is_channel_otp_required(channel: OtpChannel, db: Optional[Session] = None) -> bool:
    """True when OTP must be used. Fail-closed if configuration cannot be loaded."""
    payload = get_otp_control(db)
    if not payload.get("config_ok"):
        return True
    if channel == CHANNEL_WEB:
        return bool(payload["web_effective"])
    if channel == CHANNEL_MOBILE:
        return bool(payload["mobile_effective"])
    return True


def assert_otp_config_available(db: Optional[Session] = None) -> dict[str, Any]:
    """Used by request-OTP paths: never generate OTP when config is unknown."""
    return require_otp_control(db)


def update_otp_control(
    business_db: Session,
    auth_db: Session,
    *,
    master_enabled: bool,
    web_enabled: bool,
    mobile_enabled: bool,
    expected_version: int,
    comment: Optional[str],
    user_id: int,
    username: str,
    ip_address: Optional[str],
    user_agent: Optional[str],
) -> dict[str, Any]:
    repo = OtpSmsControlRepository(business_db)
    current = repo.ensure_row(**_seed_defaults())
    old_values = {
        "master_enabled": bool(current["master_otp_enabled"]),
        "web_enabled": bool(current["web_otp_enabled"]),
        "mobile_enabled": bool(current["mobile_otp_enabled"]),
        "row_version": int(current["row_version"]),
    }
    updated = repo.update_row(
        master_otp_enabled=master_enabled,
        web_otp_enabled=web_enabled,
        mobile_otp_enabled=mobile_enabled,
        expected_version=expected_version,
        updated_by_user_id=user_id,
        updated_by_username=username,
        comment=comment,
    )
    if updated is None:
        business_db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="OTP settings were changed by another administrator. Please reload and try again.",
        )

    new_values = {
        "master_enabled": bool(updated["master_otp_enabled"]),
        "web_enabled": bool(updated["web_otp_enabled"]),
        "mobile_enabled": bool(updated["mobile_otp_enabled"]),
        "row_version": int(updated["row_version"]),
        "comment": (comment or "")[:300] or None,
    }
    AuditRepository(auth_db).log_audit(
        action="OTP_SMS_CONTROL_CHANGED",
        user_id=user_id,
        username=username,
        entity_type="OTP_SMS_CONTROL",
        entity_id="1",
        old_values=json.dumps(old_values),
        new_values=json.dumps(new_values),
        ip_address=ip_address,
        user_agent=(user_agent or "")[:500] or None,
        status="SUCCESS",
    )
    try:
        business_db.commit()
        auth_db.commit()
    except SQLAlchemyError:
        business_db.rollback()
        auth_db.rollback()
        logger.exception("OTP SMS control save failed")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not save OTP settings. Please try again.",
        ) from None

    invalidate_otp_control_cache()
    payload = _public_payload(updated, config_ok=True)
    _store_cache(payload)
    logger.info(
        "OTP SMS control updated by %s master=%s web=%s mobile=%s",
        username,
        payload["master_enabled"],
        payload["web_enabled"],
        payload["mobile_enabled"],
    )
    return payload
