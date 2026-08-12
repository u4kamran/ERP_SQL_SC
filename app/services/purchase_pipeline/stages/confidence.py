"""Stage 12 — Assign confidence scores; require confirmation for low-confidence fields."""

from __future__ import annotations

from app.services.purchase_pipeline.base import BaseStage
from app.services.purchase_pipeline.types import (
    CONFIRM_THRESHOLD,
    FieldConfidence,
    PipelineContext,
)


class ConfidenceScoringStage(BaseStage):
    stage_id = 12
    name = "confidence_scoring"

    def run(self, ctx: PipelineContext) -> PipelineContext:
        fields: list[FieldConfidence] = []

        fields.append(
            FieldConfidence(
                field="document_class",
                value=ctx.document_class.value,
                score=ctx.document_class_score,
                requires_confirmation=ctx.document_class_score < CONFIRM_THRESHOLD,
                reason="classifier score",
            )
        )
        fields.append(
            FieldConfidence(
                field="supplier",
                value=ctx.supplier.supplier_id or ctx.supplier.name,
                score=ctx.supplier.confidence,
                requires_confirmation=ctx.supplier.confidence < CONFIRM_THRESHOLD
                or not ctx.supplier.supplier_id,
                reason="supplier identification",
            )
        )

        match_by_idx = {m.product_index: m for m in ctx.matches}
        for i, p in enumerate(ctx.products):
            m = match_by_idx.get(i)
            for fname, score in (p.field_scores or {}).items():
                if fname.startswith("recalc_"):
                    continue
                fields.append(
                    FieldConfidence(
                        field=f"line[{i}].{fname}",
                        value=getattr(p, fname, None) if hasattr(p, fname) else None,
                        score=float(score),
                        requires_confirmation=float(score) < CONFIRM_THRESHOLD,
                        reason="extraction confidence",
                    )
                )
            match_score = float(m.score) if m else 0.0
            fields.append(
                FieldConfidence(
                    field=f"line[{i}].item_id",
                    value=m.item_id if m else None,
                    score=match_score,
                    requires_confirmation=match_score < CONFIRM_THRESHOLD or not (m and m.item_id),
                    reason=m.method if m and m.method else "unmatched",
                )
            )

        # Totals always require soft confirmation when claimed totals disagreed
        mismatch = any(v.code.endswith("_MISMATCH") for v in ctx.validations)
        fields.append(
            FieldConfidence(
                field="grand_total",
                value=ctx.financials.grand_total,
                score=0.55 if mismatch else 0.8,
                requires_confirmation=mismatch or True,  # financials always reviewed
                reason="recalculated independently; printed totals never trusted",
            )
        )

        ctx.field_confidences = fields
        low = sum(1 for f in fields if f.requires_confirmation)
        if low:
            ctx.warnings.append(
                f"{low} field(s) require user confirmation (confidence < {CONFIRM_THRESHOLD:.2f})."
            )
        ctx.meta["confirm_threshold"] = CONFIRM_THRESHOLD
        return ctx
