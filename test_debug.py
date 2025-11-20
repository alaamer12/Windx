"""Debug test to check if tables are created."""
import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import NullPool
from app.database.base import Base
from app.models.user import User
from app.models.session import Session as SessionModel

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


async def main():
    print("Creating engine...")
    engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=True,
        poolclass=NullPool,
    )

    print("\nCreating tables...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    print("\nTables created. Metadata tables:", list(Base.metadata.tables.keys()))

    print("\nCreating session...")
    session_maker = async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with session_maker() as session:
        print("\nQuerying users table...")
        from sqlalchemy import select
        result = await session.execute(select(User))
        users = result.scalars().all()
        print(f"Users found: {len(users)}")

    await engine.dispose()
    print("\nSuccess!")


if __name__ == "__main__":
    asyncio.run(main())
