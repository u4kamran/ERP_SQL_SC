"""Local Gemini usage meter (tokens + estimated USD).

Google does not expose remaining prepaid credits via API, so:
- we record usageMetadata from each successful generateContent call
- admin can set a prepaid budget USD to estimate remaining dollars
"""

from __future__ import annotations

import json
import threading
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
_DATA_DIR = _PROJECT_ROOT / "data"
_USAGE_FILE = _DATA_DIR / "gemini_usage.json"
_LOCK = threading.Lock()
_MAX_EVENTS = 2000

# gemini-3.1-flash-lite (paid) — USD per 1M tokens
_RATES = {
    "voice": {"input": 0.50, "output": 1.50},  # audio input
    "vision": {"input": 0.25, "output": 1.50},  # image/text
    "text": {"input": 0.25, "output": 1.50},
    "default": {"input": 0.25, "output": 1.50},
}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _ensure() -> None:
    _DATA_DIR.mkdir(parents=True, exist_ok=True)


def _default() -> dict[str, Any]:
    return {
        "budget_usd": 0.0,
        "budget_note": "",
        "budget_updated_at": "",
        "events": [],
    }


def _load_unlocked() -> dict[str, Any]:
    _ensure()
    if not _USAGE_FILE.exists():
        return _default()
    try:
        raw = json.loads(_USAGE_FILE.read_text(encoding="utf-8"))
        if not isinstance(raw, dict):
            return _default()
        data = _default()
        data.update(raw)
        if not isinstance(data.get("events"), list):
            data["events"] = []
        return data
    except (json.JSONDecodeError, OSError):
        return _default()


def _save_unlocked(data: dict[str, Any]) -> None:
    _ensure()
    events = data.get("events") or []
    if len(events) > _MAX_EVENTS:
        data["events"] = events[-_MAX_EVENTS:]
    _USAGE_FILE.write_text(
        json.dumps(data, indent=2, default=str),
        encoding="utf-8",
    )


def estimate_cost_usd(
    *,
    feature: str,
    prompt_tokens: int,
    output_tokens: int,
) -> float:
    rates = _RATES.get(feature) or _RATES["default"]
    prompt = max(0, int(prompt_tokens or 0))
    output = max(0, int(output_tokens or 0))
    cost = (prompt / 1_000_000.0) * float(rates["input"])
    cost += (output / 1_000_000.0) * float(rates["output"])
    return round(cost, 8)


def parse_usage_metadata(body: dict[str, Any] | None) -> dict[str, int]:
    meta = (body or {}).get("usageMetadata") or (body or {}).get("usage_metadata") or {}
    prompt = int(meta.get("promptTokenCount") or meta.get("prompt_token_count") or 0)
    output = int(
        meta.get("candidatesTokenCount") or meta.get("candidates_token_count") or 0
    )
    thoughts = int(
        meta.get("thoughtsTokenCount") or meta.get("thoughts_token_count") or 0
    )
    total = int(meta.get("totalTokenCount") or meta.get("total_token_count") or 0)
    if not total:
        total = prompt + output + thoughts
    return {
        "prompt_tokens": prompt,
        "output_tokens": output + thoughts,
        "total_tokens": total,
    }


def record_usage(
    *,
    feature: str,
    model: str,
    body: dict[str, Any] | None = None,
    prompt_tokens: int | None = None,
    output_tokens: int | None = None,
    ok: bool = True,
    detail: str = "",
) -> dict[str, Any]:
    """Persist one Gemini call. Safe to call from request threads."""
    parsed = parse_usage_metadata(body) if body is not None else {
        "prompt_tokens": int(prompt_tokens or 0),
        "output_tokens": int(output_tokens or 0),
        "total_tokens": int(prompt_tokens or 0) + int(output_tokens or 0),
    }
    feat = (feature or "default").strip().lower() or "default"
    cost = estimate_cost_usd(
        feature=feat,
        prompt_tokens=parsed["prompt_tokens"],
        output_tokens=parsed["output_tokens"],
    )
    event = {
        "id": str(uuid.uuid4()),
        "created_at": _now(),
        "feature": feat,
        "model": (model or "").strip() or "gemini-3.1-flash-lite",
        "ok": bool(ok),
        "prompt_tokens": parsed["prompt_tokens"],
        "output_tokens": parsed["output_tokens"],
        "total_tokens": parsed["total_tokens"],
        "estimated_cost_usd": cost,
        "detail": (detail or "")[:200],
    }
    with _LOCK:
        data = _load_unlocked()
        data["events"].append(event)
        _save_unlocked(data)
    return event


