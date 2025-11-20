"""Check if PostgreSQL is running and accessible."""

import asyncio
import sys

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine


async def check_postgres():
    """Check PostgreSQL connection."""
    # Try to connect to PostgreSQL
    try:
        engine = create_async_engine(
            "postgresql+asyncpg://postgres:postgres@localhost:5432/postgres",
            echo=False,
        )
        
        async with engine.begin() as conn:
            result = await conn.execute(text("SELECT version()"))
            version = result.scalar()
            print("✓ PostgreSQL is running!")
            print(f"  Version: {version}")
            
        await engine.dispose()
        return True
        
    except Exception as e:
        print("✗ PostgreSQL is NOT running or not accessible!")
        print(f"  Error: {e}")
        print("\nTo fix this:")
        print("1. Install PostgreSQL if not installed")
        print("2. Start PostgreSQL service")
        print("3. Or update .env to use a different database")
        return False


if __name__ == "__main__":
    result = asyncio.run(check_postgres())
    sys.exit(0 if result else 1)
