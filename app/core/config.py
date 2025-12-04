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

from __future__ import annotations

from functools import lru_cache
from typing import Annotated, Literal

from pydantic import (
    AnyHttpUrl,
    Field,
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
    "WindxSettings",
    "Settings",
    "get_settings",
]


class DatabaseSettings(BaseSettings):
    """Database configuration settings.

    Supports both Supabase (development) and production PostgreSQL databases.
    The connection URL is automatically constructed based on the environment.

    Attributes:
        provider: Database provider (supabase or postgresql)
        connection_mode: Connection mode (direct, transaction_pooler, session_pooler)
        host: Database host
        port: Database port
        user: Database user
        password: Database password
        name: Database name
        pool_size: Connection pool size
        max_overflow: Maximum overflow connections
        pool_pre_ping: Enable connection health checks
        echo: Echo SQL queries (debug mode)
        disable_pooler_warning: Disable transaction pooler warning
    """

    provider: Annotated[
        Literal["supabase", "postgresql"],
        Field(
            default="supabase",
            description="Database provider type",
        ),
    ] = "supabase"

    connection_mode: Annotated[
        Literal["direct", "transaction_pooler", "session_pooler"],
        Field(
            default="transaction_pooler",
            description="Connection mode for Supabase (transaction_pooler recommended)",
        ),
    ] = "transaction_pooler"

    host: Annotated[
        str,
        Field(
            default="localhost",
            description="Database host",
            examples=["db.xxxxx.supabase.co", "localhost"],
        ),
    ] = "localhost"

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
            default="postgres",
            description="Database user",
            examples=["postgres"],
        ),
    ] = "postgres"

    password: Annotated[
        SecretStr,
        Field(
            default="",
            description="Database password",
        ),
    ] = SecretStr("")

    name: Annotated[
        str,
        Field(
            default="postgres",
            description="Database name",
        ),
    ] = "postgres"

    disable_pooler_warning: Annotated[
        bool,
        Field(
            default=False,
            description="Disable transaction pooler PREPARE statement warning",
        ),
    ] = False

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
    def url(self) -> str:
        """Construct database URL from components.

        Returns:
            str: Complete database connection URL
        """
        password_str = (
            self.password.get_secret_value()
            if isinstance(self.password, SecretStr)
            else self.password
        )
        return (
            f"postgresql+asyncpg://{self.user}:{password_str}@{self.host}:{self.port}/{self.name}"
        )

    @computed_field
    @property
    def is_supabase(self) -> bool:
        """Check if using Supabase provider.

        Returns:
            bool: True if provider is Supabase
        """
        return self.provider == "supabase"

    @model_validator(mode="after")
    def validate_connection_mode(self) -> DatabaseSettings:
        """Validate connection mode and show warnings."""
        import warnings

        # Show warning for transaction pooler
        if self.connection_mode == "transaction_pooler" and not self.disable_pooler_warning:
            warnings.warn(
                "Using transaction pooler mode: PREPARE statements are not supported. "
                "Set DATABASE_DISABLE_POOLER_WARNING=True to disable this warning.",
                UserWarning,
                stacklevel=2,
            )

        return self

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
            json_schema_extra={"required": True},
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


