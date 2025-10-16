"""
Unit tests for document repository.

Tests cover:
- Creating documents
- Retrieving documents by ID
- Listing documents with pagination
- Deleting documents
- Getting total count
- Error handling
"""
import pytest
from datetime import datetime
from src.document_repository import DocumentRepository
from src.models import Document, DocumentMetadata
from src.database import init_db


@pytest.fixture
def repository(temp_db_path: str):
    """Create a document repository with initialized database."""
    init_db(temp_db_path)
    return DocumentRepository(temp_db_path)


def test_create_document(repository: DocumentRepository):
    """Test creating a new document."""
    document = Document(
        id="doc_123",
        filename="test.txt",
        status="pending",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
        chunk_count=0
    )

    created_doc = repository.create_document(document, "/path/to/test.txt")

    assert created_doc is not None
    assert created_doc.id == "doc_123"
    assert created_doc.filename == "test.txt"
    assert created_doc.status == "pending"


def test_create_document_with_metadata(repository: DocumentRepository):
    """Test creating a document with metadata."""
    metadata = DocumentMetadata(
        title="Test Document",
        description="A test document",
        tags=["test", "sample"]
    )

    document = Document(
        id="doc_456",
        filename="test.pdf",
        status="pending",
        metadata=metadata,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
        chunk_count=0
    )

    created_doc = repository.create_document(document, "/path/to/test.pdf")

    assert created_doc.metadata is not None
    assert created_doc.metadata.title == "Test Document"
    assert created_doc.metadata.description == "A test document"
    assert created_doc.metadata.tags == ["test", "sample"]


def test_get_document_by_id(repository: DocumentRepository):
    """Test retrieving a document by ID."""
    document = Document(
        id="doc_789",
        filename="retrieve_test.txt",
        status="completed",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
        chunk_count=5
    )

    repository.create_document(document, "/path/to/retrieve_test.txt")

    retrieved_doc = repository.get_document_by_id("doc_789")

    assert retrieved_doc is not None
    assert retrieved_doc.id == "doc_789"
    assert retrieved_doc.filename == "retrieve_test.txt"
    assert retrieved_doc.status == "completed"
    assert retrieved_doc.chunk_count == 5


def test_get_document_by_id_not_found(repository: DocumentRepository):
    """Test retrieving a non-existent document returns None."""
    retrieved_doc = repository.get_document_by_id("nonexistent_id")

    assert retrieved_doc is None


def test_list_documents_empty(repository: DocumentRepository):
    """Test listing documents when database is empty."""
    documents = repository.list_documents(limit=10, offset=0)

    assert documents == []


def test_list_documents(repository: DocumentRepository):
    """Test listing documents with pagination."""
    # Create multiple documents
    for i in range(5):
        doc = Document(
            id=f"doc_{i}",
            filename=f"test_{i}.txt",
            storage_path=f"/path/to/test_{i}.txt",
            status="pending",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            chunk_count=0
        )
        repository.create_document(doc, f"/path/to/{doc.filename}")

    # List all documents
    documents = repository.list_documents(limit=10, offset=0)

    assert len(documents) == 5
    assert all(isinstance(doc, Document) for doc in documents)


def test_list_documents_pagination(repository: DocumentRepository):
    """Test pagination when listing documents."""
    # Create 10 documents
    for i in range(10):
        doc = Document(
            id=f"doc_{i:02d}",
            filename=f"test_{i:02d}.txt",
            storage_path=f"/path/to/test_{i:02d}.txt",
            status="pending",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            chunk_count=0
        )
        repository.create_document(doc, f"/path/to/{doc.filename}")

    # Get first page
    page1 = repository.list_documents(limit=3, offset=0)
    assert len(page1) == 3

    # Get second page
    page2 = repository.list_documents(limit=3, offset=3)
    assert len(page2) == 3

    # Pages should have different documents
    page1_ids = {doc.id for doc in page1}
    page2_ids = {doc.id for doc in page2}
    assert page1_ids.isdisjoint(page2_ids)


def test_list_documents_offset_beyond_total(repository: DocumentRepository):
    """Test listing documents with offset beyond total count."""
    # Create 3 documents
    for i in range(3):
        doc = Document(
            id=f"doc_{i}",
            filename=f"test_{i}.txt",
            storage_path=f"/path/to/test_{i}.txt",
            status="pending",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            chunk_count=0
        )
        repository.create_document(doc, f"/path/to/{doc.filename}")

    # Offset beyond total
    documents = repository.list_documents(limit=10, offset=10)

    assert documents == []


