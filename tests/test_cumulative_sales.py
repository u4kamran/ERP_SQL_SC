"""Tests for cumulative sales period generation."""

from datetime import datetime

import pytest

from app.utils.business_day import (
    business_day_end,
    business_day_start,
    cumulative_period_ends,
    cumulative_period_label,
)


def test_cumulative_period_ends_four_rows_aug_1_to_aug_5():
    """From 01 Aug 08:00 to 05 Aug 05:00 → exactly 4 cumulative periods."""
    start = datetime(2026, 8, 1, 8, 0, 0)
    end = datetime(2026, 8, 5, 5, 0, 0)
    fixed_start, ends = cumulative_period_ends(start, end)

    assert fixed_start == business_day_start(datetime(2026, 8, 1, 8, 0).date())
    assert len(ends) == 4
    assert ends[0] == business_day_end(datetime(2026, 8, 1).date())
    assert ends[-1] == business_day_end(datetime(2026, 8, 4).date())
    assert ends[-1] == datetime(2026, 8, 5, 5, 0, 0)


def test_cumulative_period_labels_fixed_start():
    """All rows share the same start; only end advances."""
    start = datetime(2026, 8, 1, 8, 0, 0)
    end = datetime(2026, 8, 5, 5, 0, 0)
    fixed_start, ends = cumulative_period_ends(start, end)

    labels = [cumulative_period_label(fixed_start, pe) for pe in ends]
    assert labels[0] == "01 Aug 2026 08:00 -> 02 Aug 2026 05:00"
    assert labels[1] == "01 Aug 2026 08:00 -> 03 Aug 2026 05:00"
    assert labels[2] == "01 Aug 2026 08:00 -> 04 Aug 2026 05:00"
    assert labels[3] == "01 Aug 2026 08:00 -> 05 Aug 2026 05:00"
    assert all(l.startswith("01 Aug 2026 08:00") for l in labels)


def test_cumulative_period_not_day_wise_sliding():
    """Must not produce 02 Aug → 03 Aug style rows."""
    start = datetime(2026, 8, 1, 8, 0, 0)
    end = datetime(2026, 8, 5, 5, 0, 0)
    fixed_start, ends = cumulative_period_ends(start, end)
    labels = [cumulative_period_label(fixed_start, pe) for pe in ends]

    assert not any(l.startswith("02 Aug 2026 08:00") for l in labels)
    assert not any(l.startswith("03 Aug 2026 08:00") for l in labels)


def test_cumulative_single_day_range():
    """From = To on same business day → one row."""
    start = datetime(2026, 8, 1, 8, 0, 0)
    end = datetime(2026, 8, 2, 5, 0, 0)
    fixed_start, ends = cumulative_period_ends(start, end)
    assert len(ends) == 1


def test_cumulative_invalid_range():
    """From after To → empty."""
    start = datetime(2026, 8, 10, 8, 0, 0)
    end = datetime(2026, 8, 1, 8, 0, 0)
    _, ends = cumulative_period_ends(start, end)
    assert ends == []


def test_cumulative_month_boundary():
    """Handles month change correctly."""
    start = datetime(2026, 7, 30, 8, 0, 0)
    end = datetime(2026, 8, 2, 5, 0, 0)
    fixed_start, ends = cumulative_period_ends(start, end)
    assert len(ends) == 3
    label = cumulative_period_label(fixed_start, ends[-1])
    assert label == "30 Jul 2026 08:00 -> 02 Aug 2026 05:00"


def test_shift_datetime_months_for_cumulative_prev():
    from app.utils.business_day import shift_datetime_months

    dt = datetime(2026, 8, 1, 8, 0, 0)
    prev = shift_datetime_months(dt, -1)
    assert prev == datetime(2026, 7, 1, 8, 0, 0)

    end = datetime(2026, 8, 2, 5, 0, 0)
    assert shift_datetime_months(end, -1) == datetime(2026, 7, 2, 5, 0, 0)
