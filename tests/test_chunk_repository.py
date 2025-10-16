"""
Unit tests for chunk repository.

Tests cover:
- Chunk creation and storage
- Retrieving chunks by document ID
- Deleting chunks by document ID
- Row to chunk conversion
- Error handling
"""
import pytest
from datetime import datetime
from src.chunk_repository import ChunkRepository
from src.models import Chunk, ChunkMetadata
from src.database import init_db


@pytest.fixture
def chunk_repository(temp_db_path: str):
    """Create a chunk repository with initialized database."""
    init_db(temp_db_path)
    return ChunkRepository(temp_db_path)


@pytest.fixture
def sample_chunk():
    """Create a sample chunk for testing."""
    return Chunk(
        id="chunk_test123",
        document_id="doc_test456",
        content="This is test chunk content for repository testing.",
        position=0,
        metadata=None
    )


@pytest.fixture
def sample_chunk_with_metadata():
    """Create a sample chunk with metadata."""
    return Chunk(
        id="chunk_meta123",
        document_id="doc_test789",
        content="Chunk with metadata content.",
        position=1,
        metadata=ChunkMetadata(page=5, section="Introduction")
    )


def test_create_chunk_success(chunk_repository, sample_chunk):
    """Test creating a chunk successfully."""
    created_chunk = chunk_repository.create_chunk(sample_chunk)

    assert created_chunk is not None
    assert created_chunk.id == sample_chunk.id
    assert created_chunk.document_id == sample_chunk.document_id
    assert created_chunk.content == sample_chunk.content
    assert created_chunk.position == sample_chunk.position


def test_create_chunk_with_metadata(chunk_repository, sample_chunk_with_metadata):
    """Test creating a chunk with metadata."""
    created_chunk = chunk_repository.create_chunk(sample_chunk_with_metadata)

    assert created_chunk.metadata is not None
    assert created_chunk.metadata.page == 5
    assert created_chunk.metadata.section == "Introduction"


def test_create_chunk_without_metadata(chunk_repository, sample_chunk):
    """Test creating a chunk without metadata."""
    created_chunk = chunk_repository.create_chunk(sample_chunk)

    assert created_chunk.metadata is None


def test_get_chunks_by_document_id_single(chunk_repository, sample_chunk):
    """Test retrieving chunks for a document with one chunk."""
    chunk_repository.create_chunk(sample_chunk)

    chunks = chunk_repository.get_chunks_by_document_id(sample_chunk.document_id)

    assert len(chunks) == 1
    assert chunks[0].id == sample_chunk.id
    assert chunks[0].document_id == sample_chunk.document_id


def test_get_chunks_by_document_id_multiple(chunk_repository):
    """Test retrieving multiple chunks for a document."""
    document_id = "doc_multi123"

    # Create multiple chunks
    chunks_to_create = [
        Chunk(id=f"chunk_{i}", document_id=document_id, content=f"Content {i}", position=i)
        for i in range(5)
    ]

    for chunk in chunks_to_create:
        chunk_repository.create_chunk(chunk)

    retrieved_chunks = chunk_repository.get_chunks_by_document_id(document_id)

    assert len(retrieved_chunks) == 5
    assert all(c.document_id == document_id for c in retrieved_chunks)


def test_get_chunks_by_document_id_ordered_by_position(chunk_repository):
    """Test that chunks are returned ordered by position."""
    document_id = "doc_order123"

    # Create chunks in random order
    positions = [3, 0, 2, 1, 4]
    for pos in positions:
        chunk = Chunk(
            id=f"chunk_pos_{pos}",
            document_id=document_id,
            content=f"Content at position {pos}",
            position=pos
        )
        chunk_repository.create_chunk(chunk)

    chunks = chunk_repository.get_chunks_by_document_id(document_id)

    # Should be ordered by position
    assert len(chunks) == 5
    positions_returned = [c.position for c in chunks]
    assert positions_returned == [0, 1, 2, 3, 4]


def test_get_chunks_by_document_id_not_found(chunk_repository):
    """Test retrieving chunks for non-existent document."""
    chunks = chunk_repository.get_chunks_by_document_id("nonexistent_doc")

    assert chunks == []


