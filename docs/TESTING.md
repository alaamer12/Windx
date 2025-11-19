## Testing Guide

## Overview

This application uses a comprehensive testing strategy with:
- **pytest** for test framework
- **httpx** for async HTTP testing (not TestClient)
- **pytest-asyncio** for async test support
- **pytest-cov** for coverage reporting
- **SQLite in-memory** for fast test database
- **TestSettings** for test-specific configuration from `.env.test`

## Test Structure

```
tests/
├── __init__.py
├── conftest.py              # Shared fixtures
├── config.py                # Test settings configuration
├── pytest.ini               # Pytest configuration
├── factories/               # Test data factories
│   ├── __init__.py
│   └── user_factory.py
├── unit/                    # Unit tests (isolated)
│   ├── __init__.py
│   └── test_user_service.py
└── integration/             # Integration tests (full stack)
    ├── __init__.py
    ├── test_auth.py
    └── test_users.py

.env.test                    # Test configuration (committed to git)
```

## Running Tests

### Run All Tests
```bash
pytest
```

### Run Specific Test File
```bash
pytest tests/integration/test_auth.py
```

### Run Specific Test Class
```bash
pytest tests/integration/test_auth.py::TestLoginEndpoint
```

### Run Specific Test
```bash
pytest tests/integration/test_auth.py::TestLoginEndpoint::test_login_with_username_success
```

### Run Tests by Marker
```bash
# Run only unit tests
pytest -m unit

# Run only integration tests
pytest -m integration

# Run auth tests
pytest -m auth
```

### Run with Coverage
```bash
# Generate HTML coverage report
pytest --cov=app --cov-report=html

# View coverage in terminal
pytest --cov=app --cov-report=term-missing

# Fail if coverage below threshold
pytest --cov=app --cov-fail-under=80
```

### Run in Parallel (faster)
```bash
# Install pytest-xdist
pip install pytest-xdist

# Run with 4 workers
pytest -n 4
```

## Test Types

### Unit Tests (`tests/unit/`)

**Purpose**: Test individual components in isolation

**Characteristics**:
- Fast execution
- Mocked dependencies
- Test business logic only
- No HTTP requests
- No real database (or minimal)

**Example**:
```python
# tests/unit/test_user_service.py
async def test_create_user_duplicate_email(db_session):
    """Test creating user with duplicate email fails."""
    user_service = UserService(db_session)
    user_in = create_user_create_schema()
    
    await user_service.create_user(user_in)
    
    user_in2 = create_user_create_schema(email=user_in.email)
    
    with pytest.raises(ConflictException):
        await user_service.create_user(user_in2)
```

### Integration Tests (`tests/integration/`)

**Purpose**: Test full stack from HTTP to database

**Characteristics**:
- Slower execution
- Real HTTP requests (via httpx)
- Real database operations
- Test complete flows
- Test API contracts

**Example**:
```python
# tests/integration/test_auth.py
async def test_login_with_username_success(client, test_user, test_user_data):
    """Test successful login with username."""
    response = await client.post(
        "/api/v1/auth/login",
        json={
            "username": test_user_data["username"],
            "password": test_user_data["password"],
        },
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
```

## Fixtures

### Database Fixtures

#### `db_session`
Provides a test database session with automatic cleanup.

```python
async def test_something(db_session: AsyncSession):
    # Use db_session for database operations
    user_service = UserService(db_session)
    user = await user_service.create_user(user_in)
```

#### `test_engine`
Provides test database engine (SQLite in-memory).

#### `test_session_maker`
Provides session maker for creating multiple sessions.

### HTTP Client Fixtures

#### `client`
Provides httpx AsyncClient for making HTTP requests.

```python
async def test_endpoint(client: AsyncClient):
    response = await client.get("/api/v1/users/")
    assert response.status_code == 200
```

### User Fixtures

#### `test_user`
Creates a regular test user in the database.

```python
async def test_something(test_user):
    assert test_user.is_active is True
    assert test_user.is_superuser is False
```

#### `test_superuser`
Creates a test superuser in the database.

