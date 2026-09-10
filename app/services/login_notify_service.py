"""Send a login-alert email to the default notify address."""

from __future__ import annotations

import logging
import threading
from html import escape

from app.config.settings import settings
from app.services import login_notify_store as store
from app.services.email_service import (
    EmailDeliveryError,
    EmailNotConfiguredError,
    EmailService,
)

logger = logging.getLogger("ahsteellab")


def notify_successful_login(
    *,
    username: str,
    full_name: str = "",
    user_email: str = "",
    ip: str = "",
    browser: str = "",
    device: str = "",
    os: str = "",
) -> None:
    """Fire-and-forget so login is not delayed by SMTP."""
    cfg = store.get_settings()
    if not cfg.get("enabled"):
        return
    to_addr = str(cfg.get("notify_email") or "").strip()
    if not to_addr:
        logger.warning("Login notify skipped — no default email address set.")
        return
    threading.Thread(
        target=_send_login_email,
        kwargs={
            "username": username,
            "full_name": full_name,
            "user_email": user_email,
            "ip": ip,
            "browser": browser,
            "device": device,
            "os": os,
            "to_addr": to_addr,
        },
        daemon=True,
        name="login-notify-email",
    ).start()


def send_test_email() -> dict:
    cfg = store.get_settings()
    to_addr = str(cfg.get("notify_email") or "").strip()
    if not to_addr:
        raise EmailDeliveryError("Set a default notify email address first.")
    _send_login_email(
        username="(test)",
        full_name="Test login alert",
        user_email="",
        ip="n/a",
        browser="Admin panel",
        device="Setup test",
        os="",
        to_addr=to_addr,
        is_test=True,
    )
    return {"sent_to": to_addr, "status": "sent"}


def _send_login_email(
    *,
    username: str,
    full_name: str,
    user_email: str,
    ip: str,
    browser: str,
    device: str,
    os: str,
    to_addr: str,
    is_test: bool = False,
) -> None:
    app = settings.app_name or "ERP"
    who = full_name.strip() or username
    subject = (
        f"{app} — test login alert"
        if is_test
        else f"{app} — login: {username}"
    )
    text = (
        f"{'This is a test login alert.' if is_test else 'A user just signed in.'}\n\n"
        f"User: {who}\n"
        f"Username: {username}\n"
        f"Account email: {user_email or '—'}\n"
        f"IP: {ip or '—'}\n"
        f"Browser: {browser or '—'}\n"
        f"Device: {device or '—'}\n"
        f"OS: {os or '—'}\n"
        f"App: {app}\n"
    )
    html = f"""
    <div style="font-family:Segoe UI,Arial,sans-serif;font-size:14px;color:#222">
      <p>{'This is a <strong>test</strong> login alert.' if is_test else 'A user just signed in to the system.'}</p>
      <table style="border-collapse:collapse">
        <tr><td style="padding:4px 12px 4px 0;color:#666">User</td><td>{escape(who)}</td></tr>
        <tr><td style="padding:4px 12px 4px 0;color:#666">Username</td><td>{escape(username)}</td></tr>
        <tr><td style="padding:4px 12px 4px 0;color:#666">Account email</td><td>{escape(user_email or '—')}</td></tr>
        <tr><td style="padding:4px 12px 4px 0;color:#666">IP</td><td>{escape(ip or '—')}</td></tr>
        <tr><td style="padding:4px 12px 4px 0;color:#666">Browser</td><td>{escape(browser or '—')}</td></tr>
        <tr><td style="padding:4px 12px 4px 0;color:#666">Device</td><td>{escape(device or '—')}</td></tr>
        <tr><td style="padding:4px 12px 4px 0;color:#666">OS</td><td>{escape(os or '—')}</td></tr>
      </table>
    </div>
    """
    status = "sent"
    detail = "Login alert emailed."
    try:
        EmailService().send_email(
            [to_addr],
            subject,
            text,
            body_html=html,
        )
        logger.info("Login notify emailed to %s for user %s", to_addr, username)
    except (EmailNotConfiguredError, EmailDeliveryError) as exc:
        status = "failed"
        detail = str(exc)[:240]
        logger.warning("Login notify email failed for %s: %s", username, detail)
    except Exception as exc:
        status = "failed"
        detail = str(exc)[:240]
        logger.exception("Login notify email failed for %s", username)

    store.record_event(
        {
            "username": username,
            "full_name": full_name,
            "user_email": user_email,
            "ip": ip,
            "browser": browser,
            "device": device,
            "os": os,
            "sent_to": to_addr,
            "status": status,
            "detail": detail,
        }
    )
    if status != "sent" and is_test:
        raise EmailDeliveryError(detail)
