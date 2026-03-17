#!/usr/bin/env python3
"""Deterministic parsing for supported journal time expressions."""

from __future__ import annotations

import re
from datetime import UTC, date, datetime, time, timedelta

from journal.journalerrors import JournalQueryError

AGO_PATTERN = re.compile(r"^(?P<amount>\d+)\s+(?P<unit>minute|minutes|hour|hours|day|days)\s+ago$")
TODAY_AT_PATTERN = re.compile(r"^(today)\s+at\s+(?P<hour>\d{1,2}):(?P<minute>\d{2})$")

WEEKDAY_LOOKUP = {
    "monday": 0,
    "tuesday": 1,
    "wednesday": 2,
    "thursday": 3,
    "friday": 4,
    "saturday": 5,
    "sunday": 6,
}


def resolve_time_value(value: datetime | str | None, *, now: datetime) -> datetime | None:
    """
    Resolve a supported query time value to a UTC datetime.

    Args:
        value: Explicit datetime or supported time expression.
        now: Reference point for relative time expressions.

    Returns:
        A resolved UTC datetime, or None if the input is None.

    Raises:
        JournalQueryError: If the time value is not supported.
    """
    if value is None:
        return None

    if isinstance(value, datetime):
        if value.tzinfo is not None:
            return value.astimezone(UTC)
        raise JournalQueryError("query datetimes must be timezone-aware")

    normalized_value = value.strip().lower()

    if not normalized_value:
        return None

    iso_value = _parse_iso_datetime(value=normalized_value)
    if iso_value is not None:
        return iso_value

    if normalized_value == "today":
        return _date_start(current_date=now.date())

    if normalized_value == "yesterday":
        return _date_start(current_date=now.date() - timedelta(days=1))

    ago_match = AGO_PATTERN.match(normalized_value)
    if ago_match:
        return _parse_ago_expression(match=ago_match, now=now)

    today_at_match = TODAY_AT_PATTERN.match(normalized_value)
    if today_at_match:
        return _combine_date_time(
            current_date=now.date(),
            hour=int(today_at_match.group("hour")),
            minute=int(today_at_match.group("minute")),
        )

    if normalized_value.startswith("last "):
        weekday_name = normalized_value.removeprefix("last ").strip()
        if weekday_name in WEEKDAY_LOOKUP:
            return _last_weekday(reference_date=now.date(), weekday_name=weekday_name)

    raise JournalQueryError(f"unsupported time expression: {value}")


def _parse_iso_datetime(*, value: str) -> datetime | None:
    """Parse an ISO 8601 datetime string when possible."""
    normalized_value = value.replace("z", "+00:00")

    try:
        parsed_value = datetime.fromisoformat(normalized_value)
    except ValueError:
        return None

    if parsed_value.tzinfo is None:
        raise JournalQueryError("ISO datetime values must be timezone-aware")

    return parsed_value.astimezone(UTC)


def _parse_ago_expression(*, match: re.Match[str], now: datetime) -> datetime:
    """Convert an 'N units ago' expression into a UTC datetime."""
    amount = int(match.group("amount"))
    unit = match.group("unit")
    delta: timedelta

    if unit in {"minute", "minutes"}:
        delta = timedelta(minutes=amount)
    elif unit in {"hour", "hours"}:
        delta = timedelta(hours=amount)
    else:
        delta = timedelta(days=amount)

    return now - delta


def _combine_date_time(*, current_date: date, hour: int, minute: int) -> datetime:
    """Combine a date with hour/minute values as a UTC datetime."""
    if hour > 23 or minute > 59:
        raise JournalQueryError("time expressions must use valid 24-hour time")

    return datetime.combine(current_date, time(hour=hour, minute=minute, tzinfo=UTC))


def _date_start(*, current_date: date) -> datetime:
    """Return the start of a date in UTC."""
    return datetime.combine(current_date, time.min, tzinfo=UTC)


def _last_weekday(*, reference_date: date, weekday_name: str) -> datetime:
    """Return the previous named weekday at midnight UTC."""
    target_weekday = WEEKDAY_LOOKUP[weekday_name]
    day_delta = (reference_date.weekday() - target_weekday) % 7

    if day_delta == 0:
        day_delta = 7

    return _date_start(current_date=reference_date - timedelta(days=day_delta))
