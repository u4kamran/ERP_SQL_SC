"""Business day boundaries for sales reports (configurable via Default Setup)."""

from __future__ import annotations

import calendar
from datetime import date, datetime, time, timedelta
from typing import Tuple

from app.services.default_setup_store import BusinessDayConfig, get_business_day_config


def _cfg() -> BusinessDayConfig:
    return get_business_day_config()


def business_day_start_hour() -> int:
    return _cfg().start_hour


def business_day_end_hour() -> int:
    return _cfg().end_hour


def business_day_start_minute() -> int:
    return _cfg().start_minute


def business_day_end_minute() -> int:
    return _cfg().end_minute


def _time_before_business_start(dt: datetime) -> bool:
    return dt.time() < _cfg().start_time


def business_date_for(dt: datetime) -> date:
    """
    Map a timestamp to its business day label.

    Business day D = D @ start → (D+1) @ end.
    Any time before start belongs to the previous calendar date's business day.
    """
    if _time_before_business_start(dt):
        return dt.date() - timedelta(days=1)
    return dt.date()


def business_day_start(d: date) -> datetime:
    cfg = _cfg()
    return datetime.combine(d, time(cfg.start_hour, cfg.start_minute, 0))


def business_day_end(d: date) -> datetime:
    """Inclusive end of business day D (next morning at end time)."""
    cfg = _cfg()
    return datetime.combine(d + timedelta(days=1), time(cfg.end_hour, cfg.end_minute, 0))


def current_business_day_start(now: datetime | None = None) -> datetime:
    now = now or datetime.now()
    return business_day_start(business_date_for(now))


def count_business_days(start: datetime, end: datetime) -> int:
    first = business_date_for(start)
    last = business_date_for(end)
    return max((last - first).days + 1, 1)


def business_day_label(d: date) -> str:
    cfg = _cfg()
    end = d + timedelta(days=1)
    return (
        f"{d.strftime('%d %b %Y')} {cfg.start_time_str}"
        f" → {end.strftime('%d %b')} {cfg.end_time_str}"
    )


def sql_business_date_expr(column: str = "DOC_DATE_T") -> str:
    """SQL Server expression for business day date (SQL 2008 compatible)."""
    cfg = _cfg()
    start_mins = cfg.start_hour * 60 + cfg.start_minute
    return f"""
        CASE
            WHEN (DATEPART(hour, {column}) * 60 + DATEPART(minute, {column})) < {start_mins}
            THEN DATEADD(day, -1, CAST({column} AS DATE))
            ELSE CAST({column} AS DATE)
        END
    """.strip()


def last_calendar_day(year: int, month: int) -> date:
    return date(year, month, calendar.monthrange(year, month)[1])


def shift_date_months(d: date, months: int) -> date:
    month_index = d.month - 1 + months
    year = d.year + month_index // 12
    month = month_index % 12 + 1
    day = min(d.day, calendar.monthrange(year, month)[1])
    return date(year, month, day)


def shift_datetime_months(value: datetime, months: int) -> datetime:
    """Shift a datetime by calendar months (clamps day to month length)."""
    month_index = value.month - 1 + months
    year = value.year + month_index // 12
    month = month_index % 12 + 1
    day = min(value.day, calendar.monthrange(year, month)[1])
    return value.replace(year=year, month=month, day=day)


def _shift_datetime_months(value: datetime, months: int) -> datetime:
    return shift_datetime_months(value, months)


def is_business_day_close(end: datetime) -> bool:
    """True when end time is before configured business-day start (closed day)."""
    return _time_before_business_start(end)


def is_full_calendar_month_period(start_bd: date, end_bd: date, end: datetime) -> bool:
    """Full business month: starts 1st at start time and ends morning after last day."""
    if start_bd.day != 1 or start_bd.month != end_bd.month or start_bd.year != end_bd.year:
        return False
    if not is_business_day_close(end):
        return False
    return end_bd == last_calendar_day(end_bd.year, end_bd.month)


def is_month_end_partial(end_bd: date, end: datetime) -> bool:
    """On last calendar day of month but before close (partial day)."""
    if end_bd != last_calendar_day(end_bd.year, end_bd.month):
        return False
    return not _time_before_business_start(end) and not is_business_day_close(end)


