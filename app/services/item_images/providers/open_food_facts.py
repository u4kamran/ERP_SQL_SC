"""Open Food Facts + related Open*Facts domains (barcode + modern name search)."""

from __future__ import annotations

import re
import time
from typing import Any, Optional
from urllib.parse import quote

import httpx

from app.services.item_images.providers.base import (
    IProductImageProvider,
    ImageCandidate,
    ItemSearchContext,
    ProductCandidate,
)

USER_AGENT = "AHSteelLabItemImages/1.0 (departmental-store-erp; contact=admin@local)"

BARCODE_HOSTS = (
    "https://world.openfoodfacts.org",
    "https://world.openbeautyfacts.org",
    "https://world.openproductsfacts.org",
)

MODERN_SEARCH = "https://search.openfoodfacts.org/search"


def _clean_barcode(raw: Optional[str]) -> Optional[str]:
    if not raw:
        return None
    digits = re.sub(r"\D+", "", str(raw).strip())
    if len(digits) < 8 or digits == "0" * len(digits):
        return None
    return digits


def _clean_title(title: str) -> str:
    """Strip size/qty noise but keep brand/product words for search."""
    t = re.sub(r"\s+", " ", (title or "").strip())
    t = re.sub(r"\b\d+\s*(ml|gm|g|kg|ltr|l|pcs|pc|pk|pack|sachet|sachets)\b", " ", t, flags=re.I)
    t = re.sub(r"\s+", " ", t).strip()
    return t[:120] or title[:120]


def _pick_image(product: dict[str, Any]) -> Optional[str]:
    for key in (
        "image_front_url",
        "image_url",
        "image_front_small_url",
        "image_small_url",
    ):
        url = (product.get(key) or "").strip()
        if url.startswith("http"):
            return url
    selected = product.get("selected_images") or {}
    front = (selected.get("front") or {}).get("display") or {}
    for size in ("xl", "l", "m", "s"):
        url = (front.get(size) or "").strip()
        if url.startswith("http"):
            return url
    return None


def _http_get_json(
    client: httpx.Client,
    url: str,
    *,
    params: dict[str, Any] | None = None,
    retries: int = 3,
) -> Any | None:
    for attempt in range(retries):
        try:
            resp = client.get(url, params=params)
            if resp.status_code == 200:
                return resp.json()
            if resp.status_code in (429, 503, 502):
                time.sleep(1.0 + attempt * 1.5)
                continue
            return None
        except Exception:
            if attempt >= retries - 1:
                return None
            time.sleep(0.8 + attempt)
    return None


