"""Unit tests for content-aware report column widths."""

from __future__ import annotations

from app.utils.report_col_widths import ColSpec, allocate_widths, measure_content_width


def test_allocate_widths_gives_leftover_to_flex_column():
    specs = (
        ColSpec("item", "Item Title", min_pt=40, max_pt=200, flex=5),
        ColSpec("gp", "GP", min_pt=20, max_pt=40, flex=0.1),
        ColSpec("qty", "Qty", min_pt=30, max_pt=50, flex=0.1),
    )
    content = [50.0, 25.0, 35.0]
    widths = allocate_widths(specs, content, available_pt=200)
    assert abs(sum(widths) - 200) < 0.5
    assert widths[0] > widths[1]
    assert widths[0] > widths[2]
    assert widths[0] <= 200


def test_allocate_widths_respects_min_on_overflow():
    specs = (
        ColSpec("item", "Item", min_pt=60, max_pt=300, flex=8),
        ColSpec("gp", "GP", min_pt=30, max_pt=80, flex=0),
        ColSpec("bill", "Bill", min_pt=30, max_pt=80, flex=0),
    )
    content = [280.0, 70.0, 70.0]  # ideal >> available
    widths = allocate_widths(specs, content, available_pt=150)
    assert abs(sum(widths) - 150) < 0.5
    assert widths[1] >= 30 - 0.01
    assert widths[2] >= 30 - 0.01
    assert widths[0] >= 60 - 0.01


def test_measure_content_width_uses_longest_value():
    w_short = measure_content_width(
        ["Rod"],
        header="Item Title",
        font_name="Helvetica",
        font_size=6.5,
        header_font_size=6.5,
        pad_pt=6,
    )
    w_long = measure_content_width(
        ["COOPER MOULD TUBE 1000-90 RS-12 (7-4)"],
        header="Item Title",
        font_name="Helvetica",
        font_size=6.5,
        header_font_size=6.5,
        pad_pt=6,
    )
    assert w_long > w_short
