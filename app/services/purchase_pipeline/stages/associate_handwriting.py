"""Stage 7 — Associate handwritten values with nearest product rows."""

from __future__ import annotations

import re

from app.services.purchase_pipeline.base import BaseStage
from app.services.purchase_pipeline.geometry import best_row_for_span
from app.services.purchase_pipeline.types import PipelineContext


class AssociateHandwritingStage(BaseStage):
    stage_id = 7
    name = "associate_handwriting"

    def run(self, ctx: PipelineContext) -> PipelineContext:
        rows = []
        for table in ctx.tables:
            for row in table.rows:
                rows.append((row.row_id, row.bbox))

        associations = []
        if not rows:
            # Synthesize rows from printed span clusters if tables empty
            ctx.meta["handwriting_associations"] = []
            if ctx.handwritten_spans:
                ctx.warnings.append(
                    "Handwritten text found but no table rows to associate — review manual IDs."
                )
            return ctx

        for span in ctx.handwritten_spans:
            hit = best_row_for_span(span, rows, min_score=0.35)
            if not hit:
                associations.append(
                    {"text": span.text, "row_id": None, "score": 0.0, "page": span.page}
                )
                continue
            row_id, score = hit
            # Prefer numeric handwritten values as manual IDs; boost right-side spans
            if re.fullmatch(r"\d{1,10}", (span.text or "").strip()):
                score = min(1.0, score + 0.15)
                # Right-side of row bbox boost
                for table in ctx.tables:
                    for row in table.rows:
                        if row.row_id == row_id and row.bbox:
                            mid_x = (row.bbox[0] + row.bbox[2]) / 2.0
                            if span.bbox[0] >= mid_x:
                                score = min(1.0, score + 0.1)
            span.row_id = row_id
            associations.append(
                {
                    "text": span.text,
                    "row_id": row_id,
                    "score": round(score, 3),
                    "page": span.page,
                    "bbox": span.bbox,
                }
            )
            for table in ctx.tables:
                for row in table.rows:
                    if row.row_id == row_id:
                        row.cells.append(span)

        ctx.meta["handwriting_associations"] = associations
        orphan = sum(1 for a in associations if a["row_id"] is None)
        if orphan:
            ctx.warnings.append(
                f"{orphan} handwritten value(s) could not be associated to a product row."
            )
        return ctx
