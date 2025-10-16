"""
Document chunking service.

This module provides text chunking functionality for breaking
documents into smaller, manageable chunks for processing.
"""
import uuid
from typing import List

from src.models import Chunk


class ChunkingService:
    """
    Service for chunking document content into smaller pieces.

    Uses a simple character-based chunking algorithm with overlap
    to ensure context preservation across chunk boundaries.
    """

    def __init__(self, chunk_size: int = 500, overlap: int = 50):
        """
        Initialize the chunking service.

        Args:
            chunk_size: Maximum size of each chunk in characters (default: 500)
            overlap: Number of overlapping characters between chunks (default: 50)
        """
        self.chunk_size = chunk_size
        self.overlap = overlap

    def chunk_document(self, document_id: str, content: str) -> List[Chunk]:
        """
        Chunk a document into smaller text segments.

        The algorithm splits text into chunks of approximately chunk_size
        characters with overlap between consecutive chunks to maintain context.

        Args:
            document_id: The document ID
            content: The document content to chunk

        Returns:
            List[Chunk]: List of chunks with sequential positions

        Examples:
            >>> service = ChunkingService(chunk_size=100, overlap=10)
            >>> chunks = service.chunk_document("doc_123", "A" * 250)
            >>> len(chunks)
            3
        """
        # Handle empty or whitespace-only content
        if not content or not content.strip():
            return []

        chunks = []
        position = 0
        start = 0

        while start < len(content):
            # Calculate end position for this chunk
            end = start + self.chunk_size

            # Extract chunk content
            chunk_content = content[start:end]

            # Skip if chunk is empty (shouldn't happen, but defensive)
            if not chunk_content:
                break

            # Create chunk with unique ID
            chunk = Chunk(
                id=self._generate_chunk_id(),
                document_id=document_id,
                content=chunk_content,
                position=position,
                metadata=None  # Basic implementation doesn't extract metadata
            )

            chunks.append(chunk)

            # Move to next chunk position with overlap
            # If this was the last chunk (we reached the end), break
            if end >= len(content):
                break

            # Move start forward by (chunk_size - overlap)
            start = end - self.overlap
            position += 1

        return chunks

    def _generate_chunk_id(self) -> str:
        """
        Generate a unique chunk ID.

        Returns:
            str: Unique chunk ID in format "chunk_<12_hex_chars>"
        """
        return f"chunk_{uuid.uuid4().hex[:12]}"
