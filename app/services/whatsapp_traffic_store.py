"""Complete WhatsApp traffic log + misuse thresholds."""

from __future__ import annotations

import json
import re
import threading
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.config.settings import settings

_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
_DATA_DIR = _PROJECT_ROOT / "data"
_FILE = _DATA_DIR / "whatsapp_traffic.json"
_LOCK = threading.Lock()
_MAX_EVENTS = 8000
_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
_OTP_DIGITS = re.compile(r"\b\d{4,8}\b")


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _now_iso() -> str:
    return _now().isoformat()


def _today() -> str:
    return _now().strftime("%Y-%m-%d")


def _ensure() -> None:
    _DATA_DIR.mkdir(parents=True, exist_ok=True)


def normalize_mobile(raw: str) -> str:
    digits = re.sub(r"\D", "", raw or "")
    if not digits:
        return ""
    if digits.startswith("92") and len(digits) >= 12:
        return f"0{digits[2:12]}"
    if len(digits) >= 10:
        return f"0{digits[-10:]}" if not digits.startswith("0") else digits[-11:]
    return digits


def _env_default_email() -> str:
    return (
        (getattr(settings, "whatsapp_traffic_alert_email", "") or "").strip()
        or (settings.login_notify_email or "").strip()
        or (settings.smtp_from_email or "").strip()
        or (settings.smtp_user or "").strip()
    )


def _default_settings() -> dict[str, Any]:
    return {
        "logging_enabled": True,
        "alerts_enabled": True,
        "alert_email": _env_default_email(),
        "inbound_per_minute": 8,
        "inbound_per_day": 40,
        "outbound_per_day": 60,
        "otp_per_hour": 6,
        "docs_per_actor_per_day": 40,
        "duplicate_count": 5,
        "duplicate_window_minutes": 10,
        "alert_cooldown_minutes": 30,
        "notes": "",
    }


def _default() -> dict[str, Any]:
    return {"settings": _default_settings(), "events": [], "last_alerts": {}}


def _load_unlocked() -> dict[str, Any]:
    _ensure()
    if not _FILE.exists():
        return _default()
    try:
        raw = json.loads(_FILE.read_text(encoding="utf-8"))
        if not isinstance(raw, dict):
            return _default()
        data = _default()
        merged = dict(_default_settings())
        merged.update(raw.get("settings") or {})
        if not str(merged.get("alert_email") or "").strip():
            merged["alert_email"] = _env_default_email()
        data["settings"] = merged
        events = raw.get("events") or []
        data["events"] = events if isinstance(events, list) else []
        alerts = raw.get("last_alerts") or {}
        data["last_alerts"] = alerts if isinstance(alerts, dict) else {}
        return data
    except (json.JSONDecodeError, OSError):
        return _default()


def _save_unlocked(data: dict[str, Any]) -> None:
    _ensure()
    events = data.get("events") or []
    if len(events) > _MAX_EVENTS:
        data["events"] = events[-_MAX_EVENTS:]
    _FILE.write_text(json.dumps(data, indent=2, default=str), encoding="utf-8")


def get_settings() -> dict[str, Any]:
    with _LOCK:
        return dict(_load_unlocked()["settings"])


def update_settings(payload: dict[str, Any]) -> dict[str, Any]:
    int_keys = {
        "inbound_per_minute",
        "inbound_per_day",
        "outbound_per_day",
        "otp_per_hour",
        "docs_per_actor_per_day",
        "duplicate_count",
        "duplicate_window_minutes",
        "alert_cooldown_minutes",
    }
    with _LOCK:
        data = _load_unlocked()
        row = dict(data["settings"])
        if "logging_enabled" in payload and payload["logging_enabled"] is not None:
            row["logging_enabled"] = bool(payload["logging_enabled"])
        if "alerts_enabled" in payload and payload["alerts_enabled"] is not None:
            row["alerts_enabled"] = bool(payload["alerts_enabled"])
        if "alert_email" in payload and payload["alert_email"] is not None:
            email = str(payload["alert_email"] or "").strip()
            if email and not _EMAIL_RE.match(email):
                raise ValueError("Enter a valid alert email address.")
            row["alert_email"] = email
        if "notes" in payload and payload["notes"] is not None:
            row["notes"] = str(payload["notes"] or "")[:300]
        for key in int_keys:
            if key in payload and payload[key] is not None:
                row[key] = max(0, int(payload[key] or 0))
        data["settings"] = row
        _save_unlocked(data)
        return dict(row)


