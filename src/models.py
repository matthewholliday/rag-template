"""
Pydantic models for API responses.

This module defines the data models used for API responses,
providing validation and serialization capabilities.
"""
from typing import Optional, List, Literal
from datetime import datetime
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


class DocumentMetadata(BaseModel):
    """
    Metadata for a document.

    Attributes:
        title: Document title
        description: Document description
        tags: List of tags associated with the document
    """

    title: Optional[str] = Field(
        None,
        description="Document title"
    )

    description: Optional[str] = Field(
        None,
        description="Document description"
    )

    tags: Optional[List[str]] = Field(
        None,
        description="Tags associated with the document"
    )


class Document(BaseModel):
    """
    Document model representing an uploaded document.

    Attributes:
        id: Unique document identifier
        filename: Original filename
        status: Processing status (pending, processing, completed, failed)
        metadata: Optional document metadata
        created_at: Document creation timestamp
        updated_at: Document last update timestamp
        chunk_count: Number of chunks generated from the document
    """

    id: str = Field(
        ...,
        description="Unique document identifier"
    )

    filename: str = Field(
        ...,
        description="Original filename"
    )

    status: Literal["pending", "processing", "completed", "failed"] = Field(
        ...,
        description="Processing status"
    )

    metadata: Optional[DocumentMetadata] = Field(
        None,
        description="Document metadata"
    )

    created_at: datetime = Field(
        ...,
        description="Document creation timestamp"
    )

    updated_at: Optional[datetime] = Field(
        None,
        description="Document last update timestamp"
    )

    chunk_count: int = Field(
        default=0,
        description="Number of chunks generated from the document"
    )

    class Config:
        """Pydantic model configuration."""
        json_schema_extra = {
            "example": {
                "id": "doc_123abc",
                "filename": "research-paper.pdf",
                "status": "completed",
                "metadata": {
                    "title": "Research Paper",
                    "description": "A comprehensive research paper",
                    "tags": ["research", "science"]
                },
                "created_at": "2025-10-16T12:00:00Z",
                "updated_at": "2025-10-16T12:05:00Z",
                "chunk_count": 15
            }
        }


class DocumentListResponse(BaseModel):
    """
    Response model for listing documents with pagination.

    Attributes:
        documents: List of documents
        total: Total number of documents
        limit: Maximum number of documents returned
        offset: Number of documents skipped
    """

    documents: List[Document] = Field(
        ...,
        description="List of documents"
    )

    total: int = Field(
        ...,
        description="Total number of documents"
    )

    limit: int = Field(
        ...,
        description="Maximum number of documents returned"
    )

    offset: int = Field(
        ...,
        description="Number of documents skipped"
    )
