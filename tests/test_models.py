"""
Unit tests for Pydantic response models.

Tests the StatusResponse model to ensure proper validation,
serialization, and schema compliance.
"""
import pytest
from pydantic import ValidationError


def test_status_response_model_exists():
    """Should be able to import StatusResponse model."""
    from src.models import StatusResponse

    assert StatusResponse is not None


def test_status_response_with_required_fields():
    """Should create StatusResponse with only the required status field."""
    from src.models import StatusResponse

    response = StatusResponse(status="ok")

    assert response.status == "ok"
    assert hasattr(response, 'timestamp')


def test_status_response_with_all_fields():
    """Should create StatusResponse with both status and timestamp fields."""
    from src.models import StatusResponse

    response = StatusResponse(
        status="ok",
        timestamp="2025-10-16T12:00:00Z"
    )

    assert response.status == "ok"
    assert response.timestamp == "2025-10-16T12:00:00Z"


def test_status_response_missing_required_status():
    """Should raise ValidationError when status field is missing."""
    from src.models import StatusResponse

    with pytest.raises(ValidationError) as exc_info:
        StatusResponse(timestamp="2025-10-16T12:00:00Z")

    error = exc_info.value
    assert 'status' in str(error), "Error should mention missing 'status' field"


def test_status_response_json_serialization():
    """Should serialize to JSON correctly with all fields."""
    from src.models import StatusResponse

    response = StatusResponse(
        status="ok",
        timestamp="2025-10-16T12:00:00Z"
    )

    json_data = response.model_dump()

    assert json_data == {
        "status": "ok",
        "timestamp": "2025-10-16T12:00:00Z"
    }


def test_status_response_json_serialization_without_timestamp():
    """Should serialize to JSON correctly when timestamp is not provided."""
    from src.models import StatusResponse

    response = StatusResponse(status="ok")

    json_data = response.model_dump(exclude_none=True)

    assert "status" in json_data
    assert json_data["status"] == "ok"


def test_status_response_status_is_string():
    """Should accept string values for status field."""
    from src.models import StatusResponse

    response = StatusResponse(status="healthy")

    assert isinstance(response.status, str)
    assert response.status == "healthy"


def test_status_response_timestamp_is_optional():
    """Should allow timestamp to be None or omitted."""
    from src.models import StatusResponse

    response = StatusResponse(status="ok", timestamp=None)

    assert response.status == "ok"
    assert response.timestamp is None
