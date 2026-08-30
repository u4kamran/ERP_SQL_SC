"""Naheed.pk provider via public storefront GraphQL (not /catalogsearch scraping)."""

from __future__ import annotations

import httpx

from app.services.item_images.query_builder import SearchQuery, build_search_queries
from app.services.item_images.providers.base import IProductImageProvider, ItemSearchContext, ProductCandidate

GRAPHQL_URL = "https://www.naheed.pk/graphql"
USER_AGENT = "AHSteelLabItemImages/1.0 (ERP product lookup; contact=admin@local)"

PRODUCTS_QUERY = """
query ($q: String!, $pageSize: Int!) {
  products(search: $q, pageSize: $pageSize) {
    items {
      sku
      name
      url_key
      image { url label }
    }
  }
}
"""


class NaheedProvider(IProductImageProvider):
    name = "naheed"
    display_name = "Naheed"
    priority = 10

    def search(self, ctx: ItemSearchContext, *, timeout: float = 15.0) -> list[ProductCandidate]:
        if not self.enabled:
            return []

        headers = {
            "User-Agent": USER_AGENT,
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        queries = build_search_queries(ctx)
        results: list[ProductCandidate] = []
        seen_urls: set[str] = set()

        with httpx.Client(timeout=timeout, headers=headers, follow_redirects=True) as client:
            for sq in queries:
                if len(results) >= 10:
                    break
                payload = {
                    "query": PRODUCTS_QUERY,
                    "variables": {"q": sq.query, "pageSize": 8},
                }
                try:
                    resp = client.post(GRAPHQL_URL, json=payload)
                    if resp.status_code != 200:
                        continue
                    data = resp.json()
                except Exception:
                    continue
                items = ((data.get("data") or {}).get("products") or {}).get("items") or []
                for item in items:
                    image = ((item.get("image") or {}).get("url") or "").strip()
                    if not image.startswith("http") or image in seen_urls:
                        continue
                    seen_urls.add(image)
                    url_key = (item.get("url_key") or "").strip()
                    product_url = f"https://www.naheed.pk/{url_key}" if url_key else None
                    results.append(
                        ProductCandidate(
                            provider=self.name,
                            image_url=image,
                            product_name=(item.get("name") or "")[:200] or None,
                            barcode=None,
                            brand=None,
                            category=None,
                            product_url=product_url,
                            search_query=sq.query[:200],
                            search_level=sq.level,
                            availability="in_stock",
                            extras={"sku": item.get("sku"), "query_label": sq.label},
                        )
                    )
        return results[:12]
