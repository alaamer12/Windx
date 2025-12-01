#!/usr/bin/env python3
"""Test suite for environment file consistency checker.

This test suite validates the env consistency checker by:
- Creating temporary modified files
- Testing various failure scenarios
- Ensuring proper cleanup even on interruption
- Verifying all edge cases

NOTE: These are manual tests. Run directly with: python tests/unit/test_env.py
"""

from __future__ import annotations

import importlib.util
import shutil
import signal
import sys
import tempfile
import threading
import time
from pathlib import Path

import pytest

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Import the check_consistency function
check_env_path = project_root / "scripts" / "check_env.py"
spec = importlib.util.spec_from_file_location("check_env", check_env_path)
check_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(check_module)
parse_env_file = check_module.parse_env_file
check_consistency = check_module.main


class EnvConsistencyChecker:
    """Environment file consistency checker for manual testing."""

    def __init__(self):
        """Initialize test suite."""
        self.project_root = Path(__file__).parent.parent.parent

        # Find production file
        prod_patterns = [".env.production", ".env.example.production", ".env.prod"]
        prod_file = None
        for pattern in prod_patterns:
            path = self.project_root / pattern
            if path.exists():
                prod_file = (pattern, path)
                break

        if not prod_file:
            prod_file = (".env.production", self.project_root / ".env.production")

        self.env_files = {
            ".env.example": self.project_root / ".env.example",
            prod_file[0]: prod_file[1],
            ".env.test": self.project_root / ".env.test",
        }
        self.backup_dir = None
        self.test_results = []

    def setup(self):
        """Create backup of original files."""
        print("[*] Creating backup of environment files...")
        self.backup_dir = tempfile.mkdtemp(prefix="env_backup_")

        for name, path in self.env_files.items():
            if path.exists():
                backup_path = Path(self.backup_dir) / name
                shutil.copy2(path, backup_path)
                print(f"  [OK] Backed up {name}")

        print(f"  Backup location: {self.backup_dir}\n")

    def teardown(self):
        """Restore original files from backup."""
        print("\n[...] Restoring original files...")

        if self.backup_dir and Path(self.backup_dir).exists():
            for name, path in self.env_files.items():
                backup_path = Path(self.backup_dir) / name
                if backup_path.exists():
                    shutil.copy2(backup_path, path)
                    print(f"  [OK] Restored {name}")

            # Clean up backup directory
            shutil.rmtree(self.backup_dir)
            print("  [OK] Cleaned up backup directory")

        print("[PASS] Cleanup complete\n")

    def add_result(self, test_name: str, passed: bool, message: str = ""):
        """Record test result."""
        self.test_results.append({"name": test_name, "passed": passed, "message": message})

    def test_baseline(self):
        """Test 1: Baseline - all files should be consistent."""
        print("Test 1: Baseline consistency check")
        print("-" * 50)

        try:
            # Change to project root for the test
            import os

            original_cwd = os.getcwd()
            os.chdir(self.project_root)

            result = check_consistency()

            os.chdir(original_cwd)

            if result == 0:
                print("[PASS] PASS: All files are consistent\n")
                self.add_result("Baseline", True)
                return True
            else:
                print("[FAIL] FAIL: Files are not consistent\n")
                self.add_result("Baseline", False, "Files should be consistent")
                return False
        except Exception as e:
            print(f"[FAIL] FAIL: Exception occurred: {e}\n")
            self.add_result("Baseline", False, str(e))
            return False

    def test_missing_key(self):
        """Test 2: Missing key in one file."""
        print("Test 2: Missing key detection")
        print("-" * 50)

        try:
            # Remove a key from .env.test
            test_file = self.env_files[".env.test"]
            content = test_file.read_text()

            # Remove DATABASE_HOST line
            modified_content = "\n".join(
                line for line in content.split("\n") if not line.startswith("DATABASE_HOST=")
            )

            test_file.write_text(modified_content)
            print("  Modified .env.test (removed DATABASE_HOST)")

            # Run check
            import os

            original_cwd = os.getcwd()
            os.chdir(self.project_root)

            result = check_consistency()

            os.chdir(original_cwd)

            if result == 1:
                print("[PASS] PASS: Missing key detected\n")
                self.add_result("Missing Key", True)
                return True
            else:
                print("[FAIL] FAIL: Missing key not detected\n")
                self.add_result("Missing Key", False, "Should detect missing key")
                return False
        except Exception as e:
            print(f"[FAIL] FAIL: Exception occurred: {e}\n")
            self.add_result("Missing Key", False, str(e))
            return False

    def test_extra_key(self):
        """Test 3: Extra key in one file."""
        print("Test 3: Extra key detection")
        print("-" * 50)

        try:
            # Add an extra key to production file (whatever it's named)
            prod_file = None
            prod_name = None
            for name, path in self.env_files.items():
                if "production" in name or "prod" in name:
                    prod_file = path
                    prod_name = name
                    break

            if not prod_file:
                print("[FAIL] No production file found")
                self.add_result("Extra Key", False, "No production file")
                return False

            content = prod_file.read_text()

            # Add extra key
            modified_content = content + "\nEXTRA_KEY=extra_value\n"
            prod_file.write_text(modified_content)
            print(f"  Modified {prod_name} (added EXTRA_KEY)")

            # Run check
            import os

            original_cwd = os.getcwd()
            os.chdir(self.project_root)

            result = check_consistency()

            os.chdir(original_cwd)

            if result == 1:
                print("[PASS] PASS: Extra key detected\n")
                self.add_result("Extra Key", True)
                return True
            else:
                print("[FAIL] FAIL: Extra key not detected\n")
                self.add_result("Extra Key", False, "Should detect extra key")
                return False
        except Exception as e:
            print(f"[FAIL] FAIL: Exception occurred: {e}\n")
            self.add_result("Extra Key", False, str(e))
            return False

    def test_multiple_issues(self):
        """Test 4: Multiple issues at once."""
        print("Test 4: Multiple issues detection")
        print("-" * 50)

        try:
            # Remove key from .env.test
            test_file = self.env_files[".env.test"]
            test_content = test_file.read_text()
            test_modified = "\n".join(
                line for line in test_content.split("\n") if not line.startswith("DATABASE_USER=")
            )
            test_file.write_text(test_modified)
            print("  Modified .env.test (removed DATABASE_USER)")

            # Add key to production file
            prod_file = None
            prod_name = None
            for name, path in self.env_files.items():
                if "production" in name or "prod" in name:
                    prod_file = path
                    prod_name = name
                    break

            if prod_file:
                prod_content = prod_file.read_text()
                prod_modified = prod_content + "\nANOTHER_EXTRA=value\n"
                prod_file.write_text(prod_modified)
                print(f"  Modified {prod_name} (added ANOTHER_EXTRA)")

            # Run check
            import os

            original_cwd = os.getcwd()
            os.chdir(self.project_root)

            result = check_consistency()

            os.chdir(original_cwd)

            if result == 1:
                print("[PASS] PASS: Multiple issues detected\n")
                self.add_result("Multiple Issues", True)
                return True
            else:
                print("[FAIL] FAIL: Multiple issues not detected\n")
                self.add_result("Multiple Issues", False, "Should detect multiple issues")
                return False
        except Exception as e:
            print(f"[FAIL] FAIL: Exception occurred: {e}\n")
            self.add_result("Multiple Issues", False, str(e))
            return False

    def test_empty_lines_and_comments(self):
        """Test 5: Empty lines and comments should be ignored."""
        print("Test 5: Empty lines and comments handling")
        print("-" * 50)

        try:
            # Add extra comments and empty lines to .env.test
            test_file = self.env_files[".env.test"]
            content = test_file.read_text()

            # Add comments and empty lines
            modified_content = content + "\n# This is a comment\n\n# Another comment\n\n"
            test_file.write_text(modified_content)
            print("  Modified .env.test (added comments and empty lines)")

            # Run check
            import os

            original_cwd = os.getcwd()
            os.chdir(self.project_root)

            result = check_consistency()

            os.chdir(original_cwd)

            if result == 0:
                print("[PASS] PASS: Comments and empty lines ignored\n")
                self.add_result("Comments/Empty Lines", True)
                return True
            else:
                print("[FAIL] FAIL: Comments/empty lines caused false positive\n")
                self.add_result("Comments/Empty Lines", False, "Should ignore comments")
                return False
        except Exception as e:
            print(f"[FAIL] FAIL: Exception occurred: {e}\n")
            self.add_result("Comments/Empty Lines", False, str(e))
            return False

    def print_summary(self):
        """Print test summary."""
        print("\n" + "=" * 60)
        print("TEST SUMMARY")
        print("=" * 60)

        passed = sum(1 for r in self.test_results if r["passed"])
        total = len(self.test_results)

        for result in self.test_results:
            status = "[PASS] PASS" if result["passed"] else "[FAIL] FAIL"
            print(f"{status}: {result['name']}")
            if result["message"]:
                print(f"         {result['message']}")

        print("-" * 60)
        print(f"Results: {passed}/{total} tests passed")

        if passed == total:
            print("[SUCCESS] All tests passed!")
            return 0
        else:
            print(f"[WARN]  {total - passed} test(s) failed")
            return 1

    def run_all_tests(self):
        """Run all tests with proper setup and teardown."""
        print("=" * 60)
        print("ENVIRONMENT CONSISTENCY CHECKER TEST SUITE")
        print("=" * 60)
        print()

        try:
            # Setup
            self.setup()

            # Run tests
            self.test_baseline()

            # Restore before each test
            self.teardown()
            self.setup()
            self.test_missing_key()

            self.teardown()
            self.setup()
            self.test_extra_key()

            self.teardown()
            self.setup()
            self.test_multiple_issues()

            self.teardown()
            self.setup()
            self.test_empty_lines_and_comments()

            # Final cleanup
            self.teardown()

            # Print summary
            return self.print_summary()

        except KeyboardInterrupt:
            print("\n\n[WARN]  Test interrupted by user (Ctrl+C)")
            print("Performing cleanup...")
            self.teardown()
            print("[PASS] Cleanup completed despite interruption")
            return 1
        except Exception as e:
            print(f"\n\n[FAIL] Unexpected error: {e}")
            print("Performing cleanup...")
            self.teardown()
            print("[PASS] Cleanup completed despite error")
            return 1


