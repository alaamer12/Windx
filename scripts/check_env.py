#!/usr/bin/env python3
"""Check consistency across environment files.

This script ensures that all environment files have the same keys,
helping to catch configuration errors early.
"""

import sys
from pathlib import Path


def parse_env_file(file_path: Path) -> set[str]:
    """Parse an env file and return set of keys.

    Args:
        file_path: Path to the .env file

    Returns:
        Set of environment variable keys
    """
    keys = set()

    if not file_path.exists():
        return keys

    with open(file_path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()

            # Skip empty lines and comments
            if not line or line.startswith("#"):
                continue

            # Extract key from KEY=VALUE
            if "=" in line:
                key = line.split("=", 1)[0].strip()
                keys.add(key)

    return keys


def find_production_env_file(project_root: Path) -> tuple[str, Path] | None:
    """Find production environment file with various naming patterns.

    Accepts: .env.production, .env.example.production, .env.prod

    Args:
        project_root: Project root directory

    Returns:
        Tuple of (name, path) or None if not found
    """
    patterns = [
        ".env.production",
        ".env.example.production",
        ".env.prod",
    ]

    for pattern in patterns:
        path = project_root / pattern
        if path.exists():
            return (pattern, path)

    return None


def main() -> int:
    """Main function to check env file consistency.

    Returns:
        Exit code (0 for success, 1 for failure)
    """
    # Define env files to check
    project_root = Path(__file__).parent.parent

    # Find production file (supports multiple patterns)
    prod_file = find_production_env_file(project_root)
    if not prod_file:
        print("[WARN] No production environment file found!")
        print("       Looked for: .env.production, .env.example.production, .env.prod")
        return 1

    env_files = {
        ".env.example": project_root / ".env.example",
        prod_file[0]: prod_file[1],
        ".env.test": project_root / ".env.test",
    }

    # Parse all env files
    env_keys = {}
    for name, path in env_files.items():
        if not path.exists():
            print(f"[FAIL] {name} not found at {path}")
            return 1

        keys = parse_env_file(path)
        env_keys[name] = keys
        print(f"[OK] {name}: {len(keys)} keys")

    # Check consistency
    reference_file = ".env.example"
    reference_keys = env_keys[reference_file]

    all_consistent = True

    for name, keys in env_keys.items():
        if name == reference_file:
            continue

        # Check for missing keys
        missing = reference_keys - keys
        if missing:
            print(f"\n[FAIL] {name} is missing keys:")
            for key in sorted(missing):
                print(f"   - {key}")
            all_consistent = False

        # Check for extra keys
        extra = keys - reference_keys
        if extra:
            print(f"\n[WARN]  {name} has extra keys:")
            for key in sorted(extra):
                print(f"   + {key}")
            all_consistent = False

    if all_consistent:
        print("\n[PASS] All environment files are consistent!")
        return 0
    else:
        print("\n[FAIL] Environment files are inconsistent!")
        print(f"\nReference file: {reference_file}")
        print("Please ensure all env files have the same keys.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