def sanitize_text(text: str, source: str = "") -> str:
    value = (text or "").replace("\r", " ").strip()
    if (source or "").lower() == "otp":
        value = _OTP_DIGITS.sub("******", value)
    return value[:400]


def record_event(
    *,
    direction: str,
    kind: str,
    source: str,
    mobile: str,
    text: str = "",
    actor: str = "",
    status: str = "ok",
    error: str = "",
    wa_message_id: str = "",
) -> dict[str, Any]:
    src = (source or "cloud_api").strip().lower()[:40]
    event = {
        "id": str(uuid.uuid4()),
        "created_at": _now_iso(),
        "direction": "in" if direction == "in" else "out",
        "kind": (kind or "text")[:20],
        "source": src,
        "mobile": normalize_mobile(mobile),
        "actor": (actor or "")[:80],
        "text": sanitize_text(text, src),
        "status": (status or "ok")[:20],
        "flag_reason": "",
        "error": (error or "")[:240],
        "wa_message_id": (wa_message_id or "")[:80],
        "alerted": False,
    }
    with _LOCK:
        data = _load_unlocked()
        if not data["settings"].get("logging_enabled", True):
            return event
        data["events"].append(event)
        _save_unlocked(data)
    return event


def flag_event(event_id: str, reason: str, *, alerted: bool = False) -> dict[str, Any] | None:
    with _LOCK:
        data = _load_unlocked()
        found = None
        for item in data["events"]:
            if item.get("id") == event_id:
                item["status"] = "flagged"
                item["flag_reason"] = (reason or "")[:240]
                if alerted:
                    item["alerted"] = True
                found = dict(item)
                break
        if found:
            _save_unlocked(data)
        return found


def should_send_alert(mobile: str) -> bool:
    key = normalize_mobile(mobile) or "(unknown)"
    with _LOCK:
        data = _load_unlocked()
        settings_row = data["settings"]
        if not settings_row.get("alerts_enabled", True):
            return False
        if not str(settings_row.get("alert_email") or "").strip():
            return False
        cooldown = int(settings_row.get("alert_cooldown_minutes") or 30)
        last = str((data.get("last_alerts") or {}).get(key) or "")
        if last and cooldown > 0:
            try:
                ts = datetime.fromisoformat(last.replace("Z", "+00:00"))
                if (_now() - ts).total_seconds() < cooldown * 60:
                    return False
            except ValueError:
                pass
        data.setdefault("last_alerts", {})[key] = _now_iso()
        _save_unlocked(data)
        return True


def _parse_ts(raw: str) -> datetime | None:
    try:
        return datetime.fromisoformat(str(raw or "").replace("Z", "+00:00"))
    except ValueError:
        return None


