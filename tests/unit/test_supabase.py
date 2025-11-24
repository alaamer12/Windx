"""Test Supabase database connection.

NOTE: This is a manual integration test for Supabase connection.
It is skipped in automated test runs to avoid external dependencies.
Run manually with: python tests/unit/test_supabase.py
"""

import asyncio
import os
import sys
from pathlib import Path

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from app.core.config import get_settings
from app.database.connection import get_engine

# Get project root and change to it
project_root = Path(__file__).parent.parent.parent
os.chdir(project_root)
sys.path.insert(0, str(project_root))



@pytest.mark.skip(reason="Manual integration test - requires live Supabase connection")
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

@pytest.mark.skip(reason="Manual integration test - requires live Supabase connection")
async def test_connection2():
    """Test different Supabase connection formats."""

    # Format 1: Standard PostgreSQL connection
    urls = [
        "postgresql+asyncpg://postgres:DhsRZdcOMMxhrzwY@db.vglmnngcvcrdzvnaopde.supabase.co:5432/postgres",
        "postgresql+asyncpg://postgres:DhsRZdcOMMxhrzwY@db.vglmnngcvcrdzvnaopde.supabase.co:6543/postgres",  # Supabase uses port 6543 for pooler
    ]

    for i, url in enumerate(urls, 1):
        print(f"\nTest {i}: Trying connection...")
        print(f"URL: {url.replace('DhsRZdcOMMxhrzwY', '***')}")

        try:
            engine = create_async_engine(url, echo=False, pool_pre_ping=True)

            async with engine.begin() as conn:
                result = await conn.execute(text("SELECT version()"))
                version = result.scalar()
                print("✓ SUCCESS!")
                print(f"  Version: {version[:80]}...")

            await engine.dispose()
            return True

        except Exception as e:
            print(f"✗ Failed: {e}")

    return False



if __name__ == "__main__":
    success = asyncio.run(test_connection())
    success2 = asyncio.run(test_connection2())
    exit(0 if success and success2 else 1)
