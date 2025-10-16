"""
Unit tests for time utility functions.

Tests the timestamp generation functionality to ensure it produces
valid ISO 8601 formatted timestamps in UTC timezone.
"""
import re
from datetime import datetime
import pytest


def test_get_current_timestamp_returns_string():
    """Should return a string type when generating timestamp."""
    from src.time_utils import get_current_timestamp

    result = get_current_timestamp()

    assert isinstance(result, str), "Timestamp should be a string"


def test_get_current_timestamp_follows_iso8601_format():
    """Should return timestamp in ISO 8601 format (YYYY-MM-DDTHH:MM:SSZ)."""
    from src.time_utils import get_current_timestamp

    result = get_current_timestamp()

    # ISO 8601 format: 2025-10-16T12:00:00Z
    iso8601_pattern = r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$'
    assert re.match(iso8601_pattern, result), \
        f"Timestamp '{result}' does not match ISO 8601 format"


def test_get_current_timestamp_uses_utc_timezone():
    """Should return timestamp with UTC timezone indicator (Z suffix)."""
    from src.time_utils import get_current_timestamp

    result = get_current_timestamp()

    assert result.endswith('Z'), \
        "Timestamp should end with 'Z' to indicate UTC timezone"


def test_get_current_timestamp_is_current():
    """Should return timestamp close to current time (within 1 second)."""
    from src.time_utils import get_current_timestamp

    before = datetime.utcnow()
    result = get_current_timestamp()
    after = datetime.utcnow()

    # Parse the returned timestamp (remove Z and parse)
    timestamp_dt = datetime.fromisoformat(result.replace('Z', '+00:00'))

    # Check it's between before and after (allowing for small time differences)
    assert before <= timestamp_dt.replace(tzinfo=None) <= after, \
        "Timestamp should represent current time"


def test_get_current_timestamp_with_custom_time():
    """Should return correctly formatted timestamp when given a datetime object."""
    from src.time_utils import get_current_timestamp
    from datetime import datetime

    # Test with a specific datetime
    test_datetime = datetime(2025, 10, 16, 12, 0, 0)
    result = get_current_timestamp(test_datetime)

    assert result == "2025-10-16T12:00:00Z", \
        f"Expected '2025-10-16T12:00:00Z' but got '{result}'"
