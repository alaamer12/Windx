"""Database utilities and helper functions.

This module provides utility functions for database operations including
query helpers, transaction management, and common database patterns.

Public Functions:
    execute_raw_query: Execute raw SQL query
    check_connection: Check database connection health
    get_table_names: Get all table names in database

Features:
    - Raw SQL execution
    - Connection health checks
    - Database introspection
    - Transaction helpers
"""

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.connection import get_engine

__all__ = [
    "execute_raw_query",
    "check_connection",
    "get_table_names",
]


async def execute_raw_query(
    db: AsyncSession,
    query: str,
    params: dict | None = None,
) -> list[dict]:
    """Execute raw SQL query and return results.

    Args:
        db (AsyncSession): Database session
        query (str): SQL query string
        params (dict | None): Query parameters

    Returns:
        list[dict]: Query results as list of dictionaries

    Example:
        ```python
        results = await execute_raw_query(
            db,
            "SELECT * FROM users WHERE email = :email",
            {"email": "user@example.com"}
        )
        ```
    """
    result = await db.execute(text(query), params or {})
    return [dict(row._mapping) for row in result.fetchall()]


async def check_connection() -> bool:
    """Check database connection health.

    Returns:
        bool: True if connection is healthy, False otherwise

    Example:
        ```python
        if await check_connection():
            print("Database is healthy")
        ```
    """
    try:
        engine = get_engine()
        async with engine.begin() as conn:
            await conn.execute(text("SELECT 1"))
        return True
    except Exception:
        return False


async def get_table_names() -> list[str]:
    """Get all table names in the database.

    Returns:
        list[str]: List of table names

    Example:
        ```python
        tables = await get_table_names()
        print(f"Tables: {tables}")
        ```
    """
    engine = get_engine()
    async with engine.begin() as conn:
        result = await conn.execute(
            text(
                """
                SELECT tablename 
                FROM pg_tables 
                WHERE schemaname = 'public'
                ORDER BY tablename
                """
            )
        )
        return [row[0] for row in result.fetchall()]