```python
async def test_admin_action(test_superuser):
    assert test_superuser.is_superuser is True
```

#### `test_user_data`
Provides test user data dictionary.

```python
def test_something(test_user_data: dict):
    assert test_user_data["email"] == "test@example.com"
```

### Authentication Fixtures

#### `auth_headers`
Provides authentication headers for test user.

```python
async def test_protected_endpoint(client, auth_headers):
    response = await client.get(
        "/api/v1/auth/me",
        headers=auth_headers,
    )
    assert response.status_code == 200
```

#### `superuser_auth_headers`
Provides authentication headers for test superuser.

```python
async def test_admin_endpoint(client, superuser_auth_headers):
    response = await client.get(
        "/api/v1/users/",
        headers=superuser_auth_headers,
    )
    assert response.status_code == 200
```

## Test Factories

### User Factory

Create test user data with unique values:

```python
from tests.factories.user_factory import (
    create_user_data,
    create_user_create_schema,
    create_multiple_users_data,
)

# Create user data dictionary
user_data = create_user_data()
user_data = create_user_data(email="custom@example.com")

# Create UserCreate schema
user_in = create_user_create_schema()
user_in = create_user_create_schema(username="custom_user")

# Create multiple users
users_data = create_multiple_users_data(count=5)
```

## Writing Tests

### Test Naming Convention

```python
# Test classes
class TestLoginEndpoint:
    """Tests for login endpoint."""
    pass

# Test methods
async def test_login_with_username_success():
    """Test successful login with username."""
    pass

async def test_login_wrong_password():
    """Test login with wrong password fails."""
    pass
```

### Test Structure (AAA Pattern)

```python
async def test_something(client, test_user):
    # Arrange - Set up test data
    user_data = {"email": "new@example.com"}
    
    # Act - Perform the action
    response = await client.post("/api/v1/users", json=user_data)
    
    # Assert - Verify the result
    assert response.status_code == 201
    assert response.json()["email"] == user_data["email"]
```

### Testing Async Code

```python
import pytest

# Mark test as async
@pytest.mark.asyncio
async def test_async_function():
    result = await some_async_function()
    assert result is not None

# Or use pytestmark at module level
pytestmark = pytest.mark.asyncio

async def test_another_async_function():
    # No decorator needed
    pass
```

### Testing Exceptions

```python
import pytest
from app.core.exceptions import NotFoundException

async def test_user_not_found(db_session):
    user_service = UserService(db_session)
    
    with pytest.raises(NotFoundException) as exc_info:
        await user_service.get_user(99999)
    
    assert "user" in str(exc_info.value.message).lower()
```

### Testing HTTP Responses

```python
async def test_endpoint(client):
    response = await client.get("/api/v1/users/")
    
    # Status code
    assert response.status_code == 200
    
    # JSON response
    data = response.json()
    assert "items" in data
    
    # Headers
    assert "X-Request-ID" in response.headers
    
    # Response time
    assert response.elapsed.total_seconds() < 1.0
```

## Best Practices

### 1. Use httpx Instead of TestClient

**❌ WRONG:**
```python
from fastapi.testclient import TestClient

def test_endpoint():
    client = TestClient(app)
    response = client.get("/api/v1/users/")
```

**✅ CORRECT:**
```python
from httpx import AsyncClient

async def test_endpoint(client: AsyncClient):
    response = await client.get("/api/v1/users/")
```

### 2. Use Fixtures for Setup

**❌ WRONG:**
```python
async def test_something(db_session):
    # Create user in every test
    user = User(email="test@example.com", ...)
    db_session.add(user)
    await db_session.commit()
    # Test logic...
```

**✅ CORRECT:**
```python
async def test_something(test_user):
    # User already created by fixture
    # Test logic...
```

### 3. Test One Thing Per Test

**❌ WRONG:**
```python
async def test_user_crud(client):
    # Create
    response = await client.post("/api/v1/users", json={...})
    assert response.status_code == 201
    
    # Read
    response = await client.get("/api/v1/users/1")
    assert response.status_code == 200
    
    # Update
    response = await client.patch("/api/v1/users/1", json={...})
    assert response.status_code == 200
    
    # Delete
    response = await client.delete("/api/v1/users/1")
    assert response.status_code == 204
```

