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
from typing import Annotated, Literal

from pydantic import (
    AnyHttpUrl,
    Field,
    PostgresDsn,
    RedisDsn,
    SecretStr,
    computed_field,
    field_validator,
    model_validator,
)
from pydantic_settings import BaseSettings, SettingsConfigDict

__all__ = [
    "DatabaseSettings",
    "SecuritySettings",
    "CacheSettings",
    "LimiterSettings",
    "Settings",
    "get_settings",
]


class DatabaseSettings(BaseSettings):
    """Database configuration settings.
    
    Supports both Supabase (development) and production PostgreSQL databases.
    The connection URL is automatically constructed based on the environment.
    
    Attributes:
        provider: Database provider (supabase or postgresql)
        host: Database host
        port: Database port
        user: Database user
        password: Database password
        name: Database name
        pool_size: Connection pool size
        max_overflow: Maximum overflow connections
        pool_pre_ping: Enable connection health checks
        echo: Echo SQL queries (debug mode)
    """

    provider: Annotated[
        Literal["supabase", "postgresql"],
        Field(
            default="supabase",
            description="Database provider type",
        ),
    ] = "supabase"

    host: Annotated[
        str,
        Field(
            description="Database host",
            examples=["db.xxxxx.supabase.co", "localhost"],
        ),
    ]

    port: Annotated[
        int,
        Field(
            default=5432,
            description="Database port",
        ),
    ] = 5432

    user: Annotated[
        str,
        Field(
            description="Database user",
            examples=["postgres"],
        ),
    ]

    password: Annotated[
        SecretStr,
        Field(
            description="Database password",
        ),
    ]

    name: Annotated[
        str,
        Field(
            default="postgres",
            description="Database name",
        ),
    ] = "postgres"

    pool_size: Annotated[
        int,
        Field(
            default=5,
            ge=1,
            le=20,
            description="Connection pool size",
        ),
    ] = 5

    max_overflow: Annotated[
        int,
        Field(
            default=10,
            ge=0,
            le=50,
            description="Maximum overflow connections beyond pool_size",
        ),
    ] = 10

    pool_pre_ping: Annotated[
        bool,
        Field(
            default=True,
            description="Enable connection health checks before using",
        ),
    ] = True

    echo: Annotated[
        bool,
        Field(
            default=False,
            description="Echo SQL queries to stdout",
        ),
    ] = False

    @computed_field
    @property
    def url(self) -> PostgresDsn:
        """Construct database URL from components.

        Returns:
            PostgresDsn: Complete database connection URL
        """
        password_str = self.password.get_secret_value() if isinstance(self.password, SecretStr) else self.password
        return PostgresDsn(
            f"postgresql+asyncpg://{self.user}:{password_str}"
            f"@{self.host}:{self.port}/{self.name}"
        )

    @computed_field
    @property
    def is_supabase(self) -> bool:
        """Check if using Supabase provider.

        Returns:
            bool: True if provider is Supabase
        """
        return self.provider == "supabase"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="DATABASE_",
        str_strip_whitespace=True,
        validate_default=True,
        validate_assignment=True,
        use_attribute_docstrings=True,
        extra="ignore",
    )


class SecuritySettings(BaseSettings):
    """Security and authentication settings.
    
    Attributes:
        secret_key: Secret key for JWT token generation
        algorithm: Algorithm for JWT encoding (default: HS256)
        access_token_expire_minutes: Token expiration time in minutes
    """

    secret_key: Annotated[
        SecretStr,
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

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="",
        str_strip_whitespace=True,
        validate_default=True,
        validate_assignment=True,
        use_attribute_docstrings=True,
        extra="ignore",
    )


