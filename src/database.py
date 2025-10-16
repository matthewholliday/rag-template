"""
Database initialization and connection management.

This module handles SQLite database setup, schema creation,
and connection lifecycle management.
"""
import sqlite3
from typing import Optional


def init_db(db_path: str) -> None:
    """
    Initialize the database with required schema.

    Creates the documents table and indexes if they don't exist.
    This function is idempotent and safe to call multiple times.

    Args:
        db_path: Path to the SQLite database file

    Schema:
        - documents table with all required fields
        - Indexes on created_at and status for query performance
        - CHECK constraint on status field
    """
    import os
    # Ensure directory exists
    db_dir = os.path.dirname(db_path)
    if db_dir and not os.path.exists(db_dir):
        os.makedirs(db_dir, exist_ok=True)

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Create documents table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS documents (
            id TEXT PRIMARY KEY,
            filename TEXT NOT NULL,
            storage_path TEXT NOT NULL,
            status TEXT NOT NULL CHECK(status IN ('pending', 'processing', 'completed', 'failed')),
            metadata_title TEXT,
            metadata_description TEXT,
            metadata_tags TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            chunk_count INTEGER DEFAULT 0
        )
    """)

    # Create indexes for performance
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_created_at
        ON documents(created_at DESC)
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_status
        ON documents(status)
    """)

    # Create chunks table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS chunks (
            id TEXT PRIMARY KEY,
            document_id TEXT NOT NULL,
            content TEXT NOT NULL,
            position INTEGER NOT NULL,
            metadata_page INTEGER,
            metadata_section TEXT,
            created_at TEXT NOT NULL,
            FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE
        )
    """)

    # Create indexes for chunks table
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_chunks_document_id
        ON chunks(document_id)
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_chunks_position
        ON chunks(document_id, position)
    """)

    conn.commit()
    conn.close()


def get_connection(db_path: str) -> sqlite3.Connection:
    """
    Get a database connection with row factory configured.

    Args:
        db_path: Path to the SQLite database file

    Returns:
        sqlite3.Connection: Database connection with Row factory

    The Row factory allows accessing columns by name like dictionaries.
    """
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn
