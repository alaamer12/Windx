# Design Document: Admin Routes Consistency and Testing

## Overview

This design document outlines the architecture and implementation approach for ensuring consistency across admin routes, properly implementing the repository pattern, and adding comprehensive testing for the experimental customer and order management features.

## Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Admin Endpoints Layer                    │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │   Customers  │  │    Orders    │  │  Hierarchy   │      │
│  │   Endpoints  │  │  Endpoints   │  │  Endpoints   │      │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘      │
│         │                  │                  │              │
│         └──────────────────┼──────────────────┘              │
│                            │                                 │
├────────────────────────────┼─────────────────────────────────┤
│                   Shared Utilities Layer                     │
│  ┌─────────────────────────┴──────────────────────────┐     │
│  │  • get_admin_context()                             │     │
│  │  • check_feature_flag()                            │     │
│  │  • format_validation_errors()                      │     │
│  │  • build_redirect_response()                       │     │
│  └────────────────────────────────────────────────────┘     │
├──────────────────────────────────────────────────────────────┤
│                   Repository Layer                           │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │   Customer   │  │    Order     │  │  Attribute   │      │
│  │  Repository  │  │  Repository  │  │    Node      │      │
│  │              │  │              │  │  Repository  │      │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘      │
│         │                  │                  │              │
├─────────┼──────────────────┼──────────────────┼──────────────┤
│                      Database Layer                          │
│         │                  │                  │              │
│  ┌──────▼──────────────────▼──────────────────▼───────┐     │
│  │              PostgreSQL Database                   │     │
│  └────────────────────────────────────────────────────┘     │
└──────────────────────────────────────────────────────────────┘
```

### Testing Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      Test Pyramid                            │
│                                                              │
│                    ┌──────────────┐                         │
│                    │ Integration  │                         │
│                    │    Tests     │                         │
│                    │  (Workflows) │                         │
│                    └──────────────┘                         │
│                  ┌──────────────────┐                       │
│                  │  Endpoint Tests  │                       │
│                  │  (API Contract)  │                       │
│                  └──────────────────┘                       │
│              ┌────────────────────────┐                     │
│              │   Repository Tests     │                     │
│              │   (Data Access)        │                     │
│              └────────────────────────┘                     │
│          ┌──────────────────────────────┐                   │
│          │      Unit Tests              │                   │
│          │  (Business Logic, Utils)     │                   │
│          └──────────────────────────────┘                   │
└──────────────────────────────────────────────────────────────┘
```

## Components and Interfaces

### 1. Common Response Definitions

**Location:** `app/core/responses.py`

**Purpose:** Provide reusable OpenAPI response documentation

**Interface:**

```python
# app/core/responses.py

from typing import Any

def get_common_responses(*status_codes: int) -> dict[int, dict[str, Any]]:
    """Get common response definitions for OpenAPI documentation.
    
    Args:
        *status_codes: HTTP status codes to include
        
    Returns:
        Dictionary mapping status codes to response definitions
        
    Example:
        responses={
            200: {"description": "Success"},
            **get_common_responses(401, 403, 500),
        }
    """
    responses = {
        401: {
            "description": "Unauthorized - Invalid or missing authentication",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Could not validate credentials"
                    }
                }
            },
        },
        403: {
            "description": "Forbidden - Insufficient permissions",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Not enough permissions"
                    }
                }
            },
        },
        404: {
            "description": "Not Found - Resource does not exist",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Resource not found"
                    }
                }
            },
        },
        422: {
            "description": "Validation Error - Invalid request data",
            "content": {
                "application/json": {
                    "example": {
                        "detail": [
                            {
                                "loc": ["body", "email"],
                                "msg": "value is not a valid email address",
                                "type": "value_error.email"
                            }
                        ]
                    }
                }
            },
        },
        500: {
            "description": "Internal Server Error - Unexpected error occurred",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Internal server error"
                    }
                }
            },
        },
    }
    
    return {code: responses[code] for code in status_codes if code in responses}
```

### 2. Shared Admin Utilities Module

