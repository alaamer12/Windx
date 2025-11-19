"""Database connection and session management module.

This module provides database connectivity using SQLAlchemy async engine
with PostgreSQL/Supabase backend. Implements dependency injection pattern
for FastAPI integration.

Public Classes:
    Base: Declarative base for all ORM models

Public Functions:
    get_engine: Create and return database engine
    get_session_maker: Create and return session maker
    get_db: FastAPI dependency for database sessions

Features:
    - Async SQLAlchemy engine with asyncpg driver
    - Session management with proper cleanup
    - FastAPI dependency injection support
    - Connection pooling and configuration
"""

from collections.abc import AsyncGenerator
from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.core.config import Settings, get_settings

__all__ = ["Base", "get_engine", "get_session_maker", "get_db"]


class Base(DeclarativeBase):
    """Base class for all database models."""

    pass


def get_engine(settings: Annotated[Settings, Depends(get_settings)]):
    """Create and return database engine.

    Args:
        settings (Settings): Application settings

    Returns:
        AsyncEngine: SQLAlchemy async engine
    """
    return create_async_engine(
        str(settings.database.url),
        echo=settings.debug,
        future=True,
    )


def get_session_maker(
    settings: Annotated[Settings, Depends(get_settings)],
) -> async_sessionmaker[AsyncSession]:
    """Create and return session maker.

    Args:
        settings (Settings): Application settings

    Returns:
        async_sessionmaker[AsyncSession]: Async session maker
    """
    engine = get_engine(settings)
    return async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autocommit=False,
        autoflush=False,
    )


async def get_db(
    settings: Annotated[Settings, Depends(get_settings)],
) -> AsyncGenerator[AsyncSession, None]:
    """Get database session dependency.

    Args:
        settings (Settings): Application settings

    Yields:
        AsyncSession: Database session
    """
    session_maker = get_session_maker(settings)
    async with session_maker() as session:
        try:
            yield session
        finally:
            await session.close()