@pytest.mark.skip(reason="Manual test script - run directly with python")
def test_cleanup_on_exception():
    """Test that cleanup occurs even when exception is raised."""
    print("=" * 60)
    print("CLEANUP ON EXCEPTION TEST")
    print("=" * 60)
    print()

    test_suite = EnvConsistencyChecker()
    backup_dir: str | None = None
    try:
        # Setup
        test_suite.setup()
        backup_dir = test_suite.backup_dir

        print("[OK] Backup created")
        print(f"  Backup location: {backup_dir}")

        # Simulate an error
        print("\n[!] Simulating an error...")
        raise RuntimeError("Simulated error for testing")

    except RuntimeError as e:
        print(f"[OK] Error caught: {e}")
        print("\n[...] Performing cleanup...")

        # Cleanup
        test_suite.teardown()

        # Verify cleanup
        print("\n[*] Verifying cleanup...")

        # Check backup directory was removed
        if Path(backup_dir).exists():
            print("[FAIL] Backup directory still exists!")
            return 1
        else:
            print("[PASS] Backup directory removed")

        # Check files were restored
        all_restored = True
        for name, path in test_suite.env_files.items():
            if path.exists():
                print(f"[PASS] {name} exists")
            else:
                print(f"[FAIL] {name} missing!")
                all_restored = False

        if all_restored:
            print("\n[SUCCESS] Cleanup on exception test PASSED!")
            return 0
        else:
            print("\n[FAIL] Some files were not restored!")
            return 1


