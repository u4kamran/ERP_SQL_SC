"""Tests for Default Setup business day configuration."""

import pytest

from app.services.default_setup_store import (
    BusinessDayConfig,
    parse_time_value,
    validate_business_day_times,
)
from app.utils.business_day import (
    business_date_for,
    business_day_end,
    business_day_start,
)


def test_validate_default_times():
    cfg = validate_business_day_times("08:00", "05:00")
    assert cfg.start_hour == 8
    assert cfg.end_hour == 5


def test_reject_identical_start_end():
    with pytest.raises(ValueError, match="identical"):
        validate_business_day_times("08:00", "08:00")


def test_parse_time_invalid():
    with pytest.raises(ValueError):
        parse_time_value("8am", field_name="Day start time")


def test_business_date_for_overnight_window():
    cfg = BusinessDayConfig(start_hour=8, start_minute=0, end_hour=5, end_minute=0)

    def _before(dt):
        from datetime import datetime
        from app.services import default_setup_store

        original = default_setup_store.get_business_day_config
        default_setup_store.get_business_day_config = lambda: cfg
        try:
            return business_date_for(dt)
        finally:
            default_setup_store.get_business_day_config = original

    from datetime import datetime

    assert _before(datetime(2026, 8, 2, 4, 59)) == datetime(2026, 8, 1).date()
    assert _before(datetime(2026, 8, 2, 5, 0)) == datetime(2026, 8, 1).date()
    assert _before(datetime(2026, 8, 2, 8, 0)) == datetime(2026, 8, 2).date()


def test_business_day_end_is_next_calendar_day():
    from datetime import date

    end = business_day_end(date(2026, 8, 1))
    assert end.day == 2
    assert end.hour == 5
    assert end.minute == 0