**Location:** `app/api/admin_utils.py`

**Purpose:** Centralize common admin functionality to eliminate duplication

**Note:** `get_admin_context()` already exists in `app/api/deps.py` and will remain there. All admin endpoints will import it from `deps.py`.

**Interface:**

```python
# app/api/admin_utils.py

from typing import Any
from fastapi import Request, status
from fastapi.responses import RedirectResponse
from pydantic import ValidationError

from app.models.user import User
from app.core.config import get_settings

# Import existing function from deps.py
from app.api.deps import get_admin_context

# New utility functions to be implemented
def get_admin_context(
    request: Request,
    current_user: User,
    active_page: str = "dashboard",
    **extra: Any,
) -> dict[str, Any]:
    """Build common admin template context with feature flags.
    
    Args:
        request: FastAPI request object
        current_user: Authenticated user
        active_page: Current active page for navigation highlighting
        **extra: Additional context variables
        
    Returns:
        Dictionary with request, current_user, active_page, and feature flags
    """
    settings = get_settings()
    context = {
        "request": request,
        "current_user": current_user,
        "active_page": active_page,
        "enable_customers": settings.windx.experimental_customers_page,
        "enable_orders": settings.windx.experimental_orders_page,
    }
    context.update(extra)
    return context


def check_feature_flag(flag_name: str) -> None:
    """Check if a feature flag is enabled, raise 404 if not.
    
    Args:
        flag_name: Name of the feature flag to check
        
    Raises:
        HTTPException: 404 if feature is disabled
    """
    settings = get_settings()
    flag_value = getattr(settings.windx, flag_name, False)
    
    if not flag_value:
        from fastapi import HTTPException
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"{flag_name.replace('_', ' ').title()} is currently disabled"
        )


def build_redirect_response(
    url: str,
    message: str | None = None,
    message_type: str = "success",
    status_code: int = status.HTTP_303_SEE_OTHER,
) -> RedirectResponse:
    """Build redirect response with optional message.
    
    Args:
        url: Target URL
        message: Optional message to display
        message_type: Type of message (success, error, warning, info)
        status_code: HTTP status code for redirect
        
    Returns:
        RedirectResponse with message in query params
    """
    if message:
        separator = "&" if "?" in url else "?"
        url = f"{url}{separator}{message_type}={message}"
    
    return RedirectResponse(url=url, status_code=status_code)


def format_validation_errors(validation_error: ValidationError) -> list[str]:
    """Convert Pydantic validation errors to user-friendly messages.
    
    Args:
        validation_error: Pydantic ValidationError
        
    Returns:
        List of formatted error messages
    """
    return [
        f"{error['loc'][0] if error['loc'] else 'unknown'}: {error['msg']}"
        for error in validation_error.errors()
    ]


class FormDataProcessor:
    """Utility class for processing form data."""
    
    @staticmethod
    def normalize_optional_string(value: str | None) -> str | None:
        """Return None for empty strings, otherwise return stripped value."""
        return value.strip() if value and value.strip() else None
    
    @staticmethod
    def convert_to_decimal(value: str | None, default=None):
        """Convert string to Decimal, returning default if empty or invalid."""
        from decimal import Decimal, InvalidOperation
        
        if not value or not value.strip():
            return default
        try:
            return Decimal(value)
        except InvalidOperation as e:
            raise ValueError(f"Invalid decimal value: {value}") from e
```

### 2. Enhanced Type Definitions

**Location:** `app/api/types.py`

**Purpose:** Provide reusable, well-documented type aliases for all endpoints

**New Type Definitions:**

