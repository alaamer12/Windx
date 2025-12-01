"""Reset superuser password.

This script resets the password for the admin superuser.
"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path to import app modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.security import get_password_hash
from app.database.connection import get_engine
from app.models.user import User


async def reset_password():
    """Reset admin password."""
    print("=== Reset Admin Password ===\n")

    # Create database session
    engine = get_engine()
    session_maker = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with session_maker() as session:
        try:
            # Find admin user
            result = await session.execute(select(User).where(User.username == "admin"))
            user = result.scalar_one_or_none()

            if not user:
                print("❌ Error: Admin user not found!")
                return

            # Reset password
            new_password = "Admin123!"
            user.hashed_password = get_password_hash(new_password)
            await session.commit()

            print("✅ Password reset successfully!")
            print(f"   Username: {user.username}")
            print(f"   Email: {user.email}")
            print(f"   New Password: {new_password}")

        except Exception as e:
            await session.rollback()
            print(f"❌ Error resetting password: {e}")
        finally:
            await session.close()

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(reset_password())
