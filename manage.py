"""Management CLI for the application.

Usage:
    python manage.py <command> [options]

Commands:
    createsuperuser          Create a new superuser account
    promote <username>       Promote an existing user to superuser
    create_tables            Create all database tables with LTREE extension
    drop_tables              Drop all database tables (requires confirmation)
    reset_db                 Drop and recreate all tables (requires confirmation)
    reset_password <username> Reset password for a user
    check_env                Validate environment configuration
    seed_data                Create sample data for development
    clean_db                 Clean orphaned types and recreate database
    verify_setup             Verify complete setup is working
    stamp_alembic            Stamp Alembic to current version
    create_sample_mfg        Create sample manufacturing data with hierarchy
    delete_sample_mfg        Delete sample manufacturing data

Examples:
    python manage.py createsuperuser
    python manage.py promote john_doe
    python manage.py create_tables
    python manage.py drop_tables --force
    python manage.py reset_db
    python manage.py reset_password admin
    python manage.py check_env
    python manage.py seed_data
    python manage.py clean_db
    python manage.py verify_setup
    python manage.py stamp_alembic
    python manage.py create_sample_mfg
    python manage.py delete_sample_mfg --force
"""

import argparse
import asyncio
import sys
from pathlib import Path
from typing import Callable

# Fix Windows CMD encoding issues with emojis
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.config import get_settings
from app.core.security import get_password_hash
from app.database.base import Base
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
            # noinspection PyTypeChecker
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
            {"username": username},
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
            {"username": username},
        )
        user = result.fetchone()

        print(f"✅ User '{username}' promoted to superuser!")
        print(f"   ID: {user.id}")
        print(f"   Email: {user.email}")

    await engine.dispose()


async def create_tables(args: argparse.Namespace):
    """Create all database tables with LTREE extension."""
    print("=== Creating Database Tables ===\n")
    
    engine = get_engine()
    
    try:
        async with engine.begin() as conn:
            # Create LTREE extension
            print("Creating LTREE extension...")
            await conn.execute(text("CREATE EXTENSION IF NOT EXISTS ltree"))
            print("✅ LTREE extension created")
            
            # Create all tables
            print("Creating tables...")
            await conn.run_sync(Base.metadata.create_all)
            print("✅ All tables created successfully")
    except Exception as e:
        print(f"❌ Error creating tables: {e}")
        sys.exit(1)
    finally:
        await engine.dispose()


async def drop_tables(args: argparse.Namespace):
    """Drop all database tables."""
    print("=== Dropping Database Tables ===\n")
    
    # Confirmation prompt unless --force is specified
    if not args.force:
        print("⚠️  WARNING: This will delete ALL data in the database!")
        response = input("Are you sure you want to continue? (yes/no): ").strip().lower()
        if response != "yes":
            print("Operation cancelled.")
            return
    
    engine = get_engine()
    
    try:
        async with engine.begin() as conn:
            print("Dropping all tables...")
            await conn.run_sync(Base.metadata.drop_all)
            print("✅ All tables dropped successfully")
    except Exception as e:
        print(f"❌ Error dropping tables: {e}")
        sys.exit(1)
    finally:
        await engine.dispose()


async def reset_db(args: argparse.Namespace):
    """Drop and recreate all database tables."""
    print("=== Resetting Database ===\n")
    
    # Confirmation prompt unless --force is specified
    if not args.force:
        print("⚠️  WARNING: This will delete ALL data and recreate the database!")
        response = input("Are you sure you want to continue? (yes/no): ").strip().lower()
        if response != "yes":
            print("Operation cancelled.")
            return
    
    engine = get_engine()
    
    try:
        async with engine.begin() as conn:
            # Drop all tables
            print("Dropping all tables...")
            await conn.run_sync(Base.metadata.drop_all)
            print("✅ All tables dropped")
            
            # Create LTREE extension
            print("Creating LTREE extension...")
            await conn.execute(text("CREATE EXTENSION IF NOT EXISTS ltree"))
            print("✅ LTREE extension created")
            
            # Create all tables
            print("Creating tables...")
            await conn.run_sync(Base.metadata.create_all)
            print("✅ All tables created successfully")
            
        print("\n✅ Database reset complete!")
    except Exception as e:
        print(f"❌ Error resetting database: {e}")
        sys.exit(1)
    finally:
        await engine.dispose()


