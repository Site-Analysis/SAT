# Copyright (c) 2026 Qnit. All rights reserved.
# SPDX-License-Identifier: LicenseRef-Proprietary

"""Datetime utility functions."""

from datetime import UTC, datetime

import pytz


def utc_now() -> datetime:
    """Get current UTC datetime with timezone info."""
    return datetime.now(UTC)


def parse_datetime(dt_str: str, tz: str | None = None) -> datetime:
    """
    Parse datetime string to datetime object.

    Args:
        dt_str: Datetime string (ISO 8601 format)
        tz: Optional timezone string

    Returns:
        Datetime object
    """
    dt = datetime.fromisoformat(dt_str.replace("Z", "+00:00"))

    if tz and dt.tzinfo is None:
        timezone_obj = pytz.timezone(tz)
        dt = timezone_obj.localize(dt)

    return dt


def format_datetime(dt: datetime, fmt: str = "%Y-%m-%d %H:%M:%S") -> str:
    """
    Format datetime object to string.

    Args:
        dt: Datetime object
        fmt: Format string

    Returns:
        Formatted datetime string
    """
    return dt.strftime(fmt)


def convert_timezone(dt: datetime, target_tz: str) -> datetime:
    """
    Convert datetime to target timezone.

    Args:
        dt: Datetime object
        target_tz: Target timezone string

    Returns:
        Converted datetime
    """
    target_timezone = pytz.timezone(target_tz)

    if dt.tzinfo is None:
        dt = pytz.utc.localize(dt)

    return dt.astimezone(target_timezone)


def validate_datetime_range(start: datetime, end: datetime) -> bool:
    """
    Validate that start datetime is before end datetime.

    Args:
        start: Start datetime
        end: End datetime

    Returns:
        True if valid, False otherwise
    """
    return start < end