class OpenFoodFactsProvider(IProductImageProvider):
    name = "open_food_facts"
    display_name = "Open Food Facts"
    priority = 90
    enabled = False

    def search(self, ctx: ItemSearchContext, *, timeout: float = 15.0) -> list[ProductCandidate]:
        if not self.enabled:
            return []
        legacy = self._search_legacy(ctx, timeout=timeout)
        return [
            ProductCandidate(
                provider=self.name,
                image_url=c.image_url,
                product_name=c.product_title,
                barcode=c.product_barcode,
                brand=c.product_brand,
                product_url=c.source_url,
                search_query=c.search_query,
                extras=c.extras,
            )
            for c in legacy
        ]

    def _search_legacy(self, ctx: ItemSearchContext, *, timeout: float = 15.0) -> list:
        results: list[ImageCandidate] = []
        barcode = _clean_barcode(ctx.barcodeid)
        title = (ctx.item_title or "").strip()
        headers = {"User-Agent": USER_AGENT, "Accept": "application/json"}

        with httpx.Client(timeout=timeout, headers=headers, follow_redirects=True) as client:
            if barcode:
                for host in BARCODE_HOSTS:
                    results.extend(self._by_barcode(client, ctx, barcode, host))
                    time.sleep(0.25)
                    if results:
                        break

            queries = self._search_queries(barcode, title)
            for query in queries:
                if len(results) >= 12:
                    break
                results.extend(self._by_modern_search(client, ctx, query))
                time.sleep(0.35)

            if len(results) < 3 and title:
                cleaned = _clean_title(title)
                if cleaned and cleaned.lower() != title.lower():
                    results.extend(self._by_modern_search(client, ctx, cleaned))
                    time.sleep(0.35)

            if len(results) < 2 and title:
                for host in ("https://world.openbeautyfacts.org", "https://world.openproductsfacts.org"):
                    results.extend(self._by_legacy_name(client, ctx, title, host))
                    time.sleep(0.5)

        return self._dedupe(results)[:12]

    def _search_queries(self, barcode: Optional[str], title: str) -> list[str]:
        queries: list[str] = []
        if barcode and title:
            queries.append(f"{barcode} {title}".strip())
        if title:
            queries.append(title)
        seen: set[str] = set()
        out: list[str] = []
        for q in queries:
            key = q.lower()
            if key in seen:
                continue
            seen.add(key)
            out.append(q[:120])
        return out

    def _by_barcode(
        self,
        client: httpx.Client,
        ctx: ItemSearchContext,
        barcode: str,
        host: str,
    ) -> list[ImageCandidate]:
        url = f"{host}/api/v2/product/{barcode}.json"
        data = _http_get_json(client, url)
        if not data or int(data.get("status") or 0) != 1:
            return []
        product = data.get("product") or {}
        image = _pick_image(product)
        if not image:
            return []
        title = (product.get("product_name") or product.get("generic_name") or "")[:200]
        brand = (product.get("brands") or "")[:120]
        source_host = host.replace("https://", "")
        return [
            ImageCandidate(
                image_url=image,
                source_url=f"{host}/product/{barcode}",
                source_name=self.name,
                search_query=barcode,
                product_title=title or None,
                product_brand=brand or None,
                product_barcode=barcode,
                extras={"host": source_host},
            )
        ]

    def _by_modern_search(
        self, client: httpx.Client, ctx: ItemSearchContext, query: str
    ) -> list[ImageCandidate]:
        data = _http_get_json(
            client,
            MODERN_SEARCH,
            params={
                "q": query[:120],
                "page_size": 8,
                "fields": "code,product_name,brands,image_front_url,image_url",
            },
        )
        if not data:
            return []
        hits = data.get("hits") or []
        out: list[ImageCandidate] = []
        for hit in hits:
            image = (hit.get("image_front_url") or hit.get("image_url") or "").strip()
            if not image.startswith("http"):
                continue
            code = str(hit.get("code") or "") or None
            title = (hit.get("product_name") or "")[:200] or None
            brands = hit.get("brands")
            brand = None
            if isinstance(brands, list) and brands:
                brand = str(brands[0])[:120]
            elif isinstance(brands, str):
                brand = brands[:120]
            out.append(
                ImageCandidate(
                    image_url=image,
                    source_url=(
                        f"https://world.openfoodfacts.org/product/{code}" if code else MODERN_SEARCH
                    ),
                    source_name=self.name,
                    search_query=query[:200],
                    product_title=title,
                    product_brand=brand,
                    product_barcode=code,
                )
            )
        return out

    def _by_legacy_name(
        self, client: httpx.Client, ctx: ItemSearchContext, query: str, host: str
    ) -> list[ImageCandidate]:
        q = quote(query[:120])
        url = f"{host}/cgi/search.pl?search_terms={q}&search_simple=1&action=process&json=1&page_size=6"
        data = _http_get_json(client, url)
        if not data:
            return []
        out: list[ImageCandidate] = []
        for product in data.get("products") or []:
            image = _pick_image(product)
            if not image:
                continue
            code = str(product.get("code") or "") or None
            title = (product.get("product_name") or "")[:200] or None
            brand = (product.get("brands") or "")[:120] or None
            out.append(
                ImageCandidate(
                    image_url=image,
                    source_url=f"{host}/product/{code}" if code else url,
                    source_name=self.name,
                    search_query=query[:200],
                    product_title=title,
                    product_brand=brand,
                    product_barcode=code,
                )
            )
        return out

    @staticmethod
    def _dedupe(candidates: list[ImageCandidate]) -> list[ImageCandidate]:
        seen: set[str] = set()
        unique: list[ImageCandidate] = []
        for c in candidates:
            key = c.image_url.strip()
            if not key or key in seen:
                continue
            seen.add(key)
            unique.append(c)
        return unique