class CacheSettings(BaseSettings):
    """Cache configuration settings.

    Attributes:
        enabled: Enable/disable caching
        redis_host: Redis host
        redis_port: Redis port
        redis_password: Redis password (optional)
        redis_db: Redis database number
        prefix: Cache key prefix
        default_ttl: Default TTL in seconds
    """

    enabled: Annotated[
        bool,
        Field(
            default=True,
            description="Enable caching",
        ),
    ] = True

    redis_host: Annotated[
        str,
        Field(
            default="localhost",
            description="Redis host",
        ),
    ] = "localhost"

    redis_port: Annotated[
        int,
        Field(
            default=6379,
            description="Redis port",
        ),
    ] = 6379

    redis_password: Annotated[
        SecretStr | None,
        Field(
            default=None,
            description="Redis password",
        ),
    ] = None

    redis_db: Annotated[
        int,
        Field(
            default=0,
            ge=0,
            le=15,
            description="Redis database number",
        ),
    ] = 0

    prefix: Annotated[
        str,
        Field(
            default="myapi:cache",
            description="Cache key prefix",
        ),
    ] = "myapi:cache"

    default_ttl: Annotated[
        int,
        Field(
            default=300,
            ge=0,
            description="Default TTL in seconds",
        ),
    ] = 300

    @computed_field
    @property
    def redis_url(self) -> RedisDsn:
        """Construct Redis URL from components.

        Returns:
            RedisDsn: Complete Redis connection URL
        """
        if self.redis_password:
            password_str = (
                self.redis_password.get_secret_value()
                if isinstance(self.redis_password, SecretStr)
                else self.redis_password
            )
            return RedisDsn(
                f"redis://:{password_str}@{self.redis_host}:{self.redis_port}/{self.redis_db}"
            )
        return RedisDsn(f"redis://{self.redis_host}:{self.redis_port}/{self.redis_db}")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="CACHE_",
        str_strip_whitespace=True,
        validate_default=True,
        validate_assignment=True,
        use_attribute_docstrings=True,
        extra="ignore",
    )


class LimiterSettings(BaseSettings):
    """Rate limiter configuration settings.

    Attributes:
        enabled: Enable/disable rate limiting
        redis_host: Redis host
        redis_port: Redis port
        redis_password: Redis password (optional)
        redis_db: Redis database number
        prefix: Rate limit key prefix
        default_times: Default number of requests
        default_seconds: Default time window in seconds
    """

    enabled: Annotated[
        bool,
        Field(
            default=True,
            description="Enable rate limiting",
        ),
    ] = True

    redis_host: Annotated[
        str,
        Field(
            default="localhost",
            description="Redis host",
        ),
    ] = "localhost"

    redis_port: Annotated[
        int,
        Field(
            default=6379,
            description="Redis port",
        ),
    ] = 6379

    redis_password: Annotated[
        SecretStr | None,
        Field(
            default=None,
            description="Redis password",
        ),
    ] = None

    redis_db: Annotated[
        int,
        Field(
            default=1,
            ge=0,
            le=15,
            description="Redis database number",
        ),
    ] = 1

    prefix: Annotated[
        str,
        Field(
            default="myapi:limiter",
            description="Rate limit key prefix",
        ),
    ] = "myapi:limiter"

    default_times: Annotated[
        int,
        Field(
            default=100,
            ge=1,
            description="Default number of requests allowed",
        ),
    ] = 100

    default_seconds: Annotated[
        int,
        Field(
            default=60,
            ge=1,
            description="Default time window in seconds",
        ),
    ] = 60

    @computed_field
    @property
    def redis_url(self) -> RedisDsn:
        """Construct Redis URL from components.

        Returns:
            RedisDsn: Complete Redis connection URL
        """
        if self.redis_password:
            password_str = (
                self.redis_password.get_secret_value()
                if isinstance(self.redis_password, SecretStr)
                else self.redis_password
            )
            return RedisDsn(
                f"redis://:{password_str}@{self.redis_host}:{self.redis_port}/{self.redis_db}"
            )
        return RedisDsn(f"redis://{self.redis_host}:{self.redis_port}/{self.redis_db}")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="LIMITER_",
        str_strip_whitespace=True,
        validate_default=True,
        validate_assignment=True,
        use_attribute_docstrings=True,
        extra="ignore",
    )


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
    cache: CacheSettings = Field(default_factory=CacheSettings)
    limiter: LimiterSettings = Field(default_factory=LimiterSettings)

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

    @model_validator(mode="after")
    def validate_settings(self) -> "Settings":
        """Validate settings after initialization.

        Returns:
            Settings: Validated settings instance

        Raises:
            ValueError: If validation fails
        """
        # Validate that at least one CORS origin is set in production
        if not self.debug and not self.backend_cors_origins:
            raise ValueError("CORS origins must be set in production mode")

        return self

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        env_nested_delimiter="__",
        str_strip_whitespace=True,
        validate_default=True,
        validate_assignment=True,
        use_attribute_docstrings=True,
        extra="ignore",  # Ignore extra fields from environment
        frozen=False,  # Allow modification after creation
    )


@lru_cache
def get_settings() -> Settings:
    """Get cached application settings.

    Returns:
        Settings: Application settings instance
    """
    return Settings()
