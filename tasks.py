"""Task runner for common development commands.

Usage:
    python tasks.py <command>

Available commands:
    Server:
        dev              - Run development server with auto-reload
        start            - Run production server
    
    Database:
        db:upgrade       - Apply database migrations
        db:downgrade     - Rollback last migration
        db:revision      - Create new migration
        db:current       - Show current migration
    
    Management:
        createsuperuser  - Create a new superuser
        promote          - Promote user to superuser (requires username)
    
    Testing:
        test             - Run all tests
        test:unit        - Run unit tests only
        test:cov         - Run tests with coverage report
    
    Code Quality:
        lint             - Check code with ruff
        lint:fix         - Fix code issues with ruff
        format           - Format code with ruff
        format:check     - Check code formatting
"""

import subprocess
import sys

COMMANDS = {
    # Server commands
    "dev": [sys.executable, "-m", "uvicorn", "main:app", "--reload"],
    "start": [sys.executable, "-m", "uvicorn", "main:app"],
    "prod": [sys.executable, "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"],

    # Database commands
    "db:upgrade": [sys.executable, "-m", "alembic", "upgrade", "head"],
    "db:downgrade": [sys.executable, "-m", "alembic", "downgrade", "-1"],
    "db:current": [sys.executable, "-m", "alembic", "current"],
    "db:history": [sys.executable, "-m", "alembic", "history"],

    # Management commands
    "createsuperuser": [sys.executable, "manage.py", "createsuperuser"],
    "promote": [sys.executable, "manage.py", "promote"],

    # Testing commands
    "test": [sys.executable, "-m", "pytest"],
    "test:unit": [sys.executable, "-m", "pytest", "-m", "unit"],
    "test:integration": [sys.executable, "-m", "pytest", "-m", "integration"],
    "test:cov": [sys.executable, "-m", "pytest", "--cov=app", "--cov-report=html", "--cov-report=term"],

    # Code quality commands
    "lint": [sys.executable, "-m", "ruff", "check", "."],
    "lint:fix": [sys.executable, "-m", "ruff", "check", "--fix", "."],
    "format": [sys.executable, "-m", "ruff", "format", "."],
    "format:check": [sys.executable, "-m", "ruff", "format", "--check", "."],
}


def run_command(command: str, args: list[str] = None):
    """Run a command."""
    if command not in COMMANDS:
        print(f"❌ Unknown command: {command}")
        print("\nAvailable commands:")
        for cmd in sorted(COMMANDS.keys()):
            print(f"  - {cmd}")
        sys.exit(1)

    cmd = COMMANDS[command].copy()

    # Add extra arguments
    if args:
        if command == "promote":
            cmd = [sys.executable, "manage.py", "promote"] + args
        elif command == "db:revision":
            cmd = [sys.executable, "-m", "alembic", "revision", "--autogenerate", "-m"] + args
        else:
            cmd.extend(args)

    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd)
    sys.exit(result.returncode)


def print_help():
    """Print help message."""
    print(__doc__)


def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print_help()
        sys.exit(1)

    command = sys.argv[1]
    args = sys.argv[2:] if len(sys.argv) > 2 else None

    if command in ["-h", "--help", "help"]:
        print_help()
        sys.exit(0)

    # Special handling for commands that need arguments
    if command == "promote":
        if not args:
            print("❌ Error: Username required!")
            print("Usage: python tasks.py promote <username>")
            sys.exit(1)
    elif command == "db:revision":
        if not args:
            print("❌ Error: Migration message required!")
            print('Usage: python tasks.py db:revision "migration message"')
            sys.exit(1)

    run_command(command, args)


if __name__ == "__main__":
    main()
