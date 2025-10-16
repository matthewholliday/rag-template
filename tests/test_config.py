"""
Unit tests for configuration management.

Tests cover:
- Loading configuration from JSON file
- Default values
- Validation
- Error handling for missing files
"""
import json
import os
import pytest
from src.config import load_config, Config


def test_load_config_from_file(temp_config_file: str):
    """Test loading configuration from a valid JSON file."""
    config = load_config(temp_config_file)

    assert isinstance(config, Config)
    assert config.storage.documents_dir is not None
    assert config.database.path is not None


def test_load_config_validates_structure(temp_config_file: str):
    """Test that loaded configuration has expected structure."""
    config = load_config(temp_config_file)

    # Check storage configuration
    assert hasattr(config, 'storage')
    assert hasattr(config.storage, 'documents_dir')

    # Check database configuration
    assert hasattr(config, 'database')
    assert hasattr(config.database, 'path')


def test_load_config_with_default_path():
    """Test loading configuration from default path (config.json)."""
    # This test assumes config.json exists in the project root
    if os.path.exists('config.json'):
        config = load_config()
        assert isinstance(config, Config)
        assert config.storage.documents_dir == "./data/documents"
        assert config.database.path == "./data/rag.db"


def test_load_config_missing_file():
    """Test that loading from non-existent file raises appropriate error."""
    with pytest.raises(FileNotFoundError):
        load_config('/nonexistent/path/config.json')


def test_load_config_invalid_json(tmp_path):
    """Test that loading invalid JSON raises appropriate error."""
    invalid_config = tmp_path / "invalid.json"
    invalid_config.write_text("{ invalid json }")

    with pytest.raises(json.JSONDecodeError):
        load_config(str(invalid_config))


def test_load_config_missing_required_fields(tmp_path):
    """Test that configuration with missing required fields raises validation error."""
    incomplete_config = tmp_path / "incomplete.json"
    incomplete_config.write_text('{"storage": {}}')

    with pytest.raises(Exception):  # Pydantic validation error
        load_config(str(incomplete_config))


def test_config_model_storage_configuration():
    """Test Config model storage configuration."""
    config_data = {
        "storage": {
            "documents_dir": "/custom/path/documents"
        },
        "database": {
            "path": "/custom/path/db.sqlite"
        }
    }

    config = Config(**config_data)

    assert config.storage.documents_dir == "/custom/path/documents"
    assert config.database.path == "/custom/path/db.sqlite"


def test_config_model_database_configuration():
    """Test Config model database configuration."""
    config_data = {
        "storage": {
            "documents_dir": "./data/documents"
        },
        "database": {
            "path": "./data/test.db"
        }
    }

    config = Config(**config_data)

    assert config.database.path == "./data/test.db"


def test_config_storage_dir_path_expansion(temp_config_file: str):
    """Test that storage directory paths are properly handled."""
    config = load_config(temp_config_file)

    # Should return a valid path string
    assert isinstance(config.storage.documents_dir, str)
    assert len(config.storage.documents_dir) > 0


def test_config_database_path_validation(temp_config_file: str):
    """Test that database path is properly validated."""
    config = load_config(temp_config_file)

    # Should return a valid path string
    assert isinstance(config.database.path, str)
    assert len(config.database.path) > 0