def detect_misuse(event: dict[str, Any]) -> str:
    """Return flag reason, or empty if traffic looks normal."""
    with _LOCK:
        data = _load_unlocked()
        settings_row = dict(data["settings"])
        events = list(data.get("events") or [])

    mobile = normalize_mobile(str(event.get("mobile") or ""))
    if not mobile:
        return ""
    now = _now()
    day = _today()
    source = str(event.get("source") or "")
    direction = str(event.get("direction") or "")
    text = str(event.get("text") or "").strip().lower()

    inbound_minute = int(settings_row.get("inbound_per_minute") or 0)
    if direction == "in" and inbound_minute > 0:
        cutoff = now.timestamp() - 60
        count = 0
        for item in events:
            if item.get("direction") != "in":
                continue
            if normalize_mobile(str(item.get("mobile") or "")) != mobile:
                continue
            ts = _parse_ts(str(item.get("created_at") or ""))
            if ts and ts.timestamp() >= cutoff:
                count += 1
        if count > inbound_minute:
            return f"Inbound flood: {count} messages in 1 minute (limit {inbound_minute})."

    inbound_day = int(settings_row.get("inbound_per_day") or 0)
    if direction == "in" and inbound_day > 0:
        count = sum(
            1
            for item in events
            if item.get("direction") == "in"
            and str(item.get("created_at") or "").startswith(day)
            and normalize_mobile(str(item.get("mobile") or "")) == mobile
        )
        if count > inbound_day:
            return f"Daily inbound limit: {count} messages today (limit {inbound_day})."

    outbound_day = int(settings_row.get("outbound_per_day") or 0)
    if direction == "out" and outbound_day > 0 and source not in {"otp"}:
        count = sum(
            1
            for item in events
            if item.get("direction") == "out"
            and str(item.get("created_at") or "").startswith(day)
            and normalize_mobile(str(item.get("mobile") or "")) == mobile
        )
        if count > outbound_day:
            return f"Daily outbound limit: {count} sends today (limit {outbound_day})."

    otp_hour = int(settings_row.get("otp_per_hour") or 0)
    if source == "otp" and otp_hour > 0:
        cutoff = now.timestamp() - 3600
        count = 0
        for item in events:
            if str(item.get("source") or "") != "otp":
                continue
            if normalize_mobile(str(item.get("mobile") or "")) != mobile:
                continue
            ts = _parse_ts(str(item.get("created_at") or ""))
            if ts and ts.timestamp() >= cutoff:
                count += 1
        if count > otp_hour:
            return f"OTP abuse: {count} codes in 1 hour (limit {otp_hour})."

    docs_day = int(settings_row.get("docs_per_actor_per_day") or 0)
    actor = str(event.get("actor") or "").strip()
    if event.get("kind") == "document" and docs_day > 0 and actor:
        count = sum(
            1
            for item in events
            if item.get("kind") == "document"
            and str(item.get("created_at") or "").startswith(day)
            and str(item.get("actor") or "") == actor
        )
        if count > docs_day:
            return f"Staff PDF overuse: {actor} sent {count} documents today (limit {docs_day})."

    dup_limit = int(settings_row.get("duplicate_count") or 0)
    dup_window = int(settings_row.get("duplicate_window_minutes") or 10)
    if dup_limit > 0 and text and source not in {"otp", "bot"}:
        cutoff = now.timestamp() - max(1, dup_window) * 60
        count = 0
        for item in events:
            if normalize_mobile(str(item.get("mobile") or "")) != mobile:
                continue
            if str(item.get("text") or "").strip().lower() != text:
                continue
            ts = _parse_ts(str(item.get("created_at") or ""))
            if ts and ts.timestamp() >= cutoff:
                count += 1
        if count > dup_limit:
            return (
                f"Repeat spam: same text {count} times in {dup_window} minutes "
                f"(limit {dup_limit})."
            )
    return ""


def dashboard(
    *,
    mobile: str = "",
    direction: str = "",
    flagged_only: bool = False,
    limit: int = 150,
) -> dict[str, Any]:
    with _LOCK:
        data = _load_unlocked()
        settings_row = dict(data["settings"])
        events = list(data.get("events") or [])

    mobile_filter = normalize_mobile(mobile)
    direction_filter = (direction or "").strip().lower()
    view = events
    if mobile_filter:
        view = [
            e
            for e in view
            if normalize_mobile(str(e.get("mobile") or "")) == mobile_filter
        ]
    if direction_filter in {"in", "out"}:
        view = [e for e in view if e.get("direction") == direction_filter]
    if flagged_only:
        view = [e for e in view if e.get("status") == "flagged"]

    day = _today()
    today = [e for e in events if str(e.get("created_at") or "").startswith(day)]
    today_in = [e for e in today if e.get("direction") == "in"]
    today_out = [e for e in today if e.get("direction") == "out"]
    today_flagged = [e for e in today if e.get("status") == "flagged"]

    by_mobile: dict[str, dict[str, Any]] = {}
    for e in today:
        key = normalize_mobile(str(e.get("mobile") or "")) or "(unknown)"
        row = by_mobile.setdefault(
            key,
            {
                "mobile": key,
                "in": 0,
                "out": 0,
                "flagged": 0,
                "failed": 0,
                "last_text": "",
                "last_at": "",
                "last_reason": "",
            },
        )
        if e.get("direction") == "in":
            row["in"] += 1
        else:
            row["out"] += 1
        if e.get("status") == "flagged":
            row["flagged"] += 1
            row["last_reason"] = e.get("flag_reason") or row["last_reason"]
        if e.get("status") == "failed":
            row["failed"] += 1
        if e.get("text"):
            row["last_text"] = e.get("text")
        row["last_at"] = e.get("created_at") or row["last_at"]

    top_mobiles = sorted(
        by_mobile.values(),
        key=lambda r: (r["flagged"], r["in"] + r["out"]),
        reverse=True,
    )[:40]

    recent = list(reversed(view[-max(1, min(limit, 500)) :]))
    return {
        "settings": settings_row,
        "today": {
            "date": day,
            "in": len(today_in),
            "out": len(today_out),
            "flagged": len(today_flagged),
            "failed": sum(1 for e in today if e.get("status") == "failed"),
        },
        "totals": {
            "events": len(events),
            "flagged": sum(1 for e in events if e.get("status") == "flagged"),
        },
        "top_mobiles": top_mobiles,
        "recent": recent,
    }
