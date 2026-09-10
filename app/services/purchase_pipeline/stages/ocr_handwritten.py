"""Stage 6 — Detect handwritten text separately from printed OCR."""

from __future__ import annotations

import re

from app.services.purchase_pipeline.base import BaseStage
from app.services.purchase_pipeline.types import PipelineContext, TextKind, TextSpan


HW_CONF_MAX = 0.72
_MANUAL_HINT = re.compile(r"^\d{1,8}$")


class DetectHandwrittenStage(BaseStage):
    stage_id = 6
    name = "detect_handwritten"

    def run(self, ctx: PipelineContext) -> PipelineContext:
        all_spans: list[TextSpan] = list(ctx.meta.get("all_spans") or [])
        printed_keys = {(s.page, round(s.cy, 1), s.text.lower()) for s in ctx.printed_spans}

        handwritten: list[TextSpan] = []
        for s in all_spans:
            key = (s.page, round(s.cy, 1), s.text.lower())
            is_low_conf = s.confidence < HW_CONF_MAX
            is_manual_like = bool(_MANUAL_HINT.match(s.text.strip()))
            # Handwriting heuristic: lower confidence OR short numeric codes near table rows
            # that were not confidently classified as printed product codes
            if is_low_conf or (is_manual_like and s.confidence < 0.9):
                # Avoid duplicating strong printed description lines
                if key in printed_keys and s.confidence >= HW_CONF_MAX and not is_manual_like:
                    continue
                handwritten.append(
                    TextSpan(
                        text=s.text,
                        confidence=s.confidence,
                        kind=TextKind.HANDWRITTEN,
                        page=s.page,
                        bbox=s.bbox,
                        engine=s.engine,
                    )
                )

        # Prefer unique handwritten spans
        uniq: list[TextSpan] = []
        seen = set()
        for h in handwritten:
            k = (h.page, h.text.lower(), round(h.cy, 0), round(h.bbox[0], 0))
            if k in seen:
                continue
            seen.add(k)
            uniq.append(h)

        ctx.handwritten_spans = uniq
        ctx.meta["handwritten_count"] = len(uniq)
        return ctx
