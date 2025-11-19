"""Application configuration module.

This module handles all application settings using pydantic-settings with
composed configuration classes for better organization and maintainability.

Public Classes:
    DatabaseSettings: Database connection configuration
    SecuritySettings: Security and JWT configuration
    Settings: Main application settings

Public Functions:
    get_settings: Get cached application settings instance

Features:
    - Nested Pydantic settings with composition
    - Environment variable loading from .env file
    - LRU cache for settings singleton
    - Type-safe configuration with validation
"""

from functools import lru_cache
from typing import Annotated

from pydantic import AnyHttpUrl, Field, PostgresDsn, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

__all__ = ["DatabaseSettings", "SecuritySettings", "Settings", "get_settings"]


class DatabaseSettings(BaseSettings):
    """Database configuration settings.
    
    Attributes:
        url: PostgreSQL database URL for Supabase connection
    """

    url: Annotated[
        PostgresDsn,
        Field(
            description="PostgreSQL database URL for Supabase connection",
            examples=["postgresql+asyncpg://user:pass@host:5432/db"],
        ),
    ]

    model_config = SettingsConfigDict(env_prefix="DATABASE_")


class SecuritySettings(BaseSettings):
    """Security and authentication settings.
    
    Attributes:
        secret_key: Secret key for JWT token generation
        algorithm: Algorithm for JWT encoding (default: HS256)
        access_token_expire_minutes: Token expiration time in minutes
    """

    secret_key: Annotated[
        str,
        Field(
            min_length=32,
            description="Secret key for JWT token generation",
        ),
    ]
    algorithm: Annotated[
        str,
        Field(
            default="HS256",
            description="Algorithm for JWT encoding",
        ),
    ]
    access_token_expire_minutes: Annotated[
        int,
        Field(
            default=30,
            gt=0,
            description="Access token expiration time in minutes",
        ),
    ]

    model_config = SettingsConfigDict(env_prefix="")


class Settings(BaseSettings):
    """Main application settings.
    
    Attributes:
        app_name: Application name
        app_version: Application version
        debug: Debug mode flag
        api_v1_prefix: API v1 route prefix
        backend_cors_origins: List of allowed CORS origins
        database: Database configuration settings
        security: Security configuration settings
    """

    app_name: Annotated[
        str,
        Field(
            default="My API",
            description="Application name",
        ),
    ]
    app_version: Annotated[
        str,
        Field(
            default="1.0.0",
            description="Application version",
        ),
    ]
    debug: Annotated[
        bool,
        Field(
            default=False,
            description="Debug mode flag",
        ),
    ]
    api_v1_prefix: Annotated[
        str,
        Field(
            default="/api/v1",
            description="API v1 route prefix",
        ),
    ]
    backend_cors_origins: Annotated[
        list[AnyHttpUrl],
        Field(
            default_factory=list,
            description="List of allowed CORS origins",
        ),
    ]

    # Nested settings
    database: DatabaseSettings = Field(default_factory=DatabaseSettings)
    security: SecuritySettings = Field(default_factory=SecuritySettings)

    @field_validator("backend_cors_origins", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: str | list[str]) -> list[str] | str:
        """Parse CORS origins from string or list.

        Args:
            v (str | list[str]): CORS origins as string or list

        Returns:
            list[str] | str: Parsed CORS origins list
        """
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, list | str):
            return v
        raise ValueError(v)

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        env_nested_delimiter="__",
    )


@lru_cache
def get_settings() -> Settings:
    """Get cached application settings.

    Returns:
        Settings: Application settings instance
    """
    return Settings()
