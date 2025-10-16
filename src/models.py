"""
Pydantic models for API responses.

This module defines the data models used for API responses,
providing validation and serialization capabilities.
"""
from typing import Optional
from pydantic import BaseModel, Field


class StatusResponse(BaseModel):
    """
    Response model for the status endpoint.

    Attributes:
        status: Current operational status of the API (e.g., "ok")
        timestamp: Current server timestamp in ISO 8601 format (optional)
    """

    status: str = Field(
        ...,
        description="Current status of the API",
        examples=["ok"]
    )

    timestamp: Optional[str] = Field(
        None,
        description="Current server timestamp in ISO 8601 format",
        examples=["2025-10-16T12:00:00Z"]
    )

    class Config:
        """Pydantic model configuration."""
        json_schema_extra = {
            "example": {
                "status": "ok",
                "timestamp": "2025-10-16T12:00:00Z"
            }
        }