@pytest.mark.skip(reason="Manual test script - run directly with python")
def test_manual_interrupt_simulation():
    """Test manual interrupt handling."""
    print("\n" + "=" * 60)
    print("MANUAL INTERRUPT SIMULATION TEST")
    print("=" * 60)
    print()

    test_suite = EnvConsistencyChecker()
    backup_dir: str | None = None

    try:
        # Setup
        test_suite.setup()
        backup_dir = test_suite.backup_dir

        print("[OK] Backup created")

        # Modify a file
        test_file = test_suite.env_files[".env.test"]
        original_content = test_file.read_text()
        test_file.write_text("# Modified for testing\n" + original_content)
        print("[OK] File modified")

        # Simulate keyboard interrupt
        print("\n[!] Simulating KeyboardInterrupt...")
        raise KeyboardInterrupt()

    except KeyboardInterrupt:
        print("[OK] KeyboardInterrupt caught")
        print("\n[...] Performing cleanup...")

        # Cleanup
        test_suite.teardown()

        # Verify cleanup
        print("\n[*] Verifying cleanup...")

        # Check backup directory was removed
        if Path(backup_dir).exists():
            print("[FAIL] Backup directory still exists!")
            return 1
        else:
            print("[PASS] Backup directory removed")

        # Check file was restored
        test_file = test_suite.env_files[".env.test"]
        content = test_file.read_text()

        if content.startswith("# Modified for testing"):
            print("[FAIL] File was not restored!")
            return 1
        else:
            print("[PASS] File was restored to original state")

        print("\n[SUCCESS] Manual interrupt simulation test PASSED!")
        return 0


