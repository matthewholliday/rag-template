"""
FastAPI application with status endpoint.

This module defines the main FastAPI application and implements
the GET /status health check endpoint.
"""
from fastapi import FastAPI
from src.models import StatusResponse
from src.time_utils import get_current_timestamp

# Create FastAPI application instance
app = FastAPI(
    title="API Title",
    version="1.0",
    description="API with status health check endpoint",
)


@app.get(
    "/status",
    response_model=StatusResponse,
    status_code=200,
    tags=["Health"],
    summary="Health check endpoint",
    description="Returns the current status of the API"
)
def get_status() -> StatusResponse:
    """
    Health check endpoint that returns API operational status.

    This endpoint provides a simple way to verify that the API is
    running and responsive. It returns a status indicator and the
    current server timestamp.

    Returns:
        StatusResponse: Object containing status and timestamp

    Example Response:
        {
            "status": "ok",
            "timestamp": "2025-10-16T12:00:00Z"
        }
    """
    return StatusResponse(
        status="ok",
        timestamp=get_current_timestamp()
    )
