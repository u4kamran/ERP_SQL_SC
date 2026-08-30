"""Queue outbound SMS in dbo.SMS_DB_ and start the local SendSMSActive processor."""

from __future__ import annotations

import logging
import os
import subprocess
import threading

from sqlalchemy.orm import Session

from app.config.settings import settings
from app.repositories.customer_app_otp_repository import CustomerAppOtpRepository

logger = logging.getLogger("ahsteellab")


def sms_sender_exe_path() -> str:
    return (getattr(settings, "customer_app_otp_sms_sender_exe", None) or "").strip()


def sms_sender_number() -> str:
    return (getattr(settings, "customer_app_otp_sms_sender", None) or "923004017067").strip()


def trigger_sms_sender_app() -> None:
    """Start the Windows SMS sender without blocking the HTTP request.

    UNC paths like \\\\shaheenhp\\... can hang on os.path.isfile; launch in a
    background thread and skip the existence probe for network paths.
    """
    exe = sms_sender_exe_path()
    if not exe:
        logger.warning("customer_app_otp_sms_sender_exe is empty; SMS_DB_ row queued but sender not started")
        return
    threading.Thread(
        target=_start_sms_sender,
        args=(exe,),
        daemon=True,
        name="sms-sender-exe",
    ).start()


def _start_sms_sender(exe: str) -> None:
    is_unc = exe.startswith("\\\\") or exe.startswith("//")
    if not is_unc and not os.path.isfile(exe):
        logger.error("SMS sender executable not found: %s", exe)
        return
    try:
        creationflags = 0
        if os.name == "nt":
            creationflags = int(getattr(subprocess, "CREATE_NO_WINDOW", 0))
        cwd = None if is_unc else (os.path.dirname(exe) or None)
        subprocess.Popen(
            [exe],
            cwd=cwd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            stdin=subprocess.DEVNULL,
            close_fds=True,
            creationflags=creationflags,
        )
        logger.info("Started SMS sender executable: %s", exe)
    except Exception:
        logger.exception("Failed to start SMS sender executable: %s", exe)


def queue_sms(
    db: Session,
    *,
    body: str,
    recipient: str,
    sender: str | None = None,
    commit: bool = True,
) -> int:
    """Insert SMS_DB_ row (STATUS=1 pending) and optionally commit + launch sender."""
    repo = CustomerAppOtpRepository(db)
    sms_id = repo.insert_sms_db_(
        body=body,
        sender=(sender or sms_sender_number()).strip(),
        recipient=recipient,
    )
    if commit:
        db.commit()
        trigger_sms_sender_app()
    return sms_id


def build_otp_sms_body(code: str, *, ttl_seconds: int = 300) -> str:
    """Plain OTP SMS — no store/company prefix."""
    minutes = max(1, int(ttl_seconds) // 60)
    return (
        f"Your verification code is {code}. "
        f"It is valid for {minutes} minutes. Do not share this code with anyone."
    )