class WindxSettings(BaseSettings):
    """Windx configurator system settings.

    Configuration for the Windx product configuration system including
    formula evaluation safety, snapshot retention, and template tracking.

    Attributes:
        formula_max_length: Maximum length for price/weight formulas
        formula_timeout_seconds: Maximum execution time for formula evaluation
        formula_allowed_functions: Comma-separated list of allowed formula functions
        formula_max_variables: Maximum number of variables in a formula
        snapshot_retention_days: Days to retain configuration snapshots
        snapshot_auto_cleanup: Enable automatic cleanup of old snapshots
        template_track_usage: Enable template usage tracking
        template_success_threshold: Minimum success rate for template recommendations (0-100)
        template_popular_limit: Number of templates to show in popular list
        price_calculation_precision: Decimal precision for price calculations
        weight_calculation_precision: Decimal precision for weight calculations
    """

    formula_max_length: Annotated[
        int,
        Field(
            default=500,
            ge=100,
            le=2000,
            description="Maximum length for price/weight formulas",
        ),
    ] = 500

    formula_timeout_seconds: Annotated[
        int,
        Field(
            default=5,
            ge=1,
            le=30,
            description="Maximum execution time for formula evaluation in seconds",
        ),
    ] = 5

    formula_allowed_functions: Annotated[
        str,
        Field(
            default="abs,min,max,round,ceil,floor,sqrt,pow",
            description="Comma-separated list of allowed formula functions",
        ),
    ] = "abs,min,max,round,ceil,floor,sqrt,pow"

    formula_max_variables: Annotated[
        int,
        Field(
            default=20,
            ge=5,
            le=100,
            description="Maximum number of variables allowed in a formula",
        ),
    ] = 20

    snapshot_retention_days: Annotated[
        int,
        Field(
            default=365,
            ge=30,
            le=3650,
            description="Number of days to retain configuration snapshots",
        ),
    ] = 365

    snapshot_auto_cleanup: Annotated[
        bool,
        Field(
            default=True,
            description="Enable automatic cleanup of old snapshots",
        ),
    ] = True

    template_track_usage: Annotated[
        bool,
        Field(
            default=True,
            description="Enable template usage tracking and analytics",
        ),
    ] = True

    template_success_threshold: Annotated[
        int,
        Field(
            default=20,
            ge=0,
            le=100,
            description="Minimum success rate percentage for template recommendations",
        ),
    ] = 20

    template_popular_limit: Annotated[
        int,
        Field(
            default=10,
            ge=5,
            le=50,
            description="Number of templates to show in popular templates list",
        ),
    ] = 10

    price_calculation_precision: Annotated[
        int,
        Field(
            default=2,
            ge=0,
            le=6,
            description="Decimal places for price calculations",
        ),
    ] = 2

    weight_calculation_precision: Annotated[
        int,
        Field(
            default=2,
            ge=0,
            le=6,
            description="Decimal places for weight calculations",
        ),
    ] = 2

    # Experimental Features
    # Note: These flags are flexible and may be renamed or removed in future versions
    experimental_customers_page: Annotated[
        bool,
        Field(
            default=True,  # Default to True for development and testing
            description="Enable experimental customers admin page (may be renamed/removed)",
            alias_priority=2,  # Allow flexible renaming
        ),
    ] = True

    experimental_orders_page: Annotated[
        bool,
        Field(
            default=True,  # Default to True for development and testing
            description="Enable experimental orders admin page (may be renamed/removed)",
            alias_priority=2,  # Allow flexible renaming
        ),
    ] = True

    @computed_field
    @property
    def allowed_functions_list(self) -> list[str]:
        """Get list of allowed formula functions.

        Returns:
            list[str]: List of allowed function names
        """
        return [f.strip() for f in self.formula_allowed_functions.split(",") if f.strip()]

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="WINDX_",
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
        cache: Cache configuration settings
        limiter: Rate limiter configuration settings
        windx: Windx configurator system settings
    """

    app_name: Annotated[
        str,
        Field(
            default="WindX Product Configurator",
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

    # Currency settings
    currency: Annotated[
        str,
        Field(
            default="USD",
            description="Currency code (ISO 4217)",
        ),
    ]
    currency_symbol: Annotated[
        str,
        Field(
            default="$",
            description="Currency symbol for display",
        ),
    ]

    # Nested settings
    database: DatabaseSettings = Field(default_factory=DatabaseSettings)
    security: SecuritySettings = Field(default_factory=SecuritySettings)
    cache: CacheSettings = Field(default_factory=CacheSettings)
    limiter: LimiterSettings = Field(default_factory=LimiterSettings)
    windx: WindxSettings = Field(default_factory=WindxSettings)

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
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)

    @model_validator(mode="after")
    def validate_settings(self) -> Settings:
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
