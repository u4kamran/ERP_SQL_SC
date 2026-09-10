"""Guest web mobile OTP verification (proves number ownership)."""

from __future__ import annotations

import hashlib
import hmac
import json
import logging
import secrets
import threading
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from app.config.settings import settings
from app.database.business_session import BusinessSessionLocal
from app.services.otp_sms_control_service import (
    CHANNEL_WEB,
    assert_otp_config_available,
    is_channel_otp_required,
)
from app.services.sms_db_queue_service import build_otp_sms_body, queue_sms
from app.services.whatsapp_service import (
    WhatsAppDeliveryError,
    WhatsAppNotConfiguredError,
    WhatsAppService,
    normalize_pk_phone,
)

logger = logging.getLogger("ahsteellab")

_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
_DATA_FILE = _PROJECT_ROOT / "data" / "mobile_otp.json"
_LOCK = threading.Lock()

OTP_TTL_SECONDS = 300
VERIFIED_TTL_DAYS = 30
MAX_ATTEMPTS = 5
RESEND_COOLDOWN_SECONDS = 45


def _now() -> datetime:
    return datetime.utcnow()


def _mobile_key(phone: str) -> str:
    normalized = normalize_pk_phone(phone) or "".join(ch for ch in (phone or "") if ch.isdigit())
    digits = "".join(ch for ch in normalized if ch.isdigit())
    return digits[-10:] if len(digits) >= 10 else ""


def _hash_code(code: str, salt: str) -> str:
    return hashlib.sha256(f"{salt}:{code}".encode("utf-8")).hexdigest()


def _load() -> dict[str, Any]:
    _DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
    if not _DATA_FILE.exists():
        return {"pending": {}, "verified": {}}
    try:
        raw = json.loads(_DATA_FILE.read_text(encoding="utf-8"))
        if not isinstance(raw, dict):
            return {"pending": {}, "verified": {}}
        return {
            "pending": raw.get("pending") or {},
            "verified": raw.get("verified") or {},
        }
    except (OSError, json.JSONDecodeError):
        return {"pending": {}, "verified": {}}


def _save(data: dict[str, Any]) -> None:
    _DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
    _DATA_FILE.write_text(json.dumps(data, indent=2, default=str), encoding="utf-8")


