"""Test Supabase connection with direct URL."""

import asyncio

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine


async def test_connection():
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
    exit(0 if success else 1)
