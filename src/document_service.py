"""
Document service layer with business logic.

This module handles document operations including upload, retrieval,
listing, and deletion with coordination between storage and repository.
"""
import uuid
from typing import Optional, List, Tuple
from datetime import datetime

from src.models import Document, DocumentMetadata
from src.document_repository import DocumentRepository
from src.storage import FileStorage


class DocumentService:
    """
    Service layer for document operations.

    Coordinates between file storage and database repository to provide
    complete document management functionality.
    """

    def __init__(self, repository: DocumentRepository, storage: FileStorage):
        """
        Initialize the document service.

        Args:
            repository: Document repository for database operations
            storage: File storage for file operations
        """
        self.repository = repository
        self.storage = storage

    def upload_document(
        self,
        filename: str,
        content: bytes,
        metadata: Optional[DocumentMetadata] = None
    ) -> Document:
        """
        Upload a new document.

        Saves the file to storage and creates a database record.

        Args:
            filename: Original filename
            content: File content as bytes
            metadata: Optional document metadata

        Returns:
            Document: The created document

        Raises:
            IOError: If file storage fails
        """
        # Generate unique document ID
        doc_id = f"doc_{uuid.uuid4().hex[:12]}"

        # Save file to storage
        storage_filename = self.storage.save_file(filename, content)

        # Create document object
        now = datetime.utcnow()
        document = Document(
            id=doc_id,
            filename=filename,
            status="pending",
            metadata=metadata,
            created_at=now,
            updated_at=now,
            chunk_count=0
        )

        # Save to database with storage path
        created_document = self.repository.create_document(document, storage_filename)

        return created_document

    def get_document(self, document_id: str) -> Optional[Document]:
        """
        Get a document by ID.

        Args:
            document_id: The document ID

        Returns:
            Optional[Document]: The document if found, None otherwise
        """
        return self.repository.get_document_by_id(document_id)

    def list_documents(self, limit: int = 20, offset: int = 0) -> Tuple[List[Document], int]:
        """
        List documents with pagination.

        Args:
            limit: Maximum number of documents to return
            offset: Number of documents to skip

        Returns:
            Tuple[List[Document], int]: (documents, total_count)
        """
        documents = self.repository.list_documents(limit=limit, offset=offset)
        total = self.repository.get_total_count()

        return documents, total

    def delete_document(self, document_id: str) -> bool:
        """
        Delete a document.

        Removes both the file from storage and the database record.
        This is a cascading delete operation.

        Args:
            document_id: The document ID to delete

        Returns:
            bool: True if document was deleted, False if not found
        """
        # Get document to find storage path
        document = self.repository.get_document_by_id(document_id)

        if document is None:
            return False

        # Delete file from storage (non-blocking, continues even if fails)
        try:
            # Get storage path from database row
            # Since Document model doesn't include storage_path, we need to query it
            # For now, we'll use a helper method
            storage_path = self._get_document_storage_path(document_id)
            if storage_path:
                self.storage.delete_file(storage_path)
        except Exception:
            # Continue with database deletion even if file deletion fails
            pass

        # Delete from database
        return self.repository.delete_document(document_id)

    def _get_document_storage_path(self, document_id: str) -> Optional[str]:
        """
        Get the storage path for a document.

        This is a helper method to retrieve the storage_path from the database
        since it's not included in the Document model.

        Args:
            document_id: The document ID

        Returns:
            Optional[str]: Storage path if found
        """
        from src.database import get_connection

        conn = get_connection(self.repository.db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT storage_path FROM documents WHERE id = ?", (document_id,))
        row = cursor.fetchone()
        conn.close()

        if row:
            return row['storage_path']

        return None