```python
# app/api/types.py

from typing import Annotated
from fastapi import Query

# Query parameter types with descriptions
IsSuperuserQuery = Annotated[
    bool | None,
    Query(
        description="Filter by superuser status (true=superusers, false=regular users, null=all)"
    ),
]

IsActiveQuery = Annotated[
    bool | None,
    Query(description="Filter by active status (true=active, false=inactive, null=all)"),
]

SearchQuery = Annotated[
    str | None,
    Query(
        min_length=1,
        max_length=100,
        description="Search term (case-insensitive)",
    ),
]

PageQuery = Annotated[
    int,
    Query(ge=1, description="Page number (1-indexed)"),
]

PageSizeQuery = Annotated[
    int,
    Query(ge=1, le=100, description="Items per page (max 100)"),
]

SortOrderQuery = Annotated[
    Literal["asc", "desc"],
    Query(description="Sort direction (asc=ascending, desc=descending)"),
]

# Form parameter types
RequiredStrForm = Annotated[str, Form(...)]
OptionalStrForm = Annotated[str | None, Form(None)]
RequiredIntForm = Annotated[int, Form(...)]
OptionalIntForm = Annotated[int | None, Form(None)]
OptionalBoolForm = Annotated[bool, Form(False)]

# Common response types
HTMLResponse = Annotated[HTMLResponse, ...]
JSONResponse = Annotated[JSONResponse, ...]
```

### 3. Professional Endpoint Documentation

**All admin endpoints will follow this pattern:**

```python
# app/api/v1/endpoints/admin_customers.py

from app.core.responses import get_common_responses

@router.get(
    "",
    response_class=HTMLResponse,
    summary="List Customers",
    description="List all customers with optional filtering by status, type, and search term. Supports pagination.",
    response_description="HTML page with customer list",
    operation_id="listCustomers",
    responses={
        200: {
            "description": "Successfully retrieved customers page",
            "content": {
                "text/html": {
                    "example": "<html>...</html>"
                }
            },
        },
        302: {
            "description": "Redirect if feature is disabled",
        },
        **get_common_responses(401, 403, 500),
    },
)
async def list_customers(
    request: Request,
    current_superuser: CurrentSuperuser,
    db: DBSession,
    page: PageQuery = 1,
    search: SearchQuery = None,
    customer_type: Annotated[
        str | None,
        Query(description="Filter by customer type (residential, commercial, contractor)"),
    ] = None,
    is_active: IsActiveQuery = None,
):
    """List all customers with filtering and pagination."""
    # Implementation
```

**For form submission endpoints:**

```python
@router.post(
    "",
    response_class=HTMLResponse,
    summary="Create Customer",
    description="Create a new customer from form submission",
    response_description="Redirect to customer list or form with errors",
    operation_id="createCustomer",
    responses={
        302: {
            "description": "Redirect to customer list on success",
        },
        400: {
            "description": "Validation error, re-render form with errors",
            "content": {
                "text/html": {
                    "example": "<html>...</html>"
                }
            },
        },
        **get_common_responses(401, 403, 404, 500),
    },
)
async def create_customer(
    request: Request,
    current_superuser: CurrentSuperuser,
    db: DBSession,
    company_name: OptionalStrForm = None,
    contact_person: OptionalStrForm = None,
    email: OptionalStrForm = None,
    phone: OptionalStrForm = None,
    customer_type: OptionalStrForm = None,
    is_active: OptionalBoolForm = True,
):
    """Create new customer from form data."""
    # Implementation
```

### 4. Refactored Admin Hierarchy Endpoint

**Changes to `app/api/v1/endpoints/admin_hierarchy.py`:**

1. **Add professional endpoint documentation:**
   - Use `summary`, `description`, `response_description`
   - Include `operation_id` for OpenAPI
   - Document all response codes with examples

2. **Use typed query/form parameters:**
   - Import types from `app.api.types`
   - Use descriptive type aliases
   - Consistent parameter ordering

3. **Use shared utilities:**
   - Import `get_admin_context` from `app.api.admin_utils`
   - Use `build_redirect_response` for all redirects
   - Use `format_validation_errors` for error formatting

**Example refactored structure:**

