"""Initialize database with initial migration.

This script creates the initial database migration and applies it.
"""

import asyncio
import sys

from app.core.database import Base, init_db
from app.models import *  # noqa: F401, F403


async def create_tables():
    """Create all database tables."""
    print("🔧 Initializing database...")

    try:
        await init_db()
        print("✓ Database initialized successfully")
        print("\n📝 Next steps:")
        print("1. Create initial migration:")
        print("   alembic revision --autogenerate -m 'Initial migration'")
        print("2. Apply migration:")
        print("   alembic upgrade head")
    except Exception as e:
        print(f"❌ Error initializing database: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(create_tables())
