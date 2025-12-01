"""Create database tables script."""

import asyncio

from sqlalchemy import text

from app.database.base import Base
from app.database.connection import get_engine

# Import all models to register them with Base.metadata


async def create_tables():
    """Create all database tables."""
    engine = get_engine()
    print("Creating LTREE extension...")
    async with engine.begin() as conn:
        # Create LTREE extension
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS ltree"))
        print("✓ LTREE extension created")

        # Create all tables
        print("Creating tables...")
        await conn.run_sync(Base.metadata.create_all)
        print("✓ All tables created successfully")


if __name__ == "__main__":
    asyncio.run(create_tables())
