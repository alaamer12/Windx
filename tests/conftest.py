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

# Import all models to register them with Base.metadata
# Import directly to avoid circular imports
from app.models.user import User  # noqa: F401
from app.models.manufacturing_type import ManufacturingType  # noqa: F401
from app.models.attribute_node import AttributeNode  # noqa: F401
from app.models.configuration import Configuration  # noqa: F401
from app.models.configuration_selection import ConfigurationSelection  # noqa: F401
from app.models.customer import Customer  # noqa: F401
from app.models.quote import Quote  # noqa: F401
from app.models.order import Order  # noqa: F401
from app.models.order_item import OrderItem  # noqa: F401
from app.models.configuration_template import ConfigurationTemplate  # noqa: F401
from app.models.template_selection import TemplateSelection  # noqa: F401

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


def check_redis_available(host: str = "localhost", port: int = 6379, timeout: float = 1.0) -> bool:
    """Check if Redis is available and accessible.

    Args:
        host: Redis host (default: localhost)
        port: Redis port (default: 6379)
        timeout: Connection timeout in seconds (default: 1.0)

    Returns:
        bool: True if Redis is available, False otherwise
    """
    try:
        import redis.asyncio as redis
        import asyncio
        
        async def _check():
            try:
                client = redis.Redis(
                    host=host,
                    port=port,
                    socket_connect_timeout=timeout,
                    socket_timeout=timeout,
                )
                await client.ping()
                await client.close()
                return True
            except Exception:
                return False
        
        # Run async check
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # If loop is already running, create a new one
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(asyncio.run, _check())
                return future.result(timeout=timeout + 1)
        else:
            return loop.run_until_complete(_check())
    except Exception:
        return False


