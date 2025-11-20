# Environment Consistency Tests

This directory contains comprehensive tests for the environment file consistency checker.

## Test Files

### `test_env_consistency.py`
Main test suite that validates the consistency checker functionality.

**Tests**:
1. **Baseline** - Verifies all files are consistent initially
2. **Missing Key** - Detects when a key is missing from a file
3. **Extra Key** - Detects when a file has extra keys
4. **Multiple Issues** - Detects multiple problems at once
5. **Comments/Empty Lines** - Ignores comments and empty lines

**Features**:
- Creates temporary backups before each test
- Restores original files after each test
- Handles keyboard interrupts gracefully
- Always performs cleanup, even on errors

**Run**:
```bash
python tests/test_env.py
```

### `test_cleanup_on_error.py`
Tests cleanup behavior when errors occur.

**Tests**:
1. **Cleanup on Exception** - Verifies cleanup when exception is raised
2. **Manual Interrupt Simulation** - Simulates Ctrl+C and verifies cleanup

**Run**:
```bash
python tests/test_cleanup_on_error.py
```

### `test_interrupt_handling.py`
Tests keyboard interrupt handling (advanced).

**Run**:
```bash
python tests/test_interrupt_handling.py
```

## Running All Tests

Run all tests at once:

```bash
# Run main test suite
python tests/test_env.py

# Run cleanup tests
python tests/test_cleanup_on_error.py
```

## Test Results

All tests should pass:

```
✅ PASS: Baseline
✅ PASS: Missing Key
✅ PASS: Extra Key
✅ PASS: Multiple Issues
✅ PASS: Comments/Empty Lines

Results: 5/5 tests passed
🎉 All tests passed!
```

## How Tests Work

### 1. Setup Phase
- Creates temporary backup directory
- Copies all environment files to backup
- Prints backup location

### 2. Test Phase
- Modifies environment files to create test scenarios
- Runs consistency checker
- Verifies expected results

### 3. Teardown Phase
- Restores original files from backup
- Removes backup directory
- Verifies cleanup completed

### 4. Error Handling
- Catches KeyboardInterrupt (Ctrl+C)
- Catches all exceptions
- Always performs cleanup
- Verifies files were restored

## Safety Features

1. **Temporary Backups**: All original files are backed up before testing
2. **Automatic Restore**: Files are restored after each test
3. **Error Recovery**: Cleanup occurs even if tests fail
4. **Interrupt Handling**: Ctrl+C is caught and cleanup is performed
5. **Verification**: Tests verify cleanup was successful

## Test Scenarios

### Scenario 1: Missing Key
```python
# .env.test before
DATABASE_HOST=localhost
DATABASE_USER=user

# .env.test after (DATABASE_HOST removed)
DATABASE_USER=user

# Expected: Checker detects missing key
```

### Scenario 2: Extra Key
```python
# .env.production before
DATABASE_HOST=localhost

# .env.production after (EXTRA_KEY added)
DATABASE_HOST=localhost
EXTRA_KEY=value

# Expected: Checker detects extra key
```

### Scenario 3: Multiple Issues
```python
# .env.test: Missing DATABASE_USER
# .env.production: Extra ANOTHER_EXTRA

# Expected: Checker detects both issues
```

### Scenario 4: Comments and Empty Lines
```python
# .env.test after
DATABASE_HOST=localhost

# This is a comment

# Another comment

# Expected: Checker ignores comments/empty lines
```

## Troubleshooting

### Tests Fail
1. Check if environment files exist
2. Verify you're in the project root
3. Check file permissions

### Cleanup Fails
1. Check if backup directory is accessible
2. Verify file permissions
3. Check disk space

### Keyboard Interrupt Not Working
1. This is expected - tests run too fast
2. Use `test_cleanup_on_error.py` instead
3. Manual interrupt simulation is tested

## Adding New Tests

To add a new test:

1. Add method to `TestEnvConsistency` class:
```python
def test_your_scenario(self):
    """Test your scenario."""
    print("Test X: Your scenario")
    print("-" * 50)
    
    try:
        # Modify files
        # Run checker
        # Verify results
        self.add_result("Your Test", True)
        return True
    except Exception as e:
        self.add_result("Your Test", False, str(e))
        return False
```

2. Add to `run_all_tests()`:
```python
self.teardown()
self.setup()
self.test_your_scenario()
```

3. Run tests to verify

## Best Practices

1. **Always use setup/teardown**: Ensures clean state
2. **Verify cleanup**: Check files were restored
3. **Handle errors**: Use try/except blocks
4. **Add results**: Use `add_result()` for tracking
5. **Print progress**: Help users understand what's happening

## CI/CD Integration

Add to your CI/CD pipeline:

```yaml
# .github/workflows/test.yml
- name: Test Environment Consistency
  run: |
    python tests/test_env_consistency.py
    python tests/test_cleanup_on_error.py
```

Exit codes:
- `0` - All tests passed
- `1` - Some tests failed

## Notes

- Tests use temporary directories for backups
- Original files are never permanently modified
- All cleanup is automatic
- Tests are safe to run anytime
- No manual cleanup needed
