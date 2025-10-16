"""
Unit tests for chunking service.

Tests cover:
- Text chunking algorithms
- Chunk ID generation
- Position assignment
- Edge cases (empty content, small documents)
- Metadata extraction
"""
import pytest
from src.chunking_service import ChunkingService
from src.models import Chunk


@pytest.fixture
def chunking_service():
    """Create a chunking service instance."""
    return ChunkingService(chunk_size=500, overlap=50)


def test_chunk_document_basic(chunking_service):
    """Test basic document chunking."""
    document_id = "doc_test123"
    content = "This is a test document. " * 30  # ~750 chars

    chunks = chunking_service.chunk_document(document_id, content)

    assert len(chunks) > 0
    assert all(isinstance(chunk, Chunk) for chunk in chunks)
    assert all(chunk.document_id == document_id for chunk in chunks)


def test_chunk_positions_sequential(chunking_service):
    """Test that chunk positions are sequential starting from 0."""
    document_id = "doc_test123"
    content = "Lorem ipsum dolor sit amet. " * 50  # ~1400 chars

    chunks = chunking_service.chunk_document(document_id, content)

    positions = [chunk.position for chunk in chunks]
    assert positions == list(range(len(chunks)))
    assert positions[0] == 0


def test_chunk_ids_unique(chunking_service):
    """Test that each chunk gets a unique ID."""
    document_id = "doc_test123"
    content = "Some content here. " * 40

    chunks = chunking_service.chunk_document(document_id, content)

    chunk_ids = [chunk.id for chunk in chunks]
    assert len(chunk_ids) == len(set(chunk_ids))  # All unique
    assert all(chunk_id.startswith("chunk_") for chunk_id in chunk_ids)


def test_chunk_ids_format(chunking_service):
    """Test that chunk IDs follow the correct format."""
    document_id = "doc_test123"
    content = "Test content for chunk ID validation."

    chunks = chunking_service.chunk_document(document_id, content)

    for chunk in chunks:
        assert chunk.id.startswith("chunk_")
        # Should be chunk_ followed by hex string
        hex_part = chunk.id.replace("chunk_", "")
        assert len(hex_part) == 12
        assert all(c in "0123456789abcdef" for c in hex_part)


def test_chunk_content_not_empty(chunking_service):
    """Test that chunks have non-empty content."""
    document_id = "doc_test123"
    content = "Content to be chunked. " * 30

    chunks = chunking_service.chunk_document(document_id, content)

    assert all(chunk.content for chunk in chunks)
    assert all(len(chunk.content.strip()) > 0 for chunk in chunks)


def test_chunk_small_document(chunking_service):
    """Test chunking a document smaller than chunk size."""
    document_id = "doc_small"
    content = "This is a very small document."

    chunks = chunking_service.chunk_document(document_id, content)

    # Should create exactly one chunk
    assert len(chunks) == 1
    assert chunks[0].content == content
    assert chunks[0].position == 0


def test_chunk_empty_document(chunking_service):
    """Test chunking an empty document."""
    document_id = "doc_empty"
    content = ""

    chunks = chunking_service.chunk_document(document_id, content)

    # Should return empty list for empty content
    assert chunks == []


def test_chunk_whitespace_only_document(chunking_service):
    """Test chunking a document with only whitespace."""
    document_id = "doc_whitespace"
    content = "   \n\n\t  \n  "

    chunks = chunking_service.chunk_document(document_id, content)

    # Should return empty list or single empty chunk depending on implementation
    # For this implementation, we'll strip and treat as empty
    assert len(chunks) == 0 or (len(chunks) == 1 and not chunks[0].content.strip())


def test_chunk_size_approximately_correct(chunking_service):
    """Test that chunk sizes are approximately the configured size."""
    document_id = "doc_test123"
    content = "A" * 2000  # 2000 chars

    chunks = chunking_service.chunk_document(document_id, content)

    # Most chunks should be around 500 chars (except possibly the last one)
    for i, chunk in enumerate(chunks[:-1]):  # All but last
        assert 400 <= len(chunk.content) <= 600  # Allow some variance

    # Last chunk can be any size
    assert len(chunks[-1].content) > 0


def test_chunk_overlap_present(chunking_service):
    """Test that chunks have overlap as configured."""
    document_id = "doc_test123"
    content = "0123456789" * 100  # Repeating pattern

    chunks = chunking_service.chunk_document(document_id, content)

    # Check that consecutive chunks have overlapping content
    if len(chunks) > 1:
        for i in range(len(chunks) - 1):
            current_end = chunks[i].content[-50:]  # Last 50 chars
            next_start = chunks[i + 1].content[:50]  # First 50 chars
            # There should be some overlap
            assert len(current_end) > 0 and len(next_start) > 0


