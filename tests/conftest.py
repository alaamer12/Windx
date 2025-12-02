"""Pytest configuration and shared fixtures.

This module provides shared fixtures for all tests including:
- Database setup and teardown
- Test client with httpx
- Authentication fixtures
- Factory fixtures for test data

Features:
    - Async test support
    - Isolated test database
    - Automatic cleanup
    - Reusable fixtures
"""

import asyncio
import os
from collections.abc import AsyncGenerator, Generator
from pathlib import Path
from typing import Any

import pytest
import pytest_asyncio

# Load test environment variables BEFORE any imports
from dotenv import load_dotenv

project_root = Path(__file__).parent.parent
test_env_file = project_root / ".env.test"
if test_env_file.exists():
    load_dotenv(test_env_file, override=True)

# Set test environment marker
os.environ["TESTING"] = "true"

# Now safe to import after env is loaded
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from app.core.config import get_settings
from app.database import Base, get_db
from app.models.session import Session  # noqa: F401

# Import all models to register them with Base.metadata
from app.models.user import User  # noqa: F401
from main import app
from tests.config import TestSettings, get_test_settings


# Test database URL - Use PostgreSQL with asyncpg (Supabase compatible)
# asyncpg is required for:
# - LTREE extension support (hierarchical data)
# - JSONB native support (flexible metadata)
# - Better async performance than psycopg
def get_test_database_url() -> str:
    """Get test database URL from settings.

    Returns:
        str: PostgreSQL connection string with asyncpg driver

    Note:
        Uses asyncpg driver for full PostgreSQL feature support including
        LTREE extension and JSONB types required by the Windx schema.
    """
    test_settings = get_test_settings()

    # Access database settings from the nested database object
    db = test_settings.database

    # Build PostgreSQL connection string with asyncpg driver
    # Note: password is a SecretStr, so we need to get its value
    password = db.password.get_secret_value() if db.password else ""

    return f"postgresql+asyncpg://{db.user}:{password}@{db.host}:{db.port}/{db.name}"