def test_get_chunks_by_document_id_isolation(chunk_repository):
    """Test that chunks are isolated by document ID."""
    doc1_id = "doc_1"
    doc2_id = "doc_2"

    # Create chunks for doc1
    for i in range(3):
        chunk = Chunk(id=f"chunk_doc1_{i}", document_id=doc1_id, content=f"Doc1 {i}", position=i)
        chunk_repository.create_chunk(chunk)

    # Create chunks for doc2
    for i in range(2):
        chunk = Chunk(id=f"chunk_doc2_{i}", document_id=doc2_id, content=f"Doc2 {i}", position=i)
        chunk_repository.create_chunk(chunk)

    doc1_chunks = chunk_repository.get_chunks_by_document_id(doc1_id)
    doc2_chunks = chunk_repository.get_chunks_by_document_id(doc2_id)

    assert len(doc1_chunks) == 3
    assert len(doc2_chunks) == 2
    assert all(c.document_id == doc1_id for c in doc1_chunks)
    assert all(c.document_id == doc2_id for c in doc2_chunks)


def test_delete_chunks_by_document_id_success(chunk_repository):
    """Test deleting all chunks for a document."""
    document_id = "doc_delete123"

    # Create chunks
    for i in range(3):
        chunk = Chunk(id=f"chunk_del_{i}", document_id=document_id, content=f"Content {i}", position=i)
        chunk_repository.create_chunk(chunk)

    # Verify chunks exist
    chunks_before = chunk_repository.get_chunks_by_document_id(document_id)
    assert len(chunks_before) == 3

    # Delete chunks
    result = chunk_repository.delete_chunks_by_document_id(document_id)

    assert result is True

    # Verify chunks are gone
    chunks_after = chunk_repository.get_chunks_by_document_id(document_id)
    assert chunks_after == []


def test_delete_chunks_by_document_id_not_found(chunk_repository):
    """Test deleting chunks for non-existent document."""
    result = chunk_repository.delete_chunks_by_document_id("nonexistent_doc")

    # Should return False when no chunks found
    assert result is False


def test_delete_chunks_does_not_affect_other_documents(chunk_repository):
    """Test that deleting chunks for one document doesn't affect others."""
    doc1_id = "doc_keep"
    doc2_id = "doc_delete"

    # Create chunks for both documents
    for i in range(2):
        chunk1 = Chunk(id=f"chunk_keep_{i}", document_id=doc1_id, content=f"Keep {i}", position=i)
        chunk2 = Chunk(id=f"chunk_del_{i}", document_id=doc2_id, content=f"Delete {i}", position=i)
        chunk_repository.create_chunk(chunk1)
        chunk_repository.create_chunk(chunk2)

    # Delete chunks for doc2
    chunk_repository.delete_chunks_by_document_id(doc2_id)

    # Verify doc1 chunks still exist
    doc1_chunks = chunk_repository.get_chunks_by_document_id(doc1_id)
    assert len(doc1_chunks) == 2

    # Verify doc2 chunks are gone
    doc2_chunks = chunk_repository.get_chunks_by_document_id(doc2_id)
    assert len(doc2_chunks) == 0


def test_create_multiple_chunks_same_position_different_docs(chunk_repository):
    """Test that multiple documents can have chunks at the same position."""
    chunk1 = Chunk(id="chunk_1", document_id="doc_1", content="Content 1", position=0)
    chunk2 = Chunk(id="chunk_2", document_id="doc_2", content="Content 2", position=0)

    chunk_repository.create_chunk(chunk1)
    chunk_repository.create_chunk(chunk2)

    doc1_chunks = chunk_repository.get_chunks_by_document_id("doc_1")
    doc2_chunks = chunk_repository.get_chunks_by_document_id("doc_2")

    assert len(doc1_chunks) == 1
    assert len(doc2_chunks) == 1
    assert doc1_chunks[0].position == 0
    assert doc2_chunks[0].position == 0


def test_chunk_content_with_special_characters(chunk_repository):
    """Test storing and retrieving chunks with special characters."""
    chunk = Chunk(
        id="chunk_special",
        document_id="doc_special",
        content="Special chars: @#$%^&*()[]{}|\\<>?/~`+=-'\"\n\t",
        position=0
    )

    chunk_repository.create_chunk(chunk)
    retrieved = chunk_repository.get_chunks_by_document_id("doc_special")

    assert len(retrieved) == 1
    assert retrieved[0].content == chunk.content


def test_chunk_content_with_unicode(chunk_repository):
    """Test storing and retrieving chunks with unicode characters."""
    chunk = Chunk(
        id="chunk_unicode",
        document_id="doc_unicode",
        content="Unicode: こんにちは 世界 🌍 Héllo",
        position=0
    )

    chunk_repository.create_chunk(chunk)
    retrieved = chunk_repository.get_chunks_by_document_id("doc_unicode")

    assert len(retrieved) == 1
    assert retrieved[0].content == chunk.content


