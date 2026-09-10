"""Reusable search query builder (levels 1–4)."""

from __future__ import annotations

import re
from dataclasses import dataclass

from app.services.item_images.normalization import normalize_search_text
from app.services.item_images.providers.base import ItemSearchContext


@dataclass(frozen=True)
class SearchQuery:
    level: int
    query: str
    label: str


def _clean_barcode(raw: str | None) -> str | None:
    if not raw:
        return None
    digits = re.sub(r"\D+", "", str(raw).strip())
    if len(digits) < 8 or digits == "0" * len(digits):
        return None
    return digits


def build_search_queries(ctx: ItemSearchContext) -> list[SearchQuery]:
    title = (ctx.item_title or "").strip()
    normalized_title = normalize_search_text(title)
    barcode = _clean_barcode(ctx.barcodeid)
    queries: list[SearchQuery] = []
    seen: set[str] = set()

    def add(level: int, query: str, label: str) -> None:
        q = re.sub(r"\s+", " ", query.strip())[:120]
        if not q:
            return
        key = q.lower()
        if key in seen:
            return
        seen.add(key)
        queries.append(SearchQuery(level=level, query=q, label=label))

    if barcode:
        add(1, barcode, "exact_barcode")
    if barcode and title:
        add(2, f"{barcode} {title}", "barcode_and_name")
    if title:
        add(3, title, "exact_name")
    if normalized_title and normalized_title.lower() != title.lower():
        add(4, normalized_title, "normalized_name")
    elif title:
        add(4, normalized_title or title, "normalized_name")

    return sorted(queries, key=lambda q: q.level)
