"""
File storage operations for uploaded documents.

This module handles saving and deleting files in the configured
storage directory, with unique filename generation to avoid conflicts.
"""
import os
import uuid
from typing import Optional


def generate_storage_filename(original_filename: str) -> str:
    """
    Generate a unique storage filename with UUID prefix.

    Args:
        original_filename: The original filename from upload

    Returns:
        str: Unique filename in format: {uuid}_{original_filename}

    Example:
        >>> generate_storage_filename("document.pdf")
        "a1b2c3d4-..._document.pdf"
    """
    unique_id = str(uuid.uuid4())
    return f"{unique_id}_{original_filename}"


class FileStorage:
    """
    Manages file storage operations for uploaded documents.

    Attributes:
        storage_dir: Base directory for file storage
    """

    def __init__(self, storage_dir: str):
        """
        Initialize file storage.

        Args:
            storage_dir: Directory path where files will be stored
        """
        self.storage_dir = storage_dir

    def ensure_directory_exists(self) -> None:
        """
        Create the storage directory if it doesn't exist.

        Creates all parent directories as needed.
        """
        os.makedirs(self.storage_dir, exist_ok=True)

    def save_file(self, filename: str, content: bytes) -> str:
        """
        Save a file to storage with a unique filename.

        Args:
            filename: Original filename
            content: File content as bytes

        Returns:
            str: The storage filename (UUID-prefixed)

        Raises:
            IOError: If file cannot be written
        """
        self.ensure_directory_exists()

        storage_filename = generate_storage_filename(filename)
        file_path = os.path.join(self.storage_dir, storage_filename)

        with open(file_path, 'wb') as f:
            f.write(content)

        return storage_filename

    def delete_file(self, storage_filename: str) -> None:
        """
        Delete a file from storage.

        Args:
            storage_filename: The storage filename to delete

        Does not raise an error if the file doesn't exist.
        """
        file_path = os.path.join(self.storage_dir, storage_filename)

        if os.path.exists(file_path):
            os.remove(file_path)

    def get_file_path(self, storage_filename: str) -> str:
        """
        Get the full file path for a storage filename.

        Args:
            storage_filename: The storage filename

        Returns:
            str: Full path to the file
        """
        return os.path.join(self.storage_dir, storage_filename)

    def file_exists(self, storage_filename: str) -> bool:
        """
        Check if a file exists in storage.

        Args:
            storage_filename: The storage filename to check

        Returns:
            bool: True if file exists, False otherwise
        """
        file_path = os.path.join(self.storage_dir, storage_filename)
        return os.path.exists(file_path)

    def read_file(self, storage_filename: str) -> bytes:
        """
        Read a file from storage.

        Args:
            storage_filename: The storage filename to read

        Returns:
            bytes: File content

        Raises:
            FileNotFoundError: If file doesn't exist
            IOError: If file cannot be read
        """
        file_path = os.path.join(self.storage_dir, storage_filename)

        with open(file_path, 'rb') as f:
            return f.read()
