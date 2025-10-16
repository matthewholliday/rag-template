"""
Configuration management for the application.

This module handles loading and validating configuration from JSON files,
providing type-safe access to application settings.
"""
import json
from typing import Optional
from pydantic import BaseModel, Field


class StorageConfig(BaseModel):
    """Storage configuration settings."""

    documents_dir: str = Field(
        ...,
        description="Directory path where uploaded documents will be stored"
    )


class DatabaseConfig(BaseModel):
    """Database configuration settings."""

    path: str = Field(
        ...,
        description="Path to the SQLite database file"
    )


class Config(BaseModel):
    """Application configuration model."""

    storage: StorageConfig
    database: DatabaseConfig


def load_config(config_path: str = "config.json") -> Config:
    """
    Load configuration from a JSON file.

    Args:
        config_path: Path to the configuration JSON file (default: "config.json")

    Returns:
        Config: Validated configuration object

    Raises:
        FileNotFoundError: If the config file doesn't exist
        json.JSONDecodeError: If the file contains invalid JSON
        pydantic.ValidationError: If the configuration is invalid

    Example:
        >>> config = load_config()
        >>> print(config.storage.documents_dir)
        ./data/documents
    """
    with open(config_path, 'r') as f:
        config_data = json.load(f)

    return Config(**config_data)


# Global configuration instance
_config: Optional[Config] = None


def get_config(config_path: str = "config.json") -> Config:
    """
    Get the global configuration instance (singleton pattern).

    This function loads the configuration once and caches it for
    subsequent calls, ensuring consistent configuration across the app.

    Args:
        config_path: Path to the configuration JSON file

    Returns:
        Config: Cached configuration object
    """
    global _config

    if _config is None:
        _config = load_config(config_path)

    return _config
