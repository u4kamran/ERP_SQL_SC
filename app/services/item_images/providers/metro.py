"""METRO Pakistan provider via public storefront Typesense search API."""

from __future__ import annotations

import httpx

from app.services.item_images.providers.base import IProductImageProvider, ItemSearchContext, ProductCandidate
from app.services.item_images.providers.metro_auth import METRO_API_BASE, METRO_ORIGIN, metro_auth_headers
from app.services.item_images.query_builder import build_search_queries

USER_AGENT = "AHSteelLabItemImages/1.0 (ERP product lookup; contact=admin@local)"
DEFAULT_STORE_IDS = ("10", "27")
SEARCH_ENDPOINT = "t_search"


class MetroProvider(IProductImageProvider):
    name = "metro"
    display_name = "METRO Pakistan"
    priority = 20

    def search(self, ctx: ItemSearchContext, *, timeout: float = 15.0) -> list[ProductCandidate]:
        if not self.enabled:
            return []

        headers = {
            "User-Agent": USER_AGENT,
            **metro_auth_headers("get", SEARCH_ENDPOINT),
        }
        queries = build_search_queries(ctx)
        results: list[ProductCandidate] = []
        seen_urls: set[str] = set()

        with httpx.Client(timeout=timeout, headers=headers, follow_redirects=True) as client:
            for sq in queries:
                if len(results) >= 10:
                    break
                for store_id in DEFAULT_STORE_IDS:
                    if len(results) >= 10:
                        break
                    params = {
                        "q": sq.query,
                        "query_by": "product_name,brand_name,description",
                        "filter_by": f"storeId:{store_id}",
                    }
                    try:
                        resp = client.get(
                            f"{METRO_API_BASE}/api/read/{SEARCH_ENDPOINT}",
                            params=params,
                        )
                        if resp.status_code != 200:
                            continue
                        payload = resp.json()
                    except Exception:
                        continue
                    if not payload.get("success"):
                        continue
                    for doc in payload.get("documents") or []:
                        image = (doc.get("url") or doc.get("s3_url") or "").strip()
                        if not image.startswith("http") or image in seen_urls:
                            continue
                        seen_urls.add(image)
                        product_id = doc.get("id")
                        product_url = (
                            f"{METRO_ORIGIN}/product/{product_id}" if product_id is not None else None
                        )
                        results.append(
                            ProductCandidate(
                                provider=self.name,
                                image_url=image,
                                product_name=(doc.get("product_name") or "")[:200] or None,
                                barcode=(str(doc.get("product_code_app")).strip()[:50] or None)
                                if doc.get("product_code_app")
                                else None,
                                brand=(doc.get("brand_name") or "")[:120] or None,
                                category=(doc.get("tier3Name") or doc.get("tier2Name") or "")[:120] or None,
                                product_url=product_url,
                                search_query=sq.query[:200],
                                search_level=sq.level,
                                availability="in_stock"
                                if int(doc.get("available_stock") or 0) > 0
                                else "out_of_stock",
                                extras={
                                    "store_id": store_id,
                                    "metro_id": product_id,
                                    "query_label": sq.label,
                                },
                            )
                        )
                        if len(results) >= 10:
                            break
        return results[:12]
