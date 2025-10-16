"""
Repository pattern for document data access.

This module provides database operations for documents,
abstracting the data access layer from business logic.
"""
import json
import sqlite3
from typing import Optional, List
from datetime import datetime

from src.database import get_connection
from src.models import Document, DocumentMetadata


class DocumentRepository:
    """
    Repository for document database operations.

    Provides methods for CRUD operations on documents.
    """

    def __init__(self, db_path: str):
        """
        Initialize the document repository.

        Args:
            db_path: Path to the SQLite database
        """
        self.db_path = db_path

    def create_document(self, document: Document, storage_path: str) -> Document:
        """
        Create a new document in the database.

        Args:
            document: Document object to create
            storage_path: Path where the file is stored

        Returns:
            Document: The created document

        Raises:
            sqlite3.Error: If database operation fails
        """
        conn = get_connection(self.db_path)
        cursor = conn.cursor()

        # Serialize metadata as JSON
        metadata_title = None
        metadata_description = None
        metadata_tags = None

        if document.metadata:
            metadata_title = document.metadata.title
            metadata_description = document.metadata.description
            if document.metadata.tags:
                metadata_tags = json.dumps(document.metadata.tags)

        cursor.execute("""
            INSERT INTO documents (
                id, filename, storage_path, status,
                metadata_title, metadata_description, metadata_tags,
                created_at, updated_at, chunk_count
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            document.id,
            document.filename,
            storage_path,
            document.status,
            metadata_title,
            metadata_description,
            metadata_tags,
            document.created_at.isoformat(),
            document.updated_at.isoformat() if document.updated_at else document.created_at.isoformat(),
            document.chunk_count
        ))

        conn.commit()
        conn.close()

        return document

    def get_document_by_id(self, document_id: str) -> Optional[Document]:
        """
        Retrieve a document by its ID.

        Args:
            document_id: The document ID

        Returns:
            Optional[Document]: The document if found, None otherwise
        """
        conn = get_connection(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT * FROM documents WHERE id = ?
        """, (document_id,))

        row = cursor.fetchone()
        conn.close()

        if row is None:
            return None

        return self._row_to_document(row)

    def list_documents(self, limit: int = 20, offset: int = 0) -> List[Document]:
        """
        List documents with pagination.

        Documents are ordered by created_at in descending order (newest first).

        Args:
            limit: Maximum number of documents to return
            offset: Number of documents to skip

        Returns:
            List[Document]: List of documents
        """
        conn = get_connection(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT * FROM documents
            ORDER BY created_at DESC
            LIMIT ? OFFSET ?
        """, (limit, offset))

        rows = cursor.fetchall()
        conn.close()

        return [self._row_to_document(row) for row in rows]

    def get_total_count(self) -> int:
        """
        Get the total count of documents.

        Returns:
            int: Total number of documents in the database
        """
        conn = get_connection(self.db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM documents")
        count = cursor.fetchone()[0]

        conn.close()
        return count

    def delete_document(self, document_id: str) -> bool:
        """
        Delete a document from the database.

        Args:
            document_id: The document ID to delete

        Returns:
            bool: True if document was deleted, False if not found
        """
        conn = get_connection(self.db_path)
        cursor = conn.cursor()

        cursor.execute("DELETE FROM documents WHERE id = ?", (document_id,))
        rows_affected = cursor.rowcount

        conn.commit()
        conn.close()

        return rows_affected > 0

    def update_document_status(self, document_id: str, status: str) -> None:
        """
        Update the status of a document.

        Args:
            document_id: The document ID
            status: New status value
        """
        conn = get_connection(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE documents
            SET status = ?, updated_at = ?
            WHERE id = ?
        """, (status, datetime.utcnow().isoformat(), document_id))

        conn.commit()
        conn.close()

    def update_chunk_count(self, document_id: str, chunk_count: int) -> None:
        """
        Update the chunk count of a document.

        Args:
            document_id: The document ID
            chunk_count: New chunk count
        """
        conn = get_connection(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE documents
            SET chunk_count = ?, updated_at = ?
            WHERE id = ?
        """, (chunk_count, datetime.utcnow().isoformat(), document_id))

        conn.commit()
        conn.close()

    def _row_to_document(self, row: sqlite3.Row) -> Document:
        """
        Convert a database row to a Document object.

        Args:
            row: Database row

        Returns:
            Document: Document object
        """
        # Parse metadata
        metadata = None
        if row['metadata_title'] or row['metadata_description'] or row['metadata_tags']:
            tags = None
            if row['metadata_tags']:
                tags = json.loads(row['metadata_tags'])

            metadata = DocumentMetadata(
                title=row['metadata_title'],
                description=row['metadata_description'],
                tags=tags
            )

        return Document(
            id=row['id'],
            filename=row['filename'],
            status=row['status'],
            metadata=metadata,
            created_at=datetime.fromisoformat(row['created_at']),
            updated_at=datetime.fromisoformat(row['updated_at']) if row['updated_at'] else None,
            chunk_count=row['chunk_count']
        )