**✅ CORRECT:**
```python
async def test_create_user(client):
    response = await client.post("/api/v1/users", json={...})
    assert response.status_code == 201

async def test_get_user(client, test_user):
    response = await client.get(f"/api/v1/users/{test_user.id}")
    assert response.status_code == 200

async def test_update_user(client, test_user):
    response = await client.patch(f"/api/v1/users/{test_user.id}", json={...})
    assert response.status_code == 200

async def test_delete_user(client, test_user):
    response = await client.delete(f"/api/v1/users/{test_user.id}")
    assert response.status_code == 204
```

### 4. Use Descriptive Test Names

**❌ WRONG:**
```python
async def test_1(client):
    pass

async def test_user(client):
    pass
```

**✅ CORRECT:**
```python
async def test_login_with_valid_credentials_returns_token(client):
    pass

async def test_login_with_invalid_password_returns_401(client):
    pass
```

### 5. Test Error Cases

```python
class TestLoginEndpoint:
    async def test_login_success(self, client):
        """Test successful login."""
        pass
    
    async def test_login_wrong_password(self, client):
        """Test login with wrong password fails."""
        pass
    
    async def test_login_nonexistent_user(self, client):
        """Test login with nonexistent user fails."""
        pass
    
    async def test_login_inactive_user(self, client):
        """Test login with inactive user fails."""
        pass
```

### 6. Use Markers for Organization

```python
import pytest

@pytest.mark.unit
@pytest.mark.services
async def test_user_service():
    pass

@pytest.mark.integration
@pytest.mark.auth
async def test_login_endpoint():
    pass

@pytest.mark.slow
async def test_expensive_operation():
    pass
```

## Coverage Goals

### Target Coverage
- **Overall**: 80%+
- **Services**: 90%+
- **Repositories**: 85%+
- **Endpoints**: 80%+

### Check Coverage
```bash
# Generate HTML report
pytest --cov=app --cov-report=html

# Open in browser
open htmlcov/index.html  # macOS
start htmlcov/index.html  # Windows
```

### Coverage by Module
```bash
pytest --cov=app --cov-report=term-missing
```

## Continuous Integration

### GitHub Actions Example

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        pip install -r requirements-test.txt
    
    - name: Run tests
      run: pytest --cov=app --cov-report=xml
    
    - name: Upload coverage
      uses: codecov/codecov-action@v3
```

## Troubleshooting

### Issue: Tests hang or timeout

**Solution**: Check for missing `await` keywords
```python
# ❌ WRONG
response = client.get("/api/v1/users/")

# ✅ CORRECT
response = await client.get("/api/v1/users/")
```

### Issue: Database errors

**Solution**: Ensure fixtures are used correctly
```python
# Use db_session fixture
async def test_something(db_session: AsyncSession):
    pass
```

### Issue: Import errors

**Solution**: Ensure PYTHONPATH includes project root
```bash
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
pytest
```

### Issue: Fixture not found

**Solution**: Check conftest.py is in correct location
```
tests/
├── conftest.py  ← Must be here
├── unit/
└── integration/
```

## Test Configuration

Tests use dedicated configuration from `.env.test` file:

```bash
# .env.test
APP_NAME=TestApp
DEBUG=True
DATABASE_PROVIDER=sqlite
CACHE_ENABLED=False
LIMITER_ENABLED=False
SECRET_KEY=test_secret_key_not_for_production
```

**Important**: `.env.test` contains only fake/test data and is safe to commit to git.

For detailed configuration guide, see [Test Configuration](./TEST_CONFIGURATION.md)

## References

- [Test Configuration Guide](./TEST_CONFIGURATION.md)
- [pytest Documentation](https://docs.pytest.org/)
- [pytest-asyncio Documentation](https://pytest-asyncio.readthedocs.io/)
- [httpx Documentation](https://www.python-httpx.org/)
- [Coverage.py Documentation](https://coverage.readthedocs.io/)