TEST_DATABASE_URL = get_test_database_url()


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Create event loop for async tests.

    Yields:
        asyncio.AbstractEventLoop: Event loop for tests
    """
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def test_settings() -> TestSettings:
    """Get test settings.

    Returns:
        TestSettings: Test configuration loaded from .env.test
    """
    return get_test_settings()


# noinspection PyUnresolvedReferences
@pytest.fixture(scope="session", autouse=True)
def setup_test_settings(test_settings: TestSettings):
    """Setup test settings globally.

    This fixture runs automatically for all tests and overrides
    the main settings with test settings.

    Args:
        test_settings (TestSettings): Test configuration
    """
    # Override the main get_settings to return test settings
    app.dependency_overrides[get_settings] = lambda: test_settings

    # Mock the FastAPILimiter to prevent errors when rate_limit is used
    # This is necessary because endpoints have rate_limit dependencies
    from unittest.mock import AsyncMock

    from fastapi_cache import FastAPICache
    from fastapi_cache.backends.inmemory import InMemoryBackend
    from fastapi_limiter import FastAPILimiter

    # Create async mock for identifier
    async def mock_identifier(request):
        return "test_key"

    # Create async mock for callback (always allow requests in tests)
    async def mock_callback(request, response, pexpire):
        return  # Allow all requests

    # Mock the FastAPILimiter redis client
    FastAPILimiter.redis = AsyncMock()
    FastAPILimiter.lua_sha = "mock_sha"
    FastAPILimiter.identifier = mock_identifier
    FastAPILimiter.http_callback = mock_callback
    FastAPILimiter.ws_callback = mock_callback

    # Initialize FastAPICache with in-memory backend for tests
    FastAPICache.init(InMemoryBackend())

    yield

    # Cleanup
    app.dependency_overrides.clear()


@pytest_asyncio.fixture(scope="function")
async def test_engine():
    """Create test database engine with asyncpg driver.

    This fixture:
    - Creates a fresh database engine for each test
    - Enables LTREE extension (required for hierarchical attributes)
    - Drops and recreates all tables for isolation
    - Uses NullPool to prevent connection pooling issues in tests
    - Properly disposes of connections after test completion

    Yields:
        AsyncEngine: Test database engine with asyncpg driver

    Note:
        asyncpg driver is used instead of psycopg for:
        - Native LTREE support
        - Better JSONB performance
        - Full async/await support
        - Supabase compatibility
    """
    engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=False,
        poolclass=NullPool,  # Disable pooling for test isolation
        # No connect_args needed for asyncpg (unlike aiosqlite)
    )

    # Create all tables with LTREE extension
    async with engine.begin() as conn:
        # Drop first to ensure clean state between tests
        await conn.run_sync(Base.metadata.drop_all)
        
        # Enable LTREE extension for hierarchical attribute nodes
        # This is required by the Windx schema for efficient tree queries
        # Use IF NOT EXISTS to avoid errors if extension already exists
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS ltree"))

        # Create all tables from SQLAlchemy models
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    # Cleanup: Drop all tables and dispose engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()

    # Wait for connections to close gracefully
    await asyncio.sleep(0.05)


@pytest_asyncio.fixture(scope="function")
async def test_session_maker(test_engine):
    """Create test session maker.

    Args:
        test_engine: Test database engine

    Yields:
        async_sessionmaker: Session maker for tests
    """
    session_maker = async_sessionmaker(
        test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autocommit=False,
        autoflush=False,
    )
    yield session_maker


@pytest_asyncio.fixture(scope="function")
async def db_session(test_session_maker) -> AsyncGenerator[AsyncSession, None]:
    """Create test database session.

    Args:
        test_session_maker: Session maker fixture

    Yields:
        AsyncSession: Test database session
    """
    async with test_session_maker() as session:
        try:
            yield session
        finally:
            await session.rollback()
            await session.close()


# noinspection PyUnresolvedReferences
@pytest_asyncio.fixture(scope="function")
async def client(
    db_session: AsyncSession, test_settings: TestSettings
) -> AsyncGenerator[AsyncClient, None]:
    """Create test HTTP client with httpx.

    Args:
        db_session (AsyncSession): Test database session
        test_settings (TestSettings): Test settings

    Yields:
        AsyncClient: HTTP client for testing
    """

    # Override database dependency
    async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
        yield db_session

    # Store existing overrides
    existing_overrides = app.dependency_overrides.copy()

    # Add database override
    app.dependency_overrides[get_db] = override_get_db

    # Create async client
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        yield ac

    # Restore original overrides (don't clear everything)
    app.dependency_overrides = existing_overrides


@pytest.fixture
def test_user_data() -> dict[str, Any]:
    """Get test user data.

    Returns:
        dict[str, Any]: Test user data
    """
    return {
        "email": "test@example.com",
        "username": "testuser",
        "password": "TestPassword123!",
        "full_name": "Test User",
    }


@pytest.fixture
def test_superuser_data() -> dict[str, Any]:
    """Get test superuser data.

    Returns:
        dict[str, Any]: Test superuser data
    """
    return {
        "email": "admin@example.com",
        "username": "admin",
        "password": "AdminPassword123!",
        "full_name": "Admin User",
        "is_superuser": True,
    }


@pytest_asyncio.fixture
async def test_user(db_session: AsyncSession, test_user_data: dict[str, Any]):
    """Create test user in database.

    Args:
        db_session (AsyncSession): Database session
        test_user_data (dict): Test user data

    Returns:
        User: Created test user
    """
    from app.schemas.user import UserCreate
    from app.services.user import UserService

    user_service = UserService(db_session)
    user_in = UserCreate(**test_user_data)
    user = await user_service.create_user(user_in)
    return user


@pytest_asyncio.fixture
async def test_superuser(db_session: AsyncSession, test_superuser_data: dict[str, Any]):
    """Create test superuser in database.

    Args:
        db_session (AsyncSession): Database session
        test_superuser_data (dict): Test superuser data

    Returns:
        User: Created test superuser
    """
    from app.schemas.user import UserCreate
    from app.services.user import UserService

    user_service = UserService(db_session)
    user_in = UserCreate(**test_superuser_data)
    user = await user_service.create_user(user_in)

    # Make superuser
    user.is_superuser = True
    db_session.add(user)
    await db_session.flush()  # Flush instead of commit to keep transaction open
    await db_session.refresh(user)

    return user


@pytest_asyncio.fixture
async def auth_headers(
    client: AsyncClient, test_user, test_user_data: dict[str, Any]
) -> dict[str, str]:
    """Get authentication headers for test user.

    Args:
        client (AsyncClient): HTTP client
        test_user: Test user (ensures user is created)
        test_user_data (dict): Test user data

    Returns:
        dict[str, str]: Authorization headers
    """
    # Login to get token
    response = await client.post(
        "/api/v1/auth/login",
        json={
            "username": test_user_data["username"],
            "password": test_user_data["password"],
        },
    )
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest_asyncio.fixture
async def superuser_auth_headers(
    client: AsyncClient,
    test_superuser,
    test_superuser_data: dict[str, Any],
) -> dict[str, str]:
    """Get authentication headers for test superuser.

    Args:
        client (AsyncClient): HTTP client
        test_superuser: Test superuser (ensures user is created)
        test_superuser_data (dict): Test superuser data

    Returns:
        dict[str, str]: Authorization headers
    """
    # Login to get token
    response = await client.post(
        "/api/v1/auth/login",
        json={
            "username": test_superuser_data["username"],
            "password": test_superuser_data["password"],
        },
    )
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
