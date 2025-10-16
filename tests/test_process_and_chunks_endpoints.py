"""
Integration tests for document processing and chunks endpoints.

Tests cover:
- POST /documents/{id}/process - Trigger document processing
- GET /documents/{id}/chunks - Retrieve document chunks
- Status transitions during processing
- Error handling (404 cases)
- Chunk generation and retrieval
"""
import json
import os
import pytest
from fastapi.testclient import TestClient
from io import BytesIO


@pytest.fixture
def test_app(temp_db_path: str, temp_storage_dir: str):
    """Create a test FastAPI application with test configuration."""
    import sys
    import importlib

    # Clear cached modules
    modules_to_clear = ['src.main', 'src.config', 'src.chunking_service', 'src.chunk_repository']
    for module in modules_to_clear:
        if module in sys.modules:
            del sys.modules[module]

    # Set env vars before importing
    os.environ["DB_PATH"] = temp_db_path
    os.environ["STORAGE_DIR"] = temp_storage_dir

    # Import after setting env vars
    from src import config as config_module
    from src.database import init_db

    # Clear the config cache
    config_module._config = None

    # Initialize test database
    init_db(temp_db_path)

    # Import main after setting env vars
    from src import main as main_module

    return main_module.app


@pytest.fixture
def client(test_app):
    """Create a test client."""
    return TestClient(test_app)


@pytest.fixture
def uploaded_document(client):
    """Upload a test document and return its ID."""
    file_content = b"This is test content for processing. " * 20  # ~760 bytes
    files = {'file': ('test_document.txt', BytesIO(file_content), 'text/plain')}
    response = client.post("/documents", files=files)
    assert response.status_code == 201
    return response.json()


# POST /documents/{id}/process endpoint tests

def test_process_document_success(client, uploaded_document):
    """Test successfully triggering document processing."""
    doc_id = uploaded_document['id']

    response = client.post(f"/documents/{doc_id}/process")

    assert response.status_code == 202
    data = response.json()

    assert 'status' in data
    assert data['status'] == 'processing'
    assert 'message' in data
    assert isinstance(data['message'], str)
    assert len(data['message']) > 0


def test_process_document_response_format(client, uploaded_document):
    """Test that process response has correct format."""
    doc_id = uploaded_document['id']

    response = client.post(f"/documents/{doc_id}/process")

    data = response.json()

    # Verify required fields
    assert 'status' in data
    assert 'message' in data

    # Verify field types
    assert isinstance(data['status'], str)
    assert isinstance(data['message'], str)


def test_process_document_not_found(client):
    """Test processing non-existent document returns 404."""
    response = client.post("/documents/nonexistent_id/process")

    assert response.status_code == 404
    assert 'detail' in response.json()


def test_process_document_updates_status(client, uploaded_document):
    """Test that processing updates document status."""
    doc_id = uploaded_document['id']

    # Initial status should be pending
    doc_response = client.get(f"/documents/{doc_id}")
    assert doc_response.json()['status'] == 'pending'

    # Trigger processing
    client.post(f"/documents/{doc_id}/process")

    # Status should be updated to processing or completed
    doc_response_after = client.get(f"/documents/{doc_id}")
    status_after = doc_response_after.json()['status']
    assert status_after in ['processing', 'completed']


def test_process_document_creates_chunks(client, uploaded_document):
    """Test that processing creates chunks."""
    doc_id = uploaded_document['id']

    # Process the document
    process_response = client.post(f"/documents/{doc_id}/process")
    assert process_response.status_code == 202

    # Get chunks
    chunks_response = client.get(f"/documents/{doc_id}/chunks")
    assert chunks_response.status_code == 200

    data = chunks_response.json()
    assert 'chunks' in data
    assert 'total' in data
    assert data['total'] > 0
    assert len(data['chunks']) > 0


