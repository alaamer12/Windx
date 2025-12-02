"""Reset test database by dropping and recreating all tables and extensions.

This script:
1. Connects to the test database
2. Drops all tables in the public schema
3. Drops and recreates the ltree extension
4. Recreates all tables from SQLAlchemy models

Usage:
    python scripts/reset_test_db.py
"""

import asyncio
import sys
from pathlib import Path

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.pool import NullPool

from app.database import Base
from tests.conftest import TEST_DATABASE_URL

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))



async def reset_database():
    """Reset the test database to a clean state."""
    print("Connecting to test database...")
    print(f"URL: {TEST_DATABASE_URL.split('@')[1]}")  # Hide password

    engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=True,
        poolclass=NullPool,
    )

    try:
        async with engine.begin() as conn:
            print("\n1. Dropping all tables in public schema...")
            # Drop all tables in public schema
            await conn.execute(
                text(
                    """
                    DO $$ DECLARE
                        r RECORD;
                    BEGIN
                        FOR r IN (SELECT tablename FROM pg_tables WHERE schemaname = 'public') LOOP
                            EXECUTE 'DROP TABLE IF EXISTS ' || quote_ident(r.tablename) || ' CASCADE';
                        END LOOP;
                    END $$;
                    """
                )
            )
            print("✓ All tables dropped")

            print("\n2. Dropping and recreating ltree extension...")
            # Drop and recreate ltree extension to fix any corruption
            await conn.execute(text("DROP EXTENSION IF EXISTS ltree CASCADE"))
            await conn.execute(text("CREATE EXTENSION ltree"))
            print("✓ ltree extension recreated")

            print("\n3. Creating all tables from SQLAlchemy models...")
            # Create all tables
            await conn.run_sync(Base.metadata.create_all)
            print("✓ All tables created")

            print("\n4. Verifying tables...")
            # Verify tables exist
            result = await conn.execute(
                text(
                    "SELECT tablename FROM pg_tables WHERE schemaname = 'public' ORDER BY tablename"
                )
            )
            tables = [row[0] for row in result]
            print(f"✓ Found {len(tables)} tables:")
            for table in tables:
                print(f"  - {table}")

        print("\n✅ Database reset complete!")

    except Exception as e:
        print(f"\n❌ Error resetting database: {e}")
        raise
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(reset_database())
