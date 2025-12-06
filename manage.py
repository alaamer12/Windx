"""Management CLI for the application.

Usage:
    python manage.py <command> [options]

Commands:
    createsuperuser              Create a new superuser account
    promote <username>           Promote an existing user to superuser
    create_tables                Create all database tables with LTREE extension
    drop_tables                  Drop all database tables (requires confirmation)
    reset_db                     Drop and recreate all tables (requires confirmation)
    reset_password <username>    Reset password for a user
    check_env                    Validate environment configuration
    seed_data                    Create sample data for development
    clean_db                     Clean orphaned types and recreate database
    verify_setup                 Verify complete setup is working
    stamp_alembic                Stamp Alembic to current version
    create_factory_mfg           Create factory-generated manufacturing data (configurable)
    delete_factory_mfg           Delete factory-generated manufacturing data
    create_factory_customers     Create factory-generated customer data
    delete_factory_customers     Delete factory-generated customer data
    check_db                     Check database connection and schema
    tables                       Display table information with pandas

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
    python manage.py create_factory_mfg --depth 3 --leaves 4
    python manage.py delete_factory_mfg --force
    python manage.py create_factory_customers --count 20
    python manage.py delete_factory_customers --force
    python manage.py check_db
    python manage.py tables --schema public
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

# Rich imports for beautiful terminal output
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.prompt import Confirm, Prompt
from rich import box
from rich.text import Text

# Initialize Rich console
console = Console()


async def create_superuser():
    """Create a new superuser account."""
    console.print(Panel.fit(
        "[bold cyan]Create Superuser Account[/bold cyan]",
        border_style="cyan"
    ))
    console.print()

    email = Prompt.ask("[cyan]Email[/cyan]").strip()
    username = Prompt.ask("[cyan]Username[/cyan]").strip()
    full_name = Prompt.ask("[cyan]Full name[/cyan] (optional)", default="").strip()
    password = Prompt.ask("[cyan]Password[/cyan]", password=True).strip()

    if not all([email, username, password]):
        console.print("\n[bold red]✗ Error:[/bold red] Email, username, and password are required!")
        sys.exit(1)

    engine = get_engine()
    session_maker = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with session_maker() as session:
        try:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console
            ) as progress:
                task = progress.add_task("[cyan]Creating superuser...", total=None)
                
                # Check if user exists
                result = await session.execute(
                    select(User).where((User.email == email) | (User.username == username))
                )
                if result.scalar_one_or_none():
                    console.print("\n[bold red]✗ Error:[/bold red] User already exists!")
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
                
                progress.update(task, completed=True)

            # Success panel
            success_table = Table(show_header=False, box=box.SIMPLE)
            success_table.add_row("[cyan]Email:[/cyan]", f"[white]{superuser.email}[/white]")
            success_table.add_row("[cyan]Username:[/cyan]", f"[white]{superuser.username}[/white]")
            success_table.add_row("[cyan]Full Name:[/cyan]", f"[white]{superuser.full_name}[/white]")
            
            console.print()
            console.print(Panel(
                success_table,
                title="[bold green]✓ Superuser Created Successfully[/bold green]",
                border_style="green"
            ))

        except Exception as e:
            await session.rollback()
            console.print(f"\n[bold red]✗ Error:[/bold red] {e}")
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


async def create_factory_mfg_command(args: argparse.Namespace):
    """Create factory-generated manufacturing data with configurable parameters."""
    from _manager_utils import create_factory_manufacturing_data
    
    console.print(Panel.fit(
        "[bold cyan]Create Factory Manufacturing Data[/bold cyan]",
        border_style="cyan"
    ))
    console.print()
    
    depth = args.depth if hasattr(args, 'depth') and args.depth else 3
    leaves = args.leaves if hasattr(args, 'leaves') and args.leaves else 3
    
    # Configuration table
    config_table = Table(show_header=False, box=box.SIMPLE)
    config_table.add_row("[cyan]Max Depth:[/cyan]", f"[yellow]{depth}[/yellow] levels")
    config_table.add_row("[cyan]Root Categories:[/cyan]", f"[yellow]{leaves}[/yellow]")
    console.print(config_table)
    console.print()
    
    engine = get_engine()
    session_maker = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("[cyan]Generating factory data...", total=None)
            
            async with session_maker() as session:
                result = await create_factory_manufacturing_data(
                    session,
                    depth=depth,
                    root_leaves=leaves,
                )
            
            progress.update(task, description="[green]✓ Factory data created")
        
        # Summary table
        summary_table = Table(title="[bold green]✓ Manufacturing Data Created[/bold green]", box=box.ROUNDED)
        summary_table.add_column("Property", style="cyan", no_wrap=True)
        summary_table.add_column("Value", style="white")
        
        summary_table.add_row("Manufacturing Type", result['manufacturing_type_name'])
        summary_table.add_row("ID", str(result['manufacturing_type_id']))
        summary_table.add_row("Base Price", f"${result['base_price']:.2f}")
        summary_table.add_row("Base Weight", f"{result['base_weight']:.2f} kg")
        summary_table.add_row("Total Nodes", f"{result['total_nodes']:,}")
        summary_table.add_row("Max Depth", str(result['max_depth']))
        summary_table.add_row("Root Categories", str(result['root_leaves']))
        
        console.print()
        console.print(summary_table)
        
        # Nodes by depth
        depth_table = Table(title="[bold]Nodes by Depth[/bold]", box=box.SIMPLE)
        depth_table.add_column("Level", justify="center", style="cyan")
        depth_table.add_column("Count", justify="right", style="yellow")
        
        for depth_level, count in sorted(result['nodes_by_depth'].items()):
            depth_table.add_row(f"Level {depth_level}", str(count))
        
        console.print()
        console.print(depth_table)
        
        # Nodes by type
        type_table = Table(title="[bold]Nodes by Type[/bold]", box=box.SIMPLE)
        type_table.add_column("Type", style="cyan")
        type_table.add_column("Count", justify="right", style="yellow")
        
        for node_type, count in result['nodes_by_type'].items():
            type_table.add_row(node_type.capitalize(), str(count))
        
        console.print()
        console.print(type_table)
        
        if result.get('deepest_path'):
            console.print()
            console.print(f"[dim]Deepest Path:[/dim] [cyan]{result['deepest_path']}[/cyan]")
        
        # Next steps
        console.print()
        console.print(Panel(
            "[cyan]•[/cyan] View in admin dashboard: [link]http://127.0.0.1:8000/api/v1/admin/dashboard[/link]\n"
            "[cyan]•[/cyan] Create configurations using this manufacturing type\n"
            "[cyan]•[/cyan] Delete with: [yellow]python manage.py delete_factory_mfg --force[/yellow]",
            title="[bold]Next Steps[/bold]",
            border_style="dim"
        ))
        
    except Exception as e:
        console.print(f"\n[bold red]✗ Error:[/bold red] {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        await engine.dispose()


async def delete_factory_mfg_command(args: argparse.Namespace):
    """Delete factory-generated manufacturing data."""
    from _manager_utils import delete_factory_manufacturing_data
    
    console.print(Panel.fit(
        "[bold red]Delete Factory Manufacturing Data[/bold red]",
        border_style="red"
    ))
    console.print()
    
    # Confirm deletion unless --force is used
    if not args.force:
        console.print("[yellow]⚠ Warning:[/yellow] This will delete all 'Factory %' manufacturing types and their nodes.")
        if not Confirm.ask("[red]Continue with deletion?[/red]", default=False):
            console.print("[dim]Deletion cancelled[/dim]")
            sys.exit(0)
        console.print()
    
    engine = get_engine()
    session_maker = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("[red]Deleting factory data...", total=None)
            
            async with session_maker() as session:
                result = await delete_factory_manufacturing_data(session)
            
            progress.update(task, description="[green]✓ Deletion complete")
        
        if result['deleted']:
            # Deletion summary table
            summary_table = Table(title="[bold green]✓ Deletion Complete[/bold green]", box=box.ROUNDED)
            summary_table.add_column("Metric", style="cyan")
            summary_table.add_column("Count", justify="right", style="yellow")
            
            summary_table.add_row("Manufacturing Types", str(result['deleted_types']))
            summary_table.add_row("Total Nodes", f"{result['deleted_nodes']:,}")
            
            console.print()
            console.print(summary_table)
            
            # Details table
            if result['types']:
                console.print()
                details_table = Table(title="[bold]Deleted Types[/bold]", box=box.SIMPLE)
                details_table.add_column("Name", style="cyan")
                details_table.add_column("ID", justify="right", style="dim")
                details_table.add_column("Nodes", justify="right", style="yellow")
                
                for type_info in result['types']:
                    details_table.add_row(
                        type_info['name'],
                        str(type_info['id']),
                        str(type_info['nodes'])
                    )
                
                console.print(details_table)
        else:
            console.print(f"\n[dim]{result['message']}[/dim]")
            
    except Exception as e:
        console.print(f"\n[bold red]✗ Error:[/bold red] {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        await engine.dispose()


async def create_factory_customers_command(args: argparse.Namespace):
    """Create factory-generated customer data."""
    from _manager_utils import create_factory_customers
    
    console.print(Panel.fit(
        "[bold cyan]Create Factory Customer Data[/bold cyan]",
        border_style="cyan"
    ))
    console.print()
    
    count = args.count if hasattr(args, 'count') and args.count else 10
    
    console.print(f"[cyan]Number of Customers:[/cyan] [yellow]{count}[/yellow]")
    console.print()
    
    engine = get_engine()
    session_maker = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("[cyan]Generating customer data...", total=None)
            
            async with session_maker() as session:
                result = await create_factory_customers(session, count=count)
            
            progress.update(task, description="[green]✓ Customer data created")
        
        # Summary table
        summary_table = Table(title="[bold green]✓ Customer Data Created[/bold green]", box=box.ROUNDED)
        summary_table.add_column("Customer Type", style="cyan")
        summary_table.add_column("Count", justify="right", style="yellow")
        
        for customer_type, type_count in result['customers_by_type'].items():
            summary_table.add_row(customer_type.capitalize(), str(type_count))
        
        summary_table.add_row("[bold]Total[/bold]", f"[bold]{result['total_customers']}[/bold]")
        
        console.print()
        console.print(summary_table)
        
        # Sample emails
        if result['sample_emails']:
            console.print()
            email_table = Table(title="[bold]Sample Emails[/bold]", box=box.SIMPLE, show_header=False)
            email_table.add_column("Email", style="cyan")
            
            for email in result['sample_emails']:
                email_table.add_row(email)
            
            console.print(email_table)
        
        # Next steps
        console.print()
        console.print(Panel(
            "[cyan]•[/cyan] View customers in admin panel\n"
            "[cyan]•[/cyan] Create configurations for these customers\n"
            "[cyan]•[/cyan] Delete with: [yellow]python manage.py delete_factory_customers --force[/yellow]",
            title="[bold]Next Steps[/bold]",
            border_style="dim"
        ))
        
    except Exception as e:
        console.print(f"\n[bold red]✗ Error:[/bold red] {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        await engine.dispose()


async def delete_factory_customers_command(args: argparse.Namespace):
    """Delete factory-generated customer data."""
    from _manager_utils import delete_factory_customers
    
    console.print(Panel.fit(
        "[bold red]Delete Factory Customer Data[/bold red]",
        border_style="red"
    ))
    console.print()
    
    # Confirm deletion unless --force is used
    if not args.force:
        console.print("[yellow]⚠ Warning:[/yellow] This will delete all factory-generated customers.")
        if not Confirm.ask("[red]Continue with deletion?[/red]", default=False):
            console.print("[dim]Deletion cancelled[/dim]")
            sys.exit(0)
        console.print()
    
    engine = get_engine()
    session_maker = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("[red]Deleting customer data...", total=None)
            
            async with session_maker() as session:
                result = await delete_factory_customers(session)
            
            progress.update(task, description="[green]✓ Deletion complete")
        
        if result['deleted']:
            # Deletion summary table
            summary_table = Table(title="[bold green]✓ Deletion Complete[/bold green]", box=box.ROUNDED)
            summary_table.add_column("Customer Type", style="cyan")
            summary_table.add_column("Deleted", justify="right", style="yellow")
            
            for customer_type, count in result['deleted_by_type'].items():
                summary_table.add_row(customer_type.capitalize(), str(count))
            
            summary_table.add_row("[bold]Total[/bold]", f"[bold]{result['deleted_customers']}[/bold]")
            
            console.print()
            console.print(summary_table)
        else:
            console.print(f"\n[dim]{result['message']}[/dim]")
            
    except Exception as e:
        console.print(f"\n[bold red]✗ Error:[/bold red] {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        await engine.dispose()


async def check_db_command(args: argparse.Namespace):
    """Check database connection and schema."""
    console.print(Panel.fit(
        "[bold cyan]Database Connection Check[/bold cyan]",
        border_style="cyan"
    ))
    console.print()
    
    engine = get_engine()
    
    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("[cyan]Connecting to database...", total=None)
            
            async with engine.begin() as conn:
                # Check connection
                await conn.execute(text("SELECT 1"))
                progress.update(task, description="[green]✓ Connected successfully")
                
                # Get database info
                result = await conn.execute(text("SELECT version()"))
                version = result.scalar()
                
                # Check LTREE extension
                result = await conn.execute(
                    text("SELECT 1 FROM pg_extension WHERE extname = 'ltree'")
                )
                ltree_installed = bool(result.scalar())
                
                # List tables
                result = await conn.execute(
                    text("SELECT tablename FROM pg_tables WHERE schemaname = 'public' ORDER BY tablename")
                )
                tables = [row[0] for row in result]
                
                progress.update(task, completed=True)
        
        # Database info table
        info_table = Table(title="[bold]Database Information[/bold]", box=box.ROUNDED)
        info_table.add_column("Property", style="cyan", no_wrap=True)
        info_table.add_column("Value", style="white")
        
        info_table.add_row("Status", "[green]✓ Connected[/green]")
        info_table.add_row("PostgreSQL Version", version[:50] + "..." if len(version) > 50 else version)
        info_table.add_row(
            "LTREE Extension",
            "[green]✓ Installed[/green]" if ltree_installed else "[red]✗ Not Installed[/red]"
        )
        info_table.add_row("Total Tables", str(len(tables)))
        
        console.print(info_table)
        console.print()
        
        # Row counts table
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("[cyan]Counting rows...", total=len(tables))
            
            counts_table = Table(title="[bold]Table Row Counts[/bold]", box=box.ROUNDED)
            counts_table.add_column("Table", style="cyan", no_wrap=True)
            counts_table.add_column("Rows", justify="right", style="yellow")
            
            async with engine.begin() as conn:
                for table in tables:
                    if table != 'alembic_version':
                        result = await conn.execute(text(f"SELECT COUNT(*) FROM {table}"))
                        count = result.scalar()
                        counts_table.add_row(table, f"{count:,}")
                    progress.advance(task)
        
        console.print(counts_table)
        
    except Exception as e:
        console.print(f"\n[bold red]✗ Error:[/bold red] {e}")
        sys.exit(1)
    finally:
        await engine.dispose()


async def tables_command(args: argparse.Namespace):
    """Display first 5 rows from each table."""
    console.print(Panel.fit(
        "[bold cyan]Database Tables - First 5 Rows[/bold cyan]",
        border_style="cyan"
    ))
    console.print()
    
    schema = args.schema if hasattr(args, 'schema') and args.schema else 'public'
    engine = get_engine()
    
    try:
        # Collect all table data first
        table_data_list = []
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("[cyan]Loading table data...", total=None)
            
            async with engine.begin() as conn:
                # Get all tables
                result = await conn.execute(
                    text("SELECT tablename FROM pg_tables WHERE schemaname = :schema ORDER BY tablename"),
                    {"schema": schema}
                )
                tables = [row[0] for row in result]
                
                if not tables:
                    console.print(f"[yellow]No tables found in schema '{schema}'[/yellow]")
                    return
                
                progress.update(task, description=f"[cyan]Loading {len(tables)} tables...")
                
                # Fetch data from all tables
                for table_name in tables:
                    try:
                        # Get column names
                        col_result = await conn.execute(
                            text("""
                                SELECT column_name, data_type 
                                FROM information_schema.columns 
                                WHERE table_schema = :schema 
                                AND table_name = :table_name 
                                ORDER BY ordinal_position
                            """),
                            {"schema": schema, "table_name": table_name}
                        )
                        columns = [(row[0], row[1]) for row in col_result]
                        
                        if not columns:
                            continue
                        
                        # Get first 5 rows
                        data_result = await conn.execute(
                            text(f"SELECT * FROM {table_name} LIMIT 5")
                        )
                        rows = data_result.fetchall()
                        
                        # Get row count
                        count_result = await conn.execute(
                            text(f"SELECT COUNT(*) FROM {table_name}")
                        )
                        total_rows = count_result.scalar()
                        
                        # Store table data
                        table_data_list.append({
                            'name': table_name,
                            'columns': columns,
                            'rows': rows,
                            'total_rows': total_rows
                        })
                        
                    except Exception as e:
                        table_data_list.append({
                            'name': table_name,
                            'error': str(e)
                        })
                
                progress.update(task, description="[green]✓ Data loaded")
        
        # Now display all tables
        console.print()
        console.print(f"[cyan]Displaying {len(table_data_list)} tables from schema '[bold]{schema}[/bold]'[/cyan]")
        console.print()
        
        for table_data in table_data_list:
            if 'error' in table_data:
                console.print(f"[yellow]⚠ Could not read table '{table_data['name']}': {table_data['error']}[/yellow]")
                console.print()
                continue
            
            # Create table
            table = Table(
                title=f"[bold]{table_data['name']}[/bold] ([dim]{table_data['total_rows']} total rows[/dim])",
                box=box.ROUNDED,
                show_lines=False
            )
            
            # Add columns (limit to reasonable number for display)
            max_cols = 8
            display_columns = table_data['columns'][:max_cols]
            
            for col_name, col_type in display_columns:
                display_name = col_name if len(col_name) <= 20 else col_name[:17] + "..."
                table.add_column(display_name, style="cyan", overflow="fold")
            
            if len(table_data['columns']) > max_cols:
                table.add_column(f"... +{len(table_data['columns']) - max_cols} more", style="dim")
            
            # Add rows
            if table_data['rows']:
                for row in table_data['rows']:
                    str_values = []
                    for i, val in enumerate(row[:max_cols]):
                        if val is None:
                            str_values.append("[dim]NULL[/dim]")
                        else:
                            str_val = str(val)
                            if len(str_val) > 50:
                                str_values.append(str_val[:47] + "...")
                            else:
                                str_values.append(str_val)
                    
                    if len(table_data['columns']) > max_cols:
                        str_values.append("[dim]...[/dim]")
                    
                    table.add_row(*str_values)
            else:
                empty_row = ["[dim]No data[/dim]"] * len(display_columns)
                if len(table_data['columns']) > max_cols:
                    empty_row.append("")
                table.add_row(*empty_row)
            
            console.print(table)
            console.print()
        
        console.print(f"[green]✓ Displayed first 5 rows from {len(table_data_list)} tables[/green]")
        
    except Exception as e:
        console.print(f"\n[bold red]✗ Error:[/bold red] {e}")
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
    "create_factory_mfg": lambda args: asyncio.run(create_factory_mfg_command(args)),
    "delete_factory_mfg": lambda args: asyncio.run(delete_factory_mfg_command(args)),
    "create_factory_customers": lambda args: asyncio.run(create_factory_customers_command(args)),
    "delete_factory_customers": lambda args: asyncio.run(delete_factory_customers_command(args)),
    "check_db": lambda args: asyncio.run(check_db_command(args)),
    "tables": lambda args: asyncio.run(tables_command(args)),
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
    
    parser.add_argument(
        "--depth",
        type=int,
        default=3,
        help="Maximum depth for factory manufacturing data (default: 3)",
    )
    
    parser.add_argument(
        "--leaves",
        type=int,
        default=3,
        help="Number of root categories for factory manufacturing data (default: 3)",
    )
    
    parser.add_argument(
        "--count",
        type=int,
        default=10,
        help="Number of items to create (for factory customers, default: 10)",
    )
    
    parser.add_argument(
        "--schema",
        type=str,
        default="public",
        help="Database schema name (for tables command, default: public)",
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
