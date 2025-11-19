# Test Suite

Comprehensive test suite for the FastAPI application using modern async testing practices.

## Quick Start

```bash
# Install test dependencies
pip install -r requirements-test.txt

# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test type
pytest -m unit          # Unit tests only
pytest -m integration   # Integration tests only
```

## Structure

```
tests/
├── conftest.py              # Shared fixtures and configuration
├── pytest.ini               # Pytest settings
├── README.md               # This file
│
├── factories/              # Test data factories
│   ├── __init__.py
│   └── user_factory.py    # User data generation
│
├── unit/                   # Unit tests (fast, isolated)
│   ├── __init__.py
│   └── test_user_service.py
│
└── integration/            # Integration tests (full stack)
    ├── __init__.py
    ├── test_auth.py       # Authentication endpoints
    └── test_users.py      # User management endpoints
```

## Test Types

### Unit Tests (`tests/unit/`)
- Test individual components in isolation
- Mock external dependencies
- Fast execution
- Focus on business logic

### Integration Tests (`tests/integration/`)
- Test complete request/response cycle
- Real database operations
- HTTP requests via httpx
- Test API contracts

## Key Features

✅ **Async Testing** - Full async/await support with pytest-asyncio  
✅ **httpx Client** - Modern async HTTP testing (not TestClient)  
✅ **SQLite In-Memory** - Fast test database  
✅ **Fixtures** - Reusable test setup (users, auth, database)  
✅ **Factories** - Generate realistic test data  
✅ **Coverage** - Track code coverage with pytest-cov  
✅ **Markers** - Organize tests by type/feature  

## Available Fixtures

### Database
- `db_session` - Test database session
- `test_engine` - Test database engine
- `test_session_maker` - Session maker

### HTTP Client
- `client` - httpx AsyncClient for API testing

### Users
- `test_user` - Regular user in database
- `test_superuser` - Superuser in database
- `test_user_data` - User data dictionary
- `test_superuser_data` - Superuser data dictionary

### Authentication
- `auth_headers` - Auth headers for test user
- `superuser_auth_headers` - Auth headers for superuser

## Running Tests

### All Tests
```bash
pytest
```

### Specific File
```bash
pytest tests/integration/test_auth.py
```

### Specific Test
```bash
pytest tests/integration/test_auth.py::TestLoginEndpoint::test_login_with_username_success
```

### By Marker
```bash
pytest -m unit           # Unit tests
pytest -m integration    # Integration tests
pytest -m auth           # Auth tests
pytest -m users          # User tests
```

### With Coverage
```bash
# Terminal report
pytest --cov=app --cov-report=term-missing

# HTML report
pytest --cov=app --cov-report=html
open htmlcov/index.html
```

### Parallel Execution
```bash
# Install pytest-xdist
pip install pytest-xdist

# Run with 4 workers
pytest -n 4
```

## Writing Tests

### Example Unit Test
```python
# tests/unit/test_user_service.py
import pytest
from app.services.user import UserService

pytestmark = pytest.mark.asyncio

async def test_create_user_success(db_session):
    """Test successful user creation."""
    user_service = UserService(db_session)
    user_in = create_user_create_schema()
    
    user = await user_service.create_user(user_in)
    
    assert user.email == user_in.email
    assert user.is_active is True
```

### Example Integration Test
```python
# tests/integration/test_auth.py
import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio

async def test_login_success(client: AsyncClient, test_user, test_user_data):
    """Test successful login."""
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
```

## Test Markers

Available markers for organizing tests:

- `@pytest.mark.unit` - Unit tests
- `@pytest.mark.integration` - Integration tests
- `@pytest.mark.slow` - Slow tests
- `@pytest.mark.auth` - Authentication tests
- `@pytest.mark.users` - User management tests
- `@pytest.mark.services` - Service layer tests
- `@pytest.mark.repositories` - Repository layer tests

## Coverage Goals

- **Overall**: 80%+
- **Services**: 90%+
- **Repositories**: 85%+
- **Endpoints**: 80%+

## Best Practices

1. ✅ Use httpx AsyncClient, not TestClient
2. ✅ Use fixtures for setup
3. ✅ Test one thing per test
4. ✅ Use descriptive test names
5. ✅ Test both success and error cases
6. ✅ Follow AAA pattern (Arrange, Act, Assert)
7. ✅ Use markers for organization
8. ✅ Keep tests independent

## Documentation

For detailed testing guide, see [docs/TESTING.md](../docs/TESTING.md)

## CI/CD

Tests run automatically on:
- Every push
- Every pull request
- Before deployment

Minimum coverage requirement: 80%
