# Type Usage Guide

## Overview

This guide documents all type aliases in `app/api/types.py` and provides examples of how to use them for professional endpoint documentation.

## Table of Contents

1. [Type Aliases Reference](#type-aliases-reference)
2. [Using Types in Endpoints](#using-types-in-endpoints)
3. [OpenAPI Documentation](#openapi-documentation)
4. [Common Response Patterns](#common-response-patterns)
5. [Best Practices](#best-practices)

---

## Type Aliases Reference

### Dependency Injection Types

These types are used for FastAPI dependency injection:

```python
from typing import Annotated
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

# Database session
DBSession = Annotated[AsyncSession, Depends(get_db)]

# Current authenticated user
CurrentUser = Annotated[User, Depends(get_current_user)]

# Current superuser (admin)
CurrentSuperuser = Annotated[User, Depends(get_current_superuser)]

# Repository dependencies
CustomerRepo = Annotated[CustomerRepository, Depends(get_customer_repository)]
OrderRepo = Annotated[OrderRepository, Depends(get_order_repository)]
ManufacturingTypeRepo = Annotated[ManufacturingTypeRepository, Depends(get_manufacturing_type_repository)]
AttributeNodeRepo = Annotated[AttributeNodeRepository, Depends(get_attribute_node_repository)]
ConfigurationRepo = Annotated[ConfigurationRepository, Depends(get_configuration_repository)]
QuoteRepo = Annotated[QuoteRepository, Depends(get_quote_repository)]
```

**Usage Example:**

```python
@router.get("/customers")
async def list_customers(
    db: DBSession,  # Database session injected
    current_superuser: CurrentSuperuser,  # Superuser required
    customer_repo: CustomerRepo,  # Repository injected
):
    """List all customers."""
    customers = await customer_repo.get_multi()
    return customers
```

### Query Parameter Types

These types provide validation and documentation for query parameters:

```python
# Boolean filters
IsActiveQuery = Annotated[
    bool | None,
    Query(description="Filter by active status (true=active, false=inactive, null=all)"),
]

IsSuperuserQuery = Annotated[
    bool | None,
    Query(description="Filter by superuser status (true=superusers, false=regular users, null=all)"),
]

# Search and filtering
SearchQuery = Annotated[
    str | None,
    Query(
        min_length=1,
        max_length=100,
        description="Search term (case-insensitive)",
    ),
]

# Pagination
PageQuery = Annotated[
    int,
    Query(ge=1, description="Page number (1-indexed)"),
]

PageSizeQuery = Annotated[
    int,
    Query(ge=1, le=100, description="Items per page (max 100)"),
]

# Sorting
SortOrderQuery = Annotated[
    Literal["asc", "desc"],
    Query(description="Sort direction (asc=ascending, desc=descending)"),
]

SortByQuery = Annotated[
    str | None,
    Query(description="Field to sort by"),
]

# Optional filters
OptionalIntQuery = Annotated[
    int | None,
    Query(description="Optional integer filter"),
]

OptionalStrQuery = Annotated[
    str | None,
    Query(description="Optional string filter"),
]
```

**Usage Example:**

```python
@router.get("/customers")
async def list_customers(
    page: PageQuery = 1,
    page_size: PageSizeQuery = 50,
    search: SearchQuery = None,
    is_active: IsActiveQuery = None,
    sort_order: SortOrderQuery = "asc",
):
    """List customers with filtering and pagination."""
    # Query parameters are automatically validated
    # OpenAPI docs show descriptions and constraints
    pass
```

### Form Parameter Types

These types are used for HTML form submissions:

```python
# Required form fields
RequiredStrForm = Annotated[str, Form(...)]
RequiredIntForm = Annotated[int, Form(...)]
RequiredBoolForm = Annotated[bool, Form(...)]

# Optional form fields
OptionalStrForm = Annotated[str | None, Form(None)]
OptionalIntForm = Annotated[int | None, Form(None)]
OptionalBoolForm = Annotated[bool, Form(False)]
OptionalDecimalForm = Annotated[Decimal | None, Form(None)]
```

**Usage Example:**

```python
@router.post("/customers")
async def create_customer(
    company_name: OptionalStrForm = None,
    contact_person: RequiredStrForm = ...,
    email: RequiredStrForm = ...,
    phone: OptionalStrForm = None,
    is_active: OptionalBoolForm = True,
):
    """Create customer from form data."""
    # Form fields are automatically parsed and validated
    pass
```

### Response Types

These types document response formats:

```python
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse

# HTML response (for templates)
HTMLResp = Annotated[HTMLResponse, ...]

# JSON response (for API)
JSONResp = Annotated[JSONResponse, ...]

# Redirect response
RedirectResp = Annotated[RedirectResponse, ...]
```

---

## Using Types in Endpoints

### Example 1: List Endpoint with Filtering

```python
from app.api.types import (
    DBSession,
    CurrentSuperuser,
    CustomerRepo,
    PageQuery,
    PageSizeQuery,
    SearchQuery,
    IsActiveQuery,
    SortOrderQuery,
)
from app.schemas.responses import get_common_responses

@router.get(
    "/customers",
    response_class=HTMLResponse,
    summary="List Customers",
    description="List all customers with optional filtering by status, type, and search term. Supports pagination and sorting.",
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
        **get_common_responses(401, 403, 500),
    },
)
async def list_customers(
    request: Request,
    current_superuser: CurrentSuperuser,
    db: DBSession,
    customer_repo: CustomerRepo,
    page: PageQuery = 1,
    page_size: PageSizeQuery = 50,
    search: SearchQuery = None,
    customer_type: Annotated[
        str | None,
        Query(description="Filter by customer type (residential, commercial, contractor)"),
    ] = None,
    is_active: IsActiveQuery = None,
    sort_order: SortOrderQuery = "asc",
):
    """List all customers with filtering and pagination.
    
    Args:
        request: FastAPI request object
        current_superuser: Authenticated superuser
        db: Database session
        customer_repo: Customer repository
        page: Page number (1-indexed)
        page_size: Items per page (max 100)
        search: Search term for company name or email
        customer_type: Filter by customer type
        is_active: Filter by active status
        sort_order: Sort direction
        
    Returns:
        HTML page with customer list
    """
    # Implementation
    pass
```

### Example 2: Create Endpoint with Form Data

```python
from app.api.types import (
    DBSession,
    CurrentSuperuser,
    CustomerRepo,
    RequiredStrForm,
    OptionalStrForm,
    OptionalBoolForm,
)
from app.schemas.responses import get_common_responses

@router.post(
    "/customers",
    response_class=HTMLResponse,
    summary="Create Customer",
    description="Create a new customer from form submission with validation",
    response_description="Redirect to customer list on success, or form with errors",
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
        **get_common_responses(401, 403, 500),
    },
)
async def create_customer(
    request: Request,
    current_superuser: CurrentSuperuser,
    db: DBSession,
    customer_repo: CustomerRepo,
    company_name: OptionalStrForm = None,
    contact_person: RequiredStrForm = ...,
    email: RequiredStrForm = ...,
    phone: OptionalStrForm = None,
    customer_type: RequiredStrForm = ...,
    tax_id: OptionalStrForm = None,
    payment_terms: OptionalStrForm = None,
    is_active: OptionalBoolForm = True,
):
    """Create new customer from form data.
    
    Args:
        request: FastAPI request object
        current_superuser: Authenticated superuser
        db: Database session
        customer_repo: Customer repository
        company_name: Company name (optional for residential)
        contact_person: Primary contact name (required)
        email: Email address (required, must be unique)
        phone: Phone number (optional)
        customer_type: Type (residential, commercial, contractor)
        tax_id: Tax ID number (optional)
        payment_terms: Payment terms (optional)
        is_active: Active status (default: true)
        
    Returns:
        Redirect to customer list on success
        HTML form with errors on validation failure
    """
    # Implementation
    pass
```

### Example 3: Detail Endpoint

```python
from app.api.types import (
    DBSession,
    CurrentSuperuser,
    CustomerRepo,
)
from app.schemas.responses import get_common_responses

@router.get(
    "/customers/{customer_id}",
    response_class=HTMLResponse,
    summary="View Customer Details",
    description="View detailed information about a specific customer including related orders and configurations",
    response_description="HTML page with customer details",
    operation_id="viewCustomer",
    responses={
        200: {
            "description": "Successfully retrieved customer details",
        },
        **get_common_responses(401, 403, 404, 500),
    },
)
async def view_customer(
    request: Request,
    customer_id: int,
    current_superuser: CurrentSuperuser,
    db: DBSession,
    customer_repo: CustomerRepo,
):
    """View customer details.
    
    Args:
        request: FastAPI request object
        customer_id: Customer ID
        current_superuser: Authenticated superuser
        db: Database session
        customer_repo: Customer repository
        
    Returns:
        HTML page with customer details
        
    Raises:
        HTTPException: 404 if customer not found
    """
    # Implementation
    pass
```

---

## OpenAPI Documentation

### Using `get_common_responses()`

The `get_common_responses()` function from `app/schemas/responses.py` provides pre-defined response documentation:

```python
from app.schemas.responses import get_common_responses

@router.get(
    "/endpoint",
    responses={
        200: {"description": "Success"},
        **get_common_responses(401, 403, 404, 500),
    },
)
async def endpoint():
    """Endpoint with common responses."""
    pass
```

**Available Response Codes:**

- `401`: Authentication required or invalid token
- `403`: Insufficient permissions
- `404`: Resource not found
- `422`: Validation error
- `429`: Rate limit exceeded
- `500`: Internal server error
- `503`: Service unavailable

**Response Models:**

```python
# Error detail model
class ErrorDetail(BaseModel):
    detail: str
    field: str | None = None
    error_code: str | None = None

# Error response model
class ErrorResponse(BaseModel):
    message: str
    details: list[ErrorDetail] = []
    request_id: str | None = None
```

### Complete Endpoint Documentation Example

```python
from app.api.types import (
    DBSession,
    CurrentSuperuser,
    CustomerRepo,
    PageQuery,
    PageSizeQuery,
    SearchQuery,
    IsActiveQuery,
)
from app.schemas.responses import get_common_responses

@router.get(
    "/customers",
    response_class=HTMLResponse,
    # Summary: Short description (shown in API docs list)
    summary="List Customers",
    
    # Description: Detailed explanation (shown in endpoint details)
    description="""
    List all customers with optional filtering and pagination.
    
    **Features:**
    - Search by company name or email
    - Filter by customer type (residential, commercial, contractor)
    - Filter by active status
    - Pagination support (up to 100 items per page)
    - Sorting by various fields
    
    **Permissions:**
    - Requires superuser role
    - Feature flag: `experimental_customers_page` must be enabled
    """,
    
    # Response description: What the endpoint returns
    response_description="HTML page with customer list and pagination controls",
    
    # Operation ID: Unique identifier for this operation
    operation_id="listCustomers",
    
    # Tags: Group endpoints in API docs
    tags=["Admin", "Customers"],
    
    # Responses: Document all possible responses
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
    
    # Deprecated: Mark endpoint as deprecated (optional)
    # deprecated=True,
)
async def list_customers(
    request: Request,
    current_superuser: CurrentSuperuser,
    db: DBSession,
    customer_repo: CustomerRepo,
    page: PageQuery = 1,
    page_size: PageSizeQuery = 50,
    search: SearchQuery = None,
    customer_type: Annotated[
        str | None,
        Query(
            description="Filter by customer type",
            example="commercial",
        ),
    ] = None,
    is_active: IsActiveQuery = None,
):
    """List all customers with filtering and pagination.
    
    This docstring appears in the generated API documentation.
    Use it to provide additional context and examples.
    
    Example:
        GET /api/v1/admin/customers?page=1&page_size=20&search=ABC&is_active=true
    """
    # Implementation
    pass
```

---

## Common Response Patterns

### Success Response (200)

```python
responses={
    200: {
        "description": "Successfully retrieved resource",
        "content": {
            "text/html": {
                "example": "<html>...</html>"
            }
        },
    },
}
```

### Created Response (201)

```python
responses={
    201: {
        "description": "Resource created successfully",
        "content": {
            "application/json": {
                "example": {
                    "id": 1,
                    "name": "New Resource",
                    "created_at": "2025-12-01T00:00:00Z"
                }
            }
        },
    },
}
```

### Redirect Response (302/303)

```python
responses={
    302: {
        "description": "Redirect to resource list on success",
    },
    303: {
        "description": "Redirect after POST (See Other)",
    },
}
```

### Validation Error (422)

```python
responses={
    422: {
        "description": "Validation error",
        "model": ErrorResponse,
        "content": {
            "application/json": {
                "example": {
                    "message": "Validation Error",
                    "details": [
                        {
                            "detail": "Field is required",
                            "field": "email",
                            "error_code": "value_error.missing"
                        }
                    ]
                }
            }
        },
    },
}
```

### Not Found (404)

```python
responses={
    404: {
        "description": "Resource not found",
        "model": ErrorResponse,
        "content": {
            "application/json": {
                "example": {
                    "message": "Customer not found",
                    "details": []
                }
            }
        },
    },
}
```

---

## Best Practices

### 1. Always Use Type Aliases

```python
# ✅ GOOD - Using type aliases
async def list_customers(
    db: DBSession,
    current_superuser: CurrentSuperuser,
    page: PageQuery = 1,
):
    pass

# ❌ BAD - Not using type aliases
async def list_customers(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_superuser)],
    page: Annotated[int, Query(ge=1)] = 1,
):
    pass
```

### 2. Document All Parameters

```python
# ✅ GOOD - All parameters documented
async def list_customers(
    page: PageQuery = 1,  # Type provides description
    search: SearchQuery = None,  # Type provides description
    customer_type: Annotated[
        str | None,
        Query(description="Filter by customer type"),  # Custom description
    ] = None,
):
    pass

# ❌ BAD - No parameter documentation
async def list_customers(
    page: int = 1,
    search: str | None = None,
    customer_type: str | None = None,
):
    pass
```

### 3. Use `get_common_responses()`

```python
# ✅ GOOD - Using common responses
@router.get(
    "/customers",
    responses={
        200: {"description": "Success"},
        **get_common_responses(401, 403, 500),
    },
)

# ❌ BAD - Manually defining common responses
@router.get(
    "/customers",
    responses={
        200: {"description": "Success"},
        401: {"description": "Unauthorized"},
        403: {"description": "Forbidden"},
        500: {"description": "Internal Server Error"},
    },
)
```

### 4. Provide Operation IDs

```python
# ✅ GOOD - Unique operation ID
@router.get(
    "/customers",
    operation_id="listCustomers",
)

# ❌ BAD - No operation ID (auto-generated, may change)
@router.get("/customers")
```

### 5. Use Descriptive Summaries

```python
# ✅ GOOD - Clear and descriptive
@router.get(
    "/customers",
    summary="List Customers",
    description="List all customers with filtering and pagination",
)

# ❌ BAD - Vague or missing
@router.get("/customers")
```

### 6. Document Response Models

```python
# ✅ GOOD - Response model documented
@router.get(
    "/customers/{customer_id}",
    response_model=CustomerResponse,
    responses={
        200: {
            "description": "Customer details",
            "model": CustomerResponse,
        },
        **get_common_responses(404, 500),
    },
)

# ❌ BAD - No response model
@router.get("/customers/{customer_id}")
```

### 7. Group Related Endpoints

```python
# ✅ GOOD - Using tags for grouping
@router.get(
    "/customers",
    tags=["Admin", "Customers"],
)

@router.post(
    "/customers",
    tags=["Admin", "Customers"],
)

# ❌ BAD - No tags (endpoints not grouped)
@router.get("/customers")
@router.post("/customers")
```

---

## Summary

### Key Takeaways

1. **Use Type Aliases**: Always use predefined types from `app/api/types.py`
2. **Document Everything**: Use `summary`, `description`, `operation_id`
3. **Common Responses**: Use `get_common_responses()` for standard errors
4. **Parameter Descriptions**: Provide clear descriptions for all parameters
5. **Response Models**: Document response structures with Pydantic models
6. **Consistent Patterns**: Follow the same documentation pattern across all endpoints

### Quick Reference

| Type | Usage | Example |
|------|-------|---------|
| `DBSession` | Database session | `db: DBSession` |
| `CurrentUser` | Authenticated user | `user: CurrentUser` |
| `CurrentSuperuser` | Admin user | `admin: CurrentSuperuser` |
| `PageQuery` | Page number | `page: PageQuery = 1` |
| `PageSizeQuery` | Items per page | `size: PageSizeQuery = 50` |
| `SearchQuery` | Search term | `search: SearchQuery = None` |
| `IsActiveQuery` | Active filter | `is_active: IsActiveQuery = None` |
| `RequiredStrForm` | Required form field | `name: RequiredStrForm` |
| `OptionalStrForm` | Optional form field | `phone: OptionalStrForm = None` |

---

## Additional Resources

- [FastAPI Type Hints](https://fastapi.tiangolo.com/python-types/)
- [FastAPI Query Parameters](https://fastapi.tiangolo.com/tutorial/query-params/)
- [FastAPI Form Data](https://fastapi.tiangolo.com/tutorial/request-forms/)
- [FastAPI Response Models](https://fastapi.tiangolo.com/tutorial/response-model/)
- [OpenAPI Specification](https://swagger.io/specification/)
