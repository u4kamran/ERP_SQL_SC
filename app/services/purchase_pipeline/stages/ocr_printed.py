"""Stage 5 — Extract printed text (high-confidence OCR spans)."""

from __future__ import annotations

from app.services.purchase_pipeline.base import BaseStage
from app.services.purchase_pipeline.types import PipelineContext, TextKind, TextSpan


PRINTED_CONF_MIN = 0.55


class ExtractPrintedOcrStage(BaseStage):
    stage_id = 5
    name = "extract_printed_ocr"

    def run(self, ctx: PipelineContext) -> PipelineContext:
        all_spans: list[TextSpan] = list(ctx.meta.get("all_spans") or [])
        printed = [
            TextSpan(
                text=s.text,
                confidence=s.confidence,
                kind=TextKind.PRINTED,
                page=s.page,
                bbox=s.bbox,
                engine=s.engine,
            )
            for s in all_spans
            if s.confidence >= PRINTED_CONF_MIN and _looks_printed(s)
        ]
        ctx.printed_spans = printed
        if not ctx.ocr_text and printed:
            ctx.ocr_text = "\n".join(s.text for s in sorted(printed, key=lambda x: (x.page, x.cy, x.bbox[0])))
        if not printed:
            ctx.warnings.append("Printed OCR produced no high-confidence spans.")
        return ctx


def _looks_printed(span: TextSpan) -> bool:
    # Digit-heavy handwritten qty often has lower OCR confidence; keep high-conf alphanumerics as printed
    t = span.text.strip()
    if not t:
        return False
    # Extremely short noisy tokens with low conf already filtered
    return True
