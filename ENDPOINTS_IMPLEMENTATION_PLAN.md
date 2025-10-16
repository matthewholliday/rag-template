# Solution Plan: Document Processing and Chunks Endpoints

## Overview
This plan outlines the implementation of two REST API endpoints for the RAG document ingestion system:
1. POST /documents/{id}/process - Triggers document reprocessing (chunking and embedding)
2. GET /documents/{id}/chunks - Retrieves all chunks generated from a document

These endpoints will enable document processing workflows and chunk retrieval capabilities as specified in the api-spec.yml.

## Requirements

### Functional Requirements
1. POST /documents/{id}/process must:
   - Accept a document ID as a path parameter
   - Return 202 Accepted with status "processing" and a message
   - Return 404 if document not found
   - Update document status to "processing" in the database
   - Trigger document chunking pipeline
   - Handle the chunking process (splitting document into text chunks)

2. GET /documents/{id}/chunks must:
   - Accept a document ID as a path parameter
   - Return an array of chunks with total count
   - Return 404 if document not found
   - Include all chunk fields: id, document_id, content, position, metadata (page, section)

### Technical Requirements
- Follow existing codebase patterns (FastAPI, repository pattern, service layer)
- Implement proper error handling for 404 cases
- Create comprehensive unit and integration tests
- Follow Python best practices (PEP 8, type hints)
- Maintain consistency with existing Document endpoints
- Use SQLite database for storing chunks

### Database Schema Requirements
- Create a `chunks` table with fields:
  - id (TEXT PRIMARY KEY)
  - document_id (TEXT, foreign key to documents)
  - content (TEXT)
  - position (INTEGER)
  - metadata_page (INTEGER, nullable)
  - metadata_section (TEXT, nullable)
  - created_at (TEXT)

## Approach

### High-Level Architecture
1. **Database Layer**: Create chunks table schema and migration
2. **Repository Layer**: Implement ChunkRepository for data access
3. **Service Layer**: Implement chunking logic and chunk retrieval in DocumentService
4. **API Layer**: Add two new endpoints to main.py
5. **Models Layer**: Add Chunk and related Pydantic models
6. **Testing**: Comprehensive test coverage for all layers

### Chunking Strategy
For this implementation, we'll use a simple text-based chunking strategy:
- Split document content by paragraphs or fixed character count (e.g., 500 characters with overlap)
- Generate unique chunk IDs (chunk_<uuid>)
- Store position as 0-indexed integer
- Extract metadata where possible (for future PDF/structured document support)

### Status Flow
Document status transitions:
- pending -> processing (when POST /documents/{id}/process is called)
- processing -> completed (when chunking succeeds)
- processing -> failed (when chunking fails)

## Implementation Steps

### Phase 1: Database Schema and Infrastructure

1. **Create database migration for chunks table**
   - Rationale: Need persistent storage for chunk data
   - Dependencies: None
   - Validation: Run init_db and verify table exists
   - Details:
     - Add chunks table creation to src/database.py init_db()
     - Include foreign key constraint to documents table
     - Add indexes on document_id for query performance
     - Add created_at index for potential sorting

2. **Create Chunk Pydantic models**
   - Rationale: Type-safe API responses and validation
   - Dependencies: None
   - Validation: Model instantiation tests pass
   - Details:
     - Add ChunkMetadata model (page, section)
     - Add Chunk model (id, document_id, content, position, metadata)
     - Add ChunkListResponse model (chunks array, total count)
     - Follow existing model patterns in src/models.py

### Phase 2: Repository Layer

3. **Implement ChunkRepository class**
   - Rationale: Separate data access from business logic
   - Dependencies: Database schema (step 1)
   - Validation: Unit tests for all repository methods
   - Details:
     - Create src/chunk_repository.py
     - Implement create_chunk(chunk: Chunk) -> Chunk
     - Implement get_chunks_by_document_id(document_id: str) -> List[Chunk]
     - Implement delete_chunks_by_document_id(document_id: str) -> bool
     - Implement _row_to_chunk() helper method
     - Follow patterns from DocumentRepository

4. **Extend DocumentRepository with chunk count updates**
   - Rationale: Keep document chunk_count synchronized
   - Dependencies: ChunkRepository (step 3)
   - Validation: Test that chunk_count updates correctly
   - Details:
     - Methods update_document_status and update_chunk_count already exist
     - Ensure they're used in the chunking workflow

### Phase 3: Business Logic Layer

5. **Implement document chunking service**
   - Rationale: Core business logic for text processing
   - Dependencies: ChunkRepository (step 3)
   - Validation: Unit tests with various document sizes and formats
   - Details:
     - Create src/chunking_service.py with ChunkingService class
     - Implement chunk_document(document_id: str, content: str) -> List[Chunk]
     - Use simple chunking algorithm (500 chars with 50 char overlap)
     - Generate unique chunk IDs
     - Set position as 0-indexed sequence
     - Handle edge cases (empty content, very small documents)

6. **Extend DocumentService with processing methods**
   - Rationale: Orchestrate chunking workflow with repository operations
   - Dependencies: ChunkingService (step 5), ChunkRepository (step 3)
   - Validation: Integration tests for process workflow
   - Details:
     - Add chunk_repository as dependency in __init__
     - Implement process_document(document_id: str) -> dict
       - Validate document exists (404 if not)
       - Update status to "processing"
       - Load document content from storage
       - Call chunking service
       - Save chunks to repository
       - Update document status to "completed" or "failed"
       - Update chunk_count
     - Implement get_document_chunks(document_id: str) -> Tuple[List[Chunk], int]
       - Validate document exists (404 if not)
       - Retrieve chunks from repository
       - Return chunks and count

### Phase 4: API Endpoints

