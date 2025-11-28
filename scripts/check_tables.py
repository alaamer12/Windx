"""Check what tables exist in the database."""
import asyncio
from sqlalchemy import text
from app.database.connection import get_engine


async def check_tables():
    """Check existing tables in the database."""
    engine = get_engine()
    
    async with engine.begin() as conn:
        # Get all tables
        result = await conn.execute(
            text("SELECT tablename FROM pg_tables WHERE schemaname='public' ORDER BY tablename")
        )
        tables = [row[0] for row in result]
        
        print(f"Found {len(tables)} tables in public schema:")
        for table in tables:
            print(f"  - {table}")
        
        # Check if sessions table exists
        if 'sessions' in tables:
            print("\n✓ sessions table exists")
        else:
            print("\n✗ sessions table DOES NOT exist")
    
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(check_tables())
