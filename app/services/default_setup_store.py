"""Persist Default Setup values (business day times) per site in data/default_setup.json."""

from __future__ import annotations

import json
import re
import threading
from dataclasses import dataclass
from datetime import time
from pathlib import Path
from typing import Any

from app.config.settings import settings

_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
_DATA_DIR = _PROJECT_ROOT / "data"
_CONFIG_FILE = _DATA_DIR / "default_setup.json"
_LOCK = threading.Lock()

_TIME_RE = re.compile(r"^(\d{1,2}):(\d{2})$")


@dataclass(frozen=True)
class BusinessDayConfig:
    start_hour: int
    start_minute: int
    end_hour: int
    end_minute: int

    @property
    def start_time(self) -> time:
        return time(self.start_hour, self.start_minute, 0)

    @property
    def end_time(self) -> time:
        return time(self.end_hour, self.end_minute, 0)

    @property
    def start_time_str(self) -> str:
        return f"{self.start_hour:02d}:{self.start_minute:02d}"

    @property
    def end_time_str(self) -> str:
        return f"{self.end_hour:02d}:{self.end_minute:02d}"

    def display_note(self) -> str:
        return (
            f"Business day: {self.start_time_str} today"
            f" → {self.end_time_str} next morning"
        )

    def hours_note(self) -> str:
        return (
            f"Business day: {self.start_time_str}"
            f" → next day {self.end_time_str}"
        )


def _defaults() -> BusinessDayConfig:
    return BusinessDayConfig(
        start_hour=settings.business_day_start_hour,
        start_minute=0,
        end_hour=settings.business_day_end_hour,
        end_minute=0,
    )


def parse_time_value(value: str, *, field_name: str) -> tuple[int, int]:
    text = (value or "").strip()
    match = _TIME_RE.match(text)
    if not match:
        raise ValueError(f"{field_name} must be HH:MM (24-hour), e.g. 08:00")
    hour = int(match.group(1))
    minute = int(match.group(2))
    if hour > 23 or minute > 59:
        raise ValueError(f"{field_name} is out of range")
    return hour, minute


def validate_business_day_times(start: str, end: str) -> BusinessDayConfig:
    sh, sm = parse_time_value(start, field_name="Day start time")
    eh, em = parse_time_value(end, field_name="Day end time")
    if sh == eh and sm == em:
        raise ValueError("Day start and end times cannot be identical")
    return BusinessDayConfig(start_hour=sh, start_minute=sm, end_hour=eh, end_minute=em)


def _ensure_data_dir() -> None:
    _DATA_DIR.mkdir(parents=True, exist_ok=True)


def _read_raw_unlocked() -> dict[str, Any]:
    _ensure_data_dir()
    if not _CONFIG_FILE.exists():
        return {}
    try:
        data = json.loads(_CONFIG_FILE.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except (json.JSONDecodeError, OSError):
        return {}


def _config_from_raw(raw: dict[str, Any]) -> BusinessDayConfig:
    start = raw.get("business_day_start_time")
    end = raw.get("business_day_end_time")
    if not start or not end:
        return _defaults()
    try:
        return validate_business_day_times(str(start), str(end))
    except ValueError:
        return _defaults()


def get_business_day_config() -> BusinessDayConfig:
    with _LOCK:
        return _config_from_raw(_read_raw_unlocked())


def get_business_day_state() -> dict[str, Any]:
    cfg = get_business_day_config()
    raw = _read_raw_unlocked()
    return {
        "business_day_start_time": cfg.start_time_str,
        "business_day_end_time": cfg.end_time_str,
        "business_hours_note": cfg.hours_note(),
        "updated_at": raw.get("updated_at"),
        "updated_by_username": raw.get("updated_by_username"),
    }


def save_business_day_config(
    start_time: str,
    end_time: str,
    *,
    username: str | None = None,
) -> dict[str, Any]:
    cfg = validate_business_day_times(start_time, end_time)
    from datetime import datetime

    payload = {
        "business_day_start_time": cfg.start_time_str,
        "business_day_end_time": cfg.end_time_str,
        "updated_at": datetime.now().isoformat(timespec="seconds"),
        "updated_by_username": username,
    }
    with _LOCK:
        _ensure_data_dir()
        _CONFIG_FILE.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return get_business_day_state()
