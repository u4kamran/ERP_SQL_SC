"""Promotion message templates and company links."""

from __future__ import annotations

import json
import threading
from pathlib import Path
from typing import Any

from app.config.settings import settings
from app.schemas.promotion_hub import PromotionTemplate

_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
_DATA_DIR = _PROJECT_ROOT / "data"
_TEMPLATES_FILE = _DATA_DIR / "promotion_templates.json"
_LOCK = threading.Lock()

_DEFAULT_TEMPLATES: list[dict[str, Any]] = [
    {
        "id": "sale",
        "name": "Sale & Offers",
        "subject": "Special offers at {company}",
        "message": "Assalam-o-Alaikum {name}!\n\nVisit us for latest steel products and special prices.\n\n{link}\n\n{company}",
        "link": "",
    },
    {
        "id": "price-scan",
        "name": "Check Price Online",
        "subject": "Check prices instantly — {company}",
        "message": "Hi {name},\n\nScan any barcode to check price online:\n{link}\n\nThank you,\n{company}",
        "link": "",
    },
    {
        "id": "new-arrival",
        "name": "New Arrivals",
        "subject": "New stock arrived — {company}",
        "message": "Dear {name},\n\nNew items have arrived at our store. Visit today or contact us on WhatsApp.\n\n{link}\n\n{company}",
        "link": "",
    },
    {
        "id": "follow-social",
        "name": "Follow Us on Social Media",
        "subject": "Stay connected with {company}",
        "message": "Hi {name},\n\nFollow us for daily updates, offers and new products:\n{link}\n\n{company}",
        "link": "",
    },
]


def _ensure_data_dir() -> None:
    _DATA_DIR.mkdir(parents=True, exist_ok=True)


def load_templates() -> list[PromotionTemplate]:
    with _LOCK:
        _ensure_data_dir()
        if not _TEMPLATES_FILE.exists():
            data = {"templates": _DEFAULT_TEMPLATES}
            _TEMPLATES_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")
        try:
            raw = json.loads(_TEMPLATES_FILE.read_text(encoding="utf-8"))
            items = raw.get("templates") or _DEFAULT_TEMPLATES
        except (json.JSONDecodeError, OSError):
            items = _DEFAULT_TEMPLATES

    base = settings.base_url.rstrip("/")
    guest_url = f"{base}/guest/scan"
    templates: list[PromotionTemplate] = []
    for item in items:
        tpl = PromotionTemplate(**item)
        if tpl.id == "price-scan" and not tpl.link:
            tpl = tpl.model_copy(update={"link": guest_url})
        templates.append(tpl)
    return templates


def company_links() -> dict[str, str]:
    base = settings.base_url.rstrip("/")
    return {
        "guest_price": f"{base}/guest/scan",
        "company_website": "https://ahsteellab.com",
        "erp_login": f"{base}/login",
        "company_name": settings.company_name or settings.app_name,
    }