async def reset_password_command(args: argparse.Namespace):
    """Reset password for a user."""
    print("=== Reset User Password ===\n")
    
    username = args.username
    
    # Prompt for new password
    new_password = input("New password: ").strip()
    if not new_password:
        print("❌ Error: Password cannot be empty!")
        sys.exit(1)
    
    confirm_password = input("Confirm password: ").strip()
    if new_password != confirm_password:
        print("❌ Error: Passwords do not match!")
        sys.exit(1)
    
    engine = get_engine()
    session_maker = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with session_maker() as session:
        try:
            # Find user
            result = await session.execute(select(User).where(User.username == username))
            user = result.scalar_one_or_none()
            
            if not user:
                print(f"❌ Error: User '{username}' not found!")
                sys.exit(1)
            
            # Update password
            user.hashed_password = get_password_hash(new_password)
            await session.commit()
            
            print(f"✅ Password reset successfully for user '{username}'!")
            print(f"   Email: {user.email}")
        except Exception as e:
            await session.rollback()
            print(f"❌ Error resetting password: {e}")
            sys.exit(1)
        finally:
            await session.close()
    
    await engine.dispose()


async def check_env_command(args: argparse.Namespace):
    """Validate environment configuration and database connectivity."""
    print("=== Environment Configuration Check ===\n")
    
    settings = get_settings()
    all_ok = True
    
    # Check required environment variables
    print("Checking environment variables...")
    
    required_vars = {
        "DATABASE_URL": settings.database.url,
        "SECRET_KEY": settings.security.secret_key.get_secret_value() if settings.security.secret_key else None,
        "ALGORITHM": settings.security.algorithm,
    }
    
    for var_name, var_value in required_vars.items():
        if var_value:
            print(f"✅ {var_name}: Set")
        else:
            print(f"❌ {var_name}: Missing")
            all_ok = False
    
    # Check database connectivity
    print("\nChecking database connectivity...")
    try:
        engine = get_engine()
        async with engine.begin() as conn:
            await conn.execute(text("SELECT 1"))
        print(f"✅ Database connection successful")
        print(f"   Provider: {settings.database.provider}")
        print(f"   Host: {settings.database.host}")
        print(f"   Database: {settings.database.name}")
        await engine.dispose()
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        all_ok = False
    
    # Check environment files consistency
    print("\nChecking environment files...")
    project_root = Path(__file__).parent
    
    env_files = {
        ".env.example": project_root / ".env.example",
        ".env.test": project_root / ".env.test",
    }
    
    # Check for production env file
    prod_patterns = [".env.production", ".env.example.production", ".env.prod"]
    prod_file = None
    for pattern in prod_patterns:
        path = project_root / pattern
        if path.exists():
            prod_file = (pattern, path)
            break
    
    if prod_file:
        env_files[prod_file[0]] = prod_file[1]
    
    for name, path in env_files.items():
        if path.exists():
            print(f"✅ {name}: Found")
        else:
            print(f"⚠️  {name}: Not found")
    
    # Final result
    print("\n" + "=" * 50)
    if all_ok:
        print("✅ All checks passed!")
        return 0
    else:
        print("❌ Some checks failed!")
        return 1


