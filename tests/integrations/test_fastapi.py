"""Tests for FastAPI integration."""

from crudites.integrations.fastapi import CorsConfig


def test_cors_config_defaults() -> None:
    """Test CorsConfig default values."""
    config = CorsConfig()
    assert config.allow_origins == ["*"]
    assert config.allow_credentials is True
    assert config.allow_methods == ["*"]
    assert config.allow_headers == ["*"]


def test_cors_config_custom_values() -> None:
    """Test CorsConfig with custom values."""
    config = CorsConfig(
        allow_origins=["http://localhost:3000"],
        allow_credentials=False,
        allow_methods=["GET", "POST"],
        allow_headers=["Content-Type", "Authorization"],
    )
    assert config.allow_origins == ["http://localhost:3000"]
    assert config.allow_credentials is False
    assert config.allow_methods == ["GET", "POST"]
    assert config.allow_headers == ["Content-Type", "Authorization"]


def test_cors_config_partial_custom_values() -> None:
    """Test CorsConfig with some custom values and some defaults."""
    config = CorsConfig(
        allow_origins=["http://localhost:3000"], allow_headers=["Content-Type"]
    )
    assert config.allow_origins == ["http://localhost:3000"]
    assert config.allow_credentials is True  # default value
    assert config.allow_methods == ["*"]  # default value
    assert config.allow_headers == ["Content-Type"]
