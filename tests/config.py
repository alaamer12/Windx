"""Test configuration module.

This module provides test-specific settings that override the main
application settings for testing purposes.

Public Classes:
    TestSettings: Test configuration settings

Features:
    - Loads from .env.test file
    - Uses SQLite in-memory database
    - Disables caching and rate limiting
    - Safe test credentials
"""

from functools import lru_cache

from pydantic import Field
from pydantic_settings import SettingsConfigDict

from app.core.config import Settings

__all__ = ["TestSettings", "get_test_settings"]


class TestSettings(Settings):
    """Test-specific settings.

    Inherits from main Settings but overrides with test-specific values.
    Loads configuration from .env.test file.

    Attributes:
        All attributes from Settings plus test-specific overrides
    """

    model_config = SettingsConfigDict(
        env_file=".env.test",
        env_file_encoding="utf-8",
        case_sensitive=False,
        env_nested_delimiter="__",
        str_strip_whitespace=True,
        validate_default=True,
        validate_assignment=True,
        use_attribute_docstrings=True,
        extra="ignore",
    )

    # Override debug to always be True in tests
    debug: bool = Field(default=True, description="Debug mode (always True in tests)")

    # Override database settings for testing
    # These will be further overridden in conftest.py to use SQLite in-memory
    database_provider: str = Field(
        default="sqlite",
        description="Database provider for tests",
    )

    # Disable caching in tests by default
    cache_enabled: bool = Field(
        default=False,
        description="Cache enabled (disabled in tests)",
    )

    # Disable rate limiting in tests by default
    limiter_enabled: bool = Field(
        default=False,
        description="Rate limiter enabled (disabled in tests)",
    )


@lru_cache
def get_test_settings() -> TestSettings:
    """Get cached test settings.

    Returns:
        TestSettings: Test settings instance (cached singleton)

    Example:
        ```python
        settings = get_test_settings()
        assert settings.debug is True
        ```
    """
    return TestSettings()
