"""Validate business-day presets and month-over-month comparison ranges."""

from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.utils.business_day import date_range_for_preset, shift_business_period


def fmt(dt: datetime) -> str:
    return dt.strftime("%d-%m-%Y %H:%M")


def assert_range(label: str, start: datetime, end: datetime, ps: datetime, pe: datetime) -> None:
    if end < start:
        raise AssertionError(f"{label}: current end before start ({fmt(end)} < {fmt(start)})")
    if pe <= ps:
        raise AssertionError(f"{label}: compare end before compare start ({fmt(pe)} <= {fmt(ps)})")
    if pe.hour == 5 and pe.minute == 0 and pe.date() == ps.date():
        raise AssertionError(f"{label}: compare end same day 05:00 ({fmt(pe)})")


def check(preset: str, now: datetime, cs: str, ce: str, ps: str, pe: str) -> None:
    s, e = date_range_for_preset(preset, now)
    pstart, pend = shift_business_period(s, e, -1)
    label = f"{preset} @ {fmt(now)}"
    assert_range(label, s, e, pstart, pend)
    assert fmt(s) == cs, f"{label} start: {fmt(s)} != {cs}"
    assert fmt(e) == ce, f"{label} end: {fmt(e)} != {ce}"
    assert fmt(pstart) == ps, f"{label} prev start: {fmt(pstart)} != {ps}"
    assert fmt(pend) == pe, f"{label} prev end: {fmt(pend)} != {pe}"


def main() -> None:
    presets = ["today", "yesterday", "this-month", "last-month", "last-7", "last-30"]
    now_list = [
        datetime(2026, 7, 31, 18, 0),
        datetime(2026, 7, 31, 4, 0),
        datetime(2026, 8, 1, 4, 0),
        datetime(2026, 8, 1, 10, 0),
        datetime(2026, 3, 31, 20, 0),
        datetime(2026, 1, 31, 20, 0),
        datetime(2026, 2, 28, 20, 0),
    ]
    for now in now_list:
        for preset in presets:
            s, e = date_range_for_preset(preset, now)
            ps, pe = shift_business_period(s, e, -1)
            assert_range(f"{preset} @ {fmt(now)}", s, e, ps, pe)

    check("yesterday", datetime(2026, 7, 31, 10, 0),
          "30-07-2026 08:00", "31-07-2026 05:00", "30-06-2026 08:00", "01-07-2026 05:00")
    check("last-month", datetime(2026, 7, 31, 18, 0),
          "01-06-2026 08:00", "01-07-2026 05:00", "01-05-2026 08:00", "01-06-2026 05:00")
    check("last-month", datetime(2026, 8, 1, 10, 0),
          "01-07-2026 08:00", "01-08-2026 05:00", "01-06-2026 08:00", "01-07-2026 05:00")
    check("this-month", datetime(2026, 7, 31, 18, 0),
          "01-07-2026 08:00", "31-07-2026 18:00", "01-06-2026 08:00", "01-07-2026 05:00")
    check("last-month", datetime(2026, 1, 31, 20, 0),
          "01-12-2025 08:00", "01-01-2026 05:00", "01-11-2025 08:00", "01-12-2025 05:00")
    check("last-month", datetime(2026, 3, 31, 20, 0),
          "01-02-2026 08:00", "01-03-2026 05:00", "01-01-2026 08:00", "01-02-2026 05:00")

    print("ALL CHECKS PASSED")


def check_yesterday_summary_data() -> None:
    """Yesterday preset must return non-zero last-month comparison when DB has data."""
    from datetime import datetime

    from app.database.business_session import BusinessSessionLocal
    from app.schemas.sales_dashboard import SalesDashboardRequest
    from app.services.sales_dashboard_service import SalesDashboardService

    now = datetime(2026, 7, 31, 18, 0)
    start, end = date_range_for_preset("yesterday", now)
    ps, pe = shift_business_period(start, end, -1)
    if pe <= ps:
        raise AssertionError(f"yesterday compare range invalid: {fmt(ps)} -> {fmt(pe)}")

    db = BusinessSessionLocal()
    try:
        summary = SalesDashboardService(db).get_summary(
            SalesDashboardRequest(start_date=start, end_date=end)
        )
    finally:
        db.close()

    if summary.current.total_sale <= 0:
        print("SKIP yesterday summary data check (no current sales in DB)")
        return
    if summary.previous.total_sale <= 0:
        raise AssertionError(
            f"yesterday last-month sale is zero; compare range {fmt(ps)} -> {fmt(pe)}"
        )
    print(f"yesterday MoM OK: current={summary.current.total_sale:.2f} previous={summary.previous.total_sale:.2f}")


if __name__ == "__main__":
    main()
    check_yesterday_summary_data()
