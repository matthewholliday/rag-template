"""
Unit tests for database initialization and connection management.

Tests cover:
- Database creation
- Schema initialization
- Index creation
- Connection management
"""
import sqlite3
import pytest
from src.database import init_db, get_connection


def test_init_db_creates_documents_table(temp_db_path: str):
    """Test that init_db creates the documents table with correct schema."""
    init_db(temp_db_path)

    conn = sqlite3.connect(temp_db_path)
    cursor = conn.cursor()

    # Check table exists
    cursor.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='documents'"
    )
    result = cursor.fetchone()
    assert result is not None
    assert result[0] == 'documents'

    # Check columns
    cursor.execute("PRAGMA table_info(documents)")
    columns = cursor.fetchall()
    column_names = [col[1] for col in columns]

    expected_columns = [
        'id', 'filename', 'storage_path', 'status',
        'metadata_title', 'metadata_description', 'metadata_tags',
        'created_at', 'updated_at', 'chunk_count'
    ]

    for col in expected_columns:
        assert col in column_names, f"Column {col} missing from documents table"

    conn.close()


def test_init_db_creates_indexes(temp_db_path: str):
    """Test that init_db creates the required indexes."""
    init_db(temp_db_path)

    conn = sqlite3.connect(temp_db_path)
    cursor = conn.cursor()

    # Check indexes exist
    cursor.execute(
        "SELECT name FROM sqlite_master WHERE type='index' AND tbl_name='documents'"
    )
    indexes = cursor.fetchall()
    index_names = [idx[0] for idx in indexes]

    assert 'idx_created_at' in index_names
    assert 'idx_status' in index_names

    conn.close()


def test_init_db_idempotent(temp_db_path: str):
    """Test that calling init_db multiple times is safe (idempotent)."""
    # First initialization
    init_db(temp_db_path)

    # Insert test data
    conn = sqlite3.connect(temp_db_path)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO documents (id, filename, storage_path, status, created_at, updated_at) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        ('test_id', 'test.txt', '/path/test.txt', 'pending', '2025-01-01T00:00:00Z', '2025-01-01T00:00:00Z')
    )
    conn.commit()

    # Second initialization should not fail or delete data
    init_db(temp_db_path)

    cursor.execute("SELECT COUNT(*) FROM documents")
    count = cursor.fetchone()[0]
    assert count == 1

    conn.close()


def test_get_connection_returns_valid_connection(temp_db_path: str):
    """Test that get_connection returns a working database connection."""
    init_db(temp_db_path)

    conn = get_connection(temp_db_path)
    assert conn is not None
    assert isinstance(conn, sqlite3.Connection)

    # Test that connection works
    cursor = conn.cursor()
    cursor.execute("SELECT 1")
    result = cursor.fetchone()
    assert result[0] == 1

    conn.close()


def test_get_connection_with_row_factory(temp_db_path: str):
    """Test that get_connection returns rows as dictionaries."""
    init_db(temp_db_path)

    conn = get_connection(temp_db_path)
    cursor = conn.cursor()

    cursor.execute(
        "INSERT INTO documents (id, filename, storage_path, status, created_at, updated_at) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        ('test_id', 'test.txt', '/path/test.txt', 'pending', '2025-01-01T00:00:00Z', '2025-01-01T00:00:00Z')
    )
    conn.commit()

    cursor.execute("SELECT * FROM documents WHERE id = ?", ('test_id',))
    row = cursor.fetchone()

    # Should be able to access by column name
    assert row['id'] == 'test_id'
    assert row['filename'] == 'test.txt'
    assert row['status'] == 'pending'

    conn.close()


def test_database_status_constraint(temp_db_path: str):
    """Test that the status column has CHECK constraint for valid values."""
    init_db(temp_db_path)

    conn = sqlite3.connect(temp_db_path)
    cursor = conn.cursor()

    # Valid status should work
    cursor.execute(
        "INSERT INTO documents (id, filename, storage_path, status, created_at, updated_at) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        ('test_id', 'test.txt', '/path/test.txt', 'pending', '2025-01-01T00:00:00Z', '2025-01-01T00:00:00Z')
    )
    conn.commit()

    # Invalid status should fail
    with pytest.raises(sqlite3.IntegrityError):
        cursor.execute(
            "INSERT INTO documents (id, filename, storage_path, status, created_at, updated_at) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            ('test_id2', 'test2.txt', '/path/test2.txt', 'invalid_status', '2025-01-01T00:00:00Z', '2025-01-01T00:00:00Z')
        )
        conn.commit()

    conn.close()


def test_database_default_chunk_count(temp_db_path: str):
    """Test that chunk_count defaults to 0 when not specified."""
    init_db(temp_db_path)

    conn = sqlite3.connect(temp_db_path)
    cursor = conn.cursor()

    cursor.execute(
        "INSERT INTO documents (id, filename, storage_path, status, created_at, updated_at) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        ('test_id', 'test.txt', '/path/test.txt', 'pending', '2025-01-01T00:00:00Z', '2025-01-01T00:00:00Z')
    )
    conn.commit()

    cursor.execute("SELECT chunk_count FROM documents WHERE id = ?", ('test_id',))
    result = cursor.fetchone()
    assert result[0] == 0

    conn.close()
