"""Match-score calculation with pack-size hard rejection (0–100)."""

from __future__ import annotations

import re
from difflib import SequenceMatcher

from app.services.item_images.normalization import pack_sizes_compatible
from app.services.item_images.providers.base import ImageCandidate, ItemSearchContext, ProductCandidate, ScoreResult


def _norm(text: str | None) -> str:
    if not text:
        return ""
    t = text.lower().strip()
    t = re.sub(r"[^a-z0-9\s]+", " ", t)
    return re.sub(r"\s+", " ", t).strip()


def _token_set(text: str) -> set[str]:
    return {t for t in _norm(text).split() if len(t) > 1}


def _clean_barcode(raw: str | None) -> str:
    if not raw:
        return ""
    return re.sub(r"\D+", "", str(raw).strip())


def score_product(ctx: ItemSearchContext, candidate: ProductCandidate) -> ScoreResult:
    return score_candidate(
        ctx,
        candidate.to_legacy(),
        candidate_title=candidate.product_name,
        candidate_barcode=candidate.barcode,
        candidate_brand=candidate.brand,
    )


def score_candidate(
    ctx: ItemSearchContext,
    candidate: ImageCandidate,
    *,
    candidate_title: str | None = None,
    candidate_barcode: str | None = None,
    candidate_brand: str | None = None,
) -> ScoreResult:
    title = candidate_title or candidate.product_title
    barcode = candidate_barcode or candidate.product_barcode
    brand = candidate_brand or candidate.product_brand

    compatible, both_detected = pack_sizes_compatible(ctx.item_title, title)
    if both_detected and not compatible:
        return ScoreResult(
            score=0,
            hard_reject=True,
            reason="pack_size_mismatch",
        )

    score = 0
    barcode_mismatch = False
    item_bc = _clean_barcode(ctx.barcodeid)
    cand_bc = _clean_barcode(barcode)

    if item_bc and cand_bc:
        if item_bc == cand_bc:
            score += 60
        else:
            barcode_mismatch = True

    item_name = _norm(ctx.item_title)
    cand_title = _norm(title)
    # PK storefront APIs (Naheed GraphQL) rarely return barcodes — allow name-only matches.
    name_max = 40 if not cand_bc else 20
    if item_name and cand_title:
        ratio = SequenceMatcher(None, item_name, cand_title).ratio()
        tokens_item = _token_set(item_name)
        tokens_cand = _token_set(cand_title)
        overlap = 0.0
        if tokens_item:
            overlap = len(tokens_item & tokens_cand) / max(len(tokens_item), 1)
        name_score = int(round(name_max * max(ratio, overlap)))
        score += name_score
    elif item_name and not cand_title:
        if not (item_bc and cand_bc and item_bc == cand_bc):
            score = max(0, score - 10)

    ctx_brand = _norm(ctx.brand)
    cand_brand_norm = _norm(brand)
    if ctx_brand and cand_brand_norm:
        if ctx_brand in cand_brand_norm or cand_brand_norm in ctx_brand:
            score += 10
        elif SequenceMatcher(None, ctx_brand, cand_brand_norm).ratio() >= 0.75:
            score += 8

    if both_detected and compatible:
        score += 10

    if barcode_mismatch:
        score = min(score, 45)

    return ScoreResult(score=max(0, min(100, score)), hard_reject=False)


def decide_status(
    score: int,
    *,
    auto_accept_min: int = 90,
    review_min: int = 75,
    no_match_min: int = 50,
) -> str:
    if score >= auto_accept_min:
        return "AUTO_APPROVED"
    if score >= review_min:
        return "REVIEW_RECOMMENDED"
    if score >= no_match_min:
        return "NEEDS_REVIEW"
    return "NO_RELIABLE_MATCH"
