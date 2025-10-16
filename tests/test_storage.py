"""
Unit tests for file storage operations.

Tests cover:
- Saving files to storage
- Deleting files from storage
- Directory creation
- Filename generation
- Error handling
"""
import os
import pytest
from src.storage import FileStorage, generate_storage_filename


def test_generate_storage_filename():
    """Test that generate_storage_filename creates unique filenames."""
    filename1 = generate_storage_filename("test.txt")
    filename2 = generate_storage_filename("test.txt")

    # Should have UUID prefix
    assert "_test.txt" in filename1
    assert "_test.txt" in filename2

    # Should be unique
    assert filename1 != filename2

    # Should preserve extension
    assert filename1.endswith(".txt")
    assert filename2.endswith(".txt")


def test_generate_storage_filename_no_extension():
    """Test filename generation for files without extension."""
    filename = generate_storage_filename("README")

    assert "_README" in filename
    # Should still work without extension


def test_generate_storage_filename_multiple_dots():
    """Test filename generation for files with multiple dots."""
    filename = generate_storage_filename("my.file.tar.gz")

    assert ".tar.gz" in filename or ".gz" in filename
    assert "_my.file" in filename or "_my" in filename


def test_file_storage_init(temp_storage_dir: str):
    """Test FileStorage initialization."""
    storage = FileStorage(temp_storage_dir)

    assert storage.storage_dir == temp_storage_dir


def test_file_storage_ensure_directory_exists(temp_storage_dir: str):
    """Test that FileStorage creates storage directory if it doesn't exist."""
    new_dir = os.path.join(temp_storage_dir, "subdir", "nested")
    storage = FileStorage(new_dir)

    storage.ensure_directory_exists()

    assert os.path.exists(new_dir)
    assert os.path.isdir(new_dir)


def test_file_storage_save_file(temp_storage_dir: str, sample_text_file: tuple[str, bytes]):
    """Test saving a file to storage."""
    storage = FileStorage(temp_storage_dir)
    filename, content = sample_text_file

    storage_filename = storage.save_file(filename, content)

    # Check return value
    assert storage_filename is not None
    assert filename in storage_filename

    # Check file exists
    file_path = os.path.join(temp_storage_dir, storage_filename)
    assert os.path.exists(file_path)

    # Check content
    with open(file_path, 'rb') as f:
        saved_content = f.read()
    assert saved_content == content


def test_file_storage_save_file_creates_directory(temp_storage_dir: str, sample_text_file: tuple[str, bytes]):
    """Test that save_file creates directory if it doesn't exist."""
    new_dir = os.path.join(temp_storage_dir, "new_directory")
    storage = FileStorage(new_dir)
    filename, content = sample_text_file

    storage_filename = storage.save_file(filename, content)

    # Directory should be created
    assert os.path.exists(new_dir)

    # File should be saved
    file_path = os.path.join(new_dir, storage_filename)
    assert os.path.exists(file_path)


def test_file_storage_save_multiple_files_unique(temp_storage_dir: str):
    """Test that saving multiple files with same name creates unique filenames."""
    storage = FileStorage(temp_storage_dir)
    content1 = b"Content 1"
    content2 = b"Content 2"

    filename1 = storage.save_file("test.txt", content1)
    filename2 = storage.save_file("test.txt", content2)

    # Filenames should be unique
    assert filename1 != filename2

    # Both files should exist
    assert os.path.exists(os.path.join(temp_storage_dir, filename1))
    assert os.path.exists(os.path.join(temp_storage_dir, filename2))

    # Content should be correct
    with open(os.path.join(temp_storage_dir, filename1), 'rb') as f:
        assert f.read() == content1
    with open(os.path.join(temp_storage_dir, filename2), 'rb') as f:
        assert f.read() == content2


def test_file_storage_delete_file(temp_storage_dir: str, sample_text_file: tuple[str, bytes]):
    """Test deleting a file from storage."""
    storage = FileStorage(temp_storage_dir)
    filename, content = sample_text_file

    # Save file first
    storage_filename = storage.save_file(filename, content)
    file_path = os.path.join(temp_storage_dir, storage_filename)
    assert os.path.exists(file_path)

    # Delete file
    storage.delete_file(storage_filename)

    # File should not exist
    assert not os.path.exists(file_path)


def test_file_storage_delete_nonexistent_file(temp_storage_dir: str):
    """Test that deleting non-existent file doesn't raise error."""
    storage = FileStorage(temp_storage_dir)

    # Should not raise exception
    storage.delete_file("nonexistent_file.txt")


def test_file_storage_get_file_path(temp_storage_dir: str):
    """Test getting full file path from storage filename."""
    storage = FileStorage(temp_storage_dir)
    storage_filename = "test_file.txt"

    file_path = storage.get_file_path(storage_filename)

    expected_path = os.path.join(temp_storage_dir, storage_filename)
    assert file_path == expected_path


def test_file_storage_file_exists(temp_storage_dir: str, sample_text_file: tuple[str, bytes]):
    """Test checking if file exists in storage."""
    storage = FileStorage(temp_storage_dir)
    filename, content = sample_text_file

    # File doesn't exist yet
    assert not storage.file_exists("nonexistent.txt")

    # Save file
    storage_filename = storage.save_file(filename, content)

    # File should exist
    assert storage.file_exists(storage_filename)


def test_file_storage_save_empty_file(temp_storage_dir: str):
    """Test saving an empty file."""
    storage = FileStorage(temp_storage_dir)
    content = b""

    storage_filename = storage.save_file("empty.txt", content)

    file_path = os.path.join(temp_storage_dir, storage_filename)
    assert os.path.exists(file_path)
    assert os.path.getsize(file_path) == 0


def test_file_storage_save_binary_file(temp_storage_dir: str):
    """Test saving binary file content."""
    storage = FileStorage(temp_storage_dir)
    # Binary content with various byte values
    content = bytes(range(256))

    storage_filename = storage.save_file("binary.dat", content)

    file_path = os.path.join(temp_storage_dir, storage_filename)
    with open(file_path, 'rb') as f:
        saved_content = f.read()

    assert saved_content == content
