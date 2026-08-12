"""Stage 1 — Classify the document."""

from __future__ import annotations

import re

from app.services.purchase_pipeline.base import BaseStage
from app.services.purchase_pipeline.types import DocumentClass, PipelineContext


_CLASS_RULES = [
    (DocumentClass.TAX_INVOICE, (r"\btax\s*invoice\b", r"\bgst\s*invoice\b", r"\bsales\s*tax\b"), 0.92),
    (DocumentClass.PURCHASE_INVOICE, (r"\binvoice\b", r"\bbill\b", r"\binv\s*#", r"\binvoice\s*no"), 0.85),
    (DocumentClass.DELIVERY_CHALLAN, (r"\bchallan\b", r"\bdelivery\s*note\b", r"\bgate\s*pass\b"), 0.88),
    (DocumentClass.CREDIT_NOTE, (r"\bcredit\s*note\b", r"\bcn\s*#", r"\breturn\s*invoice\b"), 0.9),
]


class ClassifyDocumentStage(BaseStage):
    stage_id = 1
    name = "classify_document"

    def run(self, ctx: PipelineContext) -> PipelineContext:
        sample = (ctx.ocr_text or ctx.meta.get("raw_probe_text", "") or "").lower()
        # Light probe from filename / mime when OCR not yet run
        if not sample and ctx.mime_type:
            sample = ctx.mime_type.lower()

        best_cls = DocumentClass.UNKNOWN
        best_score = 0.15
        hits = []
        for cls, patterns, weight in _CLASS_RULES:
            matched = [p for p in patterns if re.search(p, sample, re.I)]
            if matched:
                score = min(0.99, weight + 0.03 * (len(matched) - 1))
                hits.append((cls, score, matched))
                if score > best_score:
                    best_cls, best_score = cls, score

        # Default: treat business document upload as purchase invoice candidate
        if best_cls == DocumentClass.UNKNOWN and (ctx.file_bytes or ctx.images):
            best_cls = DocumentClass.PURCHASE_INVOICE
            best_score = 0.4
            ctx.warnings.append(
                "Document class uncertain — treating as purchase invoice; confirm before Save."
            )

        ctx.document_class = best_cls
        ctx.document_class_score = best_score
        ctx.meta["classify_hits"] = [(c.value, s, m) for c, s, m in hits]
        return ctx