async def seed_data_command(args: argparse.Namespace):
    """Create sample data for development."""
    print("=== Seeding Sample Data ===\n")
    
    engine = get_engine()
    session_maker = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with session_maker() as session:
        try:
            # Check if data already exists
            result = await session.execute(select(User).limit(1))
            if result.scalar_one_or_none():
                print("⚠️  Database already contains data.")
                response = input("Do you want to continue? (yes/no): ").strip().lower()
                if response != "yes":
                    print("Operation cancelled.")
                    return
            
            # Create sample users
            print("Creating sample users...")
            
            admin_user = User(
                email="admin@example.com",
                username="admin",
                full_name="Admin User",
                hashed_password=get_password_hash("Admin123!"),
                is_active=True,
                is_superuser=True,
            )
            
            regular_user = User(
                email="user@example.com",
                username="user",
                full_name="Regular User",
                hashed_password=get_password_hash("User123!"),
                is_active=True,
                is_superuser=False,
            )
            
            session.add_all([admin_user, regular_user])
            await session.commit()
            
            print("✅ Sample users created:")
            print(f"   Admin: admin@example.com / Admin123!")
            print(f"   User: user@example.com / User123!")
            
            # TODO: Add more sample data (manufacturing types, templates, etc.)
            # This can be expanded based on project needs
            
            print("\n✅ Sample data seeded successfully!")
        except Exception as e:
            await session.rollback()
            print(f"❌ Error seeding data: {e}")
            sys.exit(1)
        finally:
            await session.close()
    
    await engine.dispose()


def get_python_executable() -> str:
    """Get the correct Python executable path for the platform.
    
    Returns:
        str: Path to Python executable in virtual environment
    """
    if sys.platform == "win32":
        return ".venv\\Scripts\\python"
    else:
        return ".venv/bin/python"


def print_help():
    """Print help message."""
    print(__doc__)


async def clean_db_types_command(args: argparse.Namespace):
    """Clean orphaned PostgreSQL types and recreate database."""
    print("=== Cleaning Database Types ===\n")
    
    engine = get_engine()
    
    try:
        async with engine.begin() as conn:
            print("Step 1: Dropping all tables...")
            await conn.run_sync(Base.metadata.drop_all)
            print("✅ Tables dropped")
            
            print("\nStep 2: Dropping orphaned types...")
            # Get all custom types in public schema
            result = await conn.execute(text("""
                SELECT typname 
                FROM pg_type t
                JOIN pg_namespace n ON t.typnamespace = n.oid
                WHERE n.nspname = 'public' 
                AND t.typtype = 'c'
                AND typname IN (
                    'users', 'sessions', 'customers', 'manufacturing_types',
                    'attribute_nodes', 'configurations', 'configuration_selections',
                    'configuration_templates', 'template_selections',
                    'quotes', 'orders', 'order_items'
                )
            """))
            
            types_to_drop = [row[0] for row in result]
            if types_to_drop:
                print(f"Found {len(types_to_drop)} orphaned types: {types_to_drop}")
                
                for type_name in types_to_drop:
                    try:
                        await conn.execute(text(f"DROP TYPE IF EXISTS {type_name} CASCADE"))
                        print(f"  ✅ Dropped type: {type_name}")
                    except Exception as e:
                        print(f"  ⚠️  Could not drop {type_name}: {e}")
            else:
                print("No orphaned types found")
            
            print("\nStep 3: Creating LTREE extension...")
            await conn.execute(text("CREATE EXTENSION IF NOT EXISTS ltree"))
            print("✅ LTREE extension created")
            
            print("\nStep 4: Creating all tables...")
            await conn.run_sync(Base.metadata.create_all)
            print("✅ All tables created")
            
        print("\n" + "="*50)
        print("✅ Database cleaned and recreated!")
        print("\nNext steps:")
        print("1. Stamp alembic to current version:")
        print("   python manage.py stamp_alembic")
        print("\n2. Seed initial data:")
        print("   python manage.py seed_data")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        await engine.dispose()


