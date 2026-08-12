"""JSON-backed confirmed WhatsApp / offline chat orders."""

from __future__ import annotations

import json
import threading
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
_DATA_DIR = _PROJECT_ROOT / "data"
_ORDERS_FILE = _DATA_DIR / "whatsapp_orders.json"
_LOCK = threading.Lock()
_MAX_ORDERS = 1000
_PK_TZ = ZoneInfo("Asia/Karachi")


def _now() -> datetime:
    """Business local time (Pakistan)."""
    return datetime.now(_PK_TZ)


def _ensure() -> None:
    _DATA_DIR.mkdir(parents=True, exist_ok=True)


def _load_unlocked() -> dict[str, Any]:
    _ensure()
    if not _ORDERS_FILE.exists():
        return {"orders": {}}
    try:
        raw = json.loads(_ORDERS_FILE.read_text(encoding="utf-8"))
        orders = raw.get("orders") if isinstance(raw, dict) else {}
        if not isinstance(orders, dict):
            orders = {}
        return {"orders": orders}
    except (json.JSONDecodeError, OSError):
        return {"orders": {}}


def _save_unlocked(data: dict[str, Any]) -> None:
    _ensure()
    orders = data.get("orders") or {}
    if len(orders) > _MAX_ORDERS:
        ordered = sorted(
            orders.items(),
            key=lambda item: item[1].get("created_at") or "",
            reverse=True,
        )
        orders = dict(ordered[:_MAX_ORDERS])
        data["orders"] = orders
    _ORDERS_FILE.write_text(
        json.dumps(data, indent=2, default=str),
        encoding="utf-8",
    )


def next_order_no() -> str:
    stamp = _now().strftime("%Y%m%d")
    suffix = uuid.uuid4().hex[:4].upper()
    return f"WO-{stamp}-{suffix}"


def save_order(order: dict[str, Any]) -> dict[str, Any]:
    with _LOCK:
        data = _load_unlocked()
        order_id = order.get("order_id") or str(uuid.uuid4())
        order["order_id"] = order_id
        order["updated_at"] = _now().isoformat()
        if not order.get("created_at"):
            order["created_at"] = order["updated_at"]
        data["orders"][order_id] = order
        _save_unlocked(data)
        return dict(order)


def list_orders(status: str | None = None, limit: int = 100) -> list[dict[str, Any]]:
    with _LOCK:
        data = _load_unlocked()
        items = list(data["orders"].values())
    if status:
        items = [item for item in items if item.get("status") == status]
    items.sort(key=lambda item: item.get("created_at") or "", reverse=True)
    return items[:limit]


def get_order(order_id: str) -> dict[str, Any] | None:
    with _LOCK:
        data = _load_unlocked()
        row = data["orders"].get(order_id)
        return dict(row) if row else None


def find_by_order_no(order_no: str) -> dict[str, Any] | None:
    needle = (order_no or "").strip().upper()
    if not needle:
        return None
    with _LOCK:
        data = _load_unlocked()
        for row in data["orders"].values():
            if str(row.get("order_no") or "").strip().upper() == needle:
                return dict(row)
    return None


def find_by_mobile(phone: str, *, limit: int = 5) -> list[dict[str, Any]]:
    digits = "".join(ch for ch in (phone or "") if ch.isdigit())
    if len(digits) < 10:
        return []
    key = digits[-10:]
    with _LOCK:
        data = _load_unlocked()
        items = []
        for row in data["orders"].values():
            mobile = "".join(
                ch
                for ch in str(row.get("customer_mobile") or row.get("phone") or "")
                if ch.isdigit()
            )
            if mobile and mobile[-10:] == key:
                items.append(dict(row))
    items.sort(key=lambda item: item.get("created_at") or "", reverse=True)
    return items[:limit]


def update_order_status(order_id: str, status: str) -> dict[str, Any]:
    with _LOCK:
        data = _load_unlocked()
        order = data["orders"].get(order_id)
        if not order:
            raise KeyError(order_id)
        order["status"] = status
        order["updated_at"] = _now().isoformat()
        data["orders"][order_id] = order
        _save_unlocked(data)
        return dict(order)


def pending_count() -> int:
    with _LOCK:
        data = _load_unlocked()
        return sum(
            1
            for item in data["orders"].values()
            if item.get("status") in {"pending", "confirmed", "preparing"}
        )
