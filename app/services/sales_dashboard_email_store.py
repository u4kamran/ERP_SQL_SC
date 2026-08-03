"""Persist sales dashboard email scheduler configuration."""

from __future__ import annotations

import json
import threading
from datetime import datetime
from pathlib import Path
from typing import Any

from app.schemas.sales_dashboard_email import SalesDashboardEmailConfig

_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
_DATA_DIR = _PROJECT_ROOT / "data"
_CONFIG_FILE = _DATA_DIR / "sales_dashboard_email.json"
_LOCK = threading.Lock()

_DEFAULT_STATE: dict[str, Any] = {
    "enabled": False,
    "recipients": "",
    "interval_minutes": 30,
    "email_subject": "Sales Dashboard — Month-over-Month",
    "date_preset": "this-month",
    "last_email_at": None,
    "last_check_at": None,
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


def get_config() -> SalesDashboardEmailConfig:
    state = load_state()
    return SalesDashboardEmailConfig(
        enabled=bool(state.get("enabled")),
        recipients=str(state.get("recipients") or ""),
        interval_minutes=int(state.get("interval_minutes") or 30),
        email_subject=str(state.get("email_subject") or "Sales Dashboard — Month-over-Month"),
        date_preset=str(state.get("date_preset") or "this-month"),
    )


def update_runtime(
    *,
    last_check_at: datetime | None = None,
    last_email_at: datetime | None = None,
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
