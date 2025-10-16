"""
Pytest configuration and shared fixtures for all tests.

This module provides common test fixtures including:
- Temporary database setup
- Temporary file storage
- Test client setup
- Mock data factories
"""
import json
import os
import tempfile
from typing import Generator
import pytest
from fastapi.testclient import TestClient
import sqlite3


@pytest.fixture
def temp_db_path() -> Generator[str, None, None]:
    """
    Create a temporary SQLite database file for testing.

    Yields:
        str: Path to temporary database file

    The database file is automatically cleaned up after the test.
    """
    with tempfile.NamedTemporaryFile(mode='w', suffix='.db', delete=False) as f:
        db_path = f.name

    yield db_path

    # Cleanup
    if os.path.exists(db_path):
        os.unlink(db_path)


@pytest.fixture
def temp_storage_dir() -> Generator[str, None, None]:
    """
    Create a temporary directory for file storage testing.

    Yields:
        str: Path to temporary storage directory

    The directory and all contents are cleaned up after the test.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


@pytest.fixture
def temp_config_file(temp_db_path: str, temp_storage_dir: str) -> Generator[str, None, None]:
    """
    Create a temporary config.json file for testing.

    Args:
        temp_db_path: Path to temporary database
        temp_storage_dir: Path to temporary storage directory

    Yields:
        str: Path to temporary config file
    """
    config_data = {
        "storage": {
            "documents_dir": temp_storage_dir
        },
        "database": {
            "path": temp_db_path
        }
    }

    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(config_data, f)
        config_path = f.name

    yield config_path

    # Cleanup
    if os.path.exists(config_path):
        os.unlink(config_path)


@pytest.fixture
def sample_document_metadata() -> dict:
    """
    Provide sample document metadata for testing.

    Returns:
        dict: Sample metadata with title, description, and tags
    """
    return {
        "title": "Test Document",
        "description": "A test document for unit testing",
        "tags": ["test", "sample", "unittest"]
    }


@pytest.fixture
def sample_text_file() -> Generator[tuple[str, bytes], None, None]:
    """
    Create a sample text file for upload testing.

    Yields:
        tuple: (filename, content) pair
    """
    filename = "test_document.txt"
    content = b"This is a test document content.\nIt has multiple lines.\nFor testing purposes."
    yield (filename, content)


@pytest.fixture
def sample_pdf_file() -> Generator[tuple[str, bytes], None, None]:
    """
    Create a sample PDF-like file for upload testing.

    Note: This is a mock PDF, not a real PDF file.

    Yields:
        tuple: (filename, content) pair
    """
    filename = "test_document.pdf"
    content = b"%PDF-1.4\nMock PDF content for testing"
    yield (filename, content)


@pytest.fixture
def db_connection(temp_db_path: str) -> Generator[sqlite3.Connection, None, None]:
    """
    Provide a SQLite database connection for testing.

    Args:
        temp_db_path: Path to temporary database

    Yields:
        sqlite3.Connection: Database connection

    The connection is automatically closed after the test.
    """
    conn = sqlite3.connect(temp_db_path)
    conn.row_factory = sqlite3.Row

    yield conn

    conn.close()
