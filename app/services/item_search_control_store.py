"""Admin-configurable item search settings (JSON, no paid search engine)."""

from __future__ import annotations

import json
import threading
from pathlib import Path
from typing import Any

_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
_FILE = _PROJECT_ROOT / "data" / "item_search_control.json"
_LOCK = threading.Lock()


def _defaults() -> dict[str, Any]:
    return {
        "min_chars": 2,
        "max_results": 10,
        "debounce_ms": 250,
        "fuzzy_enabled": True,
        "alias_enabled": True,
        "barcode_enabled": True,
        "notes": "",
    }


def get_settings() -> dict[str, Any]:
    data = dict(_defaults())
    with _LOCK:
        if _FILE.exists():
            try:
                raw = json.loads(_FILE.read_text(encoding="utf-8"))
                if isinstance(raw, dict):
                    data.update({k: raw[k] for k in data if k in raw})
            except (OSError, json.JSONDecodeError):
                pass
    data["min_chars"] = int(max(1, min(int(data["min_chars"] or 2), 5)))
    data["max_results"] = int(max(5, min(int(data["max_results"] or 10), 20)))
    data["debounce_ms"] = int(max(120, min(int(data["debounce_ms"] or 250), 800)))
    data["fuzzy_enabled"] = bool(data["fuzzy_enabled"])
    data["alias_enabled"] = bool(data["alias_enabled"])
    data["barcode_enabled"] = bool(data["barcode_enabled"])
    data["notes"] = str(data.get("notes") or "")[:300]
    return data


def update_settings(payload: dict[str, Any]) -> dict[str, Any]:
    current = get_settings()
    for key in _defaults():
        if key in payload and payload[key] is not None:
            current[key] = payload[key]
    _FILE.parent.mkdir(parents=True, exist_ok=True)
    with _LOCK:
        _FILE.write_text(json.dumps(current, indent=2), encoding="utf-8")
    return get_settings()
