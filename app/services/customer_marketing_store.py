"""Persist marketing contact links (email, social media) per CUST_SMS customer."""

from __future__ import annotations

import json
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.schemas.customer_contacts import CustomerMarketingLinks

_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
_DATA_DIR = _PROJECT_ROOT / "data"
_STORE_FILE = _DATA_DIR / "customer_marketing_contacts.json"
_LOCK = threading.Lock()


def contact_key_for_sms(cust_sms_id: int) -> str:
    return f"sms:{cust_sms_id}"


def _ensure_data_dir() -> None:
    _DATA_DIR.mkdir(parents=True, exist_ok=True)


def _read_unlocked() -> dict[str, Any]:
    _ensure_data_dir()
    if not _STORE_FILE.exists():
        return {"contacts": {}}
    try:
        data = json.loads(_STORE_FILE.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            return {"contacts": {}}
        data.setdefault("contacts", {})
        return data
    except (json.JSONDecodeError, OSError):
        return {"contacts": {}}


def load_all() -> dict[str, CustomerMarketingLinks]:
    with _LOCK:
        raw = _read_unlocked().get("contacts") or {}
    result: dict[str, CustomerMarketingLinks] = {}
    for key, value in raw.items():
        if isinstance(value, dict):
            result[str(key)] = CustomerMarketingLinks(**value)
    return result


def get_links(contact_key: str) -> CustomerMarketingLinks:
    all_links = load_all()
    return all_links.get(contact_key, CustomerMarketingLinks())


def save_links(contact_key: str, links: CustomerMarketingLinks) -> CustomerMarketingLinks:
    with _LOCK:
        data = _read_unlocked()
        contacts = data.setdefault("contacts", {})
        payload = links.model_dump()
        payload["updated_at"] = datetime.now(timezone.utc).isoformat()
        contacts[contact_key] = payload
        _STORE_FILE.write_text(json.dumps(data, indent=2, default=str), encoding="utf-8")
    return links
