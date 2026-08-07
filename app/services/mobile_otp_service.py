"""Guest web mobile OTP verification (proves number ownership)."""

from __future__ import annotations

import hashlib
import hmac
import json
import logging
import random
import secrets
import threading
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from app.config.settings import settings
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

    def __init__(self):
        self.whatsapp = WhatsAppService()

    def is_required(self) -> bool:
        return bool(getattr(settings, "guest_mobile_otp_required", True))

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
        key = _mobile_key(phone)
        if not key:
            raise ValueError("Enter a valid Pakistan mobile number.")
        storage_phone = normalize_pk_phone(phone) or f"92{key}"
        display = "0" + key

        with _LOCK:
            data = _load()
            pending = data["pending"].get(key) or {}
            last_sent = pending.get("sent_at")
            if last_sent:
                try:
                    elapsed = (_now() - datetime.fromisoformat(str(last_sent))).total_seconds()
                    if elapsed < RESEND_COOLDOWN_SECONDS:
                        wait = int(RESEND_COOLDOWN_SECONDS - elapsed)
                        raise ValueError(f"Please wait {wait}s before requesting another code.")
                except ValueError:
                    pass

            code = f"{random.randint(0, 999999):06d}"
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

        sent_via = self._deliver(storage_phone, code, display)
        result: dict[str, Any] = {
            "ok": True,
            "phone": display,
            "expires_in": OTP_TTL_SECONDS,
            "sent_via": sent_via,
            "message": f"Verification code sent to {display} via {sent_via}.",
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
        key = _mobile_key(phone)
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
            "phone": display,
            "verified": True,
            "message": f"Mobile {display} verified successfully.",
        }

    def _deliver(self, storage_phone: str, code: str, display: str) -> str:
        company = settings.company_name or settings.app_name
        text = (
            f"{company} verification code: *{code}*\n"
            f"Valid for {OTP_TTL_SECONDS // 60} minutes.\n"
            "Do not share this code."
        )
        if self.whatsapp.is_configured() and settings.whatsapp_enabled:
            try:
                self.whatsapp.send_text(storage_phone, text)
                return "whatsapp"
            except (WhatsAppNotConfiguredError, WhatsAppDeliveryError) as exc:
                logger.warning("OTP WhatsApp delivery failed: %s", exc)

        if (
            settings.app_env.lower() in {"development", "dev", "local"}
            and getattr(settings, "guest_mobile_otp_dev_echo", False)
        ):
            logger.info("DEV OTP for %s: %s", display, code)
            return "dev"

        raise RuntimeError(
            "Cannot authenticate mobile on web: WhatsApp API is not configured "
            "to send the OTP. Set WHATSAPP_ENABLED=true with Cloud API credentials, "
            "or enable GUEST_MOBILE_OTP_DEV_ECHO=true for local testing only."
        )