def shift_business_period(
    start: datetime, end: datetime, months: int = -1
) -> Tuple[datetime, datetime]:
    """
    Shift a business-day period back/forward by calendar months.

    Rules:
    - Full month (e.g. last-month): Jun 1 08:00→Jul 1 05:00 compares to May 1 08:00→Jun 1 05:00
    - Single day (yesterday): 30 Jul 08:00→31 Jul 05:00 compares to 30 Jun 08:00→01 Jul 05:00
    - Month-end partial (this-month on 31st): compares to full previous month close
    - Other partial periods: same clock time one month earlier
    """
    start_bd = business_date_for(start)
    end_bd = business_date_for(end)
    prev_start_bd = shift_date_months(start_bd, months)
    prev_start = business_day_start(prev_start_bd)

    if is_full_calendar_month_period(start_bd, end_bd, end):
        prev_last = last_calendar_day(prev_start_bd.year, prev_start_bd.month)
        return prev_start, business_day_end(prev_last)

    if is_business_day_close(end):
        prev_end_bd = shift_date_months(end_bd, months)
        prev_end = business_day_end(prev_end_bd)
        if prev_end <= prev_start:
            prev_end = business_day_end(prev_start_bd)
        return prev_start, prev_end

    if is_month_end_partial(end_bd, end):
        prev_last = last_calendar_day(prev_start_bd.year, prev_start_bd.month)
        return prev_start, business_day_end(prev_last)

    prev_end = _shift_datetime_months(end, months)
    if prev_end <= prev_start and is_business_day_close(end):
        prev_end = business_day_end(shift_date_months(end_bd, months))
    return prev_start, prev_end


def align_previous_trend_dates(rows: list[dict], months: int = 1) -> list[dict]:
    """Shift previous-period sale_date forward for chart overlay with current period."""
    aligned: list[dict] = []
    for row in rows:
        sale_date = row.get("sale_date")
        if not sale_date:
            aligned.append(row)
            continue
        d = date.fromisoformat(str(sale_date)[:10])
        aligned.append({**row, "sale_date": shift_date_months(d, months).isoformat()})
    return aligned


def date_range_for_preset(preset: str, now: datetime | None = None) -> Tuple[datetime, datetime]:
    """Date ranges using business-day boundaries."""
    now = now or datetime.now()
    preset = (preset or "this-month").strip().lower()
    cfg = _cfg()
    start_t = time(cfg.start_hour, cfg.start_minute, 0)

    if preset == "today":
        bd = business_date_for(now)
        return business_day_start(bd), now

    if preset == "yesterday":
        bd = business_date_for(now) - timedelta(days=1)
        return business_day_start(bd), business_day_end(bd)

    if preset == "last-month":
        if now.month == 1:
            y, m = now.year - 1, 12
        else:
            y, m = now.year, now.month - 1
        last_d = last_calendar_day(y, m)
        start = business_day_start(date(y, m, 1))
        end = business_day_end(last_d)
        return start, end

    if preset == "last-7":
        bd = business_date_for(now)
        start_bd = bd - timedelta(days=6)
        return business_day_start(start_bd), now

    if preset == "last-30":
        bd = business_date_for(now)
        start_bd = bd - timedelta(days=29)
        return business_day_start(start_bd), now

    # this-month (default)
    start = datetime.combine(date(now.year, now.month, 1), start_t)
    if now < start:
        if now.month == 1:
            start = datetime.combine(date(now.year - 1, 12, 1), start_t)
        else:
            start = datetime.combine(date(now.year, now.month - 1, 1), start_t)
    return start, now


def default_report_range(now: datetime | None = None) -> Tuple[datetime, datetime]:
    """Default range for API when no dates passed: this month, business hours."""
    return date_range_for_preset("this-month", now)


def cumulative_period_label(start: datetime, end: datetime) -> str:
    """Label for cumulative sales row: fixed start -> varying end (matches SSMS report)."""
    cfg = _cfg()
    return (
        f"{start.strftime('%d %b %Y')} {cfg.start_time_str}"
        f" -> {end.strftime('%d %b %Y')} {cfg.end_time_str}"
    )


def cumulative_period_ends(
    start_date: datetime, end_date: datetime
) -> Tuple[datetime, list[datetime]]:
    """
    Build cumulative period end timestamps.

    Fixed start = business_day_start(business_date_for(start_date)).
    Each row ends at business_day_end(bd) for bd from start_bd through end_bd inclusive.
    Returns (fixed_start, [end1, end2, ...]) or (fixed_start, []) when invalid/empty.
    """
    if end_date < start_date:
        return business_day_start(business_date_for(start_date)), []

    start_bd = business_date_for(start_date)
    end_bd = business_date_for(end_date)
    fixed_start = business_day_start(start_bd)

    ends: list[datetime] = []
    bd = start_bd
    while bd <= end_bd:
        ends.append(business_day_end(bd))
        bd += timedelta(days=1)
    return fixed_start, ends


def business_hours_note() -> str:
    return _cfg().hours_note()
