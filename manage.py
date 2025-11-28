"""Management CLI for the application.

Usage:
    python manage.py createsuperuser
    python manage.py promote <username>
"""

import asyncio
import sys

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.security import get_password_hash
from app.database.connection import get_engine
from app.models.user import User


async def create_superuser():
    """Create a new superuser account."""
    print("=== Create Superuser ===\n")

    email = input("Email: ").strip()
    username = input("Username: ").strip()
    full_name = input("Full name (optional): ").strip()
    password = input("Password: ").strip()

    if not all([email, username, password]):
        print("\n❌ Error: Email, username, and password are required!")
        sys.exit(1)

    engine = get_engine()
    session_maker = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with session_maker() as session:
        try:
            # Check if user exists
            result = await session.execute(
                select(User).where((User.email == email) | (User.username == username))
            )
            if result.scalar_one_or_none():
                print("\n❌ Error: User already exists!")
                sys.exit(1)

            # Create superuser
            superuser = User(
                email=email,
                username=username,
                full_name=full_name or username,
                hashed_password=get_password_hash(password),
                is_active=True,
                is_superuser=True,
            )

            session.add(superuser)
            await session.commit()
            await session.refresh(superuser)

            print("\n✅ Superuser created!")
            print(f"   Email: {superuser.email}")
            print(f"   Username: {superuser.username}")

        except Exception as e:
            await session.rollback()
            print(f"\n❌ Error: {e}")
            sys.exit(1)
        finally:
            await session.close()

    await engine.dispose()


async def promote_user(username: str):
    """Promote an existing user to superuser."""
    engine = get_engine()

    async with engine.begin() as conn:
        # First check if user exists and their current status
        check_result = await conn.execute(
            text("SELECT id, email, username, is_superuser FROM users WHERE username = :username"),
            {"username": username}
        )
        existing_user = check_result.fetchone()

        if not existing_user:
            print(f"❌ User '{username}' not found!")
            sys.exit(1)

        if existing_user.is_superuser:
            print(f"⚠️  User '{username}' is already a superuser!")
            print(f"   ID: {existing_user.id}")
            print(f"   Email: {existing_user.email}")
            return

        # Promote to superuser
        result = await conn.execute(
            text(
                "UPDATE users SET is_superuser = true "
                "WHERE username = :username "
                "RETURNING id, email, username, is_superuser"
            ),
            {"username": username}
        )
        user = result.fetchone()

        print(f"✅ User '{username}' promoted to superuser!")
        print(f"   ID: {user.id}")
        print(f"   Email: {user.email}")

    await engine.dispose()


def print_help():
    """Print help message."""
    print("""
Management CLI for the application

Commands:
    createsuperuser          Create a new superuser account
    promote <username>       Promote an existing user to superuser
    
Examples:
    python manage.py createsuperuser
    python manage.py promote johwqen_doe
    """)


def main():
    """Main CLI entry point."""
    if len(sys.argv) < 2:
        print_help()
        sys.exit(1)

    command = sys.argv[1]

    if command == "createsuperuser":
        asyncio.run(create_superuser())
    elif command == "promote":
        if len(sys.argv) < 3:
            print("❌ Error: Username required!")
            print("Usage: python manage.py promote <username>")
            sys.exit(1)
        username = sys.argv[2]
        asyncio.run(promote_user(username))
    else:
        print(f"❌ Unknown command: {command}")
        print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