def set_budget(budget_usd: float, note: str = "") -> dict[str, Any]:
    with _LOCK:
        data = _load_unlocked()
        data["budget_usd"] = max(0.0, float(budget_usd or 0))
        data["budget_note"] = (note or "").strip()[:200]
        data["budget_updated_at"] = _now()
        _save_unlocked(data)
        return summary_unlocked(data)


def summary(*, limit_recent: int = 30) -> dict[str, Any]:
    with _LOCK:
        return summary_unlocked(_load_unlocked(), limit_recent=limit_recent)


def summary_unlocked(data: dict[str, Any], *, limit_recent: int = 30) -> dict[str, Any]:
    events = list(data.get("events") or [])
    ok_events = [e for e in events if e.get("ok")]
    prompt = sum(int(e.get("prompt_tokens") or 0) for e in ok_events)
    output = sum(int(e.get("output_tokens") or 0) for e in ok_events)
    total = sum(int(e.get("total_tokens") or 0) for e in ok_events)
    spent = round(sum(float(e.get("estimated_cost_usd") or 0) for e in ok_events), 6)
    budget = float(data.get("budget_usd") or 0)
    remaining = round(budget - spent, 6) if budget > 0 else None

    by_feature: dict[str, dict[str, Any]] = {}
    for e in ok_events:
        key = str(e.get("feature") or "default")
        row = by_feature.setdefault(
            key,
            {
                "feature": key,
                "calls": 0,
                "prompt_tokens": 0,
                "output_tokens": 0,
                "total_tokens": 0,
                "estimated_cost_usd": 0.0,
            },
        )
        row["calls"] += 1
        row["prompt_tokens"] += int(e.get("prompt_tokens") or 0)
        row["output_tokens"] += int(e.get("output_tokens") or 0)
        row["total_tokens"] += int(e.get("total_tokens") or 0)
        row["estimated_cost_usd"] = round(
            float(row["estimated_cost_usd"]) + float(e.get("estimated_cost_usd") or 0),
            6,
        )

    # Today (UTC date prefix)
    today = _now()[:10]
    today_events = [e for e in ok_events if str(e.get("created_at") or "").startswith(today)]
    today_tokens = sum(int(e.get("total_tokens") or 0) for e in today_events)
    today_cost = round(
        sum(float(e.get("estimated_cost_usd") or 0) for e in today_events), 6
    )

    recent = list(reversed(events[-limit_recent:]))
    return {
        "model": "gemini-3.1-flash-lite",
        "budget_usd": budget,
        "budget_note": data.get("budget_note") or "",
        "budget_updated_at": data.get("budget_updated_at") or "",
        "spent_usd": spent,
        "remaining_usd": remaining,
        "calls_total": len(ok_events),
        "calls_failed": sum(1 for e in events if not e.get("ok")),
        "prompt_tokens": prompt,
        "output_tokens": output,
        "total_tokens": total,
        "today_calls": len(today_events),
        "today_tokens": today_tokens,
        "today_cost_usd": today_cost,
        "by_feature": sorted(
            by_feature.values(),
            key=lambda r: r["estimated_cost_usd"],
            reverse=True,
        ),
        "recent": recent,
        "rates": _RATES,
        "note": (
            "Remaining $ is estimated from the budget you set here. "
            "Google does not expose live prepaid balance via API — "
            "confirm exact balance in AI Studio Billing."
        ),
        "billing_url": "https://aistudio.google.com/",
    }