class MobileOtpService:
    """Send + verify OTP for guest web chat mobile authentication."""

    def __init__(self, db=None):
        self.db = db
        self.whatsapp = WhatsAppService()

    def is_required(self) -> bool:
        return is_channel_otp_required(CHANNEL_WEB, self.db)

    def is_verified(self, phone: str) -> bool:
        key = _mobile_key(phone)
        if not key:
            return False
        with _LOCK:
            data = _load()
            row = data["verified"].get(key)
            if not row:
                return False
            try:
                expires = datetime.fromisoformat(str(row.get("expires_at")))
            except ValueError:
                return False
            if expires < _now():
                data["verified"].pop(key, None)
                _save(data)
                return False
            return True

    def send_otp(self, phone: str) -> dict[str, Any]:
        control = assert_otp_config_available(self.db)
        key = _mobile_key(phone)
        display = "0" + key if key else ""
        if not control["web_effective"]:
            return {
                "ok": True,
                "otp_required": False,
                "phone": display,
                "expires_in": None,
                "sent_via": None,
                "verified": False,
                "message": "OTP verification is not required.",
            }
        if not key:
            raise ValueError("Enter a valid Pakistan mobile number.")
        storage_phone = normalize_pk_phone(phone) or f"92{key}"

        if not _LOCK.acquire(timeout=5):
            raise RuntimeError("OTP service is busy. Please try again.")
        try:
            data = _load()
            pending = data["pending"].get(key) or {}
            last_sent = pending.get("sent_at")
            if last_sent:
                try:
                    elapsed = (_now() - datetime.fromisoformat(str(last_sent))).total_seconds()
                    if elapsed < RESEND_COOLDOWN_SECONDS:
                        wait = int(RESEND_COOLDOWN_SECONDS - elapsed)
                        raise ValueError(f"Please wait {wait}s before requesting another code.")
                except ValueError as exc:
                    if str(exc).startswith("Please wait"):
                        raise
            code = f"{secrets.randbelow(1_000_000):06d}"
            salt = secrets.token_hex(8)
            data["pending"][key] = {
                "code_hash": _hash_code(code, salt),
                "salt": salt,
                "expires_at": (_now() + timedelta(seconds=OTP_TTL_SECONDS)).isoformat(),
                "sent_at": _now().isoformat(),
                "attempts": 0,
                "phone": storage_phone,
            }
            _save(data)
        finally:
            _LOCK.release()

        sent_via = self._deliver(storage_phone, code, display)
        result: dict[str, Any] = {
            "ok": True,
            "otp_required": True,
            "phone": display,
            "expires_in": OTP_TTL_SECONDS,
            "sent_via": sent_via,
            "message": f"Verification code sent to {display} by SMS.",
        }
        # Dev-only echo so local testing works without WhatsApp/SMS gateway.
        if (
            settings.app_env.lower() in {"development", "dev", "local"}
            and getattr(settings, "guest_mobile_otp_dev_echo", False)
        ):
            result["dev_code"] = code
            result["message"] += f" (dev code: {code})"
        return result

    def verify_otp(self, phone: str, code: str) -> dict[str, Any]:
        control = assert_otp_config_available(self.db)
        key = _mobile_key(phone)
        display = "0" + key if key else ""
        if not control["web_effective"]:
            return {
                "ok": True,
                "otp_required": False,
                "phone": display,
                "verified": False,
                "message": "OTP verification is not required.",
            }

        clean_code = "".join(ch for ch in (code or "") if ch.isdigit())
        if not key or len(clean_code) != 6:
            raise ValueError("Enter the 6-digit verification code.")

        with _LOCK:
            data = _load()
            pending = data["pending"].get(key)
            if not pending:
                raise ValueError("No code pending. Request a new verification code.")
            try:
                expires = datetime.fromisoformat(str(pending.get("expires_at")))
            except ValueError:
                expires = _now() - timedelta(seconds=1)
            if expires < _now():
                data["pending"].pop(key, None)
                _save(data)
                raise ValueError("Code expired. Request a new verification code.")

            attempts = int(pending.get("attempts") or 0) + 1
            pending["attempts"] = attempts
            expected = str(pending.get("code_hash") or "")
            salt = str(pending.get("salt") or "")
            if not hmac.compare_digest(expected, _hash_code(clean_code, salt)):
                data["pending"][key] = pending
                _save(data)
                if attempts >= MAX_ATTEMPTS:
                    data["pending"].pop(key, None)
                    _save(data)
                    raise ValueError("Too many wrong attempts. Request a new code.")
                raise ValueError("Incorrect code. Please try again.")

            data["pending"].pop(key, None)
            data["verified"][key] = {
                "verified_at": _now().isoformat(),
                "expires_at": (_now() + timedelta(days=VERIFIED_TTL_DAYS)).isoformat(),
                "phone": pending.get("phone") or f"92{key}",
            }
            _save(data)

        display = "0" + key
        return {
            "ok": True,
            "otp_required": True,
            "phone": display,
            "verified": True,
            "message": f"Mobile {display} verified successfully.",
        }

    def _deliver(self, storage_phone: str, code: str, display: str) -> str:
        body = build_otp_sms_body(code, ttl_seconds=OTP_TTL_SECONDS)
        digits = "".join(ch for ch in (storage_phone or "") if ch.isdigit())
        if len(digits) < 10:
            raise RuntimeError("Enter a valid Pakistan mobile number.")
        recipient = digits if digits.startswith("92") else f"92{digits[-10:]}"

        # Always insert SMS_DB_ first (same path as the customer app).
        # SendSMSActive reads this table — WhatsApp must not skip the insert.
        db = self.db
        owned_session = False
        if db is None:
            db = BusinessSessionLocal()
            owned_session = True
        try:
            sms_id = queue_sms(db, body=body, recipient=recipient, commit=True)
            logger.info(
                "Guest chat OTP queued to SMS_DB_ id=%s recipient=%s",
                sms_id,
                recipient,
            )
        except Exception as exc:
            logger.exception("Guest chat OTP SMS_DB_ insert failed for %s", display)
            if owned_session:
                try:
                    db.rollback()
                except Exception:
                    pass
            raise RuntimeError(
                "Could not queue SMS OTP. Please try again."
            ) from exc
        finally:
            if owned_session:
                db.close()

        provider = (getattr(settings, "guest_mobile_otp_provider", "sms_db") or "sms_db").lower().strip()
        if provider in {"whatsapp", "auto"}:
            try:
                self.whatsapp.send_text(storage_phone, body)
                logger.info("Guest chat OTP also sent via WhatsApp to %s", display)
            except (WhatsAppNotConfiguredError, WhatsAppDeliveryError) as exc:
                logger.warning("Guest chat OTP WhatsApp extra send failed for %s: %s", display, exc)

        return "sms"
