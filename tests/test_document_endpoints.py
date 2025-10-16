"""
Integration tests for document API endpoints.

Tests cover:
- POST /documents - Upload document
- GET /documents - List documents with pagination
- GET /documents/{id} - Get document details
- DELETE /documents/{id} - Delete document
"""
import json
import os
import tempfile
import pytest
from fastapi.testclient import TestClient
from io import BytesIO


@pytest.fixture
def test_app(temp_db_path: str, temp_storage_dir: str):
    """Create a test FastAPI application with test configuration."""
    import sys
    import importlib

    # Clear cached modules
    modules_to_clear = ['src.main', 'src.config']
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


def test_upload_document_success(client):
    """Test successful document upload without metadata."""
    file_content = b"Test file content for upload"
    files = {
        'file': ('test_document.txt', BytesIO(file_content), 'text/plain')
    }

    response = client.post("/documents", files=files)

    assert response.status_code == 201
    data = response.json()

    assert 'id' in data
    assert data['filename'] == 'test_document.txt'
    assert data['status'] == 'pending'
    assert 'created_at' in data
    assert data['chunk_count'] == 0


def test_upload_document_with_metadata(client):
    """Test document upload with metadata."""
    file_content = b"Test file content"
    metadata = {
        "title": "Test Document",
        "description": "A test document",
        "tags": ["test", "sample"]
    }

    files = {
        'file': ('test.pdf', BytesIO(file_content), 'application/pdf')
    }
    data = {
        'metadata': json.dumps(metadata)
    }

    response = client.post("/documents", files=files, data=data)

    assert response.status_code == 201
    response_data = response.json()

    assert response_data['filename'] == 'test.pdf'
    assert response_data['metadata']['title'] == 'Test Document'
    assert response_data['metadata']['description'] == 'A test document'
    assert response_data['metadata']['tags'] == ["test", "sample"]


def test_upload_document_missing_file(client):
    """Test upload without file returns 400."""
    response = client.post("/documents", files={})

    assert response.status_code == 422  # FastAPI validation error


def test_get_document_success(client):
    """Test getting a document by ID."""
    # Upload a document first
    file_content = b"Test content"
    files = {'file': ('test.txt', BytesIO(file_content), 'text/plain')}
    upload_response = client.post("/documents", files=files)
    doc_id = upload_response.json()['id']

    # Get the document
    response = client.get(f"/documents/{doc_id}")

    assert response.status_code == 200
    data = response.json()

    assert data['id'] == doc_id
    assert data['filename'] == 'test.txt'
    assert data['status'] == 'pending'


def test_get_document_not_found(client):
    """Test getting non-existent document returns 404."""
    response = client.get("/documents/nonexistent_id")

    assert response.status_code == 404


def test_list_documents_empty(client):
    """Test listing documents when none exist."""
    response = client.get("/documents")

    assert response.status_code == 200
    data = response.json()

    assert data['documents'] == []
    assert data['total'] == 0
    assert data['limit'] == 20  # default
    assert data['offset'] == 0


def test_list_documents(client):
    """Test listing documents."""
    # Upload multiple documents
    for i in range(3):
        files = {'file': (f'test_{i}.txt', BytesIO(b'content'), 'text/plain')}
        client.post("/documents", files=files)

    response = client.get("/documents")

    assert response.status_code == 200
    data = response.json()

    assert len(data['documents']) == 3
    assert data['total'] == 3
    assert data['limit'] == 20
    assert data['offset'] == 0


def test_list_documents_with_pagination(client):
    """Test listing documents with custom pagination parameters."""
    # Upload 5 documents
    for i in range(5):
        files = {'file': (f'test_{i}.txt', BytesIO(b'content'), 'text/plain')}
        client.post("/documents", files=files)

    # Get first page
    response = client.get("/documents?limit=2&offset=0")
    assert response.status_code == 200
    data = response.json()

    assert len(data['documents']) == 2
    assert data['total'] == 5
    assert data['limit'] == 2
    assert data['offset'] == 0

    # Get second page
    response = client.get("/documents?limit=2&offset=2")
    data = response.json()

    assert len(data['documents']) == 2
    assert data['offset'] == 2


def test_list_documents_pagination_limits(client):
    """Test pagination parameter validation."""
    # Upload a document
    files = {'file': ('test.txt', BytesIO(b'content'), 'text/plain')}
    client.post("/documents", files=files)

    # Test maximum limit
    response = client.get("/documents?limit=100")
    assert response.status_code == 200

    # Test exceeding maximum limit should use max or fail validation
    response = client.get("/documents?limit=101")
    # Depending on implementation, might be 422 or adjusted to 100
    assert response.status_code in [200, 422]


def test_list_documents_offset_beyond_total(client):
    """Test listing with offset beyond total documents."""
    # Upload 2 documents
    for i in range(2):
        files = {'file': (f'test_{i}.txt', BytesIO(b'content'), 'text/plain')}
        client.post("/documents", files=files)

    response = client.get("/documents?offset=10")

    assert response.status_code == 200
    data = response.json()

    assert data['documents'] == []
    assert data['total'] == 2
    assert data['offset'] == 10


