"""
Repository pattern for chunk data access.

This module provides database operations for chunks,
abstracting the data access layer from business logic.
"""
import sqlite3
from typing import List
from datetime import datetime

from src.database import get_connection
from src.models import Chunk, ChunkMetadata


class ChunkRepository:
    """
    Repository for chunk database operations.

    Provides methods for CRUD operations on chunks.
    """

    def __init__(self, db_path: str):
        """
        Initialize the chunk repository.

        Args:
            db_path: Path to the SQLite database
        """
        self.db_path = db_path

    def create_chunk(self, chunk: Chunk) -> Chunk:
        """
        Create a new chunk in the database.

        Args:
            chunk: Chunk object to create

        Returns:
            Chunk: The created chunk

        Raises:
            sqlite3.Error: If database operation fails
        """
        conn = get_connection(self.db_path)
        cursor = conn.cursor()

        # Extract metadata fields
        metadata_page = None
        metadata_section = None

        if chunk.metadata:
            metadata_page = chunk.metadata.page
            metadata_section = chunk.metadata.section

        cursor.execute("""
            INSERT INTO chunks (
                id, document_id, content, position,
                metadata_page, metadata_section, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            chunk.id,
            chunk.document_id,
            chunk.content,
            chunk.position,
            metadata_page,
            metadata_section,
            datetime.utcnow().isoformat()
        ))

        conn.commit()
        conn.close()

        return chunk

    def get_chunks_by_document_id(self, document_id: str) -> List[Chunk]:
        """
        Retrieve all chunks for a document, ordered by position.

        Args:
            document_id: The document ID

        Returns:
            List[Chunk]: List of chunks ordered by position
        """
        conn = get_connection(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT * FROM chunks
            WHERE document_id = ?
            ORDER BY position ASC
        """, (document_id,))

        rows = cursor.fetchall()
        conn.close()

        return [self._row_to_chunk(row) for row in rows]

    def delete_chunks_by_document_id(self, document_id: str) -> bool:
        """
        Delete all chunks for a document.

        Args:
            document_id: The document ID

        Returns:
            bool: True if chunks were deleted, False if none found
        """
        conn = get_connection(self.db_path)
        cursor = conn.cursor()

        cursor.execute("DELETE FROM chunks WHERE document_id = ?", (document_id,))
        rows_affected = cursor.rowcount

        conn.commit()
        conn.close()

        return rows_affected > 0

    def _row_to_chunk(self, row: sqlite3.Row) -> Chunk:
        """
        Convert a database row to a Chunk object.

        Args:
            row: Database row

        Returns:
            Chunk: Chunk object
        """
        # Parse metadata
        metadata = None
        if row['metadata_page'] is not None or row['metadata_section'] is not None:
            metadata = ChunkMetadata(
                page=row['metadata_page'],
                section=row['metadata_section']
            )

        return Chunk(
            id=row['id'],
            document_id=row['document_id'],
            content=row['content'],
            position=row['position'],
            metadata=metadata
        )
