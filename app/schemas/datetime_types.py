"""Shared datetime types for API responses."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Annotated, Optional

from pydantic import PlainSerializer


def serialize_utc_datetime(value: datetime | None) -> str | None:
    """Serialize naive UTC datetimes from SQL Server with a Z suffix."""
    if value is None:
        return None
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    else:
        value = value.astimezone(timezone.utc)
    return value.isoformat().replace("+00:00", "Z")


UtcDatetime = Annotated[
    datetime,
    PlainSerializer(serialize_utc_datetime, when_used="json"),
]
OptionalUtcDatetime = Annotated[
    Optional[datetime],
    PlainSerializer(serialize_utc_datetime, when_used="json"),
]
