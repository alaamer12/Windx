"""Create a superuser account.

This script creates a superuser account for administrative access.
Run with: python scripts/create_superuser.py
"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path to import app modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.security import get_password_hash
from app.database.connection import get_engine
from app.models.user import User
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker


async def create_superuser():
    """Create a superuser account interactively."""
    print("=== Create Superuser ===\n")
    
    # Get user input
    email = input("Email: ").strip()
    username = input("Username: ").strip()
    full_name = input("Full name: ").strip()
    password = input("Password: ").strip()
    
    if not all([email, username, password]):
        print("\n❌ Error: Email, username, and password are required!")
        return
    
    # Create database session
    engine = get_engine()
    session_maker = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with session_maker() as session:
        try:
            # Check if user already exists
            result = await session.execute(
                select(User).where(
                    (User.email == email) | (User.username == username)
                )
            )
            existing_user = result.scalar_one_or_none()
            
            if existing_user:
                print(f"\n❌ Error: User with email '{email}' or username '{username}' already exists!")
                return
            
            # Create superuser
            hashed_password = get_password_hash(password)
            superuser = User(
                email=email,
                username=username,
                full_name=full_name or username,
                hashed_password=hashed_password,
                is_active=True,
                is_superuser=True,
            )
            
            session.add(superuser)
            await session.commit()
            await session.refresh(superuser)
            
            print(f"\n✅ Superuser created successfully!")
            print(f"   ID: {superuser.id}")
            print(f"   Email: {superuser.email}")
            print(f"   Username: {superuser.username}")
            print(f"   Is Superuser: {superuser.is_superuser}")
            
        except Exception as e:
            await session.rollback()
            print(f"\n❌ Error creating superuser: {e}")
        finally:
            await session.close()
    
    await engine.dispose()


async def promote_to_superuser():
    """Promote an existing user to superuser."""
    print("=== Promote User to Superuser ===\n")
    
    # Get user input
    identifier = input("Email or Username: ").strip()
    
    if not identifier:
        print("\n❌ Error: Email or username is required!")
        return
    
    # Create database session
    engine = get_engine()
    session_maker = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with session_maker() as session:
        try:
            # Find user
            result = await session.execute(
                select(User).where(
                    (User.email == identifier) | (User.username == identifier)
                )
            )
            user = result.scalar_one_or_none()
            
            if not user:
                print(f"\n❌ Error: User '{identifier}' not found!")
                return
            
            if user.is_superuser:
                print(f"\n⚠️  User '{user.username}' is already a superuser!")
                return
            
            # Promote to superuser
            user.is_superuser = True
            await session.commit()
            await session.refresh(user)
            
            print(f"\n✅ User promoted to superuser successfully!")
            print(f"   ID: {user.id}")
            print(f"   Email: {user.email}")
            print(f"   Username: {user.username}")
            print(f"   Is Superuser: {user.is_superuser}")
            
        except Exception as e:
            await session.rollback()
            print(f"\n❌ Error promoting user: {e}")
        finally:
            await session.close()
    
    await engine.dispose()


async def main():
    """Main function."""
    print("\nChoose an option:")
    print("1. Create new superuser")
    print("2. Promote existing user to superuser")
    
    choice = input("\nEnter choice (1 or 2): ").strip()
    
    if choice == "1":
        await create_superuser()
    elif choice == "2":
        await promote_to_superuser()
    else:
        print("\n❌ Invalid choice!")


if __name__ == "__main__":
    asyncio.run(main())
