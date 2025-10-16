"""
Unit tests for document service (business logic).

Tests cover:
- Uploading documents with and without metadata
- Getting documents
- Listing documents with pagination
- Deleting documents (cascading to file system)
- Error handling
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
from src.document_service import DocumentService
from src.models import Document, DocumentMetadata


@pytest.fixture
def mock_repository():
    """Create a mock document repository."""
    return Mock()


@pytest.fixture
def mock_storage():
    """Create a mock file storage."""
    return Mock()


@pytest.fixture
def document_service(mock_repository, mock_storage):
    """Create a document service with mocked dependencies."""
    return DocumentService(repository=mock_repository, storage=mock_storage)


def test_upload_document_without_metadata(document_service, mock_repository, mock_storage):
    """Test uploading a document without metadata."""
    filename = "test.txt"
    content = b"Test content"

    # Setup mocks
    mock_storage.save_file.return_value = "uuid_test.txt"
    mock_repository.create_document.return_value = Mock(
        id="doc_123",
        filename=filename,
        status="pending"
    )

    result = document_service.upload_document(filename, content, metadata=None)

    # Verify storage was called
    mock_storage.save_file.assert_called_once_with(filename, content)

    # Verify repository was called
    assert mock_repository.create_document.called
    call_args = mock_repository.create_document.call_args
    doc_arg = call_args[0][0]
    assert doc_arg.filename == filename
    assert doc_arg.status == "pending"
    assert doc_arg.metadata is None

    # Verify result
    assert result is not None


def test_upload_document_with_metadata(document_service, mock_repository, mock_storage):
    """Test uploading a document with metadata."""
    filename = "test.pdf"
    content = b"PDF content"
    metadata = DocumentMetadata(
        title="Test Document",
        description="A test document",
        tags=["test", "sample"]
    )

    mock_storage.save_file.return_value = "uuid_test.pdf"
    mock_repository.create_document.return_value = Mock(
        id="doc_456",
        filename=filename,
        metadata=metadata
    )

    result = document_service.upload_document(filename, content, metadata=metadata)

    # Verify metadata was passed to repository
    call_args = mock_repository.create_document.call_args
    doc_arg = call_args[0][0]
    assert doc_arg.metadata is not None
    assert doc_arg.metadata.title == "Test Document"

    assert result is not None


def test_upload_document_generates_unique_id(document_service, mock_repository, mock_storage):
    """Test that upload_document generates unique document IDs."""
    mock_storage.save_file.return_value = "uuid_test.txt"
    mock_repository.create_document.side_effect = lambda doc, path: doc

    result1 = document_service.upload_document("test.txt", b"content1")
    result2 = document_service.upload_document("test.txt", b"content2")

    assert result1.id != result2.id


def test_upload_document_sets_pending_status(document_service, mock_repository, mock_storage):
    """Test that newly uploaded documents have 'pending' status."""
    mock_storage.save_file.return_value = "uuid_test.txt"
    mock_repository.create_document.side_effect = lambda doc, path: doc

    result = document_service.upload_document("test.txt", b"content")

    assert result.status == "pending"


def test_upload_document_storage_failure(document_service, mock_repository, mock_storage):
    """Test handling of storage failure during upload."""
    mock_storage.save_file.side_effect = IOError("Disk full")

    with pytest.raises(IOError):
        document_service.upload_document("test.txt", b"content")

    # Repository should not be called if storage fails
    mock_repository.create_document.assert_not_called()


def test_get_document(document_service, mock_repository):
    """Test getting a document by ID."""
    doc_id = "doc_123"
    expected_doc = Mock(
        id=doc_id,
        filename="test.txt",
        status="completed"
    )
    mock_repository.get_document_by_id.return_value = expected_doc

    result = document_service.get_document(doc_id)

    mock_repository.get_document_by_id.assert_called_once_with(doc_id)
    assert result == expected_doc


def test_get_document_not_found(document_service, mock_repository):
    """Test getting a non-existent document."""
    mock_repository.get_document_by_id.return_value = None

    result = document_service.get_document("nonexistent_id")

    assert result is None


def test_list_documents(document_service, mock_repository):
    """Test listing documents with pagination."""
    expected_docs = [
        Mock(id="doc_1", filename="test1.txt"),
        Mock(id="doc_2", filename="test2.txt")
    ]
    mock_repository.list_documents.return_value = expected_docs
    mock_repository.get_total_count.return_value = 2

    documents, total = document_service.list_documents(limit=10, offset=0)

    mock_repository.list_documents.assert_called_once_with(limit=10, offset=0)
    mock_repository.get_total_count.assert_called_once()
    assert documents == expected_docs
    assert total == 2


def test_list_documents_with_pagination(document_service, mock_repository):
    """Test listing documents with custom pagination."""
    mock_repository.list_documents.return_value = []
    mock_repository.get_total_count.return_value = 100

    documents, total = document_service.list_documents(limit=20, offset=40)

    mock_repository.list_documents.assert_called_once_with(limit=20, offset=40)
    assert total == 100


def test_delete_document(document_service, mock_repository, mock_storage, monkeypatch):
    """Test deleting a document (cascading delete)."""
    doc_id = "doc_789"
    doc = Mock(
        id=doc_id
    )
    storage_path = "uuid_test.txt"

    mock_repository.get_document_by_id.return_value = doc
    mock_repository.delete_document.return_value = True

    # Mock the _get_document_storage_path method
    monkeypatch.setattr(document_service, '_get_document_storage_path', lambda x: storage_path)

    result = document_service.delete_document(doc_id)

    # Should retrieve document first
    mock_repository.get_document_by_id.assert_called_once_with(doc_id)

    # Should delete file
    mock_storage.delete_file.assert_called_once_with(storage_path)

    # Should delete from database
    mock_repository.delete_document.assert_called_once_with(doc_id)

    assert result is True


def test_delete_document_not_found(document_service, mock_repository, mock_storage):
    """Test deleting a non-existent document."""
    mock_repository.get_document_by_id.return_value = None

    result = document_service.delete_document("nonexistent_id")

    # Should not attempt file or db deletion
    mock_storage.delete_file.assert_not_called()
    mock_repository.delete_document.assert_not_called()

    assert result is False


def test_delete_document_file_deletion_error(document_service, mock_repository, mock_storage):
    """Test handling of file deletion errors."""
    doc_id = "doc_error"
    doc = Mock(
        id=doc_id,
        storage_path="uuid_test.txt"
    )
    mock_repository.get_document_by_id.return_value = doc
    mock_storage.delete_file.side_effect = IOError("Permission denied")
    mock_repository.delete_document.return_value = True

    # Should still delete from database even if file deletion fails
    result = document_service.delete_document(doc_id)

    mock_repository.delete_document.assert_called_once_with(doc_id)
    assert result is True


def test_delete_document_db_deletion_error(document_service, mock_repository, mock_storage, monkeypatch):
    """Test handling of database deletion errors."""
    doc_id = "doc_error"
    doc = Mock(
        id=doc_id
    )
    storage_path = "uuid_test.txt"

    mock_repository.get_document_by_id.return_value = doc
    mock_repository.delete_document.return_value = False

    # Mock the _get_document_storage_path method
    monkeypatch.setattr(document_service, '_get_document_storage_path', lambda x: storage_path)

    result = document_service.delete_document(doc_id)

    # File should still be deleted
    mock_storage.delete_file.assert_called_once()

    assert result is False


def test_upload_document_sets_timestamps(document_service, mock_repository, mock_storage):
    """Test that upload_document sets created_at and updated_at timestamps."""
    mock_storage.save_file.return_value = "uuid_test.txt"
    mock_repository.create_document.side_effect = lambda doc, path: doc

    result = document_service.upload_document("test.txt", b"content")

    assert result.created_at is not None
    assert result.updated_at is not None
    assert isinstance(result.created_at, datetime)
    assert isinstance(result.updated_at, datetime)


def test_upload_document_sets_chunk_count_zero(document_service, mock_repository, mock_storage):
    """Test that newly uploaded documents have chunk_count of 0."""
    mock_storage.save_file.return_value = "uuid_test.txt"
    mock_repository.create_document.side_effect = lambda doc, path: doc

    result = document_service.upload_document("test.txt", b"content")

    assert result.chunk_count == 0


def test_list_documents_empty_database(document_service, mock_repository):
    """Test listing documents when database is empty."""
    mock_repository.list_documents.return_value = []
    mock_repository.get_total_count.return_value = 0

    documents, total = document_service.list_documents(limit=10, offset=0)

    assert documents == []
    assert total == 0
