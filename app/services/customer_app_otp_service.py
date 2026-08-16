"""Customer-app OTP via SMS_DB_ — one-time mobile ownership proof (not per invoice)."""

from __future__ import annotations

import hashlib
import hmac
import logging
import re
import secrets
from datetime import datetime, timedelta
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.config.settings import settings
from app.repositories.customer_app_otp_repository import CustomerAppOtpRepository

logger = logging.getLogger("ahsteellab")


def _mask_mobile(display: str) -> str:
    digits = re.sub(r"\D", "", display or "")
    if len(digits) < 4:
        return "****"
    return f"{digits[:2]}******{digits[-3:]}"


class CustomerAppOtpService:
    """
    Secure OTP for the customer shopping app.

    - Backend generates crypto 6-digit OTP
    - Stores hash only in customer_app_otp
    - Queues SMS via existing SMS_DB_ (STATUS=1 pending)
    - One-time verify; remains verified for configured days (not per invoice)
    """

    def __init__(self, db: Session):
        self.db = db
        self.repo = CustomerAppOtpRepository(db)

    @staticmethod
    def mobile_key(value: str) -> str:
        digits = re.sub(r"\D", "", value or "")
        if len(digits) < 10:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Enter a valid mobile number with at least 10 digits (03XXXXXXXXX).",
            )
        return digits[-10:]

    @staticmethod
    def mobile_display(value: str) -> str:
        key = CustomerAppOtpService.mobile_key(value)
        return "0" + key

    @staticmethod
    def mobile_recipient_92(value: str) -> str:
        return "92" + CustomerAppOtpService.mobile_key(value)

    @staticmethod
    def _hash_otp(code: str, salt: str) -> str:
        return hashlib.sha256(f"{salt}:{code}".encode("utf-8")).hexdigest()

    @staticmethod
    def _generate_otp() -> str:
        return f"{secrets.randbelow(1_000_000):06d}"

    def is_required(self) -> bool:
        return bool(getattr(settings, "customer_app_otp_required", True))

    def is_verified(self, mobile: str) -> bool:
        try:
            key = self.mobile_key(mobile)
        except HTTPException:
            return False
        return self.repo.is_verified(key)

    def require_verified(self, mobile: str) -> None:
        if not self.is_required():
            return
        if not self.is_verified(mobile):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=(
                    "Please verify your mobile number with the OTP code once "
                    "before saving or viewing carts."
                ),
            )

    def status(self, mobile: str) -> dict[str, Any]:
        verified = False
        try:
            verified = self.is_verified(mobile) if mobile else False
        except HTTPException:
            verified = False
        return {
            "required": self.is_required(),
            "verified": verified,
            "provider": (settings.customer_app_otp_provider or "sms_db").lower(),
        }

    def request_otp(self, mobile: str, *, client_ip: str | None = None) -> dict[str, Any]:
        key = self.mobile_key(mobile)
        display = self.mobile_display(mobile)
        recipient = self.mobile_recipient_92(mobile)
        ttl = int(getattr(settings, "customer_app_otp_ttl_seconds", 300) or 300)
        cooldown = int(getattr(settings, "customer_app_otp_resend_cooldown_seconds", 45) or 45)
        max_req = int(getattr(settings, "customer_app_otp_max_requests_per_window", 3) or 3)
        window_min = int(getattr(settings, "customer_app_otp_request_window_minutes", 15) or 15)
        max_attempts = int(getattr(settings, "customer_app_otp_max_attempts", 5) or 5)
        provider = (settings.customer_app_otp_provider or "sms_db").lower().strip()
        sender = (settings.customer_app_otp_sms_sender or "923004017067").strip()

        # Cooldown against latest request (server clock)
        secs = self.repo.seconds_since_last_request(key)
        if secs is not None and secs < cooldown:
            wait = max(1, int(cooldown - secs))
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Please wait {wait}s before requesting another code.",
            )

        recent = self.repo.count_recent_requests(key, window_minutes=window_min)
        if recent >= max_req:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=(
                    f"Too many OTP requests. Please try again after {window_min} minutes."
                ),
            )

        code = self._generate_otp()
        salt = secrets.token_hex(8)
        otp_hash = self._hash_otp(code, salt)
        request_id = secrets.token_urlsafe(18)
        expires_at = datetime.now() + timedelta(seconds=ttl)
        minutes = max(1, ttl // 60)
        company = (settings.company_name or settings.app_name or "Shafique Departmental Store").rstrip(".")
        body = (
            f"{company}: Your verification code is {code}. "
            f"It is valid for {minutes} minutes. Do not share this code with anyone."
        )

        try:
            self.repo.supersede_pending(key)
            otp_id = self.repo.insert_otp(
                request_id=request_id,
                mobile_key=key,
                mobile_display=display,
                otp_hash=otp_hash,
                salt=salt,
                expires_at=expires_at,
                max_attempts=max_attempts,
                client_ip=client_ip,
            )
            sms_id: int | None = None
            sent_via = "sms_db"

            if provider == "test":
                # Never send real SMS in test mode. Never allow fixed OTP 123456.
                if settings.app_env.lower() not in {"development", "dev", "local"}:
                    raise HTTPException(
                        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                        detail="OTP test provider is not allowed in production.",
                    )
                sent_via = "test"
            else:
                sms_id = self.repo.insert_sms_db_(
                    body=body,
                    sender=sender,
                    recipient=recipient,
                )
                self.repo.attach_sms_id(otp_id, sms_id)

            self.db.commit()
        except HTTPException:
            self.db.rollback()
            raise
        except Exception as exc:
            self.db.rollback()
            logger.exception("OTP request failed for %s", _mask_mobile(display))
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Could not send verification code. Please try again.",
            ) from exc

        logger.info(
            "OTP requested for %s request_id=%s sms_id=%s via=%s",
            _mask_mobile(display),
            request_id,
            sms_id,
            sent_via,
        )

        result: dict[str, Any] = {
            "ok": True,
            "phone": display,
            "request_id": request_id,
            "expires_in": ttl,
            "sent_via": sent_via,
            "verified": False,
            "message": (
                f"OTP sent successfully to {display}."
                if sent_via == "sms_db"
                else f"OTP generated for {display} (test mode — check server logs if echo enabled)."
            ),
            "dev_code": None,
        }
        # Plain OTP only in local test + explicit echo — never production sms_db.
        if (
            sent_via == "test"
            and settings.app_env.lower() in {"development", "dev", "local"}
            and getattr(settings, "customer_app_otp_dev_echo", False)
        ):
            result["dev_code"] = code
            result["message"] += f" (dev code: {code})"
        return result

    def verify_otp(
        self,
        mobile: str,
        code: str,
        *,
        request_id: str | None = None,
    ) -> dict[str, Any]:
        key = self.mobile_key(mobile)
        display = self.mobile_display(mobile)
        clean = "".join(ch for ch in (code or "") if ch.isdigit())
        if len(clean) != 6:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Enter the 6-digit verification code.",
            )

        row: dict[str, Any] | None = None
        if request_id and request_id.strip():
            row = self.repo.get_by_request_id(request_id.strip())
            if not row or row.get("mobile_key") != key:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid or expired verification request. Please request a new OTP.",
                )
        else:
            row = self.repo.latest_pending(key)

        if not row or row.get("status") != "PENDING":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid OTP. Please check the code and try again.",
            )

        expires_at = row.get("expires_at")
        if isinstance(expires_at, datetime) and expires_at.replace(tzinfo=None) < datetime.now():
            self.repo.mark_expired(int(row["id"]))
            self.db.commit()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="OTP expired. Please request a new code.",
            )

        attempts = int(row.get("attempt_count") or 0) + 1
        max_attempts = int(row.get("max_attempts") or 5)
        expected = str(row.get("otp_hash") or "")
        salt = str(row.get("salt") or "")
        if not hmac.compare_digest(expected, self._hash_otp(clean, salt)):
            self.repo.bump_attempt(int(row["id"]), attempts)
            if attempts >= max_attempts:
                self.repo.mark_blocked(int(row["id"]))
                self.db.commit()
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="This OTP has expired or been blocked. Please request a new OTP.",
                )
            self.db.commit()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid OTP. Please check the code and try again.",
            )

        days = int(getattr(settings, "customer_app_otp_verified_days", 30) or 30)
        verified_until = datetime.now() + timedelta(days=days)
        try:
            self.repo.mark_verified(int(row["id"]), verified_until=verified_until)
            self.db.commit()
        except Exception:
            self.db.rollback()
            raise

        logger.info(
            "OTP verified for %s request_id=%s",
            _mask_mobile(display),
            row.get("request_id"),
        )
        return {
            "ok": True,
            "phone": display,
            "request_id": row.get("request_id"),
            "verified": True,
            "message": "Mobile number verified successfully.",
            "expires_in": None,
            "sent_via": None,
            "dev_code": None,
        }
