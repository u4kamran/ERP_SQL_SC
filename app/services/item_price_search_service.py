"""Advanced public-safe item price search with ranking and disambiguation."""

from __future__ import annotations

import re
from dataclasses import dataclass
from difflib import SequenceMatcher
from typing import Any

from sqlalchemy.orm import Session

from app.repositories.fin_item_classic_repository import FinItemClassicRepository
from app.schemas.guest_price_lookup import (
    GuestPriceLookupResponse,
    GuestPriceSearchMatch,
    GuestPriceSearchResponse,
)
from app.services.guest_price_lookup_service import (
    GuestPriceLookupService,
    to_proper_case,
)

_STOP_WORDS = {
    "a",
    "an",
    "the",
    "of",
    "for",
    "and",
    "or",
    "to",
    "in",
    "on",
    "my",
    "me",
    "please",
    "pls",
    "price",
    "prices",
    "rate",
    "rates",
    "cost",
    "kitna",
    "kitni",
    "hai",
    "hy",
    "he",
    "ka",
    "ki",
    "ke",
    "item",
    "product",
    "check",
    "find",
    "search",
    "tell",
    "what",
    "whats",
    "how",
    "much",
    "rs",
    "rupee",
    "rupees",
    "sale",
    "sales",
    "want",
    "need",
    "send",
    "show",
    "batao",
    "bata",
    "do",
    "is",
    "are",
}

_PREFIX_RE = re.compile(
    r"^(?:price|rate|cost|check|find|search|tell|show|what(?:'s| is)?|"
    r"kitna|kitni|batao|bata)\s+(?:of\s+|for\s+|about\s+)?",
    re.I,
)


@dataclass
class RankedCandidate:
    manual_id: int
    item_id: float
    item_title: str
    item_short: str
    barcodeid: str
    barcodeid_ws: str
    score: float
    match_reason: str


