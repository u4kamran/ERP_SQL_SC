"""Stage 4 — Detect tables and rows from span geometry."""

from __future__ import annotations

from app.services.purchase_pipeline.base import BaseStage
from app.services.purchase_pipeline.geometry import expand_bbox
from app.services.purchase_pipeline.types import PipelineContext, TableBlock, TableRow, TextSpan


class DetectTablesStage(BaseStage):
    stage_id = 4
    name = "detect_tables"

    def run(self, ctx: PipelineContext) -> PipelineContext:
        spans = list(ctx.printed_spans) or list(ctx.meta.get("all_spans") or [])
        table_regions = [r for r in ctx.layout_regions if r.role == "table"]
        tables: list[TableBlock] = []
        next_row_id = 1

        pages = sorted({s.page for s in spans}) or [0]
        for page in pages:
            page_spans = [s for s in spans if s.page == page]
            region = next((r for r in table_regions if r.page == page), None)
            if region:
                page_spans = [s for s in page_spans if _in_band(s, region.bbox)]
            if not page_spans:
                continue

            rows_groups = _cluster_rows(page_spans, y_tol=16.0)
            rows: list[TableRow] = []
            for group in rows_groups:
                # Skip short header-like single-word rows at top if mostly alpha labels
                text_join = " ".join(g.text for g in group).lower()
                if _looks_like_header(text_join) and not rows:
                    continue
                bbox = expand_bbox(group)
                rows.append(
                    TableRow(
                        row_id=next_row_id,
                        page=page,
                        bbox=bbox,
                        cells=sorted(group, key=lambda s: s.bbox[0]),
                        y_center=(bbox[1] + bbox[3]) / 2.0,
                    )
                )
                next_row_id += 1

            if rows:
                tables.append(
                    TableBlock(
                        page=page,
                        bbox=expand_bbox([c for r in rows for c in r.cells]),
                        rows=rows,
                        header_texts=_guess_headers(page_spans[:12]),
                    )
                )

        ctx.tables = tables
        if not tables:
            ctx.warnings.append("No table rows detected — line extraction may be incomplete.")
        return ctx


def _in_band(span: TextSpan, bbox) -> bool:
    cy = span.cy
    return bbox[1] - 8 <= cy <= bbox[3] + 8


def _cluster_rows(spans: list[TextSpan], y_tol: float) -> list[list[TextSpan]]:
    ordered = sorted(spans, key=lambda s: (s.cy, s.bbox[0]))
    groups: list[list[TextSpan]] = []
    for s in ordered:
        if not groups:
            groups.append([s])
            continue
        if abs(groups[-1][0].cy - s.cy) <= y_tol:
            groups[-1].append(s)
        else:
            groups.append([s])
    return groups


def _looks_like_header(text: str) -> bool:
    keys = ("qty", "quantity", "rate", "price", "amount", "description", "item", "code", "disc", "tax")
    hits = sum(1 for k in keys if k in text)
    return hits >= 2


def _guess_headers(spans: list[TextSpan]) -> list[str]:
    return [s.text for s in spans if len(s.text) < 24][:10]
