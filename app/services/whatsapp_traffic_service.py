"""Log WhatsApp traffic and email an alert on misuse."""

from __future__ import annotations

import logging
import threading
from html import escape

from app.config.settings import settings
from app.services import whatsapp_traffic_store as store
from app.services.email_service import (
    EmailDeliveryError,
    EmailNotConfiguredError,
    EmailService,
)

logger = logging.getLogger("ahsteellab")


def log_inbound(
    *,
    mobile: str,
    text: str = "",
    kind: str = "text",
    source: str = "webhook",
) -> None:
    _log(
        direction="in",
        kind=kind,
        source=source,
        mobile=mobile,
        text=text,
        status="ok",
    )


def log_outbound(
    *,
    mobile: str,
    text: str = "",
    kind: str = "text",
    source: str = "cloud_api",
    actor: str = "",
    status: str = "ok",
    error: str = "",
    wa_message_id: str = "",
) -> None:
    _log(
        direction="out",
        kind=kind,
        source=source,
        mobile=mobile,
        text=text,
        actor=actor,
        status=status,
        error=error,
        wa_message_id=wa_message_id,
    )


def _log(**kwargs) -> None:
    try:
        cfg = store.get_settings()
        if not cfg.get("logging_enabled", True):
            return
        event = store.record_event(**kwargs)
        if event.get("status") == "failed":
            return
        reason = store.detect_misuse(event)
        if not reason:
            return
        alerted = False
        if cfg.get("alerts_enabled", True) and store.should_send_alert(event.get("mobile") or ""):
            alerted = True
            threading.Thread(
                target=_send_misuse_email,
                kwargs={"event": event, "reason": reason},
                daemon=True,
                name="whatsapp-traffic-alert",
            ).start()
        store.flag_event(event["id"], reason, alerted=alerted)
        logger.warning(
            "WhatsApp misuse mobile=%s source=%s reason=%s",
            event.get("mobile"),
            event.get("source"),
            reason,
        )
    except Exception:
        logger.exception("WhatsApp traffic log failed")


def send_test_alert() -> dict:
    cfg = store.get_settings()
    to_addr = str(cfg.get("alert_email") or "").strip()
    if not to_addr:
        raise EmailDeliveryError("Set a WhatsApp alert email address first.")
    sample = {
        "mobile": "03001234567",
        "direction": "in",
        "source": "webhook",
        "kind": "text",
        "actor": "",
        "text": "TEST — ignore this sample traffic.",
    }
    _send_misuse_email(
        event=sample,
        reason="Test alert from WhatsApp Traffic panel.",
        is_test=True,
        to_addr=to_addr,
    )
    return {"sent_to": to_addr, "status": "sent"}


def _send_misuse_email(
    *,
    event: dict,
    reason: str,
    is_test: bool = False,
    to_addr: str = "",
) -> None:
    cfg = store.get_settings()
    recipient = to_addr or str(cfg.get("alert_email") or "").strip()
    if not recipient:
        return
    app = settings.app_name or "ERP"
    mobile = event.get("mobile") or "—"
    subject = (
        f"{app} — test WhatsApp misuse alert"
        if is_test
        else f"{app} — WhatsApp misuse: {mobile}"
    )
    text = (
        f"{reason}\n\n"
        f"Mobile: {mobile}\n"
        f"Direction: {event.get('direction') or '—'}\n"
        f"Source: {event.get('source') or '—'}\n"
        f"Type: {event.get('kind') or '—'}\n"
        f"Staff user: {event.get('actor') or '—'}\n"
        f"Text: {event.get('text') or '—'}\n"
        f"App: {app}\n"
        "Open Administration → WhatsApp Traffic for the full log."
    )
    html = f"""
    <div style="font-family:Segoe UI,Arial,sans-serif;font-size:14px;color:#222">
      <p><strong>{escape(reason)}</strong></p>
      <table style="border-collapse:collapse">
        <tr><td style="padding:4px 12px 4px 0;color:#666">Mobile</td><td>{escape(str(mobile))}</td></tr>
        <tr><td style="padding:4px 12px 4px 0;color:#666">Direction</td><td>{escape(str(event.get('direction') or '—'))}</td></tr>
        <tr><td style="padding:4px 12px 4px 0;color:#666">Source</td><td>{escape(str(event.get('source') or '—'))}</td></tr>
        <tr><td style="padding:4px 12px 4px 0;color:#666">Type</td><td>{escape(str(event.get('kind') or '—'))}</td></tr>
        <tr><td style="padding:4px 12px 4px 0;color:#666">Staff user</td><td>{escape(str(event.get('actor') or '—'))}</td></tr>
        <tr><td style="padding:4px 12px 4px 0;color:#666">Text</td><td>{escape(str(event.get('text') or '—'))}</td></tr>
      </table>
      <p style="color:#666;font-size:12px">Open WhatsApp Traffic in admin for the complete log.</p>
    </div>
    """
    try:
        EmailService().send_email([recipient], subject, text, body_html=html)
        logger.info("WhatsApp misuse alert emailed to %s for %s", recipient, mobile)
    except (EmailNotConfiguredError, EmailDeliveryError) as exc:
        logger.warning("WhatsApp misuse alert email failed: %s", exc)
        if is_test:
            raise
    except Exception:
        logger.exception("WhatsApp misuse alert email failed")
        if is_test:
            raise EmailDeliveryError("Could not send WhatsApp misuse alert.") from None
