"""Voice search abuse controls + audit log (mobile, text, IP, cost)."""

from __future__ import annotations

import json
import re
import threading
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.services.gemini_usage_store import estimate_cost_usd, parse_usage_metadata

_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
_DATA_DIR = _PROJECT_ROOT / "data"
_FILE = _DATA_DIR / "voice_search_control.json"
_LOCK = threading.Lock()
_MAX_EVENTS = 5000


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _now_iso() -> str:
    return _now().isoformat()


def _today() -> str:
    return _now().strftime("%Y-%m-%d")


def _ensure() -> None:
    _DATA_DIR.mkdir(parents=True, exist_ok=True)


def _default_settings() -> dict[str, Any]:
    return {
        "cloud_voice_enabled": True,
        "guest_voice_enabled": True,
        "whatsapp_voice_enabled": True,
        "require_mobile": True,
        "daily_limit_per_mobile": 10,
        "minute_limit_per_ip": 5,
        "daily_budget_usd": 2.0,
        "max_clip_seconds": 15,
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
        settings = dict(_default_settings())
        settings.update(raw.get("settings") or {})
        data["settings"] = settings
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


def normalize_mobile(raw: str) -> str:
    digits = re.sub(r"\D", "", raw or "")
    if not digits:
        return ""
    if digits.startswith("92") and len(digits) >= 12:
        return f"0{digits[2:12]}"
    if len(digits) >= 10:
        return f"0{digits[-10:]}" if not digits.startswith("0") else digits[-11:]
    return digits


def get_settings() -> dict[str, Any]:
    with _LOCK:
        return dict(_load_unlocked()["settings"])


def update_settings(payload: dict[str, Any]) -> dict[str, Any]:
    with _LOCK:
        data = _load_unlocked()
        settings = dict(data["settings"])
        for key in _default_settings():
            if key not in payload:
                continue
            value = payload[key]
            if key in {
                "cloud_voice_enabled",
                "guest_voice_enabled",
                "whatsapp_voice_enabled",
                "require_mobile",
            }:
                settings[key] = bool(value)
            elif key in {
                "daily_limit_per_mobile",
                "minute_limit_per_ip",
                "max_clip_seconds",
            }:
                settings[key] = max(0, int(value or 0))
            elif key == "daily_budget_usd":
                settings[key] = max(0.0, float(value or 0))
            elif key == "notes":
                settings[key] = str(value or "")[:300]
        data["settings"] = settings
        _save_unlocked(data)
        return dict(settings)


def _count_ok_today_mobile(events: list[dict[str, Any]], mobile: str) -> int:
    day = _today()
    key = normalize_mobile(mobile)
    if not key:
        return 0
    return sum(
        1
        for e in events
        if e.get("status") == "ok"
        and str(e.get("created_at") or "").startswith(day)
        and normalize_mobile(str(e.get("mobile") or "")) == key
    )


def _count_ip_last_minute(events: list[dict[str, Any]], ip: str) -> int:
    if not ip:
        return 0
    cutoff = _now().timestamp() - 60
    count = 0
    for e in events:
        if str(e.get("ip") or "") != ip:
            continue
        try:
            ts = datetime.fromisoformat(str(e.get("created_at") or "").replace("Z", "+00:00"))
            if ts.timestamp() >= cutoff:
                count += 1
        except ValueError:
            continue
    return count


def _spent_today_usd(events: list[dict[str, Any]]) -> float:
    day = _today()
    return round(
        sum(
            float(e.get("estimated_cost_usd") or 0)
            for e in events
            if e.get("status") == "ok" and str(e.get("created_at") or "").startswith(day)
        ),
        6,
    )


def check_allowed(
    *,
    channel: str,
    mobile: str = "",
    ip: str = "",
) -> tuple[bool, str]:
    """Return (allowed, reason). reason is empty when allowed."""
    settings = get_settings()
    if not settings.get("cloud_voice_enabled", True):
        return False, "Cloud voice is disabled by admin."
    ch = (channel or "guest").lower()
    if ch == "guest" and not settings.get("guest_voice_enabled", True):
        return False, "Guest web voice is disabled by admin."
    if ch == "whatsapp" and not settings.get("whatsapp_voice_enabled", True):
        return False, "WhatsApp voice is disabled by admin."

    mobile_key = normalize_mobile(mobile)
    if settings.get("require_mobile", True) and ch == "guest" and not mobile_key:
        return False, "Enter your mobile number before using voice search."

    with _LOCK:
        events = list(_load_unlocked().get("events") or [])

    budget = float(settings.get("daily_budget_usd") or 0)
    if budget > 0:
        spent = _spent_today_usd(events)
        if spent >= budget:
            return False, "Daily voice budget reached. Please type your search."

    daily_limit = int(settings.get("daily_limit_per_mobile") or 0)
    if daily_limit > 0 and mobile_key:
        used = _count_ok_today_mobile(events, mobile_key)
        if used >= daily_limit:
            return False, (
                f"Daily voice limit reached ({daily_limit}/day for this mobile). "
                "Please type your search."
            )

    minute_limit = int(settings.get("minute_limit_per_ip") or 0)
    if minute_limit > 0 and ip:
        used_ip = _count_ip_last_minute(events, ip)
        if used_ip >= minute_limit:
            return False, "Too many voice requests. Please wait a minute and try again."

    return True, ""


def record_event(
    *,
    channel: str,
    mobile: str = "",
    ip: str = "",
    search_text: str = "",
    status: str = "ok",
    block_reason: str = "",
    model: str = "gemini-3.1-flash-lite",
    body: dict[str, Any] | None = None,
    detail: str = "",
    user_agent: str = "",
) -> dict[str, Any]:
    usage = parse_usage_metadata(body) if body else {
        "prompt_tokens": 0,
        "output_tokens": 0,
        "total_tokens": 0,
    }
    feature = "voice"
    cost = (
        estimate_cost_usd(
            feature=feature,
            prompt_tokens=usage["prompt_tokens"],
            output_tokens=usage["output_tokens"],
        )
        if status == "ok"
        else 0.0
    )
    event = {
        "id": str(uuid.uuid4()),
        "created_at": _now_iso(),
        "channel": (channel or "guest").lower(),
        "mobile": normalize_mobile(mobile),
        "ip": (ip or "")[:64],
        "search_text": (search_text or "").strip()[:300],
        "status": status,
        "block_reason": (block_reason or "").strip()[:240],
        "model": (model or "gemini-3.1-flash-lite")[:80],
        "prompt_tokens": usage["prompt_tokens"],
        "output_tokens": usage["output_tokens"],
        "total_tokens": usage["total_tokens"],
        "estimated_cost_usd": cost,
        "detail": (detail or "").strip()[:240],
        "user_agent": (user_agent or "")[:180],
    }
    with _LOCK:
        data = _load_unlocked()
        data["events"].append(event)
        _save_unlocked(data)
    return event


def dashboard(*, mobile: str = "", limit: int = 100) -> dict[str, Any]:
    with _LOCK:
        data = _load_unlocked()
        settings = dict(data["settings"])
        events = list(data.get("events") or [])

    mobile_filter = normalize_mobile(mobile)
    if mobile_filter:
        events_view = [
            e
            for e in events
            if normalize_mobile(str(e.get("mobile") or "")) == mobile_filter
        ]
    else:
        events_view = events

    day = _today()
    today = [e for e in events if str(e.get("created_at") or "").startswith(day)]
    today_ok = [e for e in today if e.get("status") == "ok"]
    today_blocked = [e for e in today if e.get("status") == "blocked"]
    today_failed = [e for e in today if e.get("status") == "failed"]

    # Top mobiles today (misuse finder)
    by_mobile: dict[str, dict[str, Any]] = {}
    for e in today:
        key = normalize_mobile(str(e.get("mobile") or "")) or "(no mobile)"
        row = by_mobile.setdefault(
            key,
            {
                "mobile": key,
                "ok": 0,
                "blocked": 0,
                "failed": 0,
                "tokens": 0,
                "cost_usd": 0.0,
                "last_text": "",
                "last_at": "",
            },
        )
        st = e.get("status")
        if st == "ok":
            row["ok"] += 1
        elif st == "blocked":
            row["blocked"] += 1
        else:
            row["failed"] += 1
        row["tokens"] += int(e.get("total_tokens") or 0)
        row["cost_usd"] = round(float(row["cost_usd"]) + float(e.get("estimated_cost_usd") or 0), 6)
        if e.get("search_text"):
            row["last_text"] = e.get("search_text")
        row["last_at"] = e.get("created_at") or row["last_at"]

    top_mobiles = sorted(
        by_mobile.values(),
        key=lambda r: (r["ok"] + r["blocked"] + r["failed"], r["cost_usd"]),
        reverse=True,
    )[:30]

    recent = list(reversed(events_view[-max(1, min(limit, 500)) :]))
    spent_today = _spent_today_usd(events)
    budget = float(settings.get("daily_budget_usd") or 0)
    return {
        "settings": settings,
        "today": {
            "date": day,
            "ok": len(today_ok),
            "blocked": len(today_blocked),
            "failed": len(today_failed),
            "tokens": sum(int(e.get("total_tokens") or 0) for e in today_ok),
            "spent_usd": spent_today,
            "budget_usd": budget,
            "remaining_usd": round(budget - spent_today, 6) if budget > 0 else None,
        },
        "top_mobiles": top_mobiles,
        "recent": recent,
        "totals": {
            "events": len(events),
            "ok": sum(1 for e in events if e.get("status") == "ok"),
            "blocked": sum(1 for e in events if e.get("status") == "blocked"),
            "failed": sum(1 for e in events if e.get("status") == "failed"),
        },
    }