def test_process_document_updates_chunk_count(client, uploaded_document):
    """Test that processing updates document chunk_count."""
    doc_id = uploaded_document['id']

    # Initial chunk_count should be 0
    doc_before = client.get(f"/documents/{doc_id}").json()
    assert doc_before['chunk_count'] == 0

    # Process the document
    client.post(f"/documents/{doc_id}/process")

    # chunk_count should be updated
    doc_after = client.get(f"/documents/{doc_id}").json()
    assert doc_after['chunk_count'] > 0


def test_process_document_idempotent(client, uploaded_document):
    """Test that processing can be called multiple times."""
    doc_id = uploaded_document['id']

    # Process first time
    response1 = client.post(f"/documents/{doc_id}/process")
    assert response1.status_code == 202

    # Process second time
    response2 = client.post(f"/documents/{doc_id}/process")
    assert response2.status_code == 202


def test_process_small_document(client):
    """Test processing a very small document."""
    # Upload small document
    files = {'file': ('small.txt', BytesIO(b'Small content'), 'text/plain')}
    upload_response = client.post("/documents", files=files)
    doc_id = upload_response.json()['id']

    # Process
    response = client.post(f"/documents/{doc_id}/process")

    assert response.status_code == 202
    data = response.json()
    assert data['status'] == 'processing'


def test_process_large_document(client):
    """Test processing a larger document."""
    # Upload large document
    large_content = b"This is a test sentence. " * 200  # ~5000 bytes
    files = {'file': ('large.txt', BytesIO(large_content), 'text/plain')}
    upload_response = client.post("/documents", files=files)
    doc_id = upload_response.json()['id']

    # Process
    response = client.post(f"/documents/{doc_id}/process")

    assert response.status_code == 202

    # Should create multiple chunks
    chunks_response = client.get(f"/documents/{doc_id}/chunks")
    data = chunks_response.json()
    assert data['total'] > 1


# GET /documents/{id}/chunks endpoint tests

def test_get_chunks_success(client, uploaded_document):
    """Test successfully retrieving chunks."""
    doc_id = uploaded_document['id']

    # Process to create chunks
    client.post(f"/documents/{doc_id}/process")

    # Get chunks
    response = client.get(f"/documents/{doc_id}/chunks")

    assert response.status_code == 200
    data = response.json()

    assert 'chunks' in data
    assert 'total' in data
    assert isinstance(data['chunks'], list)
    assert isinstance(data['total'], int)


def test_get_chunks_response_format(client, uploaded_document):
    """Test that chunks response has correct format."""
    doc_id = uploaded_document['id']

    # Process to create chunks
    client.post(f"/documents/{doc_id}/process")

    # Get chunks
    response = client.get(f"/documents/{doc_id}/chunks")
    data = response.json()

    # Verify required fields
    assert 'chunks' in data
    assert 'total' in data

    # Verify chunks array
    assert isinstance(data['chunks'], list)
    assert data['total'] == len(data['chunks'])


def test_get_chunks_chunk_schema(client, uploaded_document):
    """Test that each chunk has correct schema."""
    doc_id = uploaded_document['id']

    # Process to create chunks
    client.post(f"/documents/{doc_id}/process")

    # Get chunks
    response = client.get(f"/documents/{doc_id}/chunks")
    chunks = response.json()['chunks']

    assert len(chunks) > 0

    for chunk in chunks:
        # Required fields
        assert 'id' in chunk
        assert 'document_id' in chunk
        assert 'content' in chunk
        assert 'position' in chunk

        # Field types
        assert isinstance(chunk['id'], str)
        assert isinstance(chunk['document_id'], str)
        assert isinstance(chunk['content'], str)
        assert isinstance(chunk['position'], int)

        # Values
        assert chunk['document_id'] == doc_id
        assert chunk['id'].startswith('chunk_')
        assert len(chunk['content']) > 0


def test_get_chunks_not_found(client):
    """Test retrieving chunks for non-existent document returns 404."""
    response = client.get("/documents/nonexistent_id/chunks")

    assert response.status_code == 404
    assert 'detail' in response.json()


