"""Test configuration module.

This module provides test-specific settings that override the main
application settings for testing purposes.

Public Classes:
    TestSettings: Test configuration settings

Features:
    - Loads from .env.test file
    - Uses PostgreSQL database (Supabase or local)
    - Supports LTREE and JSONB PostgreSQL types
    - Disables caching and rate limiting
    - Safe test credentials
"""

from functools import lru_cache

from pydantic import Field, model_validator
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

    @model_validator(mode="after")
    def override_database_schema(self):
        """Override database schema to test_windx for test isolation."""
        # Force test schema to be test_windx
        self.database.schema_ = "test_windx"
        return self

    # Override database settings for testing
    # Now uses PostgreSQL with asyncpg for LTREE and JSONB support
    database_provider: str = Field(
        default="postgresql",
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

    # Test user credentials
    test_admin_username: str = Field(
        default="test_admin",
        description="Test admin username",
    )
    test_admin_email: str = Field(
        default="test_admin@example.com",
        description="Test admin email",
    )
    test_admin_password: str = Field(
        default="AdminPassword123!",
        description="Test admin password",
    )
    test_user_username: str = Field(
        default="test_user",
        description="Test regular user username",
    )
    test_user_email: str = Field(
        default="test_user@example.com",
        description="Test regular user email",
    )
    test_user_password: str = Field(
        default="UserPassword123!",
        description="Test regular user password",
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
