# Document Upload Solution - Implementation Plan

## Overview
This plan details the implementation of document upload functionality for the RAG template API, including file upload, storage, metadata management, and CRUD operations.

## Requirements Summary

### In Scope
- POST /documents - Upload document with multipart/form-data
- GET /documents - List documents with pagination
- GET /documents/{id} - Get document details
- DELETE /documents/{id} - Delete document
- SQLite database for metadata persistence
- File storage in configured directory
- Repository pattern for data access
- Configuration management via config.json

### Out of Scope
- Document processing/chunking
- Embedding generation
- Query/search functionality
- POST /documents/{id}/process endpoint
- GET /documents/{id}/chunks endpoint

## Architecture Decisions

### 1. Layer Architecture
```
API Layer (main.py)
    ↓
Service Layer (document_service.py) - Business logic, file operations
    ↓
Repository Layer (document_repository.py) - Database operations
    ↓
Database (SQLite)
```

### 2. File Storage Strategy
- Store files with UUID-prefixed filenames to avoid conflicts
- Format: `{uuid}_{original_filename}`
- Maintain original filename in database metadata
- Create storage directory if it doesn't exist

### 3. Database Schema
```sql
CREATE TABLE documents (
    id TEXT PRIMARY KEY,
    filename TEXT NOT NULL,
    storage_path TEXT NOT NULL,
    status TEXT NOT NULL CHECK(status IN ('pending', 'processing', 'completed', 'failed')),
    metadata_title TEXT,
    metadata_description TEXT,
    metadata_tags TEXT,  -- JSON array stored as TEXT
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    chunk_count INTEGER DEFAULT 0
);

CREATE INDEX idx_created_at ON documents(created_at DESC);
CREATE INDEX idx_status ON documents(status);
```

## Implementation Steps

### Step 1: Database Infrastructure
**File**: `src/database.py`

**Tasks**:
1. Create database connection management
2. Implement database initialization with schema creation
3. Create index for performance optimization
4. Add connection lifecycle functions (get_connection, init_db)

**Testing Considerations**:
- Test database creation
- Test schema creation
- Test connection management
- Use temporary databases for testing

---

### Step 2: Document Models
**File**: `src/models.py` (extend existing)

**Tasks**:
1. Create `DocumentMetadata` model (title, description, tags)
2. Create `Document` model matching OpenAPI schema
3. Create `DocumentListResponse` model for pagination
4. Add validation for status enum values
5. Ensure proper datetime serialization

**Testing Considerations**:
- Test model validation
- Test metadata JSON serialization
- Test datetime formatting
- Test enum constraints

---

### Step 3: Document Repository
**File**: `src/document_repository.py`

**Tasks**:
1. Implement `DocumentRepository` class with dependency injection
2. Create `create_document()` method
3. Create `get_document_by_id()` method
4. Create `list_documents()` method with pagination
5. Create `delete_document()` method
6. Create `get_total_count()` method for pagination
7. Handle database exceptions properly

**Testing Considerations**:
- Test CRUD operations
- Test pagination logic
- Test error handling for not found
- Test transaction management
- Use in-memory database for unit tests

---

### Step 4: Configuration Management
**File**: `src/config.py`

**Tasks**:
1. Create `Config` model using Pydantic
2. Load configuration from config.json
3. Provide default values
4. Validate configuration on startup
5. Create singleton pattern for config access

**Testing Considerations**:
- Test config loading
- Test default values
- Test validation
- Test with missing files

---

### Step 5: File Storage Service
**File**: `src/storage.py`

**Tasks**:
1. Create `FileStorage` class
2. Implement `save_file()` method - save uploaded file with UUID prefix
3. Implement `delete_file()` method - remove file from filesystem
4. Implement `ensure_directory_exists()` method
5. Generate unique storage filenames
6. Handle file system errors gracefully

**Testing Considerations**:
- Test file saving
- Test file deletion
- Test directory creation
- Test filename generation
- Test error handling
- Use temporary directories for testing

---

### Step 6: Document Service (Business Logic)
**File**: `src/document_service.py`

**Tasks**:
1. Create `DocumentService` class with repository and storage dependencies
2. Implement `upload_document()` method:
   - Generate unique document ID
   - Save file to storage
   - Create database record with status='pending'
   - Return Document model
3. Implement `get_document()` method
4. Implement `list_documents()` method with pagination
5. Implement `delete_document()` method:
   - Delete from database
   - Delete from file system
   - Handle cascading operations
6. Add error handling and logging

**Testing Considerations**:
- Test upload with metadata
- Test upload without metadata
- Test list with various pagination parameters
- Test get with valid/invalid IDs
- Test delete cascading
- Test error scenarios (file errors, db errors)
- Mock repository and storage dependencies

---