def test_get_chunks_before_processing(client, uploaded_document):
    """Test retrieving chunks before processing returns empty array."""
    doc_id = uploaded_document['id']

    # Get chunks before processing
    response = client.get(f"/documents/{doc_id}/chunks")

    assert response.status_code == 200
    data = response.json()

    assert data['chunks'] == []
    assert data['total'] == 0


def test_get_chunks_ordered_by_position(client, uploaded_document):
    """Test that chunks are ordered by position."""
    doc_id = uploaded_document['id']

    # Process to create chunks
    client.post(f"/documents/{doc_id}/process")

    # Get chunks
    response = client.get(f"/documents/{doc_id}/chunks")
    chunks = response.json()['chunks']

    # Verify chunks are ordered by position
    positions = [chunk['position'] for chunk in chunks]
    assert positions == sorted(positions)

    # Verify positions start at 0 and are sequential
    assert positions == list(range(len(positions)))


def test_get_chunks_total_matches_count(client, uploaded_document):
    """Test that total field matches actual chunk count."""
    doc_id = uploaded_document['id']

    # Process to create chunks
    client.post(f"/documents/{doc_id}/process")

    # Get chunks
    response = client.get(f"/documents/{doc_id}/chunks")
    data = response.json()

    assert data['total'] == len(data['chunks'])


def test_get_chunks_document_id_consistency(client, uploaded_document):
    """Test that all chunks have the same document_id."""
    doc_id = uploaded_document['id']

    # Process to create chunks
    client.post(f"/documents/{doc_id}/process")

    # Get chunks
    response = client.get(f"/documents/{doc_id}/chunks")
    chunks = response.json()['chunks']

    assert len(chunks) > 0
    assert all(chunk['document_id'] == doc_id for chunk in chunks)


def test_get_chunks_unique_chunk_ids(client, uploaded_document):
    """Test that all chunk IDs are unique."""
    doc_id = uploaded_document['id']

    # Process to create chunks
    client.post(f"/documents/{doc_id}/process")

    # Get chunks
    response = client.get(f"/documents/{doc_id}/chunks")
    chunks = response.json()['chunks']

    chunk_ids = [chunk['id'] for chunk in chunks]
    assert len(chunk_ids) == len(set(chunk_ids))  # All unique


def test_get_chunks_metadata_fields(client, uploaded_document):
    """Test that chunk metadata fields are present."""
    doc_id = uploaded_document['id']

    # Process to create chunks
    client.post(f"/documents/{doc_id}/process")

    # Get chunks
    response = client.get(f"/documents/{doc_id}/chunks")
    chunks = response.json()['chunks']

    for chunk in chunks:
        # Metadata field should be present (can be null or object)
        assert 'metadata' in chunk


def test_chunks_isolated_by_document(client):
    """Test that chunks are isolated by document."""
    # Upload two documents
    files1 = {'file': ('doc1.txt', BytesIO(b'Content for doc 1 ' * 30), 'text/plain')}
    files2 = {'file': ('doc2.txt', BytesIO(b'Content for doc 2 ' * 30), 'text/plain')}

    doc1_id = client.post("/documents", files=files1).json()['id']
    doc2_id = client.post("/documents", files=files2).json()['id']

    # Process both
    client.post(f"/documents/{doc1_id}/process")
    client.post(f"/documents/{doc2_id}/process")

    # Get chunks for each
    chunks1 = client.get(f"/documents/{doc1_id}/chunks").json()['chunks']
    chunks2 = client.get(f"/documents/{doc2_id}/chunks").json()['chunks']

    # Verify isolation
    assert len(chunks1) > 0
    assert len(chunks2) > 0
    assert all(c['document_id'] == doc1_id for c in chunks1)
    assert all(c['document_id'] == doc2_id for c in chunks2)

    # Chunk IDs should not overlap
    chunk_ids_1 = set(c['id'] for c in chunks1)
    chunk_ids_2 = set(c['id'] for c in chunks2)
    assert chunk_ids_1.isdisjoint(chunk_ids_2)