@pytest.fixture(scope="function")
def redis_test_settings(request, test_settings: TestSettings) -> TestSettings:
    """Override test settings to enable Redis for tests marked with @pytest.mark.redis.

    This fixture automatically enables cache and rate limiter for tests that need Redis.
    It checks if the test is marked with @pytest.mark.redis and enables Redis accordingly.
    
    If Redis is not available, the test will be skipped with a helpful message.

    Args:
        request: Pytest request object to check markers
        test_settings: Base test settings

    Returns:
        TestSettings: Modified settings with Redis enabled if test has redis marker
        
    Raises:
        pytest.skip: If test has redis marker but Redis is not available
    """
    # Check if test has redis marker
    has_redis_marker = request.node.get_closest_marker("redis") is not None
    
    if has_redis_marker:
        # Check if Redis is available
        redis_host = test_settings.cache.redis_host
        redis_port = test_settings.cache.redis_port
        
        if not check_redis_available(redis_host, redis_port):
            pytest.skip(
                f"Redis is not available at {redis_host}:{redis_port}. "
                "Start Redis with: docker run -d -p 6379:6379 redis:7-alpine"
            )
        
        # Create a copy of settings with Redis enabled
        from copy import deepcopy
        redis_settings = deepcopy(test_settings)
        redis_settings.cache.enabled = True
        redis_settings.limiter.enabled = True
        return redis_settings
    
    return test_settings


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
    - Creates a separate schema for test isolation (test_windx)
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
        
        Schema isolation ensures tests don't affect development data.
    """
    test_settings = get_test_settings()
    schema = test_settings.database.schema_
    
    # Create engine with schema in connect_args
    engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=False,
        poolclass=NullPool,  # Disable pooling for test isolation
        connect_args={
            "server_settings": {
                "search_path": f"{schema}, public"
            }
        }
    )

    # Create schema and tables with LTREE extension
    async with engine.begin() as conn:
        # Create schema if it doesn't exist
        await conn.execute(text(f"CREATE SCHEMA IF NOT EXISTS {schema}"))
        
        # Set search path for this connection (include public for extensions)
        await conn.execute(text(f"SET search_path TO {schema}, public"))
        
        # Enable LTREE extension in public schema (accessible from all schemas)
        # This is required by the Windx schema for efficient tree queries
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS ltree SCHEMA public"))
        
        # Drop all tables in test schema if they exist
        await conn.execute(text(f"""
            DO $$ 
            DECLARE
                r RECORD;
            BEGIN
                FOR r IN (SELECT tablename FROM pg_tables WHERE schemaname = '{schema}') 
                LOOP
                    EXECUTE 'DROP TABLE IF EXISTS {schema}.' || quote_ident(r.tablename) || ' CASCADE';
                END LOOP;
            END $$;
        """))
        
        # Create all tables in test schema
        # The simplest approach: set schema on metadata, create tables, then reset
        def create_tables_in_schema(connection):
            # Temporarily bind all tables to the test schema
            for table_name, table in Base.metadata.tables.items():
                table.schema = schema
            
            # Create all tables
            Base.metadata.create_all(bind=connection)
            
            # Reset schema to None for other code
            for table_name, table in Base.metadata.tables.items():
                table.schema = None
        
        await conn.run_sync(create_tables_in_schema)
        
        # Verify tables were created
        result = await conn.execute(text(f"""
            SELECT COUNT(*) FROM information_schema.tables 
            WHERE table_schema = '{schema}'
        """))
        created_count = result.scalar()
        
        # Also check public schema
        result = await conn.execute(text("""
            SELECT COUNT(*) FROM information_schema.tables 
            WHERE table_schema = 'public'
        """))
        public_count = result.scalar()
        
        print(f"[DEBUG] Tables in {schema} schema: {created_count}")
        print(f"[DEBUG] Tables in public schema: {public_count}")
        
        if created_count == 0:
            # Debug: show where tables actually are
            result = await conn.execute(text("""
                SELECT DISTINCT table_schema 
                FROM information_schema.tables 
                WHERE table_schema NOT IN ('pg_catalog', 'information_schema')
            """))
            schemas = [row[0] for row in result]
            print(f"[DEBUG] Schemas with tables: {schemas}")

    yield engine

    # Cleanup: Drop all tables in test schema (not the schema itself for reuse)
    async with engine.begin() as conn:
        await conn.execute(text(f"SET search_path TO {schema}, public"))
        # Drop all tables in test schema
        await conn.execute(text(f"""
            DO $$ 
            DECLARE
                r RECORD;
            BEGIN
                FOR r IN (SELECT tablename FROM pg_tables WHERE schemaname = '{schema}') 
                LOOP
                    EXECUTE 'DROP TABLE IF EXISTS {schema}.' || quote_ident(r.tablename) || ' CASCADE';
                END LOOP;
            END $$;
        """))

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
def test_user_data(test_settings: TestSettings) -> dict[str, Any]:
    """Get test user data from environment.

    Args:
        test_settings: Test settings with credentials

    Returns:
        dict[str, Any]: Test user data
    """
    return {
        "email": test_settings.test_user_email,
        "username": test_settings.test_user_username,
        "password": test_settings.test_user_password,
        "full_name": "Test User",
    }


@pytest.fixture
def test_admin_data(test_settings: TestSettings) -> dict[str, Any]:
    """Get test admin data from environment.

    Args:
        test_settings: Test settings with credentials

    Returns:
        dict[str, Any]: Test admin data
    """
    return {
        "email": test_settings.test_admin_email,
        "username": test_settings.test_admin_username,
        "password": test_settings.test_admin_password,
        "full_name": "Test Admin",
    }


@pytest.fixture
def test_superuser_data(test_admin_data: dict[str, Any]) -> dict[str, Any]:
    """Get test superuser data from environment.

    Args:
        test_admin_data: Admin credentials from environment

    Returns:
        dict[str, Any]: Test superuser data
    """
    return {
        **test_admin_data,
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
    from app.core.security import get_password_hash
    from app.models.user import User
    from app.repositories.user import UserRepository

    user_repo = UserRepository(db_session)
    
    # Check if user already exists (in case of committed transaction from previous test)
    existing_user = await user_repo.get_by_email(test_user_data["email"])
    if existing_user:
        # Return existing user
        return existing_user
    
    # Create user directly without service (to avoid commit)
    hashed_password = get_password_hash(test_user_data["password"])
    user = User(
        email=test_user_data["email"],
        username=test_user_data["username"],
        full_name=test_user_data.get("full_name"),
        hashed_password=hashed_password,
        is_superuser=False,
        is_active=True,
    )
    
    db_session.add(user)
    await db_session.flush()  # Flush to get ID but don't commit
    await db_session.refresh(user)

    return user


@pytest.fixture
def test_passwords(test_settings: TestSettings) -> dict[str, str]:
    """Get test passwords from settings.

    This fixture provides a single source of truth for test passwords,
    preventing hardcoded passwords in test files.

    Args:
        test_settings: Test settings with credentials

    Returns:
        dict[str, str]: Dictionary with password keys
    """
    return {
        "admin": test_settings.test_admin_password,
        "user": test_settings.test_user_password,
    }


@pytest_asyncio.fixture
async def test_superuser(db_session: AsyncSession, test_superuser_data: dict[str, Any]):
    """Create test superuser in database.

    Args:
        db_session (AsyncSession): Database session
        test_superuser_data (dict): Test superuser data

    Returns:
        User: Created test superuser
    """
    from app.core.security import get_password_hash
    from app.models.user import User
    from app.repositories.user import UserRepository

    user_repo = UserRepository(db_session)
    
    # Check if user already exists (in case of committed transaction from previous test)
    existing_user = await user_repo.get_by_email(test_superuser_data["email"])
    if existing_user:
        # Return existing user
        return existing_user
    
    # Create user directly without service (to avoid commit)
    hashed_password = get_password_hash(test_superuser_data["password"])
    user = User(
        email=test_superuser_data["email"],
        username=test_superuser_data["username"],
        full_name=test_superuser_data.get("full_name"),
        hashed_password=hashed_password,
        is_superuser=True,
        is_active=True,
    )
    
    db_session.add(user)
    await db_session.flush()  # Flush to get ID but don't commit
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