def test_list_documents_ordered_by_created_at(repository: DocumentRepository):
    """Test that documents are ordered by created_at DESC."""
    import time

    # Create documents with different timestamps
    for i in range(3):
        doc = Document(
            id=f"doc_{i}",
            filename=f"test_{i}.txt",
            storage_path=f"/path/to/test_{i}.txt",
            status="pending",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            chunk_count=0
        )
        repository.create_document(doc, f"/path/to/{doc.filename}")
        time.sleep(0.01)  # Small delay to ensure different timestamps

    documents = repository.list_documents(limit=10, offset=0)

    # Most recent first
    assert documents[0].id == "doc_2"
    assert documents[1].id == "doc_1"
    assert documents[2].id == "doc_0"


def test_get_total_count(repository: DocumentRepository):
    """Test getting total count of documents."""
    # Initially empty
    assert repository.get_total_count() == 0

    # Add documents
    for i in range(7):
        doc = Document(
            id=f"doc_{i}",
            filename=f"test_{i}.txt",
            storage_path=f"/path/to/test_{i}.txt",
            status="pending",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            chunk_count=0
        )
        repository.create_document(doc, f"/path/to/{doc.filename}")

    assert repository.get_total_count() == 7


def test_delete_document(repository: DocumentRepository):
    """Test deleting a document."""
    document = Document(
        id="doc_delete",
        filename="delete_test.txt",
        status="pending",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
        chunk_count=0
    )

    repository.create_document(document, "/path/to/delete_test.txt")
    assert repository.get_document_by_id("doc_delete") is not None

    # Delete document
    result = repository.delete_document("doc_delete")

    assert result is True
    assert repository.get_document_by_id("doc_delete") is None


def test_delete_document_not_found(repository: DocumentRepository):
    """Test deleting a non-existent document."""
    result = repository.delete_document("nonexistent_id")

    assert result is False


def test_delete_document_decreases_count(repository: DocumentRepository):
    """Test that deleting document decreases total count."""
    # Create documents
    for i in range(3):
        doc = Document(
            id=f"doc_{i}",
            filename=f"test_{i}.txt",
            storage_path=f"/path/to/test_{i}.txt",
            status="pending",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            chunk_count=0
        )
        repository.create_document(doc, f"/path/to/{doc.filename}")

    assert repository.get_total_count() == 3

    repository.delete_document("doc_1")

    assert repository.get_total_count() == 2


def test_create_document_preserves_all_status_values(repository: DocumentRepository):
    """Test creating documents with all valid status values."""
    statuses = ["pending", "processing", "completed", "failed"]

    for i, status in enumerate(statuses):
        doc = Document(
            id=f"doc_{status}",
            filename=f"test_{status}.txt",
            storage_path=f"/path/to/test_{status}.txt",
            status=status,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            chunk_count=0
        )
        repository.create_document(doc, f"/path/to/{doc.filename}")

    # Verify all documents were created with correct status
    for status in statuses:
        retrieved = repository.get_document_by_id(f"doc_{status}")
        assert retrieved is not None
        assert retrieved.status == status


def test_create_document_with_null_metadata(repository: DocumentRepository):
    """Test creating a document with no metadata."""
    document = Document(
        id="doc_no_meta",
        filename="test.txt",
        status="pending",
        metadata=None,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
        chunk_count=0
    )

    created_doc = repository.create_document(document, "/path/to/test.txt")

    assert created_doc.metadata is None


def test_update_document_status(repository: DocumentRepository):
    """Test updating document status."""
    document = Document(
        id="doc_update",
        filename="test.txt",
        status="pending",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
        chunk_count=0
    )

    repository.create_document(document, "/path/to/test.txt")

    # Update status
    repository.update_document_status("doc_update", "completed")

    # Verify update
    updated = repository.get_document_by_id("doc_update")
    assert updated.status == "completed"


def test_update_document_chunk_count(repository: DocumentRepository):
    """Test updating document chunk count."""
    document = Document(
        id="doc_chunks",
        filename="test.txt",
        status="pending",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
        chunk_count=0
    )

    repository.create_document(document, "/path/to/test.txt")

    # Update chunk count
    repository.update_chunk_count("doc_chunks", 15)

    # Verify update
    updated = repository.get_document_by_id("doc_chunks")
    assert updated.chunk_count == 15