def test_delete_document_removes_chunks(client, uploaded_document):
    """Test that deleting a document also removes its chunks."""
    doc_id = uploaded_document['id']

    # Process to create chunks
    client.post(f"/documents/{doc_id}/process")

    # Verify chunks exist
    chunks_before = client.get(f"/documents/{doc_id}/chunks")
    assert chunks_before.status_code == 200
    assert chunks_before.json()['total'] > 0

    # Delete document
    delete_response = client.delete(f"/documents/{doc_id}")
    assert delete_response.status_code == 204

    # Verify document is gone
    doc_response = client.get(f"/documents/{doc_id}")
    assert doc_response.status_code == 404

    # Chunks endpoint should also return 404
    chunks_after = client.get(f"/documents/{doc_id}/chunks")
    assert chunks_after.status_code == 404


def test_process_document_with_metadata(client):
    """Test processing document that has metadata."""
    metadata = {
        "title": "Test Doc",
        "description": "Document with metadata",
        "tags": ["test"]
    }

    files = {'file': ('meta.txt', BytesIO(b'Content ' * 30), 'text/plain')}
    data = {'metadata': json.dumps(metadata)}

    upload_response = client.post("/documents", files=files, data=data)
    doc_id = upload_response.json()['id']

    # Process
    response = client.post(f"/documents/{doc_id}/process")

    assert response.status_code == 202

    # Should create chunks
    chunks_response = client.get(f"/documents/{doc_id}/chunks")
    assert chunks_response.json()['total'] > 0


def test_process_empty_document(client):
    """Test processing a document with empty content."""
    files = {'file': ('empty.txt', BytesIO(b''), 'text/plain')}
    upload_response = client.post("/documents", files=files)
    doc_id = upload_response.json()['id']

    # Process
    response = client.post(f"/documents/{doc_id}/process")

    assert response.status_code == 202

    # Should complete without errors (may have 0 chunks)
    doc_status = client.get(f"/documents/{doc_id}").json()
    assert doc_status['status'] in ['processing', 'completed', 'failed']


def test_get_chunks_content_not_truncated(client, uploaded_document):
    """Test that chunk content is not truncated."""
    doc_id = uploaded_document['id']

    # Process to create chunks
    client.post(f"/documents/{doc_id}/process")

    # Get chunks
    response = client.get(f"/documents/{doc_id}/chunks")
    chunks = response.json()['chunks']

    # All chunks should have reasonable content length
    for chunk in chunks:
        assert len(chunk['content']) > 0
        # Should have actual content, not just "..."
        assert chunk['content'] != "..."


def test_reprocess_document(client, uploaded_document):
    """Test reprocessing a document that was already processed."""
    doc_id = uploaded_document['id']

    # First processing
    client.post(f"/documents/{doc_id}/process")
    chunks_first = client.get(f"/documents/{doc_id}/chunks").json()

    # Second processing
    client.post(f"/documents/{doc_id}/process")
    chunks_second = client.get(f"/documents/{doc_id}/chunks").json()

    # Both should succeed
    assert chunks_first['total'] > 0
    assert chunks_second['total'] > 0


def test_chunk_count_matches_chunks_total(client, uploaded_document):
    """Test that document chunk_count matches chunks total."""
    doc_id = uploaded_document['id']

    # Process
    client.post(f"/documents/{doc_id}/process")

    # Get document
    doc = client.get(f"/documents/{doc_id}").json()

    # Get chunks
    chunks_response = client.get(f"/documents/{doc_id}/chunks").json()

    # Should match
    assert doc['chunk_count'] == chunks_response['total']


def test_process_document_special_characters(client):
    """Test processing document with special characters."""
    content = b"Special chars: @#$%^&*()[]{}|\\<>?/~`+=- \n\t"
    files = {'file': ('special.txt', BytesIO(content * 20), 'text/plain')}

    upload_response = client.post("/documents", files=files)
    doc_id = upload_response.json()['id']

    # Process
    response = client.post(f"/documents/{doc_id}/process")

    assert response.status_code == 202

    # Should successfully create chunks
    chunks = client.get(f"/documents/{doc_id}/chunks").json()
    assert chunks['total'] > 0
