"""Stage 9 — Multi-strategy product matching (never assume first hit is correct)."""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional, Tuple

from app.services.purchase_pipeline.base import BaseStage
from app.services.purchase_pipeline.embeddings import SemanticEmbedder, fuzzy_ratio, jaccard
from app.services.purchase_pipeline.types import PipelineContext, ProductMatch, StructuredProduct


class MatchProductsStage(BaseStage):
    stage_id = 9
    name = "match_products"

    def run(self, ctx: PipelineContext) -> PipelineContext:
        matches: List[ProductMatch] = []
        supplier_key = _supplier_key(ctx)
        corpus_titles: List[str] = []
        catalog: List[Dict[str, Any]] = []

        # Prefetch a soft catalog for fuzzy/embedding when DB available
        if ctx.db is not None and ctx.products:
            catalog = self._prefetch_catalog(ctx)
            corpus_titles = [str(c.get("item_title") or "") for c in catalog]
        embedder = SemanticEmbedder(corpus_titles)

        for idx, product in enumerate(ctx.products):
            match = self._match_one(ctx, product, idx, supplier_key, catalog, embedder)
            matches.append(match)

        ctx.matches = matches
        unmatched = sum(1 for m in matches if not m.item_id)
        if unmatched:
            ctx.warnings.append(f"{unmatched} product(s) unmatched — confirm item IDs before Save.")
        return ctx

    def _match_one(
        self,
        ctx: PipelineContext,
        product: StructuredProduct,
        index: int,
        supplier_key: str,
        catalog: List[Dict[str, Any]],
        embedder: SemanticEmbedder,
    ) -> ProductMatch:
        candidates: List[Dict[str, Any]] = []

        # 1. Handwritten Manual ID — FIRST priority (usually handwritten on invoice)
        hw = (product.handwritten_manual_id or "").strip()
        if hw:
            if ctx.learning_store:
                iid = ctx.learning_store.lookup_manual_id(supplier_key=supplier_key, handwritten=hw)
                if iid and ctx.db is not None:
                    hit = self._by_item_id(ctx, iid)
                    if hit:
                        ctx.learning_applied.append(f"hw_manual→{iid}")
                        return self._ok(index, hit, "handwritten_manual_id", 0.96, candidates)
            digits = re.sub(r"\D", "", hw)
            if digits and ctx.db is not None:
                try:
                    hit = self._by_manual(ctx, float(digits))
                    if hit:
                        return self._ok(index, hit, "handwritten_manual_id", 0.94, candidates)
                except ValueError:
                    pass

        # 2. Barcode (only if manual ID missing)
        if product.barcode and ctx.db is not None:
            hit = self._by_barcode(ctx, product.barcode)
            if hit:
                return self._ok(index, hit, "barcode", 0.9, candidates)

        # 3. Supplier product code (learning + OEM-ish search)
        if product.printed_product_code:
            if ctx.learning_store:
                iid = ctx.learning_store.lookup_supplier_code(
                    supplier_key=supplier_key, code=product.printed_product_code
                )
                if iid and ctx.db is not None:
                    hit = self._by_item_id(ctx, iid)
                    if hit:
                        ctx.learning_applied.append(f"supplier_code→{iid}")
                        return self._ok(index, hit, "supplier_code", 0.88, candidates)
            if ctx.db is not None:
                hit = self._search_code(ctx, product.printed_product_code)
                if hit:
                    return self._ok(index, hit, "supplier_code", 0.8, candidates)

        # 4. Product alias (learning)
        alias_query = product.printed_description or product.printed_product_code
        if alias_query and ctx.learning_store:
            iid = ctx.learning_store.lookup_alias(supplier_key=supplier_key, text=alias_query)
            if iid and ctx.db is not None:
                hit = self._by_item_id(ctx, iid)
                if hit:
                    ctx.learning_applied.append(f"alias→{iid}")
                    return self._ok(index, hit, "alias", 0.88, candidates)

        # 5. Exact name
        desc = (product.printed_description or "").strip()
        if desc and catalog:
            for c in catalog:
                title = str(c.get("item_title") or "").strip()
                if title and title.lower() == desc.lower():
                    return self._ok(index, c, "exact_name", 0.92, candidates)

        # 6. Fuzzy matching
        if desc and catalog:
            ranked = sorted(
                ((fuzzy_ratio(desc, str(c.get("item_title") or "")), c) for c in catalog),
                key=lambda x: x[0],
                reverse=True,
            )
            for score, c in ranked[:5]:
                candidates.append({**c, "fuzzy": round(score, 3)})
            if ranked and ranked[0][0] >= 0.82:
                return self._ok(index, ranked[0][1], "fuzzy", ranked[0][0], candidates)
            if ranked and ranked[0][0] >= 0.65:
                # Suggest but low score
                m = self._ok(index, ranked[0][1], "fuzzy", ranked[0][0] * 0.85, candidates)
                return m

        # 7. Semantic embeddings
        if desc and catalog:
            pairs = [(str(c.get("item_title") or ""), float(c.get("item_id") or 0)) for c in catalog]
            bi, score = embedder.best_match(desc, pairs, min_score=0.4)
            if bi >= 0:
                for i, c in enumerate(catalog[:8]):
                    candidates.append({**c, "embedding": round(embedder.similarity(desc, str(c.get("item_title") or "")), 3)})
                return self._ok(index, catalog[bi], "embedding", score, candidates)

        # Soft search fallback via repo
        if desc and ctx.db is not None:
            try:
                from app.repositories.fin_pur_repository import FinPurRepository, _vget

                rows = FinPurRepository(ctx.db).search_items(desc[:60], limit=8)
                candidates = [
                    {
                        "item_id": float(_vget(r, "item_id")),
                        "item_title": str(_vget(r, "item_title", default="") or ""),
                        "manualid": _vget(r, "manualid"),
                        "barcodeid": _vget(r, "barcodeid"),
                        "co_id": _vget(r, "co_id"),
                    }
                    for r in rows
                ]
                if len(candidates) == 1:
                    return self._ok(index, candidates[0], "fuzzy", 0.7, candidates)
                if candidates:
                    m = self._ok(index, candidates[0], "fuzzy", 0.45, candidates)
                    return m
            except Exception:  # noqa: BLE001
                pass

        return ProductMatch(product_index=index, method="", score=0.0, candidates=candidates[:10])

    def _prefetch_catalog(self, ctx: PipelineContext) -> List[Dict[str, Any]]:
        from app.repositories.fin_pur_repository import FinPurRepository, _vget

        repo = FinPurRepository(ctx.db)
        seen = set()
        out: List[Dict[str, Any]] = []
        queries = []
        for p in ctx.products:
            if p.printed_description:
                queries.append(p.printed_description[:40])
            if p.printed_product_code:
                queries.append(p.printed_product_code)
            if p.barcode:
                queries.append(p.barcode)
        for q in queries[:12]:
            try:
                for r in repo.search_items(q, limit=15):
                    iid = float(_vget(r, "item_id"))
                    if iid in seen:
                        continue
                    seen.add(iid)
                    out.append(
                        {
                            "item_id": iid,
                            "item_title": str(_vget(r, "item_title", default="") or ""),
                            "manualid": _vget(r, "manualid"),
                            "barcodeid": _vget(r, "barcodeid"),
                            "co_id": int(_vget(r, "co_id") or 0) or None,
                        }
                    )
            except Exception:  # noqa: BLE001
                continue
        return out[:200]

    def _by_barcode(self, ctx: PipelineContext, barcode: str) -> Optional[Dict[str, Any]]:
        from app.repositories.fin_pur_repository import FinPurRepository, _vget

        repo = FinPurRepository(ctx.db)
        view = repo.get_item_view(barcode=barcode) or repo.get_item_view(barcode_ws=barcode)
        if not view:
            return None
        item = repo.get_item(float(_vget(view, "item_id"))) or view
        return {
            "item_id": float(_vget(item, "item_id")),
            "item_title": str(_vget(item, "item_title", default="") or ""),
            "manualid": _vget(item, "manualid"),
            "barcodeid": _vget(item, "barcodeid"),
            "co_id": int(_vget(item, "co_id") or 0) or None,
        }

    def _by_manual(self, ctx: PipelineContext, manual_id: float) -> Optional[Dict[str, Any]]:
        from app.repositories.fin_pur_repository import FinPurRepository, _vget

        repo = FinPurRepository(ctx.db)
        view = repo.get_item_view(manual_id=manual_id)
        if not view:
            return None
        item = repo.get_item(float(_vget(view, "item_id"))) or view
        return {
            "item_id": float(_vget(item, "item_id")),
            "item_title": str(_vget(item, "item_title", default="") or ""),
            "manualid": _vget(item, "manualid"),
            "barcodeid": _vget(item, "barcodeid"),
            "co_id": int(_vget(item, "co_id") or 0) or None,
        }

    def _by_item_id(self, ctx: PipelineContext, item_id: float) -> Optional[Dict[str, Any]]:
        from app.repositories.fin_pur_repository import FinPurRepository, _vget

        item = FinPurRepository(ctx.db).get_item(item_id)
        if not item:
            return None
        return {
            "item_id": float(_vget(item, "item_id")),
            "item_title": str(_vget(item, "item_title", default="") or ""),
            "manualid": _vget(item, "manualid"),
            "barcodeid": _vget(item, "barcodeid"),
            "co_id": int(_vget(item, "co_id") or 0) or None,
        }

    def _search_code(self, ctx: PipelineContext, code: str) -> Optional[Dict[str, Any]]:
        from app.repositories.fin_pur_repository import FinPurRepository, _vget

        rows = FinPurRepository(ctx.db).search_items(code, limit=5)
        if len(rows) == 1:
            r = rows[0]
            return {
                "item_id": float(_vget(r, "item_id")),
                "item_title": str(_vget(r, "item_title", default="") or ""),
                "manualid": _vget(r, "manualid"),
                "barcodeid": _vget(r, "barcodeid"),
                "co_id": None,
            }
        return None

    def _ok(
        self,
        index: int,
        hit: Dict[str, Any],
        method: str,
        score: float,
        candidates: List[Dict[str, Any]],
    ) -> ProductMatch:
        return ProductMatch(
            product_index=index,
            item_id=float(hit["item_id"]) if hit.get("item_id") is not None else None,
            item_title=str(hit.get("item_title") or ""),
            manual_id=float(hit["manualid"]) if hit.get("manualid") not in (None, "") else None,
            barcodeid=str(hit["barcodeid"]) if hit.get("barcodeid") else None,
            co_id=hit.get("co_id"),
            method=method,
            score=float(score),
            candidates=candidates[:10] or [hit],
        )


def _supplier_key(ctx: PipelineContext) -> str:
    if ctx.supplier.supplier_id:
        return str(ctx.supplier.supplier_id)
    if ctx.supplier.tax_id:
        return ctx.supplier.tax_id.lower()
    return (ctx.supplier.name or "unknown").lower()[:80]