```python
# app/api/v1/endpoints/admin_hierarchy.py

from app.api.admin_utils import (
    get_admin_context,
    build_redirect_response,
    format_validation_errors,
    FormDataProcessor,
)
from app.api.types import (
    CurrentSuperuser,
    DBSession,
    AttributeNodeRepo,
    ManufacturingTypeRepo,
    OptionalIntQuery,
    OptionalStrQuery,
    RequiredStrForm,
    OptionalStrForm,
    RequiredIntForm,
    OptionalIntForm,
    OptionalBoolForm,
)
from app.core.responses import get_common_responses

@router.get(
    "/",
    response_class=HTMLResponse,
    summary="Hierarchy Management Dashboard",
    description="View and manage hierarchical attribute trees for manufacturing types",
    response_description="HTML page with hierarchy visualization",
    operation_id="hierarchyDashboard",
    responses={
        200: {
            "description": "Successfully retrieved hierarchy dashboard",
        },
        **get_common_responses(401, 403, 500),
    },
)
async def hierarchy_dashboard(
    request: Request,
    current_superuser: CurrentSuperuser,
    db: DBSession,
    mfg_repo: ManufacturingTypeRepo,
    attr_repo: AttributeNodeRepo,
    manufacturing_type_id: OptionalIntQuery = None,
    success: OptionalStrQuery = None,
    error: OptionalStrQuery = None,
):
    """Render hierarchy management dashboard with tree visualization."""
    context = get_admin_context(
        request,
        current_superuser,
        active_page="hierarchy",
        manufacturing_types=await mfg_repo.get_active(),
        selected_type_id=manufacturing_type_id,
        success=success,
        error=error,
    )
    
    # ... rest of implementation
```

### 3. Test Fixtures and Factories

**Location:** `tests/factories/`

**Customer Factory:**

```python
# tests/factories/customer_factory.py

import factory
from factory import Faker, LazyAttribute
from factory.alchemy import SQLAlchemyModelFactory

from app.models.customer import Customer
from tests.conftest import async_session_maker


class CustomerFactory(SQLAlchemyModelFactory):
    """Factory for creating Customer test instances."""
    
    class Meta:
        model = Customer
        sqlalchemy_session = async_session_maker
        sqlalchemy_session_persistence = "commit"
    
    id = factory.Sequence(lambda n: n)
    company_name = Faker("company")
    contact_person = Faker("name")
    email = Faker("email")
    phone = Faker("phone_number")
    customer_type = "commercial"
    tax_id = Faker("ssn")
    payment_terms = "net_30"
    is_active = True
    notes = Faker("text", max_nb_chars=200)
    
    address = LazyAttribute(lambda obj: {
        "street": Faker("street_address").generate(),
        "city": Faker("city").generate(),
        "state": Faker("state_abbr").generate(),
        "zip": Faker("zipcode").generate(),
        "country": "USA",
    })
    
    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        """Override create to handle async session."""
        # Implementation for async factory
        pass
    
    class Params:
        """Factory traits for common scenarios."""
        
        residential = factory.Trait(
            customer_type="residential",
            company_name=None,
        )
        
        inactive = factory.Trait(
            is_active=False,
        )
        
        contractor = factory.Trait(
            customer_type="contractor",
            payment_terms="net_15",
        )
```

**Order Factory:**

```python
# tests/factories/order_factory.py

import factory
from factory import Faker, SubFactory
from factory.alchemy import SQLAlchemyModelFactory
from datetime import date, timedelta

from app.models.order import Order
from tests.conftest import async_session_maker
from tests.factories.customer_factory import CustomerFactory
from tests.factories.quote_factory import QuoteFactory


class OrderFactory(SQLAlchemyModelFactory):
    """Factory for creating Order test instances."""
    
    class Meta:
        model = Order
        sqlalchemy_session = async_session_maker
        sqlalchemy_session_persistence = "commit"
    
    id = factory.Sequence(lambda n: n)
    quote = SubFactory(QuoteFactory)
    order_number = factory.Sequence(lambda n: f"ORD-{date.today().strftime('%Y%m%d')}-{n:03d}")
    order_date = factory.LazyFunction(date.today)
    required_date = factory.LazyFunction(lambda: date.today() + timedelta(days=30))
    status = "confirmed"
    special_instructions = Faker("text", max_nb_chars=200)
    
    installation_address = factory.LazyAttribute(lambda obj: {
        "street": Faker("street_address").generate(),
        "city": Faker("city").generate(),
        "state": Faker("state_abbr").generate(),
        "zip": Faker("zipcode").generate(),
        "country": "USA",
        "contact_name": Faker("name").generate(),
        "contact_phone": Faker("phone_number").generate(),
    })
    
    class Params:
        """Factory traits for common scenarios."""
        
        in_production = factory.Trait(
            status="production",
        )
        
        shipped = factory.Trait(
            status="shipped",
        )
        
        completed = factory.Trait(
            status="installed",
        )
```

