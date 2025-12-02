"""Database migration helper script.

This script helps run Alembic migrations with the correct environment configuration.
"""
from __future__ import annotations

import argparse
import os
import subprocess
import sys


def run_migration(env: str, command: str, message: str | None = None) -> int:
    """Run Alembic migration command with specified environment.

    Args:
        env (str): Environment name (development or production)
        command (str): Alembic command to run
        message (str | None): Migration message (for revision command)

    Returns:
        int: Exit code from Alembic command
    """
    env_file = f".env.{env}"

    if not os.path.exists(env_file):
        print(f"❌ Error: {env_file} not found")
        return 1

    print(f"🔧 Using environment: {env_file}")

    # Load environment variables from file
    with open(env_file) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, value = line.split("=", 1)
                os.environ[key] = value.strip('"').strip("'")

    # Build Alembic command
    alembic_cmd = ["alembic", command]

    if command == "revision":
        alembic_cmd.append("--autogenerate")
        if message:
            alembic_cmd.extend(["-m", message])
        else:
            print("❌ Error: Migration message required for revision command")
            return 1

    print(f"🚀 Running: {' '.join(alembic_cmd)}")

    # Run Alembic command
    result = subprocess.run(alembic_cmd)
    return result.returncode


def main():
    """Main entry point for migration script."""
    parser = argparse.ArgumentParser(description="Database migration helper")
    parser.add_argument(
        "--env",
        choices=["development", "production"],
        default="development",
        help="Environment to use (default: development)",
    )
    parser.add_argument(
        "command",
        choices=["upgrade", "downgrade", "revision", "current", "history"],
        help="Alembic command to run",
    )
    parser.add_argument(
        "--message",
        "-m",
        help="Migration message (required for revision command)",
    )
    parser.add_argument(
        "target",
        nargs="?",
        default="head",
        help="Migration target (default: head)",
    )

    args = parser.parse_args()

    # Handle revision command
    if args.command == "revision":
        exit_code = run_migration(args.env, args.command, args.message)
    # Handle other commands
    elif args.command in ["upgrade", "downgrade"]:
        # Temporarily modify command to include target
        original_command = args.command
        args.command = f"{args.command} {args.target}"
        exit_code = run_migration(args.env, args.command, None)
    else:
        exit_code = run_migration(args.env, args.command, None)

    sys.exit(exit_code)


if __name__ == "__main__":
    main()
