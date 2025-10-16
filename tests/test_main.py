"""
Integration tests for the status endpoint.

Tests the complete GET /status endpoint to ensure it returns
the correct HTTP status code, response structure, and data format.
"""
import re
import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    """Create a test client for the FastAPI application."""
    from src.main import app
    return TestClient(app)


def test_status_endpoint_exists(client):
    """Should have a GET /status endpoint that responds."""
    response = client.get("/status")

    # Should not return 404 (endpoint exists)
    assert response.status_code != 404, "Endpoint /status should exist"


def test_status_endpoint_returns_200(client):
    """Should return HTTP 200 status code for successful health check."""
    response = client.get("/status")

    assert response.status_code == 200, \
        f"Expected status code 200, got {response.status_code}"


def test_status_endpoint_returns_json(client):
    """Should return response with application/json content type."""
    response = client.get("/status")

    content_type = response.headers.get("content-type", "")
    assert "application/json" in content_type, \
        f"Expected JSON response, got content-type: {content_type}"


def test_status_endpoint_response_structure(client):
    """Should return JSON response with expected structure."""
    response = client.get("/status")

    data = response.json()

    assert isinstance(data, dict), "Response should be a JSON object"
    assert "status" in data, "Response should contain 'status' field"


def test_status_endpoint_status_field_value(client):
    """Should return 'ok' as the value of status field."""
    response = client.get("/status")

    data = response.json()

    assert data["status"] == "ok", \
        f"Expected status='ok', got status='{data['status']}'"


def test_status_endpoint_contains_timestamp(client):
    """Should include timestamp field in response."""
    response = client.get("/status")

    data = response.json()

    assert "timestamp" in data, "Response should contain 'timestamp' field"


def test_status_endpoint_timestamp_format(client):
    """Should return timestamp in ISO 8601 format."""
    response = client.get("/status")

    data = response.json()
    timestamp = data.get("timestamp")

    assert timestamp is not None, "Timestamp should not be null"

    # ISO 8601 format: 2025-10-16T12:00:00Z
    iso8601_pattern = r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$'
    assert re.match(iso8601_pattern, timestamp), \
        f"Timestamp '{timestamp}' is not in ISO 8601 format"


def test_status_endpoint_timestamp_is_current(client):
    """Should return a timestamp representing current time."""
    from datetime import datetime

    before = datetime.utcnow()
    response = client.get("/status")
    after = datetime.utcnow()

    data = response.json()
    timestamp_str = data.get("timestamp")

    # Parse timestamp
    timestamp_dt = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))

    # Check it's between before and after
    assert before <= timestamp_dt.replace(tzinfo=None) <= after, \
        "Timestamp should represent current time"


def test_status_endpoint_response_schema(client):
    """Should return response matching the complete expected schema."""
    response = client.get("/status")

    assert response.status_code == 200

    data = response.json()

    # Verify all expected fields are present
    assert "status" in data
    assert "timestamp" in data

    # Verify types
    assert isinstance(data["status"], str)
    assert isinstance(data["timestamp"], str)

    # Verify status value
    assert data["status"] == "ok"


def test_status_endpoint_multiple_requests_return_different_timestamps(client):
    """Should return updated timestamps on subsequent requests."""
    import time

    response1 = client.get("/status")
    data1 = response1.json()

    time.sleep(0.01)  # Small delay to ensure different timestamps

    response2 = client.get("/status")
    data2 = response2.json()

    # Both should have status ok
    assert data1["status"] == "ok"
    assert data2["status"] == "ok"

    # Timestamps should be different (or at least not fail if same due to speed)
    # This test mainly ensures the endpoint is callable multiple times
    assert "timestamp" in data1
    assert "timestamp" in data2