async def verify_setup_command(args: argparse.Namespace):
    """Verify complete setup is working."""
    print("="*60)
    print("WINDX APPLICATION SETUP VERIFICATION")
    print("="*60)
    
    engine = get_engine()
    all_ok = True
    
    try:
        async with engine.begin() as conn:
            # 1. Check LTREE extension
            print("\n1. Checking LTREE extension...")
            result = await conn.execute(
                text("SELECT 1 FROM pg_extension WHERE extname = 'ltree'")
            )
            if result.scalar():
                print("   ✅ LTREE extension installed")
            else:
                print("   ❌ LTREE extension missing")
                all_ok = False
            
            # 2. Check all tables exist
            print("\n2. Checking database tables...")
            result = await conn.execute(
                text("SELECT tablename FROM pg_tables WHERE schemaname = 'public' ORDER BY tablename")
            )
            tables = [row[0] for row in result]
            expected_tables = [
                'alembic_version', 'attribute_nodes', 'configuration_selections',
                'configuration_templates', 'configurations', 'customers',
                'manufacturing_types', 'order_items', 'orders', 'quotes',
                'sessions', 'template_selections', 'users'
            ]
            
            missing = set(expected_tables) - set(tables)
            if missing:
                print(f"   ❌ Missing tables: {missing}")
                all_ok = False
            else:
                print(f"   ✅ All {len(expected_tables)} tables exist")
            
            # 3. Check admin user
            print("\n3. Checking admin user...")
            result = await conn.execute(
                text("SELECT username, email, is_superuser, is_active FROM users WHERE username = 'admin'")
            )
            admin = result.fetchone()
            if admin:
                print(f"   ✅ Admin user found")
                print(f"      Username: {admin[0]}")
                print(f"      Email: {admin[1]}")
                print(f"      Superuser: {admin[2]}")
                print(f"      Active: {admin[3]}")
                
                if not admin[2]:
                    print("   ❌ Admin user is not a superuser!")
                    all_ok = False
                if not admin[3]:
                    print("   ❌ Admin user is not active!")
                    all_ok = False
            else:
                print("   ⚠️  Admin user not found (run: python manage.py seed_data)")
            
            # 4. Check Alembic version
            print("\n4. Checking Alembic migrations...")
            result = await conn.execute(
                text("SELECT version_num FROM alembic_version")
            )
            version = result.scalar()
            if version:
                print(f"   ✅ Alembic version: {version}")
            else:
                print("   ⚠️  No Alembic version found (run: python manage.py stamp_alembic)")
            
            # 5. Check user count
            print("\n5. Checking user accounts...")
            result = await conn.execute(text("SELECT COUNT(*) FROM users"))
            user_count = result.scalar()
            print(f"   ✅ Total users: {user_count}")
            
        print("\n" + "="*60)
        if all_ok:
            print("✅ ALL CHECKS PASSED - SETUP COMPLETE!")
            print("="*60)
            print("\nYou can now:")
            print("1. Start the server:")
            print(f"   {get_python_executable()} -m uvicorn main:app --reload")
            print("\n2. Login to admin panel:")
            print("   http://127.0.0.1:8000/api/v1/admin/login")
            print("   Username: admin")
            print("   Password: Admin123!")
            print("\n3. View API docs:")
            print("   http://127.0.0.1:8000/docs")
            return 0
        else:
            print("⚠️  SOME CHECKS FAILED OR INCOMPLETE")
            print("="*60)
            print("\nPlease review the warnings above.")
            return 1
            
    except Exception as e:
        print(f"\n❌ Error during verification: {e}")
        import traceback
        traceback.print_exc()
        return 1
    finally:
        await engine.dispose()


async def stamp_alembic_command(args: argparse.Namespace):
    """Stamp Alembic to current version without running migrations."""
    print("=== Stamping Alembic Version ===\n")
    
    import subprocess
    
    python_exe = get_python_executable()
    result = subprocess.run(
        [python_exe, "-m", "alembic", "stamp", "head"],
        capture_output=True,
        text=True
    )
    
    if result.returncode == 0:
        print("✅ Alembic stamped to head version")
        print(result.stdout)
    else:
        print("❌ Error stamping Alembic:")
        print(result.stderr)
        sys.exit(1)