7. **Implement POST /documents/{id}/process endpoint**
   - Rationale: User-facing API for triggering processing
   - Dependencies: DocumentService.process_document (step 6)
   - Validation: Integration tests for success and 404 cases
   - Details:
     - Add endpoint to src/main.py
     - Define response model (status: "processing", message: str)
     - Handle document not found -> 404
     - Call document_service.process_document(id)
     - Return 202 Accepted
     - Follow existing endpoint patterns

8. **Implement GET /documents/{id}/chunks endpoint**
   - Rationale: User-facing API for retrieving chunks
   - Dependencies: DocumentService.get_document_chunks (step 6)
   - Validation: Integration tests for success, 404, and empty cases
   - Details:
     - Add endpoint to src/main.py
     - Use ChunkListResponse model
     - Handle document not found -> 404
     - Call document_service.get_document_chunks(id)
     - Return chunks array and total count
     - Follow existing endpoint patterns

### Phase 5: Testing

9. **Write comprehensive unit tests**
   - Rationale: Ensure individual components work correctly
   - Dependencies: All implementation steps
   - Validation: All tests pass with good coverage
   - Details:
     - tests/test_chunk_repository.py - Repository CRUD operations
     - tests/test_chunking_service.py - Chunking algorithm logic
     - Extend tests/test_document_service.py with processing tests
     - Test edge cases, error conditions, boundary values

10. **Write integration tests for endpoints**
    - Rationale: Ensure end-to-end functionality
    - Dependencies: Step 9
    - Validation: All integration tests pass
    - Details:
      - Extend tests/test_document_endpoints.py
      - Test POST /documents/{id}/process success (202)
      - Test POST /documents/{id}/process not found (404)
      - Test GET /documents/{id}/chunks success with chunks
      - Test GET /documents/{id}/chunks success with no chunks
      - Test GET /documents/{id}/chunks not found (404)
      - Test document status transitions
      - Test chunk_count updates

### Phase 6: Integration and Cleanup

11. **Update main.py initialization**
    - Rationale: Wire up new dependencies
    - Dependencies: All implementation complete
    - Validation: Application starts without errors
    - Details:
      - Initialize ChunkRepository
      - Pass to DocumentService
      - Ensure database initialization includes chunks table

12. **Delete document cascade to chunks**
    - Rationale: Maintain referential integrity
    - Dependencies: ChunkRepository (step 3)
    - Validation: Test that deleting document deletes chunks
    - Details:
      - Update DocumentService.delete_document
      - Delete chunks before deleting document
      - Use chunk_repository.delete_chunks_by_document_id
      - Ensure cleanup is resilient to errors

## Risk Considerations

- **Large Document Processing**: Very large documents could cause memory issues or timeouts
  - Mitigation: Implement streaming or batch processing for large files in future iterations
  - For MVP, document reasonable size limits in API documentation

- **Concurrent Processing**: Multiple process requests for same document could cause conflicts
  - Mitigation: Check document status before processing; skip if already "processing"
  - Consider adding optimistic locking in future iterations

- **Database Performance**: Chunk retrieval could be slow for documents with many chunks
  - Mitigation: Index on document_id, consider pagination in future
  - Current implementation should be fine for MVP with reasonable chunk counts

- **Chunking Quality**: Simple character-based chunking may split mid-sentence
  - Mitigation: Document this as known limitation
  - Plan for improved chunking algorithms (sentence-aware, semantic) in future iterations

- **Transaction Management**: Partial failures could leave database in inconsistent state
  - Mitigation: Use try-catch blocks and update status to "failed" on errors
  - Consider database transactions for atomic operations

## Testing Strategy

### Unit Testing
- Repository layer: Test all CRUD operations with various inputs
- Service layer: Test chunking algorithm with different content sizes
- Model layer: Test Pydantic validation and serialization

### Integration Testing
- End-to-end API tests for both endpoints
- Test success paths (200/202 responses)
- Test error paths (404 responses)
- Test status transitions and chunk_count updates
- Test cascade deletion of chunks

### Test Coverage Goals
- Minimum 90% code coverage
- All edge cases covered (empty documents, missing documents, etc.)
- All error paths tested

### Test Data
- Small documents (< 100 chars)
- Medium documents (500-1000 chars)
- Large documents (> 2000 chars)
- Documents with special characters
- Empty content edge case

## Success Criteria

1. **Functional Completeness**
   - POST /documents/{id}/process returns 202 with correct response structure
   - POST /documents/{id}/process returns 404 for non-existent documents
   - GET /documents/{id}/chunks returns chunks array with total count
   - GET /documents/{id}/chunks returns 404 for non-existent documents
   - Document status updates correctly (pending -> processing -> completed)
   - chunk_count field updates correctly

2. **Code Quality**
   - All code follows PEP 8 style guidelines
   - Type hints present throughout
   - Comprehensive docstrings for all public methods
   - Consistent with existing codebase patterns

3. **Testing**
   - All unit tests pass
   - All integration tests pass
   - Test coverage > 90%
   - No failing test cases

4. **API Compliance**
   - Endpoints match api-spec.yml exactly
   - Response schemas match specification
   - HTTP status codes match specification
   - Error responses properly formatted

5. **Database Integrity**
   - Chunks table created successfully
   - Foreign key constraints enforced
   - Cascade deletion works correctly
   - No orphaned chunks after document deletion

## Implementation Notes

- Follow test-driven development (TDD) approach where practical
- Implement in the order specified to maintain working system at each step
- Run tests after each phase to catch issues early
- Use existing patterns from codebase (DocumentRepository, DocumentService, etc.)
- Keep functions pure and side effects isolated to boundaries
- Document any deviations from this plan with rationale
