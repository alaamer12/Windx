# Test Configuration Guide

## Overview

The test suite uses a dedicated configuration system that loads settings from `.env.test` file. This ensures tests run in an isolated environment with safe, fake credentials.

## Configuration Files

### `.env.test`
Test environment configuration file that contains:
- Test database settings (SQLite in-memory)
- Fake security credentials (safe to commit)
- Disabled caching and rate limiting
- Test-specific feature flags

**Important**: This file is **committed to git** because it contains only test/fake data.

### `tests/config.py`
Python module that defines `TestSettings` class which:
- Inherits from main `Settings` class
- Loads configuration from `.env.test`
- Overrides production settings with test values
- Provides `get_test_settings()` function

## Test Settings

### Database Configuration

```python
# .env.test
DATABASE_PROVIDER=sqlite
DATABASE_HOST=:memory:
DATABASE_NAME=test_db
DATABASE_ECHO=False
```

**Features**:
- Uses SQLite in-memory database (fast, isolated)
- No persistent data between test runs
- Automatic cleanup after tests
- No need for database migrations in tests

### Security Configuration

```python
# .env.test
SECRET_KEY=test_secret_key_not_for_production_use_only_for_testing_12345
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

**Important**: These are **fake credentials** for testing only. Never use in production!

### Cache Configuration

```python
# .env.test
CACHE_ENABLED=False
```

**Why disabled**:
- Tests should be deterministic
- No external dependencies (Redis)
- Faster test execution
- Easier to debug

### Rate Limiter Configuration

```python
# .env.test
LIMITER_ENABLED=False
```

**Why disabled**:
- Tests can make unlimited requests
- No rate limit errors in tests
- Faster test execution
- Test rate limiting separately if needed

## Using Test Settings

### In Tests

Test settings are automatically loaded via fixtures:

```python
# tests/conftest.py
@pytest.fixture(scope="session")
def test_settings() -> TestSettings:
    """Get test settings."""
    return get_test_settings()
```

### Accessing Settings in Tests

```python
def test_something(test_settings: TestSettings):
    """Test using settings."""
    assert test_settings.debug is True
    assert test_settings.cache_enabled is False
    assert test_settings.database_provider == "sqlite"
```

### Override Settings for Specific Tests

```python
def test_with_custom_settings(test_settings: TestSettings):
    """Test with custom settings."""
    # Temporarily override
    original_value = test_settings.cache_enabled
    test_settings.cache_enabled = True
    
    # Test logic...
    
    # Restore
    test_settings.cache_enabled = original_value
```

## Configuration Hierarchy

```
1. Default values in Settings class
   ↓
2. .env.test file (test-specific)
   ↓
3. Environment variables (if set)
   ↓
4. Test fixtures (runtime overrides)
```

## Test Database

### SQLite In-Memory

```python
# Automatically configured in conftest.py
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"
```

**Benefits**:
- ✅ Fast (in-memory)
- ✅ Isolated (no shared state)
- ✅ Clean (fresh for each test)
- ✅ No setup required
- ✅ No cleanup needed

### Database Fixtures

```python
@pytest_asyncio.fixture(scope="function")
async def test_engine():
    """Create test database engine."""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=False,
        poolclass=NullPool,
    )
    
    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    yield engine
    
    # Drop tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    
    await engine.dispose()
```

## Environment Variables

### Test-Specific Variables

Set in `.env.test`:
```bash
APP_NAME=TestApp
DEBUG=True
DATABASE_PROVIDER=sqlite
CACHE_ENABLED=False
LIMITER_ENABLED=False
```

### Override at Runtime

```bash
# Override specific setting
DATABASE_ECHO=True pytest tests/

