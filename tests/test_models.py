"""
Unit tests for Pydantic response models.

Tests the StatusResponse and document-related models to ensure proper validation,
serialization, and schema compliance.
"""
import pytest
from datetime import datetime
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


# Document Metadata Model Tests


def test_document_metadata_model_all_fields():
    """Test DocumentMetadata with all fields."""
    from src.models import DocumentMetadata

    metadata = DocumentMetadata(
        title="Test Document",
        description="A test document",
        tags=["test", "sample", "unit"]
    )

    assert metadata.title == "Test Document"
    assert metadata.description == "A test document"
    assert metadata.tags == ["test", "sample", "unit"]


def test_document_metadata_model_optional_fields():
    """Test DocumentMetadata with optional fields."""
    from src.models import DocumentMetadata

    metadata = DocumentMetadata()

    assert metadata.title is None
    assert metadata.description is None
    assert metadata.tags is None


def test_document_metadata_json_serialization():
    """Test DocumentMetadata JSON serialization."""
    from src.models import DocumentMetadata

    metadata = DocumentMetadata(
        title="Test",
        tags=["tag1", "tag2"]
    )

    json_data = metadata.model_dump(exclude_none=True)

    assert json_data["title"] == "Test"
    assert json_data["tags"] == ["tag1", "tag2"]
    assert "description" not in json_data


# Document Model Tests


def test_document_model_required_fields():
    """Test Document model with only required fields."""
    from src.models import Document

    doc = Document(
        id="doc_123",
        filename="test.txt",
        status="pending",
        created_at=datetime.utcnow()
    )

    assert doc.id == "doc_123"
    assert doc.filename == "test.txt"
    assert doc.status == "pending"
    assert doc.created_at is not None


def test_document_model_all_fields():
    """Test Document model with all fields."""
    from src.models import Document, DocumentMetadata

    metadata = DocumentMetadata(title="Test", description="Desc", tags=["tag1"])
    now = datetime.utcnow()

    doc = Document(
        id="doc_456",
        filename="test.pdf",
        status="completed",
        metadata=metadata,
        created_at=now,
        updated_at=now,
        chunk_count=10
    )

    assert doc.id == "doc_456"
    assert doc.filename == "test.pdf"
    assert doc.status == "completed"
    assert doc.metadata.title == "Test"
    assert doc.chunk_count == 10


def test_document_model_status_enum():
    """Test Document model status enum validation."""
    from src.models import Document

    valid_statuses = ["pending", "processing", "completed", "failed"]

    for status in valid_statuses:
        doc = Document(
            id=f"doc_{status}",
            filename="test.txt",
            status=status,
            created_at=datetime.utcnow()
        )
        assert doc.status == status


def test_document_model_invalid_status():
    """Test Document model rejects invalid status."""
    from src.models import Document

    with pytest.raises(ValidationError):
        Document(
            id="doc_invalid",
            filename="test.txt",
            status="invalid_status",
            created_at=datetime.utcnow()
        )


def test_document_model_datetime_serialization():
    """Test Document model datetime serialization."""
    from src.models import Document

    now = datetime.utcnow()
    doc = Document(
        id="doc_123",
        filename="test.txt",
        status="pending",
        created_at=now,
        updated_at=now
    )

    json_data = doc.model_dump()

    assert "created_at" in json_data
    assert "updated_at" in json_data


def test_document_model_default_chunk_count():
    """Test Document model default chunk_count."""
    from src.models import Document

    doc = Document(
        id="doc_123",
        filename="test.txt",
        status="pending",
        created_at=datetime.utcnow()
    )

    assert doc.chunk_count == 0


# DocumentListResponse Model Tests


def test_document_list_response_model():
    """Test DocumentListResponse model."""
    from src.models import Document, DocumentListResponse

    doc1 = Document(
        id="doc_1",
        filename="test1.txt",
        status="pending",
        created_at=datetime.utcnow()
    )
    doc2 = Document(
        id="doc_2",
        filename="test2.txt",
        status="completed",
        created_at=datetime.utcnow()
    )

    response = DocumentListResponse(
        documents=[doc1, doc2],
        total=2,
        limit=10,
        offset=0
    )

    assert len(response.documents) == 2
    assert response.total == 2
    assert response.limit == 10
    assert response.offset == 0


def test_document_list_response_empty():
    """Test DocumentListResponse with empty list."""
    from src.models import DocumentListResponse

    response = DocumentListResponse(
        documents=[],
        total=0,
        limit=20,
        offset=0
    )

    assert response.documents == []
    assert response.total == 0


def test_document_list_response_json_serialization():
    """Test DocumentListResponse JSON serialization."""
    from src.models import Document, DocumentListResponse

    doc = Document(
        id="doc_1",
        filename="test.txt",
        status="pending",
        created_at=datetime.utcnow()
    )

    response = DocumentListResponse(
        documents=[doc],
        total=1,
        limit=20,
        offset=0
    )

    json_data = response.model_dump()

    assert "documents" in json_data
    assert "total" in json_data
    assert "limit" in json_data
    assert "offset" in json_data
    assert json_data["total"] == 1
