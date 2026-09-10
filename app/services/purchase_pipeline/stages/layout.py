"""Stage 3 — Analyze page layout (header / table / footer bands)."""

from __future__ import annotations

from app.services.purchase_pipeline.base import BaseStage
from app.services.purchase_pipeline.types import LayoutRegion, PipelineContext, TextSpan


class AnalyzeLayoutStage(BaseStage):
    stage_id = 3
    name = "analyze_layout"

    def run(self, ctx: PipelineContext) -> PipelineContext:
        spans = list(ctx.printed_spans) + list(ctx.handwritten_spans)
        # If OCR not yet split, use whatever spans exist in meta
        if not spans and ctx.meta.get("all_spans"):
            spans = list(ctx.meta["all_spans"])

        regions: list[LayoutRegion] = []
        by_page: dict[int, list[TextSpan]] = {}
        for s in spans:
            by_page.setdefault(s.page, []).append(s)

        if not by_page and ctx.images:
            for i, img in enumerate(ctx.images):
                w, h = getattr(img, "size", (1000, 1400))
                regions.extend(_default_bands(i, float(w), float(h)))
            ctx.layout_regions = regions
            return ctx

        for page, page_spans in by_page.items():
            ys = [s.cy for s in page_spans]
            xs = [s.bbox[0] for s in page_spans] + [s.bbox[2] for s in page_spans]
            if not ys:
                continue
            y_min, y_max = min(ys), max(ys)
            x_min, x_max = min(xs), max(xs)
            height = max(1.0, y_max - y_min)
            header_y = y_min + height * 0.18
            footer_y = y_min + height * 0.82
            regions.append(
                LayoutRegion("header", page, (x_min, y_min, x_max, header_y), role="header")
            )
            regions.append(
                LayoutRegion(
                    "table_band", page, (x_min, header_y, x_max, footer_y), role="table"
                )
            )
            regions.append(
                LayoutRegion("footer", page, (x_min, footer_y, x_max, y_max), role="footer")
            )

        ctx.layout_regions = regions
        return ctx


def _default_bands(page: int, w: float, h: float) -> list[LayoutRegion]:
    return [
        LayoutRegion("header", page, (0, 0, w, h * 0.18), "header"),
        LayoutRegion("table_band", page, (0, h * 0.18, w, h * 0.82), "table"),
        LayoutRegion("footer", page, (0, h * 0.82, w, h), "footer"),
    ]