### 4. Test Structure

**Customer Tests:**

```
tests/
├── integration/
│   ├── test_admin_customers.py          # Full workflow tests
│   └── test_customer_repository.py      # Repository integration tests
└── unit/
    └── test_customer_validation.py      # Schema validation tests
```

**Order Tests:**

```
tests/
├── integration/
│   ├── test_admin_orders.py             # Full workflow tests
│   └── test_order_repository.py         # Repository integration tests
└── unit/
    └── test_order_validation.py         # Schema validation tests
```

## Data Models

### Customer Test Data Structure

```python
# Example test customer data
{
    "company_name": "Test Company Inc",
    "contact_person": "John Doe",
    "email": "john@testcompany.com",
    "phone": "555-1234",
    "customer_type": "commercial",
    "tax_id": "12-3456789",
    "payment_terms": "net_30",
    "address": {
        "street": "123 Test St",
        "city": "Test City",
        "state": "TS",
        "zip": "12345",
        "country": "USA"
    },
    "notes": "Test customer for integration testing",
    "is_active": True
}
```

### Order Test Data Structure

```python
# Example test order data
{
    "quote_id": 1,
    "order_number": "ORD-20251201-001",
    "order_date": "2025-12-01",
    "required_date": "2025-12-31",
    "status": "confirmed",
    "special_instructions": "Call before delivery",
    "installation_address": {
        "street": "456 Install Ave",
        "city": "Install City",
        "state": "IC",
        "zip": "54321",
        "country": "USA",
        "contact_name": "Jane Smith",
        "contact_phone": "555-5678"
    }
}
```

## Error Handling

### Consistent Error Response Pattern

All admin endpoints will follow this error handling pattern:

```python
try:
    # Perform operation
    result = await repository.create(data)
    await db.commit()
    
    return build_redirect_response(
        url="/admin/resource",
        message="Resource created successfully",
        message_type="success"
    )
    
except ValidationError as ve:
    # Re-render form with validation errors
    return templates.TemplateResponse(
        "admin/resource_form.html.jinja",
        get_admin_context(
            request,
            current_user,
            validation_errors=format_validation_errors(ve),
            form_data=original_form_data,
        ),
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
    )
    
except IntegrityError as ie:
    # Handle database constraint violations
    return build_redirect_response(
        url="/admin/resource",
        message=f"Database error: {str(ie)}",
        message_type="error"
    )
    
except Exception as e:
    # Handle unexpected errors
    logger.exception("Unexpected error in resource creation")
    return build_redirect_response(
        url="/admin/resource",
        message="An unexpected error occurred",
        message_type="error"
    )
```

### Feature Flag Error Handling

```python
@router.get("/customers")
async def list_customers(...):
    """List customers endpoint."""
    settings = get_settings()
    
    if not settings.windx.experimental_customers_page:
        return build_redirect_response(
            url="/admin/dashboard",
            message="Customers module is currently disabled",
            message_type="warning"
        )
    
    # ... rest of implementation
```

## Testing Strategy

### 1. Unit Tests

**Focus:** Individual functions and utilities

**Coverage:**
- `FormDataProcessor` methods
- `format_validation_errors` function
- `build_redirect_response` function
- Schema validation logic

**Example:**

