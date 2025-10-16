"""
Time utility functions for timestamp generation.

This module provides pure functions for generating ISO 8601 formatted
timestamps in UTC timezone.
"""
from datetime import datetime
from typing import Optional


def get_current_timestamp(dt: Optional[datetime] = None) -> str:
    """
    Generate an ISO 8601 formatted timestamp string in UTC.

    This function is designed to be pure by accepting an optional datetime
    parameter for testing purposes. When no datetime is provided, it uses
    the current UTC time.

    Args:
        dt: Optional datetime object to format. If None, uses current UTC time.

    Returns:
        str: ISO 8601 formatted timestamp string with 'Z' suffix indicating UTC
             (format: YYYY-MM-DDTHH:MM:SSZ)

    Examples:
        >>> get_current_timestamp(datetime(2025, 10, 16, 12, 0, 0))
        '2025-10-16T12:00:00Z'
    """
    if dt is None:
        dt = datetime.utcnow()

    # Format to ISO 8601 with 'Z' suffix for UTC
    # Using manual formatting to ensure consistent format
    timestamp = dt.strftime('%Y-%m-%dT%H:%M:%SZ')

    return timestamp
