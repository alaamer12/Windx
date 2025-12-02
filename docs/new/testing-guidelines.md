# Testing Guidelines

## Overview

This document provides comprehensive guidelines for writing tests in the Windx application, covering test structure, factory usage, common scenarios, and best practices.

## Table of Contents

1. [Test Structure and Organization](#test-structure-and-organization)
2. [Factory Usage Patterns](#factory-usage-patterns)
3. [Common Test Scenarios](#common-test-scenarios)
4. [Fixture Usage](#fixture-usage)
5. [Best Practices](#best-practices)
6. [Running Tests](#running-tests)

---

## Test Structure and Organization

### Directory Structure

```
tests/
├── conftest.py                      # Shared fixtures
├── factories/                       # Test data factories
│   ├── __init__.py
│   ├── user_factory.py
│   ├── customer_factory.py
│   ├── manufacturing_type_factory.py
│   ├── attribute_node_factory.py
│   ├── configuration_factory.py
│   ├── quote_factory.py
│   └── order_factory.py
├── integration/                     # Integration tests
│   ├── test_admin_customers.py
│   ├── test_admin_orders.py
│   ├── test_customer_repository.py
│   ├── test_order_repository.py
│   ├── test_customer_order_workflow.py
│   └── test_feature_flags.py
└── unit/                           # Unit tests
    ├── test_admin_utils.py
    ├── test_customer_validation.py
    └── test_order_validation.py
```

### Test File Naming

- **Integration tests**: `test_<feature>_<type>.py`
  - Examples: `test_admin_customers.py`, `test_customer_repository.py`
- **Unit tests**: `test_<module>_<function>.py`
  - Examples: `test_admin_utils.py`, `test_validation.py`
- **Workflow tests**: `test_<workflow>_workflow.py`
  - Examples: `test_customer_order_workflow.py`

### Test Function Naming

Use descriptive names that explain what is being tested:

```python
# ✅ GOOD - Clear and descriptive
async def test_create_customer_with_valid_data_succeeds():
    """Test that creating a customer with valid data succeeds."""
    pass

async def test_create_customer_with_duplicate_email_raises_conflict():
    """Test that creating a customer with duplicate email raises ConflictException."""
    pass

# ❌ BAD - Vague and unclear
async def test_customer():
    pass

async def test_create():
    pass
```

**Naming Convention:**
```
test_<action>_<condition>_<expected_result>
```

Examples:
- `test_create_customer_with_valid_data_succeeds`
- `test_update_order_status_with_invalid_status_fails`
- `test_list_customers_with_search_returns_filtered_results`

---

## Factory Usage Patterns

### Basic Factory Usage

Factories provide a convenient way to create test data with sensible defaults:

```python
from tests.factories.customer_factory import CustomerFactory

async def test_customer_creation(db_session):
    """Test creating a customer using factory."""
    # Create customer with default values
    customer = await CustomerFactory.create()
    
    assert customer.id is not None
    assert customer.is_active is True
    assert customer.email is not None
```

### Overriding Factory Defaults

Override specific fields while keeping other defaults:

```python
async def test_customer_with_specific_email(db_session):
    """Test creating customer with specific email."""
    customer = await CustomerFactory.create(
        email="specific@example.com",
        company_name="Specific Company"
    )
    
    assert customer.email == "specific@example.com"
    assert customer.company_name == "Specific Company"
    # Other fields use factory defaults
```

### Using Factory Traits

Traits provide pre-configured variations:

```python
async def test_residential_customer(db_session):
    """Test creating residential customer using trait."""
    # Use residential trait
    customer = await CustomerFactory.create(residential=True)
    
    assert customer.customer_type == "residential"
    assert customer.company_name is None  # Residential customers don't have company

async def test_inactive_customer(db_session):
    """Test creating inactive customer using trait."""
    customer = await CustomerFactory.create(inactive=True)
    
    assert customer.is_active is False
```

### Creating Multiple Instances

Create multiple test instances efficiently:

```python
async def test_list_customers_pagination(db_session):
    """Test customer listing with pagination."""
    # Create 15 customers
    customers = await CustomerFactory.create_batch(15)
    
    assert len(customers) == 15
    assert all(c.id is not None for c in customers)
```

### Creating Related Entities

Factories can create related entities automatically:

```python
async def test_order_with_related_entities(db_session):
    """Test creating order with all related entities."""
    # OrderFactory automatically creates quote, configuration, customer
    order = await OrderFactory.create()
    
    assert order.quote is not None
    assert order.quote.configuration is not None
    assert order.quote.configuration.customer is not None
```

### Factory Build vs Create

- **`build()`**: Creates instance without saving to database
- **`create()`**: Creates and saves instance to database

```python
async def test_customer_validation(db_session):
    """Test customer validation without database."""
    # Build instance without saving
    customer = CustomerFactory.build(email="invalid-email")
    
    # Validate without database interaction
    with pytest.raises(ValidationError):
        CustomerCreate(**customer.__dict__)

async def test_customer_persistence(db_session):
    """Test customer is saved to database."""
    # Create and save to database
    customer = await CustomerFactory.create()
    
    # Verify it's in database
    result = await db_session.execute(
        select(Customer).where(Customer.id == customer.id)
    )
    assert result.scalar_one() is not None
```

---

## Common Test Scenarios

### 1. Repository CRUD Tests

Test basic create, read, update, delete operations:

```python
async def test_customer_repository_create(db_session):
    """Test creating customer through repository."""
    repo = CustomerRepository(db_session)
    
    customer_in = CustomerCreate(
        company_name="Test Company",
        contact_person="John Doe",
        email="john@test.com",
        customer_type="commercial",
    )
    
    customer = await repo.create(customer_in)
    await db_session.commit()
    
    assert customer.id is not None
    assert customer.company_name == "Test Company"
    assert customer.is_active is True

async def test_customer_repository_get(db_session):
    """Test retrieving customer by ID."""
    repo = CustomerRepository(db_session)
    customer = await CustomerFactory.create()
    
    retrieved = await repo.get(customer.id)
    
    assert retrieved is not None
    assert retrieved.id == customer.id
    assert retrieved.email == customer.email

async def test_customer_repository_update(db_session):
    """Test updating customer."""
    repo = CustomerRepository(db_session)
    customer = await CustomerFactory.create()
    
    update_data = CustomerUpdate(company_name="Updated Company")
    updated = await repo.update(customer, update_data)
    await db_session.commit()
    
    assert updated.company_name == "Updated Company"

async def test_customer_repository_delete(db_session):
    """Test deleting customer."""
    repo = CustomerRepository(db_session)
    customer = await CustomerFactory.create()
    
    await repo.delete(customer.id)
    await db_session.commit()
    
    deleted = await repo.get(customer.id)
    assert deleted is None
```

### 2. Filtering and Search Tests

Test query filtering and search functionality:

```python
async def test_list_customers_filter_by_type(db_session):
    """Test filtering customers by type."""
    # Create customers of different types
    await CustomerFactory.create(customer_type="residential")
    await CustomerFactory.create(customer_type="commercial")
    await CustomerFactory.create(customer_type="contractor")
    
    repo = CustomerRepository(db_session)
    commercial = await repo.get_multi(customer_type="commercial")
    
    assert len(commercial) == 1
    assert commercial[0].customer_type == "commercial"

async def test_search_customers_by_name(db_session):
    """Test searching customers by company name."""
    await CustomerFactory.create(company_name="ABC Company")
    await CustomerFactory.create(company_name="XYZ Corporation")
    await CustomerFactory.create(company_name="ABC Industries")
    
    repo = CustomerRepository(db_session)
    results = await repo.search(query="ABC")
    
    assert len(results) == 2
    assert all("ABC" in c.company_name for c in results)
```

### 3. Pagination Tests

Test pagination functionality:

```python
async def test_list_customers_pagination(db_session):
    """Test customer listing with pagination."""
    # Create 25 customers
    await CustomerFactory.create_batch(25)
    
    repo = CustomerRepository(db_session)
    
    # Get first page
    page1 = await repo.get_multi(skip=0, limit=10)
    assert len(page1) == 10
    
    # Get second page
    page2 = await repo.get_multi(skip=10, limit=10)
    assert len(page2) == 10
    
    # Get third page
    page3 = await repo.get_multi(skip=20, limit=10)
    assert len(page3) == 5
    
    # Verify no overlap
    page1_ids = {c.id for c in page1}
    page2_ids = {c.id for c in page2}
    assert page1_ids.isdisjoint(page2_ids)
```

### 4. Validation Tests

Test input validation:

```python
async def test_create_customer_with_invalid_email_fails(db_session):
    """Test that invalid email raises validation error."""
    repo = CustomerRepository(db_session)
    
    customer_in = CustomerCreate(
        company_name="Test Company",
        contact_person="John Doe",
        email="invalid-email",  # Invalid format
        customer_type="commercial",
    )
    
    with pytest.raises(ValidationError) as exc_info:
        await repo.create(customer_in)
    
    assert "email" in str(exc_info.value)

async def test_create_customer_with_missing_required_field_fails(db_session):
    """Test that missing required field raises validation error."""
    with pytest.raises(ValidationError) as exc_info:
        CustomerCreate(
            company_name="Test Company",
            # Missing required email field
            customer_type="commercial",
        )
    
    assert "email" in str(exc_info.value)
```

### 5. Authorization Tests

Test access control:

```python
async def test_regular_user_cannot_access_admin_customers(client, user_token):
    """Test that regular users cannot access admin customer pages."""
    response = await client.get(
        "/api/v1/admin/customers",
        cookies={"access_token": user_token},
    )
    
    assert response.status_code == 403

async def test_superuser_can_access_admin_customers(client, superuser_token):
    """Test that superusers can access admin customer pages."""
    response = await client.get(
        "/api/v1/admin/customers",
        cookies={"access_token": superuser_token},
    )
    
    assert response.status_code == 200
```

### 6. Feature Flag Tests

Test feature flag behavior:

```python
async def test_customers_page_disabled_redirects(client, superuser_token, monkeypatch):
    """Test that disabled feature flag redirects to dashboard."""
    # Disable feature flag
    monkeypatch.setenv("WINDX__EXPERIMENTAL_CUSTOMERS_PAGE", "false")
    
    response = await client.get(
        "/api/v1/admin/customers",
        cookies={"access_token": superuser_token},
        follow_redirects=False,
    )
    
    assert response.status_code == 302
    assert "/admin/dashboard" in response.headers["location"]
    assert "warning" in response.headers["location"]

async def test_customers_page_enabled_shows_page(client, superuser_token, monkeypatch):
    """Test that enabled feature flag shows customer page."""
    # Enable feature flag
    monkeypatch.setenv("WINDX__EXPERIMENTAL_CUSTOMERS_PAGE", "true")
    
    response = await client.get(
        "/api/v1/admin/customers",
        cookies={"access_token": superuser_token},
    )
    
    assert response.status_code == 200
```

### 7. Workflow Tests

Test complete end-to-end workflows:

```python
async def test_complete_customer_to_order_workflow(client, superuser_token, db_session):
    """Test complete workflow from customer creation to order placement."""
    # 1. Create customer
    customer_response = await client.post(
        "/api/v1/admin/customers",
        data={
            "company_name": "Test Company",
            "contact_person": "John Doe",
            "email": "john@test.com",
            "customer_type": "commercial",
        },
        cookies={"access_token": superuser_token},
    )
    assert customer_response.status_code == 302
    
    # Extract customer ID from redirect
    customer_id = extract_id_from_redirect(customer_response.headers["location"])
    
    # 2. Create manufacturing type and configuration
    mfg_type = await ManufacturingTypeFactory.create()
    config = await ConfigurationFactory.create(
        customer_id=customer_id,
        manufacturing_type_id=mfg_type.id,
    )
    
    # 3. Generate quote
    quote = await QuoteFactory.create(configuration_id=config.id)
    
    # 4. Create order
    order_response = await client.post(
        "/api/v1/admin/orders",
        data={
            "quote_id": quote.id,
            "required_date": "2025-12-31",
        },
        cookies={"access_token": superuser_token},
    )
    assert order_response.status_code == 302
    
    # 5. Verify complete chain
    order_id = extract_id_from_redirect(order_response.headers["location"])
    order = await db_session.get(Order, order_id)
    
    assert order.quote_id == quote.id
    assert order.quote.configuration_id == config.id
    assert order.quote.configuration.customer_id == customer_id
```

---

## Fixture Usage

### Common Fixtures

#### Database Session Fixture

```python
@pytest.fixture
async def db_session():
    """Provide database session for tests."""
    async with async_session_maker() as session:
        yield session
        await session.rollback()  # Rollback after test
```

#### Authenticated User Fixtures

```python
@pytest.fixture
async def user_token(client, db_session):
    """Provide authentication token for regular user."""
    user = await UserFactory.create(is_superuser=False)
    token = create_access_token(user.id)
    return token

@pytest.fixture
async def superuser_token(client, db_session):
    """Provide authentication token for superuser."""
    user = await UserFactory.create(is_superuser=True)
    token = create_access_token(user.id)
    return token
```

#### Test Client Fixture

```python
@pytest.fixture
async def client():
    """Provide test client for API requests."""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac
```

### Using Fixtures

```python
async def test_with_fixtures(db_session, client, superuser_token):
    """Test using multiple fixtures."""
    # db_session: Database session for queries
    # client: HTTP client for API requests
    # superuser_token: Authentication token
    
    response = await client.get(
        "/api/v1/admin/customers",
        cookies={"access_token": superuser_token},
    )
    
    assert response.status_code == 200
```

### Fixture Scopes

- **function** (default): New instance for each test
- **class**: Shared across test class
- **module**: Shared across test module
- **session**: Shared across entire test session

```python
@pytest.fixture(scope="session")
async def app_config():
    """Application configuration shared across all tests."""
    return get_settings()

@pytest.fixture(scope="module")
async def test_database():
    """Test database shared across module."""
    # Setup database
    yield db
    # Teardown database

@pytest.fixture(scope="function")
async def clean_database(db_session):
    """Clean database for each test."""
    yield db_session
    await db_session.rollback()
```

---

## Best Practices

### 1. Test Independence

Each test should be independent and not rely on other tests:

```python
# ✅ GOOD - Independent test
async def test_create_customer(db_session):
    """Test creating customer."""
    customer = await CustomerFactory.create()
    assert customer.id is not None

# ❌ BAD - Depends on previous test
async def test_update_customer(db_session):
    """Test updating customer."""
    # Assumes customer from previous test exists
    customer = await db_session.get(Customer, 1)
    # ...
```

### 2. Arrange-Act-Assert Pattern

Structure tests with clear sections:

```python
async def test_create_customer_with_valid_data(db_session):
    """Test creating customer with valid data."""
    # Arrange - Set up test data
    repo = CustomerRepository(db_session)
    customer_in = CustomerCreate(
        company_name="Test Company",
        contact_person="John Doe",
        email="john@test.com",
        customer_type="commercial",
    )
    
    # Act - Perform the action
    customer = await repo.create(customer_in)
    await db_session.commit()
    
    # Assert - Verify the result
    assert customer.id is not None
    assert customer.company_name == "Test Company"
    assert customer.is_active is True
```

### 3. Test One Thing

Each test should verify one specific behavior:

```python
# ✅ GOOD - Tests one thing
async def test_create_customer_sets_default_active_status(db_session):
    """Test that new customers are active by default."""
    customer = await CustomerFactory.create()
    assert customer.is_active is True

async def test_create_customer_generates_id(db_session):
    """Test that new customers get an ID."""
    customer = await CustomerFactory.create()
    assert customer.id is not None

# ❌ BAD - Tests multiple things
async def test_create_customer(db_session):
    """Test customer creation."""
    customer = await CustomerFactory.create()
    assert customer.id is not None
    assert customer.is_active is True
    assert customer.email is not None
    assert customer.created_at is not None
    # Too many assertions
```

### 4. Use Descriptive Assertions

Make assertions clear and specific:

```python
# ✅ GOOD - Clear assertion with message
async def test_customer_email_is_unique(db_session):
    """Test that duplicate emails are rejected."""
    await CustomerFactory.create(email="test@example.com")
    
    with pytest.raises(IntegrityError) as exc_info:
        await CustomerFactory.create(email="test@example.com")
    
    assert "unique constraint" in str(exc_info.value).lower()

# ❌ BAD - Vague assertion
async def test_customer_email(db_session):
    """Test customer email."""
    customer = await CustomerFactory.create()
    assert customer.email  # What are we testing?
```

### 5. Clean Up Test Data

Use fixtures and context managers for cleanup:

```python
@pytest.fixture
async def temp_customer(db_session):
    """Create temporary customer that's cleaned up after test."""
    customer = await CustomerFactory.create()
    yield customer
    # Cleanup
    await db_session.delete(customer)
    await db_session.commit()

async def test_with_temp_customer(temp_customer):
    """Test using temporary customer."""
    assert temp_customer.id is not None
    # Customer is automatically cleaned up after test
```

### 6. Use Parametrize for Similar Tests

Test multiple scenarios with one test function:

```python
@pytest.mark.parametrize("customer_type,expected_terms", [
    ("residential", None),
    ("commercial", "net_30"),
    ("contractor", "net_15"),
])
async def test_customer_default_payment_terms(
    db_session,
    customer_type,
    expected_terms,
):
    """Test default payment terms for different customer types."""
    customer = await CustomerFactory.create(customer_type=customer_type)
    assert customer.payment_terms == expected_terms
```

### 7. Mock External Dependencies

Mock external services and APIs:

```python
async def test_send_welcome_email(db_session, mocker):
    """Test that welcome email is sent on customer creation."""
    # Mock email service
    mock_send = mocker.patch("app.services.email.send_email")
    
    customer = await CustomerFactory.create()
    
    # Verify email was sent
    mock_send.assert_called_once()
    assert customer.email in mock_send.call_args[0]
```

### 8. Test Error Cases

Don't just test happy paths:

```python
async def test_create_customer_with_invalid_email_fails(db_session):
    """Test that invalid email raises validation error."""
    with pytest.raises(ValidationError):
        await CustomerFactory.create(email="invalid-email")

async def test_get_nonexistent_customer_returns_none(db_session):
    """Test that getting nonexistent customer returns None."""
    repo = CustomerRepository(db_session)
    customer = await repo.get(99999)
    assert customer is None

async def test_update_customer_with_duplicate_email_fails(db_session):
    """Test that updating to duplicate email fails."""
    await CustomerFactory.create(email="existing@example.com")
    customer = await CustomerFactory.create(email="other@example.com")
    
    with pytest.raises(IntegrityError):
        customer.email = "existing@example.com"
        await db_session.commit()
```

---

## Running Tests

### Run All Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run with verbose output
pytest -v

# Run with output capture disabled (see print statements)
pytest -s
```

### Run Specific Tests

```bash
# Run specific test file
pytest tests/integration/test_admin_customers.py

# Run specific test function
pytest tests/integration/test_admin_customers.py::test_create_customer

# Run tests matching pattern
pytest -k "customer"

# Run tests with specific marker
pytest -m "integration"
```

### Run Tests in Parallel

```bash
# Install pytest-xdist
pip install pytest-xdist

# Run tests in parallel
pytest -n auto
```

### Generate Coverage Report

```bash
# Generate HTML coverage report
pytest --cov=app --cov-report=html

# Open coverage report
# Windows
start htmlcov/index.html

# Linux/Mac
open htmlcov/index.html
```

### Watch Mode

```bash
# Install pytest-watch
pip install pytest-watch

# Run tests on file changes
ptw
```

---

## Summary

### Key Takeaways

1. **Structure**: Organize tests by type (unit, integration, workflow)
2. **Factories**: Use factories for consistent test data
3. **Fixtures**: Leverage fixtures for setup and teardown
4. **Independence**: Each test should be independent
5. **Clarity**: Use descriptive names and clear assertions
6. **Coverage**: Test both happy paths and error cases
7. **Cleanup**: Always clean up test data
8. **Patterns**: Follow AAA pattern (Arrange-Act-Assert)

### Test Checklist

Before committing code, ensure:

- [ ] All tests pass
- [ ] New features have tests
- [ ] Test coverage is 90%+
- [ ] Tests are independent
- [ ] Tests have descriptive names
- [ ] Error cases are tested
- [ ] Fixtures are used appropriately
- [ ] No test data leaks between tests

---

## Additional Resources

- [Pytest Documentation](https://docs.pytest.org/)
- [Factory Boy Documentation](https://factoryboy.readthedocs.io/)
- [Testing FastAPI Applications](https://fastapi.tiangolo.com/tutorial/testing/)
- [SQLAlchemy Testing](https://docs.sqlalchemy.org/en/20/orm/session_transaction.html#joining-a-session-into-an-external-transaction-such-as-for-test-suites)