### Step 7: API Endpoints
**File**: `src/main.py` (extend existing)

**Tasks**:
1. Add multipart form data handling dependencies
2. Implement POST /documents endpoint:
   - Accept UploadFile and optional metadata JSON
   - Parse metadata from form field
   - Call document service
   - Return 201 with Document response
3. Implement GET /documents endpoint:
   - Accept query params (limit, offset)
   - Validate pagination parameters
   - Return DocumentListResponse
4. Implement GET /documents/{id} endpoint:
   - Return Document or 404
5. Implement DELETE /documents/{id} endpoint:
   - Return 204 on success or 404
6. Add proper error handling (400, 404, 500)
7. Initialize database on startup
8. Create dependency injection for service

**Testing Considerations**:
- Test all endpoints with TestClient
- Test successful operations
- Test error responses (400, 404)
- Test pagination edge cases
- Test file upload validation
- Test metadata parsing
- Integration tests with real SQLite

---

### Step 8: Integration and Error Handling

**Tasks**:
1. Add application startup event to initialize database
2. Add proper exception handling middleware
3. Add logging throughout the application
4. Ensure proper cleanup of resources
5. Add file size validation
6. Add file type validation (if needed)

**Testing Considerations**:
- End-to-end integration tests
- Test error scenarios
- Test concurrent operations
- Test database connection pooling

---

### Step 9: Update Dependencies
**File**: `requirements.txt`

**Tasks**:
1. Add `aiosqlite` for async SQLite support (if needed)
2. Add `python-multipart` for file uploads
3. Verify all dependencies are compatible

---

## Data Flow Examples

### Upload Document Flow
```
1. Client sends POST /documents with file + metadata
2. FastAPI receives multipart/form-data
3. Document Service:
   a. Generates UUID for document
   b. Calls FileStorage to save file
   c. Calls Repository to create database record
   d. Returns Document model
4. API returns 201 with Document JSON
```

### List Documents Flow
```
1. Client sends GET /documents?limit=20&offset=0
2. FastAPI validates query parameters
3. Document Service:
   a. Calls Repository to get paginated results
   b. Calls Repository to get total count
4. API returns DocumentListResponse with pagination metadata
```

### Delete Document Flow
```
1. Client sends DELETE /documents/{id}
2. Document Service:
   a. Checks if document exists
   b. Calls FileStorage to delete file
   c. Calls Repository to delete record
3. API returns 204 No Content
```

## Testing Strategy

### Unit Tests
- Models (Pydantic validation)
- Repository (database operations)
- Storage (file operations)
- Service (business logic with mocked dependencies)
- Config (configuration loading)

### Integration Tests
- API endpoints with TestClient
- End-to-end flows
- Database + File System integration
- Error handling

### Test Organization
```
tests/
├── test_models.py (existing, extend)
├── test_database.py
├── test_document_repository.py
├── test_storage.py
├── test_document_service.py
├── test_config.py
├── test_document_endpoints.py (integration)
└── conftest.py (fixtures)
```

## Error Handling Requirements

1. **File Upload Errors**
   - Invalid file format: 400 Bad Request
   - File too large: 400 Bad Request
   - Storage failure: 500 Internal Server Error

2. **Database Errors**
   - Document not found: 404 Not Found
   - Duplicate ID: 500 Internal Server Error
   - Connection errors: 500 Internal Server Error

3. **Validation Errors**
   - Invalid pagination params: 400 Bad Request
   - Invalid metadata format: 400 Bad Request

## Success Criteria

1. All endpoints return correct status codes per OpenAPI spec
2. Files are stored in configured directory
3. Database correctly stores and retrieves metadata
4. Pagination works correctly with edge cases
5. Deletion removes both file and database record
6. All tests pass with good coverage (>90%)
7. Error handling is comprehensive and returns proper responses
8. Code follows project TDD and functional programming principles

## Implementation Order

1. Database infrastructure (bottom-up approach)
2. Models
3. Repository layer
4. Configuration management
5. Storage layer
6. Service layer (business logic)
7. API endpoints
8. Integration and testing
9. Error handling refinement

This order ensures each layer has its dependencies ready before implementation.

## Risks and Mitigations

| Risk | Mitigation |
|------|-----------|
| File system race conditions | Use UUID-based filenames |
| Database connection issues | Implement proper connection management |
| Orphaned files | Implement transaction-like behavior in service layer |
| Large file uploads | Add file size validation |
| Concurrent access | Use appropriate SQLite PRAGMA settings |

## Out of Scope Reminder

The following are explicitly NOT included in this implementation:
- Document processing logic (chunking, embedding)
- POST /documents/{id}/process endpoint
- GET /documents/{id}/chunks endpoint
- POST /query endpoint
- Async file processing workers
- Background task queues

These features may be added in future iterations but are not part of this implementation phase.