"""Test Supabase database connection.

Run this test from the project root with:
    .venv/Scripts/python tests/unit/test_supabase.py
"""

import asyncio
import os
import sys
from pathlib import Path

# Get project root and change to it
project_root = Path(__file__).parent.parent.parent
os.chdir(project_root)
sys.path.insert(0, str(project_root))

from sqlalchemy import text

from app.core.config import get_settings
from app.database.connection import get_engine


async def test_connection():
    """Test Supabase connection."""
    settings = get_settings()

    print(f"Testing connection to: {settings.database.provider}")
    print(f"Host: {settings.database.host}")
    print(f"Database: {settings.database.name}")
    print(f"User: {settings.database.user}")
    print()

    try:
        engine = get_engine()

        async with engine.begin() as conn:
            # Test basic query
            result = await conn.execute(text("SELECT version()"))
            version = result.scalar()
            print("✓ Connection successful!")
            print(f"  PostgreSQL version: {version[:50]}...")

            # Test another query
            result = await conn.execute(text("SELECT current_database()"))
            db_name = result.scalar()
            print(f"  Current database: {db_name}")

        await engine.dispose()
        return True

    except Exception as e:
        print("✗ Connection failed!")
        print(f"  Error: {e}")
        return False


if __name__ == "__main__":
    success = asyncio.run(test_connection())
    exit(0 if success else 1)
