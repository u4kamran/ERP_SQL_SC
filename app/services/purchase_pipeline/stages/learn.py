"""Stage 13 — Prepare / apply learning from user corrections."""

from __future__ import annotations

from typing import Any, Dict, List

from app.services.purchase_pipeline.base import BaseStage
from app.services.purchase_pipeline.types import PipelineContext


class LearnFromCorrectionsStage(BaseStage):
    """
    During process(): applies existing learned mappings (already used in match stage)
    and records which learning keys were available.

    Persist new corrections via LearningStore.record_correction() from the save/learn API
    when the user overrides matches — this stage remains replaceable and unit-testable.
    """

    stage_id = 13
    name = "learn_from_corrections"

    def run(self, ctx: PipelineContext) -> PipelineContext:
        supplier_key = (
            str(ctx.supplier.supplier_id)
            if ctx.supplier.supplier_id
            else (ctx.supplier.tax_id or ctx.supplier.name or "unknown")
        )
        pending: List[Dict[str, Any]] = []
        for i, p in enumerate(ctx.products):
            pending.append(
                {
                    "product_index": i,
                    "supplier_key": supplier_key,
                    "printed_description": p.printed_description,
                    "printed_product_code": p.printed_product_code,
                    "handwritten_manual_id": p.handwritten_manual_id,
                    "barcode": p.barcode,
                }
            )
        ctx.learning_pending = pending
        if ctx.learning_applied:
            ctx.meta["learning_hits"] = list(ctx.learning_applied)
        return ctx


def apply_user_corrections(
    store,
    *,
    supplier_key: str,
    corrections: List[Dict[str, Any]],
) -> List[str]:
    """
    Call from API after user confirms item matches.

    Each correction dict may include:
      item_id, alias, handwritten_manual_id, supplier_product_code, extraction_rule
    """
    applied: List[str] = []
    for corr in corrections:
        item_id = corr.get("item_id")
        if item_id is None:
            continue
        applied.extend(
            store.record_correction(
                supplier_key=str(corr.get("supplier_key") or supplier_key),
                item_id=float(item_id),
                alias=str(corr.get("alias") or corr.get("printed_description") or ""),
                handwritten_manual_id=str(corr.get("handwritten_manual_id") or ""),
                supplier_product_code=str(
                    corr.get("supplier_product_code") or corr.get("printed_product_code") or ""
                ),
                extraction_rule=corr.get("extraction_rule"),
            )
        )
    return applied
