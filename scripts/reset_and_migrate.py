"""Reset Alembic version and run migrations fresh."""
import asyncio
from sqlalchemy import text
from app.database.connection import get_engine


async def reset_and_migrate():
    """Reset Alembic version table and prepare for fresh migrations."""
    engine = get_engine()
    
    async with engine.begin() as conn:
        # Delete all rows from alembic_version
        print("Resetting alembic_version table...")
        await conn.execute(text("DELETE FROM alembic_version"))
        print("✓ Alembic version table reset")
    
    await engine.dispose()
    print("\nNow run: .venv\\Scripts\\python -m alembic upgrade head")


if __name__ == "__main__":
    asyncio.run(reset_and_migrate())
