"""
FastAPI application with document management endpoints.

This module defines the main FastAPI application and implements
document upload, retrieval, listing, and deletion endpoints.
"""
import json
import os
from typing import Optional
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Query
from fastapi.responses import Response

from src.models import StatusResponse, Document, DocumentListResponse, DocumentMetadata
from src.time_utils import get_current_timestamp
from src.config import get_config
from src.database import init_db
from src.document_repository import DocumentRepository
from src.storage import FileStorage
from src.document_service import DocumentService

# Load configuration - use environment variables if set for testing
import os
config_path = os.getenv("CONFIG_PATH", "config.json")
try:
    config = get_config(config_path)
except FileNotFoundError:
    # For testing, create a default config
    from src.config import Config, StorageConfig, DatabaseConfig
    config = Config(
        storage=StorageConfig(documents_dir=os.getenv("STORAGE_DIR", "./data/documents")),
        database=DatabaseConfig(path=os.getenv("DB_PATH", "./data/rag.db"))
    )

# Initialize database on startup
init_db(config.database.path)

# Create dependencies
repository = DocumentRepository(config.database.path)
storage = FileStorage(config.storage.documents_dir)
document_service = DocumentService(repository, storage)

# Create FastAPI application instance
app = FastAPI(
    title="RAG Data Ingestion API",
    version="1.0",
    description="REST API for document ingestion and retrieval-augmented generation",
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


@app.post(
    "/documents",
    response_model=Document,
    status_code=201,
    tags=["Documents"],
    summary="Upload a document",
    description="Upload a single document for ingestion and processing"
)
async def upload_document(
    file: UploadFile = File(..., description="Document file to upload"),
    metadata: Optional[str] = Form(None, description="Optional metadata as JSON string")
) -> Document:
    """
    Upload a document with optional metadata.

    Args:
        file: The uploaded file
        metadata: Optional JSON string containing title, description, and tags

    Returns:
        Document: The created document with metadata

    Raises:
        HTTPException: 400 if metadata JSON is invalid
    """
    # Parse metadata if provided
    doc_metadata = None
    if metadata:
        try:
            metadata_dict = json.loads(metadata)
            doc_metadata = DocumentMetadata(**metadata_dict)
        except (json.JSONDecodeError, ValueError) as e:
            raise HTTPException(status_code=400, detail=f"Invalid metadata JSON: {str(e)}")

    # Read file content
    content = await file.read()

    # Upload document
    document = document_service.upload_document(
        filename=file.filename or "unnamed",
        content=content,
        metadata=doc_metadata
    )

    return document


@app.get(
    "/documents",
    response_model=DocumentListResponse,
    status_code=200,
    tags=["Documents"],
    summary="List documents",
    description="Retrieve a list of all uploaded documents with pagination"
)
def list_documents(
    limit: int = Query(20, ge=1, le=100, description="Maximum number of documents to return"),
    offset: int = Query(0, ge=0, description="Number of documents to skip")
) -> DocumentListResponse:
    """
    List documents with pagination.

    Args:
        limit: Maximum number of documents to return (1-100, default 20)
        offset: Number of documents to skip (default 0)

    Returns:
        DocumentListResponse: List of documents with pagination metadata
    """
    documents, total = document_service.list_documents(limit=limit, offset=offset)

    return DocumentListResponse(
        documents=documents,
        total=total,
        limit=limit,
        offset=offset
    )


@app.get(
    "/documents/{id}",
    response_model=Document,
    status_code=200,
    tags=["Documents"],
    summary="Get document details",
    description="Retrieve details and processing status for a specific document"
)
def get_document(id: str) -> Document:
    """
    Get a document by ID.

    Args:
        id: Document ID

    Returns:
        Document: The document details

    Raises:
        HTTPException: 404 if document not found
    """
    document = document_service.get_document(id)

    if document is None:
        raise HTTPException(status_code=404, detail="Document not found")

    return document


@app.delete(
    "/documents/{id}",
    status_code=204,
    tags=["Documents"],
    summary="Delete document",
    description="Remove document and all associated data"
)
def delete_document(id: str) -> Response:
    """
    Delete a document by ID.

    Args:
        id: Document ID

    Returns:
        Response: 204 No Content on success

    Raises:
        HTTPException: 404 if document not found
    """
    deleted = document_service.delete_document(id)

    if not deleted:
        raise HTTPException(status_code=404, detail="Document not found")

    return Response(status_code=204)
