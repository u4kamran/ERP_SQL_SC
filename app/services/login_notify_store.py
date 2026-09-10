"""Login-alert settings + send log (default notify email)."""

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
_FILE = _DATA_DIR / "login_notify.json"
_LOCK = threading.Lock()
_MAX_EVENTS = 500
_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _ensure() -> None:
    _DATA_DIR.mkdir(parents=True, exist_ok=True)


def _env_default_email() -> str:
    return (
        (settings.login_notify_email or "").strip()
        or (settings.smtp_from_email or "").strip()
        or (settings.smtp_user or "").strip()
    )


def _default_settings() -> dict[str, Any]:
    return {
        "enabled": bool(settings.login_notify_enabled),
        "notify_email": _env_default_email(),
        "notes": "",
    }


def _default() -> dict[str, Any]:
    return {"settings": _default_settings(), "events": []}


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
        if not str(merged.get("notify_email") or "").strip():
            merged["notify_email"] = _env_default_email()
        data["settings"] = merged
        events = raw.get("events") or []
        data["events"] = events if isinstance(events, list) else []
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
    with _LOCK:
        data = _load_unlocked()
        settings_row = dict(data["settings"])
        if "enabled" in payload and payload["enabled"] is not None:
            settings_row["enabled"] = bool(payload["enabled"])
        if "notify_email" in payload and payload["notify_email"] is not None:
            email = str(payload["notify_email"] or "").strip()
            if email and not _EMAIL_RE.match(email):
                raise ValueError("Enter a valid notify email address.")
            settings_row["notify_email"] = email
        if "notes" in payload and payload["notes"] is not None:
            settings_row["notes"] = str(payload["notes"] or "")[:300]
        data["settings"] = settings_row
        _save_unlocked(data)
        return dict(settings_row)


def record_event(payload: dict[str, Any]) -> dict[str, Any]:
    event = {
        "id": str(uuid.uuid4()),
        "created_at": _now_iso(),
        "username": str(payload.get("username") or "")[:80],
        "full_name": str(payload.get("full_name") or "")[:120],
        "user_email": str(payload.get("user_email") or "")[:120],
        "ip": str(payload.get("ip") or "")[:64],
        "browser": str(payload.get("browser") or "")[:80],
        "device": str(payload.get("device") or "")[:80],
        "os": str(payload.get("os") or "")[:80],
        "sent_to": str(payload.get("sent_to") or "")[:120],
        "status": str(payload.get("status") or "failed")[:20],
        "detail": str(payload.get("detail") or "")[:240],
    }
    with _LOCK:
        data = _load_unlocked()
        data["events"].append(event)
        _save_unlocked(data)
    return event


def dashboard(*, limit: int = 80) -> dict[str, Any]:
    with _LOCK:
        data = _load_unlocked()
        settings_row = dict(data["settings"])
        events = list(data.get("events") or [])

    recent = list(reversed(events[-max(1, min(limit, 200)) :]))
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    today_events = [e for e in events if str(e.get("created_at") or "").startswith(today)]
    return {
        "settings": settings_row,
        "smtp_configured": False,
        "smtp_hint": "",
        "today": {
            "date": today,
            "sent": sum(1 for e in today_events if e.get("status") == "sent"),
            "failed": sum(1 for e in today_events if e.get("status") != "sent"),
        },
        "totals": {
            "events": len(events),
            "sent": sum(1 for e in events if e.get("status") == "sent"),
            "failed": sum(1 for e in events if e.get("status") != "sent"),
        },
        "recent": recent,
    }