async def create_sample_mfg_command(args: argparse.Namespace):
    """Create sample manufacturing data with hierarchy."""
    from _manager_utils import create_sample_manufacturing_data
    
    print("=== Creating Sample Manufacturing Data ===\n")
    
    engine = get_engine()
    session_maker = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    try:
        async with session_maker() as session:
            result = await create_sample_manufacturing_data(session)
            
            print("[SUCCESS] Sample manufacturing data created successfully!")
            print("\nSummary:")
            print(f"   Manufacturing Type: {result['manufacturing_type_name']}")
            print(f"   ID: {result['manufacturing_type_id']}")
            print(f"   Total Nodes: {result['total_nodes']}")
            print("\n   Nodes by Depth:")
            for depth, count in result['nodes_by_depth'].items():
                print(f"     Level {depth}: {count} nodes")
            print("\n   Nodes by Type:")
            for node_type, count in result['nodes_by_type'].items():
                print(f"     {node_type.capitalize()}: {count} nodes")
            print("\nYou can now:")
            print("   - View in admin dashboard: http://127.0.0.1:8000/api/v1/admin/dashboard")
            print("   - Create configurations using this manufacturing type")
            print("   - Delete with: python manage.py delete_sample_mfg")
    except Exception as e:
        print(f"[ERROR] Error creating sample data: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        await engine.dispose()


async def delete_sample_mfg_command(args: argparse.Namespace):
    """Delete sample manufacturing data."""
    from _manager_utils import delete_sample_manufacturing_data
    
    print("=== Deleting Sample Manufacturing Data ===\n")
    
    # Confirm deletion unless --force is used
    if not args.force:
        confirm = input("[WARNING] This will delete 'Sample Casement Window' and all its nodes. Continue? (yes/no): ")
        if confirm.lower() not in ["yes", "y"]:
            print("[CANCELLED] Deletion cancelled")
            sys.exit(0)
    
    engine = get_engine()
    session_maker = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    try:
        async with session_maker() as session:
            result = await delete_sample_manufacturing_data(session)
            
            if result['deleted']:
                print(f"[SUCCESS] {result['message']}")
                print("\nDeleted:")
                print(f"   Manufacturing Type: {result['manufacturing_type_name']}")
                print(f"   ID: {result['manufacturing_type_id']}")
                print(f"   Attribute Nodes: {result['deleted_nodes']}")
            else:
                print(f"[INFO] {result['message']}")
    except Exception as e:
        print(f"[ERROR] Error deleting sample data: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        await engine.dispose()


# Command registry mapping command names to functions
COMMAND_REGISTRY: dict[str, Callable[[argparse.Namespace], None]] = {
    "createsuperuser": lambda args: asyncio.run(create_superuser()),
    "promote": lambda args: asyncio.run(promote_user(args.username)),
    "create_tables": lambda args: asyncio.run(create_tables(args)),
    "drop_tables": lambda args: asyncio.run(drop_tables(args)),
    "reset_db": lambda args: asyncio.run(reset_db(args)),
    "reset_password": lambda args: asyncio.run(reset_password_command(args)),
    "check_env": lambda args: asyncio.run(check_env_command(args)),
    "seed_data": lambda args: asyncio.run(seed_data_command(args)),
    "clean_db": lambda args: asyncio.run(clean_db_types_command(args)),
    "verify_setup": lambda args: sys.exit(asyncio.run(verify_setup_command(args))),
    "stamp_alembic": lambda args: asyncio.run(stamp_alembic_command(args)),
    "create_sample_mfg": lambda args: asyncio.run(create_sample_mfg_command(args)),
    "delete_sample_mfg": lambda args: asyncio.run(delete_sample_mfg_command(args)),
}


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Management CLI for the application",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    
    parser.add_argument(
        "command",
        nargs="?",
        choices=list(COMMAND_REGISTRY.keys()),
        help="Command to execute",
    )
    
    parser.add_argument(
        "username",
        nargs="?",
        help="Username (for promote and reset_password commands)",
    )
    
    parser.add_argument(
        "--force",
        action="store_true",
        help="Skip confirmation prompts for destructive operations",
    )
    
    args = parser.parse_args()
    
    # Show help if no command provided
    if not args.command:
        print_help()
        sys.exit(1)
    
    # Validate username for commands that require it
    if args.command in ["promote", "reset_password"] and not args.username:
        print(f"❌ Error: Username required for '{args.command}' command!")
        print(f"Usage: python manage.py {args.command} <username>")
        sys.exit(1)
    
    # Execute command
    try:
        COMMAND_REGISTRY[args.command](args)
    except KeyError:
        print(f"❌ Unknown command: {args.command}")
        print_help()
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error executing command: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
