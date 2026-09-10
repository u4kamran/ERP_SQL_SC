"""UPCitemdb provider (optional barcode lookup fallback)."""

from __future__ import annotations

import re
from typing import Optional

import httpx

from app.config.settings import settings
from app.services.item_images.providers.base import (
    IProductImageProvider,
    ItemSearchContext,
    ProductCandidate,
)


def _clean_barcode(raw: Optional[str]) -> Optional[str]:
    if not raw:
        return None
    digits = re.sub(r"\D+", "", str(raw).strip())
    if len(digits) < 8:
        return None
    return digits


class UpcItemDbProvider(IProductImageProvider):
    name = "upcitemdb"
    display_name = "UPCitemdb"
    priority = 80
    enabled = False

    def search(self, ctx: ItemSearchContext, *, timeout: float = 15.0) -> list[ProductCandidate]:
        if not self.enabled:
            return []
        token = (settings.upcitemdb_api_key.get_secret_value() if settings.upcitemdb_api_key else "") or ""
        barcode = _clean_barcode(ctx.barcodeid)
        if not barcode:
            return []

        headers = {"Accept": "application/json", "User-Agent": "AHSteelLabItemImages/1.0"}
        if token:
            headers["user_key"] = token
            headers["key_type"] = "3scale"
            url = f"https://api.upcitemdb.com/prod/v1/lookup?upc={barcode}"
        else:
            url = f"https://api.upcitemdb.com/prod/trial/lookup?upc={barcode}"

        try:
            with httpx.Client(timeout=timeout, headers=headers, follow_redirects=True) as client:
                resp = client.get(url)
                if resp.status_code != 200:
                    return []
                data = resp.json()
        except Exception:
            return []

        out: list[ProductCandidate] = []
        for item in data.get("items") or []:
            images = item.get("images") or []
            title = (item.get("title") or "")[:200] or None
            brand = (item.get("brand") or "")[:120] or None
            category = (item.get("category") or "")[:120] or None
            offers = item.get("offers") or []
            source_url = offers[0].get("link") if offers and isinstance(offers[0], dict) else f"https://www.upcitemdb.com/upc/{barcode}"
            for img in images[:3]:
                if not isinstance(img, str) or not img.startswith("http"):
                    continue
                out.append(
                    ProductCandidate(
                        provider=self.name,
                        image_url=img,
                        product_name=title,
                        barcode=barcode,
                        brand=brand,
                        category=category,
                        product_url=source_url,
                        search_query=barcode,
                        search_level=1,
                    )
                )
        return out[:8]