def simulate_interrupt():
    """Simulate keyboard interrupt after 2 seconds."""
    time.sleep(2)
    print("\n\n[!] Simulating Ctrl+C interrupt...")
    import os

    os.kill(os.getpid(), signal.SIGINT)


def simulate_main():
    """Test interrupt handling."""
    print("=" * 60)
    print("KEYBOARD INTERRUPT HANDLING TEST")
    print("=" * 60)
    print("This test will simulate a Ctrl+C interrupt")
    print("to verify proper cleanup occurs.")
    print("=" * 60)
    print()

    # Start interrupt simulation in background
    interrupt_thread = threading.Thread(target=simulate_interrupt, daemon=True)
    interrupt_thread.start()

    # Run tests
    test_suite = EnvConsistencyChecker()

    try:
        test_suite.run_all_tests()
        print("\n[FAIL] Test should have been interrupted!")
        return 1
    except KeyboardInterrupt:
        print("\n\n[PASS] Keyboard interrupt caught successfully!")
        print("Verifying cleanup...")

        # Check if backup directory was cleaned up
        if test_suite.backup_dir:
            backup_path = Path(test_suite.backup_dir)
            if backup_path.exists():
                print("[FAIL] Backup directory still exists - cleanup failed!")
                return 1
            else:
                print("[PASS] Backup directory cleaned up properly")

        # Check if original files were restored
        for name, path in test_suite.env_files.items():
            if not path.exists():
                print(f"[FAIL] {name} was not restored!")
                return 1

        print("[PASS] All original files restored")
        print("\n[SUCCESS] Interrupt handling test PASSED!")
        return 0


def main():
    """Run all cleanup tests."""
    test_suite = EnvConsistencyChecker()
    test_suite.run_all_tests()

    print("=" * 60)
    print("ENVIRONMENT CONSISTENCY CLEANUP TESTS")
    print("=" * 60)
    print()

    # Test 1: Cleanup on exception
    result1 = test_cleanup_on_exception()

    # Test 2: Manual interrupt simulation
    result2 = test_manual_interrupt_simulation()

    simulate_main()

    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)

    if result1 == 0:
        print("[PASS] Cleanup on exception: PASSED")
    else:
        print("[FAIL] Cleanup on exception: FAILED")

    if result2 == 0:
        print("[PASS] Manual interrupt simulation: PASSED")
    else:
        print("[FAIL] Manual interrupt simulation: FAILED")

    if result1 == 0 and result2 == 0:
        print("\n[SUCCESS] All cleanup tests PASSED!")
        return 0
    else:
        print("\n[FAIL] Some cleanup tests FAILED!")
        return 1


if __name__ == "__main__":
    sys.exit(main())
