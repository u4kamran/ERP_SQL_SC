"""Persist database sync run history."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

_DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data"
_STATE_FILE = _DATA_DIR / "db_sync_state.json"


def load_state() -> dict[str, Any]:
    if not _STATE_FILE.exists():
        return {}
    try:
        return json.loads(_STATE_FILE.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}


def save_state(state: dict[str, Any]) -> None:
    _DATA_DIR.mkdir(parents=True, exist_ok=True)
    _STATE_FILE.write_text(json.dumps(state, indent=2), encoding="utf-8")


def record_run(
    *,
    status: str,
    message: str,
    details: dict[str, Any] | None = None,
) -> dict[str, Any]:
    state = load_state()
    state["last_run"] = datetime.now().isoformat(timespec="seconds")
    state["last_status"] = status
    state["last_message"] = message
    if details:
        state["last_details"] = details
    save_state(state)
    return state
