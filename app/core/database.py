"""Database connection and session management module.

This module provides database connectivity using SQLAlchemy async engine
with PostgreSQL/Supabase backend. Implements dependency injection pattern
for FastAPI integration with support for easy database provider switching.

Public Classes:
    Base: Declarative base for all ORM models

Public Functions:
    get_engine: Create and return cached database engine
    get_session_maker: Create and return cached session maker
    get_db: FastAPI dependency for database sessions
    init_db: Initialize database connection on startup
    close_db: Close database connections on shutdown

Features:
    - Async SQLAlchemy engine with asyncpg driver
    - Session management with proper cleanup
    - FastAPI dependency injection support
    - Connection pooling optimized per provider
    - Automatic commit/rollback handling
    - Supabase and PostgreSQL support
"""

from collections.abc import AsyncGenerator
from functools import lru_cache

from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from app.core.config import Settings, get_settings

__all__ = ["Base", "get_engine", "get_session_maker", "get_db", "init_db", "close_db"]


class Base(DeclarativeBase):
    """Base class for all database models.
    
    All SQLAlchemy ORM models should inherit from this class.
    """

    pass


@lru_cache
def get_engine(settings: Settings | None = None) -> AsyncEngine:
    """Create and return cached database engine.

    This function creates a single engine instance that is reused across
    the application. The engine is configured based on the database provider
    (Supabase or PostgreSQL) with appropriate connection pooling settings.

    Args:
        settings (Settings | None): Application settings. If None, fetches from get_settings()

    Returns:
        AsyncEngine: SQLAlchemy async engine (cached singleton)
    """
    if settings is None:
        settings = get_settings()

    engine_kwargs = {
        "url": str(settings.database.url),
        "echo": settings.database.echo or settings.debug,
        "future": True,
        "pool_pre_ping": settings.database.pool_pre_ping,
        "pool_size": settings.database.pool_size,
        "max_overflow": settings.database.max_overflow,
    }

    # Supabase-specific optimizations
    if settings.database.is_supabase:
        # Supabase has connection limits, so we use smaller pool
        engine_kwargs["pool_size"] = min(settings.database.pool_size, 5)
        engine_kwargs["max_overflow"] = min(settings.database.max_overflow, 5)
        # Supabase connections can be flaky, enable pre-ping
        engine_kwargs["pool_pre_ping"] = True

    return create_async_engine(**engine_kwargs)


@lru_cache
def get_session_maker(settings: Settings | None = None) -> async_sessionmaker[AsyncSession]:
    """Create and return cached session maker.

    Args:
        settings (Settings | None): Application settings. If None, fetches from get_settings()

    Returns:
        async_sessionmaker[AsyncSession]: Async session maker factory (cached singleton)
    """
    if settings is None:
        settings = get_settings()

    engine = get_engine(settings)
    return async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autocommit=False,
        autoflush=False,
    )


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Get database session dependency.

    This is a FastAPI dependency that provides a database session
    for each request. The session is automatically closed after use.
    Commits on success, rolls back on exception.

    Yields:
        AsyncSession: Database session with automatic cleanup
    """
    session_maker = get_session_maker()
    async with session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db() -> None:
    """Initialize database connection.

    This function should be called on application startup to ensure
    the database connection is established and ready.

    Example:
        @app.on_event("startup")
        async def startup():
            await init_db()
    """
    settings = get_settings()
    engine = get_engine(settings)

    # Test connection
    async with engine.begin() as conn:
        # Simple query to verify connection
        await conn.execute(text("SELECT 1"))

    print(f"✓ Database connected: {settings.database.provider} @ {settings.database.host}")


async def close_db() -> None:
    """Close database connections.

    This function should be called on application shutdown to properly
    close all database connections and clean up resources.

    Example:
        @app.on_event("shutdown")
        async def shutdown():
            await close_db()
    """
    settings = get_settings()
    engine = get_engine(settings)
    await engine.dispose()
    print("✓ Database connections closed")