def test_chunk_large_content(chunk_repository):
    """Test storing and retrieving chunks with large content."""
    large_content = "A" * 10000  # 10KB of content

    chunk = Chunk(
        id="chunk_large",
        document_id="doc_large",
        content=large_content,
        position=0
    )

    chunk_repository.create_chunk(chunk)
    retrieved = chunk_repository.get_chunks_by_document_id("doc_large")

    assert len(retrieved) == 1
    assert len(retrieved[0].content) == 10000
    assert retrieved[0].content == large_content


def test_chunk_metadata_page_only(chunk_repository):
    """Test chunk with only page metadata."""
    chunk = Chunk(
        id="chunk_page",
        document_id="doc_meta",
        content="Content with page metadata",
        position=0,
        metadata=ChunkMetadata(page=10, section=None)
    )

    chunk_repository.create_chunk(chunk)
    retrieved = chunk_repository.get_chunks_by_document_id("doc_meta")

    assert len(retrieved) == 1
    assert retrieved[0].metadata is not None
    assert retrieved[0].metadata.page == 10
    assert retrieved[0].metadata.section is None


def test_chunk_metadata_section_only(chunk_repository):
    """Test chunk with only section metadata."""
    chunk = Chunk(
        id="chunk_section",
        document_id="doc_meta2",
        content="Content with section metadata",
        position=0,
        metadata=ChunkMetadata(page=None, section="Conclusion")
    )

    chunk_repository.create_chunk(chunk)
    retrieved = chunk_repository.get_chunks_by_document_id("doc_meta2")

    assert len(retrieved) == 1
    assert retrieved[0].metadata is not None
    assert retrieved[0].metadata.page is None
    assert retrieved[0].metadata.section == "Conclusion"


def test_chunk_high_position_value(chunk_repository):
    """Test chunk with very high position value."""
    chunk = Chunk(
        id="chunk_high_pos",
        document_id="doc_pos",
        content="High position chunk",
        position=999999
    )

    chunk_repository.create_chunk(chunk)
    retrieved = chunk_repository.get_chunks_by_document_id("doc_pos")

    assert len(retrieved) == 1
    assert retrieved[0].position == 999999


def test_get_chunks_empty_database(chunk_repository):
    """Test retrieving chunks from empty database."""
    chunks = chunk_repository.get_chunks_by_document_id("any_doc_id")

    assert chunks == []


def test_delete_chunks_empty_database(chunk_repository):
    """Test deleting chunks from empty database."""
    result = chunk_repository.delete_chunks_by_document_id("any_doc_id")

    assert result is False


def test_create_and_retrieve_preserves_all_fields(chunk_repository):
    """Test that all chunk fields are preserved through create and retrieve."""
    original = Chunk(
        id="chunk_complete",
        document_id="doc_complete",
        content="Complete chunk content",
        position=42,
        metadata=ChunkMetadata(page=7, section="Methodology")
    )

    chunk_repository.create_chunk(original)
    retrieved = chunk_repository.get_chunks_by_document_id("doc_complete")

    assert len(retrieved) == 1
    chunk = retrieved[0]

    assert chunk.id == original.id
    assert chunk.document_id == original.document_id
    assert chunk.content == original.content
    assert chunk.position == original.position
    assert chunk.metadata.page == original.metadata.page
    assert chunk.metadata.section == original.metadata.section


def test_create_chunk_with_empty_content(chunk_repository):
    """Test creating a chunk with empty content string."""
    chunk = Chunk(
        id="chunk_empty_content",
        document_id="doc_test",
        content="",
        position=0
    )

    created = chunk_repository.create_chunk(chunk)
    assert created.content == ""

    retrieved = chunk_repository.get_chunks_by_document_id("doc_test")
    assert len(retrieved) == 1
    assert retrieved[0].content == ""


def test_chunks_with_newlines_in_content(chunk_repository):
    """Test chunks with newlines in content."""
    chunk = Chunk(
        id="chunk_newlines",
        document_id="doc_newlines",
        content="Line 1\nLine 2\nLine 3\n",
        position=0
    )

    chunk_repository.create_chunk(chunk)
    retrieved = chunk_repository.get_chunks_by_document_id("doc_newlines")

    assert len(retrieved) == 1
    assert "\n" in retrieved[0].content
    assert retrieved[0].content.count("\n") == 3