def test_delete_document_success(client):
    """Test deleting a document."""
    # Upload a document
    file_content = b"Content to delete"
    files = {'file': ('delete_test.txt', BytesIO(file_content), 'text/plain')}
    upload_response = client.post("/documents", files=files)
    doc_id = upload_response.json()['id']

    # Delete the document
    response = client.delete(f"/documents/{doc_id}")

    assert response.status_code == 204

    # Verify document is gone
    get_response = client.get(f"/documents/{doc_id}")
    assert get_response.status_code == 404


def test_delete_document_not_found(client):
    """Test deleting non-existent document returns 404."""
    response = client.delete("/documents/nonexistent_id")

    assert response.status_code == 404


def test_delete_document_removes_file(client, temp_storage_dir: str):
    """Test that deleting a document also removes the file from storage."""
    # Upload a document
    file_content = b"File to be deleted"
    files = {'file': ('file_delete.txt', BytesIO(file_content), 'text/plain')}
    upload_response = client.post("/documents", files=files)
    doc_id = upload_response.json()['id']

    # Check file exists in storage
    storage_files_before = os.listdir(temp_storage_dir)
    assert len(storage_files_before) > 0

    # Delete the document
    client.delete(f"/documents/{doc_id}")

    # Check file is removed (or count decreased)
    storage_files_after = os.listdir(temp_storage_dir)
    assert len(storage_files_after) < len(storage_files_before)


def test_upload_multiple_documents_unique_ids(client):
    """Test that multiple uploads generate unique document IDs."""
    doc_ids = []

    for i in range(3):
        files = {'file': ('test.txt', BytesIO(b'content'), 'text/plain')}
        response = client.post("/documents", files=files)
        doc_ids.append(response.json()['id'])

    # All IDs should be unique
    assert len(doc_ids) == len(set(doc_ids))


def test_upload_document_stores_file(client, temp_storage_dir: str):
    """Test that uploaded file is actually stored in the storage directory."""
    files_before = os.listdir(temp_storage_dir)

    file_content = b"Content to store"
    files = {'file': ('stored_file.txt', BytesIO(file_content), 'text/plain')}
    response = client.post("/documents", files=files)

    assert response.status_code == 201

    files_after = os.listdir(temp_storage_dir)
    assert len(files_after) == len(files_before) + 1


def test_upload_document_invalid_metadata_format(client):
    """Test upload with invalid metadata JSON."""
    files = {'file': ('test.txt', BytesIO(b'content'), 'text/plain')}
    data = {'metadata': 'not valid json'}

    response = client.post("/documents", files=files, data=data)

    # Should return 400 bad request
    assert response.status_code == 400


def test_list_documents_default_pagination(client):
    """Test that default pagination values are applied."""
    response = client.get("/documents")

    assert response.status_code == 200
    data = response.json()

    assert 'limit' in data
    assert 'offset' in data
    assert data['limit'] == 20  # Default limit
    assert data['offset'] == 0  # Default offset


def test_get_document_includes_all_fields(client):
    """Test that retrieved document includes all expected fields."""
    metadata = {
        "title": "Complete Document",
        "description": "Has all fields",
        "tags": ["complete"]
    }

    files = {'file': ('complete.txt', BytesIO(b'content'), 'text/plain')}
    data = {'metadata': json.dumps(metadata)}
    upload_response = client.post("/documents", files=files, data=data)
    doc_id = upload_response.json()['id']

    response = client.get(f"/documents/{doc_id}")
    doc_data = response.json()

    # Check all required fields
    assert 'id' in doc_data
    assert 'filename' in doc_data
    assert 'status' in doc_data
    assert 'created_at' in doc_data
    assert 'updated_at' in doc_data
    assert 'chunk_count' in doc_data
    assert 'metadata' in doc_data


def test_list_documents_ordered_by_created_at(client):
    """Test that documents are ordered by created_at descending."""
    import time

    doc_ids = []
    for i in range(3):
        files = {'file': (f'test_{i}.txt', BytesIO(b'content'), 'text/plain')}
        response = client.post("/documents", files=files)
        doc_ids.append(response.json()['id'])
        time.sleep(0.01)  # Small delay

    response = client.get("/documents")
    data = response.json()

    # Most recent should be first
    assert data['documents'][0]['id'] == doc_ids[-1]
    assert data['documents'][-1]['id'] == doc_ids[0]


def test_upload_document_with_special_characters_in_filename(client):
    """Test uploading file with special characters in filename."""
    files = {'file': ('test file (1).txt', BytesIO(b'content'), 'text/plain')}
    response = client.post("/documents", files=files)

    assert response.status_code == 201
    assert response.json()['filename'] == 'test file (1).txt'


def test_concurrent_uploads_no_conflict(client):
    """Test that concurrent uploads don't cause conflicts."""
    responses = []

    # Simulate concurrent uploads
    for i in range(5):
        files = {'file': ('concurrent.txt', BytesIO(b'content'), 'text/plain')}
        response = client.post("/documents", files=files)
        responses.append(response)

    # All should succeed
    assert all(r.status_code == 201 for r in responses)

    # All should have unique IDs
    doc_ids = [r.json()['id'] for r in responses]
    assert len(doc_ids) == len(set(doc_ids))
