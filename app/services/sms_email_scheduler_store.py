"""Persist SMS email scheduler configuration and runtime state."""

from __future__ import annotations

import json
import threading
from datetime import datetime
from pathlib import Path
from typing import Any

from app.schemas.sms_email_scheduler import SmsEmailSchedulerConfig

_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
_DATA_DIR = _PROJECT_ROOT / "data"
_CONFIG_FILE = _DATA_DIR / "sms_email_scheduler.json"
_LOCK = threading.Lock()

_DEFAULT_STATE: dict[str, Any] = {
    "enabled": False,
    "recipients": "",
    "body_keyword": "Total Sales",
    "window_start": "08:00",
    "window_end": "01:30",
    "check_interval_minutes": 30,
    "email_subject": "Sales Summary Alert",
    "last_emailed_id": 0,
    "last_check_at": None,
    "last_email_at": None,
    "last_email_record_id": None,
    "last_error": None,
    "next_check_at": None,
    "last_check_message": None,
}


def _ensure_data_dir() -> None:
    _DATA_DIR.mkdir(parents=True, exist_ok=True)


def _read_state_unlocked() -> dict[str, Any]:
    _ensure_data_dir()
    if not _CONFIG_FILE.exists():
        return dict(_DEFAULT_STATE)
    try:
        data = json.loads(_CONFIG_FILE.read_text(encoding="utf-8"))
        merged = dict(_DEFAULT_STATE)
        merged.update(data)
        return merged
    except (json.JSONDecodeError, OSError):
        return dict(_DEFAULT_STATE)


def load_state() -> dict[str, Any]:
    with _LOCK:
        return _read_state_unlocked()


def save_state(updates: dict[str, Any]) -> dict[str, Any]:
    with _LOCK:
        current = _read_state_unlocked()
        current.update(updates)
        _CONFIG_FILE.write_text(json.dumps(current, indent=2, default=str), encoding="utf-8")
        return current


def get_config() -> SmsEmailSchedulerConfig:
    state = load_state()
    return SmsEmailSchedulerConfig(
        enabled=bool(state.get("enabled")),
        recipients=str(state.get("recipients") or ""),
        body_keyword=str(state.get("body_keyword") or "Total Sales"),
        window_start=str(state.get("window_start") or "08:00"),
        window_end=str(state.get("window_end") or "01:30"),
        check_interval_minutes=int(state.get("check_interval_minutes") or 30),
        email_subject=str(state.get("email_subject") or "Sales Summary Alert"),
        last_emailed_id=int(state.get("last_emailed_id") or 0),
    )


def update_runtime(
    *,
    last_check_at: datetime | None = None,
    last_email_at: datetime | None = None,
    last_email_record_id: int | None = None,
    last_emailed_id: int | None = None,
    next_check_at: datetime | None = None,
    last_check_message: str | None = None,
    last_error: str | None = None,
    clear_error: bool = False,
) -> None:
    updates: dict[str, Any] = {}
    if last_check_at is not None:
        updates["last_check_at"] = last_check_at.isoformat()
    if last_email_at is not None:
        updates["last_email_at"] = last_email_at.isoformat()
    if last_email_record_id is not None:
        updates["last_email_record_id"] = last_email_record_id
    if last_emailed_id is not None:
        updates["last_emailed_id"] = last_emailed_id
    if next_check_at is not None:
        updates["next_check_at"] = next_check_at.isoformat()
    if last_check_message is not None:
        updates["last_check_message"] = last_check_message[:500]
    if clear_error:
        updates["last_error"] = None
    elif last_error is not None:
        updates["last_error"] = last_error[:500]
    if updates:
        save_state(updates)