# Override multiple settings
DEBUG=False CACHE_ENABLED=True pytest tests/
```

## Security Considerations

### Safe to Commit

✅ `.env.test` - Contains only test/fake data
✅ `tests/config.py` - No sensitive data
✅ Test fixtures - No real credentials

### Never Commit

❌ `.env` - Production secrets
❌ `.env.development` - Development secrets
❌ `.env.production` - Production secrets

### Test Credentials

```python
# .env.test - FAKE credentials for testing
SECRET_KEY=test_secret_key_not_for_production_use_only_for_testing_12345
DATABASE_PASSWORD=test_password
```

**These are intentionally fake and safe to expose!**

## Configuration Examples

### Example 1: Basic Test

```python
# tests/integration/test_auth.py
import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio

async def test_login(client: AsyncClient, test_settings):
    """Test login with test settings."""
    # Settings automatically loaded from .env.test
    assert test_settings.debug is True
    
    response = await client.post(
        "/api/v1/auth/login",
        json={"username": "test", "password": "test"},
    )
    
    assert response.status_code in [200, 401]
```

### Example 2: Custom Settings

```python
# tests/unit/test_config.py
from tests.config import TestSettings

def test_settings_loaded():
    """Test that settings are loaded correctly."""
    settings = TestSettings()
    
    assert settings.app_name == "TestApp"
    assert settings.debug is True
    assert settings.cache_enabled is False
    assert settings.limiter_enabled is False
```

### Example 3: Database Settings

```python
# tests/unit/test_database.py
def test_database_settings(test_settings):
    """Test database configuration."""
    assert test_settings.database.provider == "sqlite"
    assert test_settings.database.echo is False
```

## Troubleshooting

### Issue: Settings not loading

**Problem**: Tests use production settings instead of test settings

**Solution**: Ensure `.env.test` exists and `get_test_settings()` is called
```python
# Check if .env.test exists
ls -la .env.test

# Verify settings in test
def test_settings(test_settings):
    print(test_settings.model_dump())
```

### Issue: Database errors

**Problem**: Tests fail with database connection errors

**Solution**: Verify SQLite is configured correctly
```python
# tests/conftest.py
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"
```

### Issue: Cache/Limiter errors

**Problem**: Tests fail with Redis connection errors

**Solution**: Ensure cache and limiter are disabled
```python
# .env.test
CACHE_ENABLED=False
LIMITER_ENABLED=False
```

### Issue: Import errors

**Problem**: Cannot import TestSettings

**Solution**: Ensure tests/config.py exists and PYTHONPATH is set
```bash
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
pytest
```

## Best Practices

### 1. Keep Test Settings Simple

```python
# ✅ GOOD - Simple, clear settings
CACHE_ENABLED=False
LIMITER_ENABLED=False
DEBUG=True

# ❌ BAD - Complex, production-like settings
CACHE_ENABLED=True
CACHE_REDIS_HOST=redis.example.com
LIMITER_ENABLED=True
```

### 2. Use Fake Data

```python
# ✅ GOOD - Obviously fake
SECRET_KEY=test_secret_key_not_for_production
DATABASE_PASSWORD=test_password

# ❌ BAD - Looks real
SECRET_KEY=sk_live_abc123xyz
DATABASE_PASSWORD=MyRealPassword123
```

### 3. Disable External Services

```python
# ✅ GOOD - No external dependencies
CACHE_ENABLED=False
LIMITER_ENABLED=False

# ❌ BAD - Requires external services
CACHE_ENABLED=True
LIMITER_ENABLED=True
```

### 4. Document Test Settings

```python
# .env.test
# Test Environment Configuration
# This file contains test-specific settings and can be committed to git
# It uses fake/test data that is safe to expose

# Application Settings
APP_NAME=TestApp  # Test application name
DEBUG=True        # Always debug in tests
```

## Configuration Checklist

- [ ] `.env.test` file exists
- [ ] `.env.test` is NOT in `.gitignore`
- [ ] Test settings use SQLite in-memory
- [ ] Cache is disabled
- [ ] Rate limiter is disabled
- [ ] Credentials are fake/test only
- [ ] Settings are documented
- [ ] Tests use `test_settings` fixture

## References

- [Testing Guide](./TESTING.md)
- [Configuration Guide](./CONFIGURATION.md)
- [Coding Standards](../.kiro/steering/coding-standards.md)