class ItemPriceSearchService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = FinItemClassicRepository(db)
        self.guest = GuestPriceLookupService(db)

    def search(
        self,
        query: str,
        *,
        limit: int = 8,
        force_list: bool = False,
    ) -> GuestPriceSearchResponse:
        cleaned = self.normalize_query(query)
        if not cleaned:
            return GuestPriceSearchResponse(
                query=query or "",
                cleaned_query="",
                match_type="none",
                message="Please type an item name, barcode, or code.",
            )

        # Exact barcode / code first
        digits = re.sub(r"\D", "", cleaned)
        if re.fullmatch(r"\d{8,20}", cleaned) or re.fullmatch(r"\d{8,20}", digits):
            try:
                item = self.guest.lookup_any(digits or cleaned)
                return GuestPriceSearchResponse(
                    query=query,
                    cleaned_query=cleaned,
                    match_type="exact",
                    items=[self._as_match(item, 1.0, "barcode")],
                    message="Exact barcode match.",
                )
            except Exception:
                pass

        if re.fullmatch(r"\d{1,8}", cleaned):
            try:
                item = self.guest.lookup_manual_id(int(cleaned))
                return GuestPriceSearchResponse(
                    query=query,
                    cleaned_query=cleaned,
                    match_type="exact",
                    items=[self._as_match(item, 1.0, "manual_id")],
                    message="Exact item code match.",
                )
            except Exception:
                pass

        ranked = self._rank_candidates(cleaned, limit=max(limit * 3, 36))
        if not ranked:
            return GuestPriceSearchResponse(
                query=query,
                cleaned_query=cleaned,
                match_type="none",
                message=(
                    f"No item found for '{cleaned}'. "
                    "Try a shorter name, brand, barcode, or item code."
                ),
            )

        top = ranked[:limit]
        priced: list[GuestPriceSearchMatch] = []
        for candidate in top:
            try:
                item = self.guest.lookup_manual_id(candidate.manual_id)
            except Exception:
                continue
            priced.append(
                self._as_match(item, candidate.score, candidate.match_reason)
            )

        if not priced:
            return GuestPriceSearchResponse(
                query=query,
                cleaned_query=cleaned,
                match_type="none",
                message=f"No priced item found for '{cleaned}'.",
            )

        # Brand / name typing (e.g. "dalda"): always return a pick list for buttons.
        if force_list:
            return GuestPriceSearchResponse(
                query=query,
                cleaned_query=cleaned,
                match_type="multiple" if len(priced) > 1 else "single",
                items=priced,
                message=(
                    f"Found {len(priced)} item(s) for '{cleaned}'. "
                    "Tap an option below."
                ),
            )

        best = priced[0]
        # Strong exact / near-exact title
        if best.score >= 0.92 and (
            len(priced) == 1 or best.score - priced[1].score >= 0.12
        ):
            return GuestPriceSearchResponse(
                query=query,
                cleaned_query=cleaned,
                match_type="exact" if best.score >= 0.98 else "single",
                items=[best],
                message="Best match found.",
            )

        if len(priced) == 1 or best.score >= 0.88 and best.score - priced[1].score >= 0.18:
            return GuestPriceSearchResponse(
                query=query,
                cleaned_query=cleaned,
                match_type="single",
                items=[best],
                message="Closest match found.",
            )

        return GuestPriceSearchResponse(
            query=query,
            cleaned_query=cleaned,
            match_type="multiple",
            items=priced,
            message=(
                f"Found {len(priced)} possible items for '{cleaned}'. "
                "Reply with the option number."
            ),
        )

    def format_price_card(self, item: GuestPriceLookupResponse | GuestPriceSearchMatch) -> str:
        rate = self._money(item.sales_rate)
        wo_gst = self._money(item.sales_price_wo_gst)
        market = self._money(item.market_price)
        gst = self._money(item.gst_amount)
        title = to_proper_case(item.item_title) or item.item_title
        short = to_proper_case(item.item_short) if item.item_short else None
        lines = [
            f"*{title}*",
            f"Code: {item.manual_id}",
        ]
        if short:
            lines.append(f"Short: {short}")
        if item.barcodeid:
            lines.append(f"Barcode: {item.barcodeid}")
        lines.append(f"Rate: Rs {rate}")
        if item.sales_price_wo_gst is not None:
            lines.append(f"Without GST: Rs {wo_gst}")
        if item.gst_amount:
            lines.append(f"GST: Rs {gst}")
        if item.market_price:
            lines.append(f"Market: Rs {market}")
        if item.uom_title:
            lines.append(f"Unit: {to_proper_case(item.uom_title)}")
        if item.co_title:
            lines.append(f"Company: {to_proper_case(item.co_title)}")
        if item.promotion:
            lines.append("Promotion: Yes")
        return "\n".join(lines)

    def format_options_list(
        self,
        items: list[GuestPriceSearchMatch],
        *,
        title: str,
        page: int = 0,
        page_size: int = 8,
    ) -> str:
        start = page * page_size
        chunk = items[start : start + page_size]
        if not chunk:
            return "No more options. Type a new item name."
        lines = [title, ""]
        for idx, item in enumerate(chunk, start=start + 1):
            rate = self._money(item.sales_rate)
            title = to_proper_case(item.item_title) or item.item_title
            short_raw = to_proper_case(item.item_short) if item.item_short else ""
            short = f" ({short_raw})" if short_raw else ""
            lines.append(f"{idx}) {title}{short}")
            lines.append(f"   Code {item.manual_id} · Rs {rate}")
        remaining = len(items) - (start + len(chunk))
        lines.append("")
        lines.append("Reply with the number to see full rate.")
        if remaining > 0:
            lines.append(f"Reply MORE for next {min(remaining, page_size)} options.")
        lines.append("Reply NEW to search again, or MENU for main menu.")
        return "\n".join(lines)

    @classmethod
    def normalize_query(cls, query: str) -> str:
        text = (query or "").strip()
        text = text.replace("؟", "?").replace("۔", ".")
        text = _PREFIX_RE.sub("", text).strip()
        text = re.sub(r"[\"'`]+", "", text)
        text = re.sub(r"[^\w\s\-+./]", " ", text, flags=re.UNICODE)
        text = re.sub(r"\s+", " ", text).strip()
        tokens = [t for t in text.split() if t.lower() not in _STOP_WORDS and len(t) > 1]
        if tokens:
            return " ".join(tokens)
        return text

    def _rank_candidates(self, cleaned: str, *, limit: int) -> list[RankedCandidate]:
        tokens = [t for t in cleaned.lower().split() if t]
        raw_rows: list[dict[str, Any]] = []
        seen: set[int] = set()

        for row in self.repo.search_items(cleaned, limit=limit):
            self._collect_row(row, seen, raw_rows)

        if len(tokens) >= 2:
            for row in self.repo.search_items_all_tokens(tokens, limit=limit):
                self._collect_row(row, seen, raw_rows)

        for token in tokens:
            if len(token) < 3:
                continue
            for row in self.repo.search_items(token, limit=min(20, limit)):
                self._collect_row(row, seen, raw_rows)

        ranked: list[RankedCandidate] = []
        for row in raw_rows:
            candidate = self._score_row(row, cleaned, tokens)
            if candidate and candidate.score >= 0.28:
                ranked.append(candidate)
        ranked.sort(key=lambda item: (-item.score, item.item_title.lower()))
        return ranked[:limit]

    @staticmethod
    def _collect_row(
        row: dict[str, Any],
        seen: set[int],
        out: list[dict[str, Any]],
    ) -> None:
        try:
            manual_id = int(float(row.get("manualid") or 0))
        except (TypeError, ValueError):
            return
        if manual_id <= 0 or manual_id in seen:
            return
        seen.add(manual_id)
        out.append(row)

    def _score_row(
        self,
        row: dict[str, Any],
        cleaned: str,
        tokens: list[str],
    ) -> RankedCandidate | None:
        title = str(row.get("Item_Title") or row.get("ITEM_TITLE") or "").strip()
        short = str(row.get("item_short") or row.get("ITEM_SHORT") or "").strip()
        barcode = str(row.get("barcodeid") or "").strip()
        barcode_ws = str(row.get("barcodeid_ws") or row.get("BARCODEID_WS") or "").strip()
        try:
            manual_id = int(float(row.get("manualid") or 0))
            item_id = float(row.get("item_id") or row.get("ITEM_ID") or 0)
        except (TypeError, ValueError):
            return None
        if manual_id <= 0 or not title:
            return None

        title_l = title.lower()
        short_l = short.lower()
        cleaned_l = cleaned.lower()
        hay = f"{title_l} {short_l}"
        score = 0.0
        reason = "text"

        if cleaned_l == title_l:
            score = 1.0
            reason = "exact_title"
        elif cleaned_l == short_l and short_l:
            score = 0.98
            reason = "exact_short"
        elif cleaned in {barcode, barcode_ws}:
            score = 1.0
            reason = "barcode"
        elif cleaned.isdigit() and cleaned == str(manual_id):
            score = 1.0
            reason = "manual_id"
        else:
            fuzzy = max(
                SequenceMatcher(None, cleaned_l, title_l).ratio(),
                SequenceMatcher(None, cleaned_l, short_l).ratio() if short_l else 0.0,
            )
            score = fuzzy * 0.72
            reason = "fuzzy"
            if self._has_phrase(cleaned_l, title_l) or (
                short_l and self._has_phrase(cleaned_l, short_l)
            ):
                score = max(score, 0.86)
                reason = "contains"
            if tokens:
                hits = sum(1 for token in tokens if self._has_phrase(token, hay))
                ratio = hits / len(tokens)
                score = max(score, 0.35 + ratio * 0.5)
                if hits == len(tokens):
                    score = max(score, 0.9)
                    reason = "all_tokens"
                elif hits:
                    reason = f"tokens_{hits}/{len(tokens)}"
                else:
                    # Avoid weak fuzzy-only junk for short queries like "oil"→"foil"
                    if len(cleaned_l) <= 4:
                        score = min(score, 0.25)
            # Prefer titles that start with the query
            if title_l.startswith(cleaned_l) or any(
                title_l.startswith(token) for token in tokens[:1]
            ):
                score = min(1.0, score + 0.06)

        return RankedCandidate(
            manual_id=manual_id,
            item_id=item_id,
            item_title=title,
            item_short=short,
            barcodeid=barcode,
            barcodeid_ws=barcode_ws,
            score=round(min(score, 1.0), 4),
            match_reason=reason,
        )

    @staticmethod
    def _has_phrase(needle: str, haystack: str) -> bool:
        """Word-boundary aware contains (prevents oil matching foil)."""
        needle = (needle or "").strip().lower()
        haystack = (haystack or "").strip().lower()
        if not needle or not haystack:
            return False
        if len(needle) <= 3:
            return bool(re.search(rf"(?<!\w){re.escape(needle)}(?!\w)", haystack))
        return needle in haystack

    @staticmethod
    def _as_match(
        item: GuestPriceLookupResponse,
        score: float,
        reason: str,
    ) -> GuestPriceSearchMatch:
        return GuestPriceSearchMatch(
            **item.model_dump(),
            score=score,
            match_reason=reason,
        )

    @staticmethod
    def _money(value: float | None) -> str:
        if value is None:
            return "—"
        try:
            number = float(value)
        except (TypeError, ValueError):
            return "—"
        if number == int(number):
            return f"{int(number):,}"
        return f"{number:,.2f}"