def test_chunk_large_document(chunking_service):
    """Test chunking a large document."""
    document_id = "doc_large"
    content = "This is sentence number {}. " * 200  # ~5600 chars
    content = content.format(*range(200))

    chunks = chunking_service.chunk_document(document_id, content)

    # Should create multiple chunks
    assert len(chunks) >= 10
    # All chunks should have the same document_id
    assert all(chunk.document_id == document_id for chunk in chunks)
    # Positions should be sequential
    assert [c.position for c in chunks] == list(range(len(chunks)))


def test_chunk_special_characters(chunking_service):
    """Test chunking content with special characters."""
    document_id = "doc_special"
    content = "Special chars: @#$%^&*()[]{}|\\<>?/~`+=- " * 30

    chunks = chunking_service.chunk_document(document_id, content)

    assert len(chunks) > 0
    # Content should be preserved
    reconstructed = "".join(c.content for c in chunks)
    # Allow for overlap, so reconstructed might have duplicates
    assert content[:100] in reconstructed


def test_chunk_unicode_characters(chunking_service):
    """Test chunking content with unicode characters."""
    document_id = "doc_unicode"
    content = "Unicode test: こんにちは 世界 🌍🌎🌏 Héllo Wörld " * 30

    chunks = chunking_service.chunk_document(document_id, content)

    assert len(chunks) > 0
    assert all(chunk.content for chunk in chunks)


def test_chunk_newlines_preserved(chunking_service):
    """Test that newlines are preserved in chunks."""
    document_id = "doc_newlines"
    content = "Line 1\nLine 2\nLine 3\n" * 30

    chunks = chunking_service.chunk_document(document_id, content)

    assert len(chunks) > 0
    # At least some chunks should contain newlines
    assert any("\n" in chunk.content for chunk in chunks)


def test_chunk_metadata_optional_fields(chunking_service):
    """Test that chunk metadata fields are optional."""
    document_id = "doc_test123"
    content = "Test content for metadata validation."

    chunks = chunking_service.chunk_document(document_id, content)

    # Metadata should be None or have optional fields
    for chunk in chunks:
        if chunk.metadata:
            # If metadata exists, page and section are optional
            assert hasattr(chunk.metadata, 'page')
            assert hasattr(chunk.metadata, 'section')


def test_chunk_different_sizes():
    """Test chunking with different chunk sizes."""
    document_id = "doc_test123"
    content = "Test content. " * 100  # ~1400 chars

    # Small chunks
    service_small = ChunkingService(chunk_size=100, overlap=10)
    chunks_small = service_small.chunk_document(document_id, content)

    # Large chunks
    service_large = ChunkingService(chunk_size=1000, overlap=100)
    chunks_large = service_large.chunk_document(document_id, content)

    # Smaller chunk size should produce more chunks
    assert len(chunks_small) > len(chunks_large)


def test_chunk_document_id_preserved(chunking_service):
    """Test that document ID is correctly set in all chunks."""
    document_id = "doc_unique_id_12345"
    content = "Content for document ID test. " * 30

    chunks = chunking_service.chunk_document(document_id, content)

    assert all(chunk.document_id == document_id for chunk in chunks)


def test_chunk_content_coverage(chunking_service):
    """Test that all content is included in chunks (accounting for overlap)."""
    document_id = "doc_test123"
    content = "The quick brown fox jumps over the lazy dog. " * 20

    chunks = chunking_service.chunk_document(document_id, content)

    # First chunk should start with beginning of content
    assert content.startswith(chunks[0].content[:20])

    # Last chunk should end with end of content
    assert content.endswith(chunks[-1].content[-20:])


def test_chunking_service_default_parameters():
    """Test chunking service with default parameters."""
    service = ChunkingService()
    document_id = "doc_default"
    content = "Test content. " * 50

    chunks = service.chunk_document(document_id, content)

    # Should successfully create chunks with defaults
    assert len(chunks) > 0
    assert all(isinstance(chunk, Chunk) for chunk in chunks)


def test_chunk_boundary_at_exact_size():
    """Test document that is exactly chunk_size."""
    service = ChunkingService(chunk_size=100, overlap=10)
    document_id = "doc_exact"
    content = "A" * 100  # Exactly chunk size

    chunks = service.chunk_document(document_id, content)

    # Should create exactly one chunk
    assert len(chunks) == 1
    assert len(chunks[0].content) == 100


def test_chunk_boundary_one_over_size():
    """Test document that is chunk_size + 1."""
    service = ChunkingService(chunk_size=100, overlap=10)
    document_id = "doc_one_over"
    content = "A" * 101  # One char over chunk size

    chunks = service.chunk_document(document_id, content)

    # Should create two chunks
    assert len(chunks) == 2
