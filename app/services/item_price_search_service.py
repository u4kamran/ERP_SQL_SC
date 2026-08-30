"""Advanced public-safe item price search with ranking and disambiguation."""

from __future__ import annotations

import re
from dataclasses import dataclass
from difflib import SequenceMatcher
from typing import Any

from sqlalchemy.orm import Session

from app.repositories.fin_item_classic_repository import FinItemClassicRepository
from app.repositories.item_search_support_repository import ItemSearchSupportRepository
from app.schemas.guest_price_lookup import (
    GuestPriceLookupResponse,
    GuestPriceSearchMatch,
    GuestPriceSearchResponse,
)
from app.services.guest_price_lookup_service import (
    GuestPriceLookupService,
    is_hidden_shop_title,
    to_proper_case,
)
from app.services import item_search_control_store as search_settings

_PACK_UNITS = {
    "liter",
    "litre",
    "ltr",
    "l",
    "kg",
    "gm",
    "gms",
    "g",
    "ml",
    "oz",
    "pack",
    "pkt",
    "pcs",
    "pc",
}

_NL_PREFIX_RE = re.compile(
    r"^(?:i\s+need|give\s+me|do\s+you\s+have|please\s+give|mujhe|please)\s+",
    re.I,
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
    co_title: str = ""
    sales_rate: float | None = None
    stock_qty: float | None = None
    min_level: float | None = None


class ItemPriceSearchService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = FinItemClassicRepository(db)
        self.guest = GuestPriceLookupService(db)
        self.support = ItemSearchSupportRepository(db)

    def search(
        self,
        query: str,
        *,
        limit: int = 8,
        force_list: bool = False,
        channel: str = "web",
        log: bool = False,
    ) -> GuestPriceSearchResponse:
        cfg = search_settings.get_settings()
        limit = max(1, min(int(limit or cfg["max_results"]), int(cfg["max_results"])))
        suggested_qty, working = self.extract_qty(query)
        cleaned = self.normalize_query(working)
        empty_hint = (
            "No matching products found.\n"
            "Try:\n"
            "• Another spelling\n"
            "• Product brand\n"
            "• Barcode\n"
            "• Shorter search term"
        )
        if not cleaned or len(cleaned) < int(cfg["min_chars"]) and not cleaned.isdigit():
            return GuestPriceSearchResponse(
                query=query or "",
                cleaned_query=cleaned,
                match_type="none",
                message="Please type an item name, barcode, or code.",
                suggested_qty=suggested_qty,
            )

        if cfg["barcode_enabled"]:
            digits = re.sub(r"\D", "", cleaned)
            if re.fullmatch(r"\d{8,20}", cleaned) or re.fullmatch(r"\d{8,20}", digits):
                try:
                    item = self.guest.lookup_any(digits or cleaned)
                    if is_hidden_shop_title(getattr(item, "item_title", None)):
                        raise ValueError("hidden placeholder item")
                    result = GuestPriceSearchResponse(
                        query=query,
                        cleaned_query=cleaned,
                        match_type="exact",
                        items=[self._as_match(item, 1.0, "barcode")],
                        message="Exact barcode match.",
                        suggested_qty=suggested_qty,
                    )
                    if log:
                        self.support.log_search(
                            query_text=query,
                            cleaned_query=cleaned,
                            result_count=1,
                            channel=channel,
                        )
                    return result
                except Exception:
                    pass

            if re.fullmatch(r"\d{1,8}", cleaned):
                try:
                    item = self.guest.lookup_manual_id(int(cleaned))
                    if is_hidden_shop_title(getattr(item, "item_title", None)):
                        raise ValueError("hidden placeholder item")
                    result = GuestPriceSearchResponse(
                        query=query,
                        cleaned_query=cleaned,
                        match_type="exact",
                        items=[self._as_match(item, 1.0, "manual_id")],
                        message="Exact item code match.",
                        suggested_qty=suggested_qty,
                    )
                    if log:
                        self.support.log_search(
                            query_text=query,
                            cleaned_query=cleaned,
                            result_count=1,
                            channel=channel,
                        )
                    return result
                except Exception:
                    pass

        ranked = self._rank_candidates(cleaned, limit=max(limit * 3, 36), cfg=cfg)
        if not ranked:
            if log:
                self.support.log_search(
                    query_text=query,
                    cleaned_query=cleaned,
                    result_count=0,
                    channel=channel,
                )
            return GuestPriceSearchResponse(
                query=query,
                cleaned_query=cleaned,
                match_type="none",
                message=empty_hint,
                suggested_qty=suggested_qty,
                empty_hint=empty_hint,
            )

        top = ranked[:limit]
        priced: list[GuestPriceSearchMatch] = []
        for candidate in top:
            priced.append(self._match_from_candidate(candidate, suggested_qty))

        if not priced:
            if log:
                self.support.log_search(
                    query_text=query,
                    cleaned_query=cleaned,
                    result_count=0,
                    channel=channel,
                )
            return GuestPriceSearchResponse(
                query=query,
                cleaned_query=cleaned,
                match_type="none",
                message=f"No priced item found for '{cleaned}'.",
                suggested_qty=suggested_qty,
                empty_hint=empty_hint,
            )

        if log:
            self.support.log_search(
                query_text=query,
                cleaned_query=cleaned,
                result_count=len(priced),
                channel=channel,
            )

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
                suggested_qty=suggested_qty,
            )

        best = priced[0]
        if best.score >= 0.92 and (
            len(priced) == 1 or best.score - priced[1].score >= 0.12
        ):
            return GuestPriceSearchResponse(
                query=query,
                cleaned_query=cleaned,
                match_type="exact" if best.score >= 0.98 else "single",
                items=[best],
                message="Best match found.",
                suggested_qty=suggested_qty,
            )

        if len(priced) == 1 or best.score >= 0.88 and best.score - priced[1].score >= 0.18:
            return GuestPriceSearchResponse(
                query=query,
                cleaned_query=cleaned,
                match_type="single",
                items=[best],
                message="Closest match found.",
                suggested_qty=suggested_qty,
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
            suggested_qty=suggested_qty,
        )

    def autocomplete(
        self,
        query: str,
        *,
        limit: int | None = None,
        channel: str = "web",
    ) -> GuestPriceSearchResponse:
        cfg = search_settings.get_settings()
        cap = int(limit or cfg["max_results"])
        return self.search(
            query,
            limit=cap,
            force_list=True,
            channel=channel,
            log=True,
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
        text = _NL_PREFIX_RE.sub("", text).strip()
        text = _PREFIX_RE.sub("", text).strip()
        text = re.sub(r"[\"'`]+", "", text)
        text = re.sub(
            r"(\d+(?:\.\d+)?)\s*-?\s*(g|gm|gms|kg|ml|ltr|l|liter|litre)\b",
            r"\1\2",
            text,
            flags=re.I,
        )
        text = re.sub(r"[^\w\s\-+./]", " ", text, flags=re.UNICODE)
        text = re.sub(r"\s+", " ", text).strip()
        tokens = [t for t in text.split() if t.lower() not in _STOP_WORDS and len(t) > 1]
        if tokens:
            return " ".join(tokens)
        return text

    @classmethod
    def extract_qty(cls, query: str) -> tuple[float | None, str]:
        text = re.sub(r"\s+", " ", (query or "").strip())
        text = _NL_PREFIX_RE.sub("", text).strip()
        match = re.match(r"^(\d+(?:\.\d+)?)\s+(.+)$", text, flags=re.I)
        if not match:
            return None, text
        qty = float(match.group(1))
        rest = match.group(2).strip()
        first = (rest.split() or [""])[0].lower()
        if first in _PACK_UNITS or re.match(r"^\d", first) or qty > 99 or qty < 1:
            if first in _PACK_UNITS:
                leftover = " ".join(rest.split()[1:]).strip()
                return None, leftover or text
            return None, text
        return qty, rest

    def _rank_candidates(
        self, cleaned: str, *, limit: int, cfg: dict[str, Any] | None = None
    ) -> list[RankedCandidate]:
        cfg = cfg or search_settings.get_settings()
        tokens = [t for t in cleaned.lower().split() if t]
        queries = [cleaned]
        if cfg.get("alias_enabled"):
            try:
                for token in tokens[:4]:
                    expand = self.support.lookup_alias(token)
                    if (
                        expand
                        and expand.lower() != token.lower()
                        and expand.lower() not in cleaned.lower()
                    ):
                        queries.append(expand)
            except Exception:
                self.db.rollback()

        raw_rows: list[dict[str, Any]] = []
        seen: set[int] = set()
        fetch_limit = max(limit, 40)

        for qtext in queries:
            q_tokens = [t for t in qtext.lower().split() if t]
            prefix = q_tokens[0] if q_tokens else qtext
            for row in self.repo.search_items_smart(qtext, prefix=prefix, limit=fetch_limit):
                self._collect_row(row, seen, raw_rows)
            if len(q_tokens) >= 2:
                for row in self.repo.search_items_all_tokens(q_tokens, limit=fetch_limit):
                    self._collect_row(row, seen, raw_rows)

        ranked: list[RankedCandidate] = []
        for row in raw_rows:
            best: RankedCandidate | None = None
            for qtext in queries:
                q_tokens = [t for t in qtext.lower().split() if t]
                candidate = self._score_row(row, qtext, q_tokens)
                if candidate and (best is None or candidate.score > best.score):
                    best = candidate
            if best and best.score >= 0.28:
                ranked.append(best)

        if cfg.get("fuzzy_enabled") and len(ranked) < 3 and tokens:
            stem = tokens[0][:4] if len(tokens[0]) >= 3 else tokens[0]
            if len(stem) >= 3:
                extra = self.repo.search_items_smart(stem, prefix=stem, limit=80)
                for row in extra:
                    self._collect_row(row, seen, raw_rows)
                ranked = []
                for row in raw_rows:
                    best: RankedCandidate | None = None
                    score_queries = queries + [cleaned]
                    for qtext in score_queries:
                        q_tokens = [t for t in qtext.lower().split() if t]
                        candidate = self._score_row(row, qtext, q_tokens)
                        if candidate and (best is None or candidate.score > best.score):
                            best = candidate
                    if best and best.score >= 0.22:
                        ranked.append(best)

        ranked.sort(key=lambda item: (-item.score, item.item_title.lower()))
        ranked = [item for item in ranked if not is_hidden_shop_title(item.item_title)]
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
        brand = str(row.get("co_title") or row.get("CO_TITLE") or "").strip()
        try:
            stock = float(row.get("cqty") or row.get("CQTY") or 0)
        except (TypeError, ValueError):
            stock = None
        try:
            min_level = float(row.get("min_level") or row.get("MIN_LEVEL") or 0)
        except (TypeError, ValueError):
            min_level = None
        try:
            rate = float(row.get("sales_rate") or row.get("SALES_RATE") or 0)
        except (TypeError, ValueError):
            rate = None
        try:
            manual_id = int(float(row.get("manualid") or 0))
            item_id = float(row.get("item_id") or row.get("ITEM_ID") or 0)
        except (TypeError, ValueError):
            return None
        if manual_id <= 0 or not title:
            return None
        if is_hidden_shop_title(title):
            return None

        title_l = title.lower()
        short_l = short.lower()
        brand_l = brand.lower()
        cleaned_l = cleaned.lower()
        hay = f"{title_l} {short_l} {brand_l}"
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
                    if len(cleaned_l) <= 4:
                        score = min(score, 0.25)
            if title_l.startswith(cleaned_l):
                score = min(1.0, max(score, 0.93))
                reason = "prefix_title"
            elif any(word.startswith(cleaned_l) for word in title_l.split()):
                score = min(1.0, max(score, 0.88))
                reason = "word_prefix"
            elif short_l.startswith(cleaned_l) and short_l:
                score = min(1.0, max(score, 0.87))
                reason = "prefix_short"
            elif brand_l.startswith(cleaned_l) and brand_l:
                score = min(1.0, max(score, 0.82))
                reason = "brand"
            elif self._has_phrase(cleaned_l, brand_l) and brand_l:
                score = min(1.0, max(score, 0.78))
                reason = "brand"

        return RankedCandidate(
            manual_id=manual_id,
            item_id=item_id,
            item_title=title,
            item_short=short,
            barcodeid=barcode,
            barcodeid_ws=barcode_ws,
            score=round(min(score, 1.0), 4),
            match_reason=reason,
            co_title=brand,
            sales_rate=rate,
            stock_qty=stock,
            min_level=min_level,
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
        stock = getattr(item, "stock_qty", None)
        in_stock = True if stock is None else float(stock) > 0
        return GuestPriceSearchMatch(
            **item.model_dump(),
            score=score,
            match_reason=reason,
            stock_qty=stock,
            in_stock=in_stock,
            stock_label=ItemPriceSearchService._stock_label(stock, None),
        )

    def _match_from_candidate(
        self, candidate: RankedCandidate, suggested_qty: float | None
    ) -> GuestPriceSearchMatch:
        stock = candidate.stock_qty
        in_stock = stock is None or float(stock) > 0
        return GuestPriceSearchMatch(
            manual_id=candidate.manual_id,
            barcodeid=candidate.barcodeid or None,
            barcodeid_ws=candidate.barcodeid_ws or None,
            item_title=to_proper_case(candidate.item_title) or candidate.item_title,
            item_short=to_proper_case(candidate.item_short) if candidate.item_short else None,
            uom_title=None,
            co_title=to_proper_case(candidate.co_title) if candidate.co_title else None,
            sales_rate=candidate.sales_rate,
            score=candidate.score,
            match_reason=candidate.match_reason,
            stock_qty=stock,
            in_stock=in_stock,
            stock_label=self._stock_label(stock, candidate.min_level),
            suggested_qty=suggested_qty,
        )

    @staticmethod
    def _stock_label(stock: float | None, min_level: float | None) -> str:
        if stock is None:
            return "unknown"
        if stock <= 0:
            return "out"
        if min_level is not None and stock <= float(min_level):
            return "low"
        if stock <= 5:
            return "low"
        return "in_stock"

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