```python
# tests/unit/test_admin_utils.py

def test_normalize_optional_string_with_empty():
    """Test that empty strings return None."""
    assert FormDataProcessor.normalize_optional_string("") is None
    assert FormDataProcessor.normalize_optional_string("   ") is None

def test_normalize_optional_string_with_value():
    """Test that non-empty strings are stripped."""
    assert FormDataProcessor.normalize_optional_string("  test  ") == "test"
```

### 2. Repository Integration Tests

**Focus:** Database operations through repositories

**Coverage:**
- CRUD operations
- Filtering and searching
- Relationship loading
- Error handling

**Example:**

```python
# tests/integration/test_customer_repository.py

async def test_create_customer(db_session):
    """Test creating a customer through repository."""
    repo = CustomerRepository(db_session)
    
    customer_data = CustomerCreate(
        company_name="Test Co",
        contact_person="John Doe",
        email="john@test.com",
        customer_type="commercial",
    )
    
    customer = await repo.create(customer_data)
    await db_session.commit()
    
    assert customer.id is not None
    assert customer.company_name == "Test Co"
    assert customer.is_active is True
```

### 3. Endpoint Integration Tests

**Focus:** HTTP endpoints and request/response handling

**Coverage:**
- Successful operations
- Validation errors
- Authorization checks
- Feature flag behavior
- Template rendering

**Example:**

```python
# tests/integration/test_admin_customers.py

async def test_create_customer_success(client, superuser_token):
    """Test successful customer creation."""
    response = await client.post(
        "/api/v1/admin/customers",
        data={
            "company_name": "Test Company",
            "contact_person": "John Doe",
            "email": "john@test.com",
            "customer_type": "commercial",
        },
        cookies={"access_token": superuser_token},
    )
    
    assert response.status_code == 302
    assert "success" in response.headers["location"]
```

### 4. Workflow Integration Tests

**Focus:** End-to-end user workflows

**Coverage:**
- Customer creation → Configuration → Quote → Order
- Hierarchy management workflows
- Error recovery scenarios

**Example:**

```python
# tests/integration/test_customer_order_workflow.py

async def test_complete_order_workflow(client, superuser_token, db_session):
    """Test complete workflow from customer to order."""
    # 1. Create customer
    customer = await create_test_customer(client, superuser_token)
    
    # 2. Create configuration
    config = await create_test_configuration(client, customer.id)
    
    # 3. Generate quote
    quote = await create_test_quote(client, config.id)
    
    # 4. Create order
    order = await create_test_order(client, quote.id)
    
    # Verify complete chain
    assert order.quote_id == quote.id
    assert quote.configuration_id == config.id
    assert config.customer_id == customer.id
```

## Performance Considerations

### 1. Query Optimization

- Use `selectinload` for eager loading relationships in list views
- Implement pagination for all list endpoints
- Add database indexes for commonly filtered/searched fields

### 2. Template Rendering

- Cache template compilation
- Minimize database queries in template context
- Use async template rendering where possible

### 3. Test Performance

- Use fixtures for common test data
- Implement database transaction rollback for test isolation
- Use parallel test execution where possible

## Security Considerations

### 1. Authorization

- All admin endpoints require superuser role
- Feature flags provide additional access control
- Session validation on every request

### 2. Input Validation

- Pydantic schemas validate all input data
- SQL injection prevention through ORM
- XSS prevention through template escaping

### 3. Error Messages

- Don't expose sensitive information in error messages
- Log detailed errors server-side
- Show user-friendly messages client-side

## Database Migration Strategy

### Schema Changes

**New indexes for performance:**

```sql
-- Customer table indexes
CREATE INDEX IF NOT EXISTS idx_customers_email ON customers(email);
CREATE INDEX IF NOT EXISTS idx_customers_company_name ON customers(company_name);
CREATE INDEX IF NOT EXISTS idx_customers_type_active ON customers(customer_type, is_active);

-- Order table indexes
CREATE INDEX IF NOT EXISTS idx_orders_order_number ON orders(order_number);
CREATE INDEX IF NOT EXISTS idx_orders_status ON orders(status);
CREATE INDEX IF NOT EXISTS idx_orders_order_date ON orders(order_date DESC);
CREATE INDEX IF NOT EXISTS idx_orders_customer_id ON orders(quote_id);
```

