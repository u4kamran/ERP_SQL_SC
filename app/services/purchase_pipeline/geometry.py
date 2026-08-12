"""Geometry helpers for handwriting ↔ row association."""

from __future__ import annotations

from typing import Iterable, Optional, Tuple

from app.services.purchase_pipeline.types import BBox, TextSpan


def bbox_overlap_ratio(a: BBox, b: BBox) -> float:
    ax0, ay0, ax1, ay1 = a
    bx0, by0, bx1, by1 = b
    ix0, iy0 = max(ax0, bx0), max(ay0, by0)
    ix1, iy1 = min(ax1, bx1), min(ay1, by1)
    iw, ih = max(0.0, ix1 - ix0), max(0.0, iy1 - iy0)
    inter = iw * ih
    if inter <= 0:
        return 0.0
    area_a = max(1e-6, (ax1 - ax0) * (ay1 - ay0))
    area_b = max(1e-6, (bx1 - bx0) * (by1 - by0))
    return inter / min(area_a, area_b)


def vertical_distance(a: BBox, b: BBox) -> float:
    return abs(((a[1] + a[3]) / 2.0) - ((b[1] + b[3]) / 2.0))


def horizontal_distance(a: BBox, b: BBox) -> float:
    return abs(((a[0] + a[2]) / 2.0) - ((b[0] + b[2]) / 2.0))


def row_alignment_score(span: TextSpan, row_bbox: BBox, *, row_height: float = 24.0) -> float:
    """1.0 when vertically centered on the row, decaying with distance."""
    dist = vertical_distance(span.bbox, row_bbox)
    if dist <= row_height * 0.35:
        return 1.0
    if dist >= row_height * 1.5:
        return 0.0
    return max(0.0, 1.0 - (dist / (row_height * 1.5)))


def proximity_score(span: TextSpan, row_bbox: BBox) -> float:
    """Combine vertical alignment, overlap, and horizontal closeness."""
    align = row_alignment_score(span, row_bbox)
    overlap = bbox_overlap_ratio(span.bbox, row_bbox)
    # Prefer spans inside or just to the right/left of the row band
    v_pen = vertical_distance(span.bbox, row_bbox)
    h_pen = horizontal_distance(span.bbox, row_bbox)
    dist_score = 1.0 / (1.0 + (v_pen / 40.0) + (h_pen / 400.0))
    return 0.45 * align + 0.35 * overlap + 0.20 * dist_score


def best_row_for_span(
    span: TextSpan,
    rows: Iterable[Tuple[int, BBox]],
    *,
    min_score: float = 0.35,
) -> Optional[Tuple[int, float]]:
    best_id: Optional[int] = None
    best_score = 0.0
    for row_id, bbox in rows:
        score = proximity_score(span, bbox)
        if score > best_score:
            best_score = score
            best_id = row_id
    if best_id is None or best_score < min_score:
        return None
    return best_id, best_score


def expand_bbox(spans: Iterable[TextSpan]) -> BBox:
    xs0, ys0, xs1, ys1 = [], [], [], []
    for s in spans:
        xs0.append(s.bbox[0])
        ys0.append(s.bbox[1])
        xs1.append(s.bbox[2])
        ys1.append(s.bbox[3])
    if not xs0:
        return (0.0, 0.0, 0.0, 0.0)
    return (min(xs0), min(ys0), max(xs1), max(ys1))
