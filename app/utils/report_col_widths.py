"""Content-aware column widths for report tables (PDF / print).

Widths are derived from the current filtered dataset: header length, longest
practical cell text, min/max caps, and flex priority. Numeric columns stay
compact; description columns take remaining space.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Sequence

from reportlab.pdfbase.pdfmetrics import stringWidth


@dataclass(frozen=True)
class ColSpec:
    key: str
    header: str
    min_pt: float
    max_pt: float
    flex: float = 0.0  # share of leftover space after mins
    pad_pt: float = 6.0
    font_name: str = "Helvetica"
    font_size: float = 6.5
    header_font_size: float = 6.5


def _text_width(text: str, font_name: str, font_size: float) -> float:
    return stringWidth(text or "", font_name, font_size)


def measure_content_width(
    values: Iterable[str],
    *,
    header: str,
    font_name: str,
    font_size: float,
    header_font_size: float,
    pad_pt: float,
) -> float:
    widest = _text_width(header, font_name, header_font_size)
    for value in values:
        widest = max(widest, _text_width(str(value or ""), font_name, font_size))
    return widest + pad_pt


def allocate_widths(
    specs: Sequence[ColSpec],
    content_widths: Sequence[float],
    available_pt: float,
) -> list[float]:
    """Fit columns into available_pt using content, min/max, and flex priority."""
    if len(specs) != len(content_widths):
        raise ValueError("specs and content_widths length mismatch")
    if available_pt <= 0:
        raise ValueError("available_pt must be positive")

    # Ideal = clamp(content, min, max)
    ideal = [
        min(spec.max_pt, max(spec.min_pt, content))
        for spec, content in zip(specs, content_widths)
    ]
    total_ideal = sum(ideal)

    if abs(total_ideal - available_pt) < 0.5:
        return ideal

    if total_ideal < available_pt:
        leftover = available_pt - total_ideal
        flex_total = sum(spec.flex for spec in specs)
        widths = list(ideal)
        if flex_total <= 0:
            room = [spec.max_pt - w for spec, w in zip(specs, ideal)]
            room_total = sum(max(0.0, r) for r in room)
            if room_total <= 0:
                # No capped room — give leftover to the first column
                widths[0] += leftover
                return widths
            return [
                w + leftover * (max(0.0, r) / room_total)
                for w, r in zip(ideal, room)
            ]
        room = [max(0.0, spec.max_pt - w) for spec, w in zip(specs, widths)]
        weighted = [spec.flex * r for spec, r in zip(specs, room)]
        weight_sum = sum(weighted)
        remaining = leftover
        if weight_sum > 0:
            for i, _spec in enumerate(specs):
                share = remaining * (weighted[i] / weight_sum)
                take = min(share, room[i])
                widths[i] += take
        # Any leftover after max caps goes to the highest-flex column (Item Title).
        remaining = available_pt - sum(widths)
        if remaining > 0.01:
            flex_idx = max(range(len(specs)), key=lambda i: specs[i].flex)
            widths[flex_idx] += remaining
        return widths

    # Overflow: shrink low-flex columns first (keep description as wide as possible)
    widths = list(ideal)
    overflow = total_ideal - available_pt
    # Shrinkable amount above min, ordered by ascending flex then by excess
    candidates = sorted(
        range(len(specs)),
        key=lambda i: (specs[i].flex, -(widths[i] - specs[i].min_pt)),
    )
    for i in candidates:
        if overflow <= 0:
            break
        shrinkable = widths[i] - specs[i].min_pt
        if shrinkable <= 0:
            continue
        take = min(shrinkable, overflow)
        widths[i] -= take
        overflow -= take

    if overflow > 0:
        # Last resort: shrink even flexed columns toward min
        for i in sorted(range(len(specs)), key=lambda j: -specs[j].flex):
            if overflow <= 0:
                break
            shrinkable = widths[i] - specs[i].min_pt
            if shrinkable <= 0:
                continue
            take = min(shrinkable, overflow)
            widths[i] -= take
            overflow -= take

    drift = available_pt - sum(widths)
    if abs(drift) > 0.01 and widths:
        widths[-1] += drift
    return widths