**Migration file structure:**

```python
# alembic/versions/XXXX_add_admin_indexes.py

"""Add indexes for admin page performance

Revision ID: XXXX
Revises: YYYY
Create Date: 2025-12-01 XX:XX:XX.XXXXXX
"""

from alembic import op

revision = 'XXXX'
down_revision = 'YYYY'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add indexes for admin pages."""
    # Customer indexes
    op.create_index(
        'idx_customers_email',
        'customers',
        ['email'],
        unique=False,
        if_not_exists=True
    )
    op.create_index(
        'idx_customers_company_name',
        'customers',
        ['company_name'],
        unique=False,
        if_not_exists=True
    )
    op.create_index(
        'idx_customers_type_active',
        'customers',
        ['customer_type', 'is_active'],
        unique=False,
        if_not_exists=True
    )
    
    # Order indexes
    op.create_index(
        'idx_orders_order_number',
        'orders',
        ['order_number'],
        unique=False,
        if_not_exists=True
    )
    op.create_index(
        'idx_orders_status',
        'orders',
        ['status'],
        unique=False,
        if_not_exists=True
    )
    op.create_index(
        'idx_orders_order_date',
        'orders',
        ['order_date'],
        unique=False,
        postgresql_ops={'order_date': 'DESC'},
        if_not_exists=True
    )


def downgrade() -> None:
    """Remove indexes."""
    op.drop_index('idx_orders_order_date', table_name='orders', if_exists=True)
    op.drop_index('idx_orders_status', table_name='orders', if_exists=True)
    op.drop_index('idx_orders_order_number', table_name='orders', if_exists=True)
    op.drop_index('idx_customers_type_active', table_name='customers', if_exists=True)
    op.drop_index('idx_customers_company_name', table_name='customers', if_exists=True)
    op.drop_index('idx_customers_email', table_name='customers', if_exists=True)
```

### Type Safety Migration

**Verify type changes don't break existing code:**

1. Run type checker: `mypy app/`
2. Run tests: `pytest tests/`
3. Check for deprecation warnings
4. Update any code using old type patterns

## Implementation Migration Strategy

### Phase 1: Enhanced Type Definitions
1. Add new type aliases to `app/api/types.py`
2. Create `app/core/responses.py` with `get_common_responses()`
3. Add unit tests for type validation
4. Run mypy to verify type safety

### Phase 2: Create Shared Utilities
1. Create `app/api/admin_utils.py`
2. Move common functions from existing endpoints
3. Add comprehensive unit tests
4. Verify no breaking changes

### Phase 3: Database Migrations
1. Create Alembic migration for new indexes
2. Test migration on development database
3. Verify query performance improvements
4. Document rollback procedure

### Phase 4: Refactor Admin Endpoints
1. Update admin_auth.py with professional documentation
2. Update admin_customers.py with typed parameters
3. Update admin_orders.py with typed parameters
4. Update admin_hierarchy.py with shared utilities
5. Ensure all tests pass after each file

### Phase 5: Add Test Infrastructure
1. Create customer and order factories
2. Add repository integration tests
3. Add endpoint integration tests
4. Verify 90%+ test coverage

### Phase 6: Add Workflow Tests
1. Create end-to-end workflow tests
2. Add feature flag toggle tests
3. Add error scenario tests
4. Add performance regression tests

### Phase 7: Documentation
1. Update repository pattern documentation
2. Add testing guidelines
3. Create code examples
4. Document type usage patterns

## Success Metrics

1. **Code Duplication:** Reduce duplicate code by 80%
2. **Test Coverage:** Achieve 90%+ coverage for admin endpoints
3. **Consistency:** All admin endpoints follow same patterns
4. **Maintainability:** New admin features can be added in < 2 hours
5. **Reliability:** Zero regressions in existing functionality
