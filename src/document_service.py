"""
Document service layer with business logic.

This module handles document operations including upload, retrieval,
listing, deletion, processing, and chunk management with coordination
between storage, repositories, and chunking service.
"""
import uuid
from typing import Optional, List, Tuple
from datetime import datetime

from src.models import Document, DocumentMetadata, Chunk
from src.document_repository import DocumentRepository
from src.storage import FileStorage
from src.chunk_repository import ChunkRepository
from src.chunking_service import ChunkingService


class DocumentService:
    """
    Service layer for document operations.

    Coordinates between file storage, database repositories, and chunking
    service to provide complete document management functionality.
    """

    def __init__(
        self,
        repository: DocumentRepository,
        storage: FileStorage,
        chunk_repository: Optional[ChunkRepository] = None,
        chunking_service: Optional[ChunkingService] = None
    ):
        """
        Initialize the document service.

        Args:
            repository: Document repository for database operations
            storage: File storage for file operations
            chunk_repository: Chunk repository for chunk database operations (optional)
            chunking_service: Chunking service for document processing (optional)
        """
        self.repository = repository
        self.storage = storage
        self.chunk_repository = chunk_repository
        self.chunking_service = chunking_service or ChunkingService()

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

        Removes chunks, file from storage, and the database record.
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

        # Delete chunks if chunk repository is configured
        if self.chunk_repository is not None:
            try:
                self.chunk_repository.delete_chunks_by_document_id(document_id)
            except Exception:
                # Continue even if chunk deletion fails
                pass

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

    def process_document(self, document_id: str) -> dict:
        """
        Process a document by chunking its content.

        Loads the document content from storage, chunks it using the chunking
        service, and stores the chunks in the database. Updates document status
        and chunk count.

        Args:
            document_id: The document ID to process

        Returns:
            dict: Processing status response with 'status' and 'message' keys

        Raises:
            ValueError: If document not found or chunk_repository not configured
        """
        # Validate document exists
        document = self.repository.get_document_by_id(document_id)
        if document is None:
            raise ValueError(f"Document {document_id} not found")

        # Validate chunk repository is configured
        if self.chunk_repository is None:
            raise ValueError("Chunk repository not configured")

        try:
            # Update status to processing
            self.repository.update_document_status(document_id, "processing")

            # Get storage path and load content
            storage_path = self._get_document_storage_path(document_id)
            if not storage_path:
                raise ValueError(f"Storage path not found for document {document_id}")

            # Read file content
            content = self.storage.read_file(storage_path)

            # Decode bytes to string (assuming UTF-8)
            content_str = content.decode('utf-8', errors='ignore')

            # Delete existing chunks for this document (for reprocessing)
            self.chunk_repository.delete_chunks_by_document_id(document_id)

            # Chunk the document
            chunks = self.chunking_service.chunk_document(document_id, content_str)

            # Save chunks to database
            for chunk in chunks:
                self.chunk_repository.create_chunk(chunk)

            # Update document status and chunk count
            self.repository.update_chunk_count(document_id, len(chunks))
            self.repository.update_document_status(document_id, "completed")

            return {
                "status": "processing",
                "message": "Document processing initiated"
            }

        except Exception as e:
            # Update status to failed on error
            self.repository.update_document_status(document_id, "failed")
            raise

    def get_document_chunks(self, document_id: str) -> Tuple[List[Chunk], int]:
        """
        Get all chunks for a document.

        Args:
            document_id: The document ID

        Returns:
            Tuple[List[Chunk], int]: (chunks, total_count)

        Raises:
            ValueError: If document not found or chunk_repository not configured
        """
        # Validate document exists
        document = self.repository.get_document_by_id(document_id)
        if document is None:
            raise ValueError(f"Document {document_id} not found")

        # Validate chunk repository is configured
        if self.chunk_repository is None:
            raise ValueError("Chunk repository not configured")

        # Get chunks
        chunks = self.chunk_repository.get_chunks_by_document_id(document_id)

        return chunks, len(chunks)
