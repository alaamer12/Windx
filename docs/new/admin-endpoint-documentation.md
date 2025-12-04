# Admin Endpoint Documentation

## Overview

This document provides comprehensive documentation for admin endpoints, including shared utilities, error handling patterns, feature flag usage, and troubleshooting guidance.

## Table of Contents

1. [Shared Utilities](#shared-utilities)
2. [Error Handling Patterns](#error-handling-patterns)
3. [Feature Flag Usage](#feature-flag-usage)
4. [Troubleshooting Guide](#troubleshooting-guide)
5. [Common Patterns](#common-patterns)

---

## Shared Utilities

### Location

Shared admin utilities are located in:
- `app/api/deps.py` - Dependency injection functions
- `app/api/admin_utils.py` - Admin-specific utilities (if created)

### `get_admin_context()`

**Purpose**: Build common template context for admin pages

**Location**: `app/api/deps.py`

**Signature**:
```python
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
```

**Usage Example**:
```python
from app.api.deps import get_admin_context

@router.get("/customers")
async def list_customers(
    request: Request,
    current_superuser: CurrentSuperuser,
    db: DBSession,
):
    """List customers page."""
    customers = await get_customers(db)
    
    context = get_admin_context(
        request,
        current_superuser,
        active_page="customers",
        customers=customers,
        total_count=len(customers),
    )
    
    return templates.TemplateResponse(
        "admin/customers/list.html.jinja",
        context,
    )
```

**Context Variables**:
- `request`: FastAPI Request object
- `current_user`: Authenticated User object
- `active_page`: String for navigation highlighting
- `enable_customers`: Boolean feature flag
- `enable_orders`: Boolean feature flag
- Any additional `**extra` variables passed

### `check_feature_flag()`

**Purpose**: Check if a feature flag is enabled, raise 404 if not

**Signature**:
```python
def check_feature_flag(flag_name: str) -> None:
    """Check if a feature flag is enabled, raise 404 if not.
    
    Args:
        flag_name: Name of the feature flag to check
        
    Raises:
        HTTPException: 404 if feature is disabled
    """
```

**Usage Example**:
```python
@router.get("/customers")
async def list_customers(
    request: Request,
    current_superuser: CurrentSuperuser,
):
    """List customers page."""
    # Check feature flag first
    check_feature_flag("experimental_customers_page")
    
    # Continue with implementation
    # ...
```

### `build_redirect_response()`

**Purpose**: Build redirect response with optional message

**Signature**:
```python
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
```

**Usage Example**:
```python
@router.post("/customers")
async def create_customer(
    request: Request,
    current_superuser: CurrentSuperuser,
    db: DBSession,
    # ... form parameters
):
    """Create customer."""
    try:
        customer = await create_customer_logic(...)
        
        return build_redirect_response(
            url="/admin/customers",
            message="Customer created successfully",
            message_type="success",
        )
    except ValidationError as e:
        return build_redirect_response(
            url="/admin/customers/new",
            message=str(e),
            message_type="error",
        )
```

### `format_validation_errors()`

**Purpose**: Convert Pydantic validation errors to user-friendly messages

**Signature**:
```python
def format_validation_errors(validation_error: ValidationError) -> list[str]:
    """Convert Pydantic validation errors to user-friendly messages.
    
    Args:
        validation_error: Pydantic ValidationError
        
    Returns:
        List of formatted error messages
    """
```

**Usage Example**:
```python
from pydantic import ValidationError

@router.post("/customers")
async def create_customer(
    request: Request,
    current_superuser: CurrentSuperuser,
    # ... form parameters
):
    """Create customer."""
    try:
        customer_in = CustomerCreate(
            email=email,
            company_name=company_name,
            # ...
        )
        customer = await repo.create(customer_in)
        
    except ValidationError as ve:
        errors = format_validation_errors(ve)
        
        context = get_admin_context(
            request,
            current_superuser,
            active_page="customers",
            validation_errors=errors,
            form_data=request.form,
        )
        
        return templates.TemplateResponse(
            "admin/customers/form.html.jinja",
            context,
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        )
```

### `FormDataProcessor`

**Purpose**: Utility class for processing form data

**Methods**:

```python
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

**Usage Example**:
```python
from app.api.admin_utils import FormDataProcessor

@router.post("/customers")
async def create_customer(
    company_name: OptionalStrForm = None,
    phone: OptionalStrForm = None,
    # ...
):
    """Create customer."""
    # Normalize optional strings (empty strings become None)
    company_name = FormDataProcessor.normalize_optional_string(company_name)
    phone = FormDataProcessor.normalize_optional_string(phone)
    
    customer_in = CustomerCreate(
        company_name=company_name,
        phone=phone,
        # ...
    )
```

---

## Error Handling Patterns

### Pattern 1: Validation Errors

**Scenario**: Form validation fails

**Pattern**:
```python
@router.post("/customers")
async def create_customer(
    request: Request,
    current_superuser: CurrentSuperuser,
    db: DBSession,
    # ... form parameters
):
    """Create customer."""
    try:
        # Validate and create
        customer_in = CustomerCreate(...)
        customer = await repo.create(customer_in)
        await db.commit()
        
        return build_redirect_response(
            url="/admin/customers",
            message="Customer created successfully",
        )
        
    except ValidationError as ve:
        # Re-render form with errors
        errors = format_validation_errors(ve)
        
        context = get_admin_context(
            request,
            current_superuser,
            active_page="customers",
            validation_errors=errors,
            form_data={
                "company_name": company_name,
                "email": email,
                # ... preserve form data
            },
        )
        
        return templates.TemplateResponse(
            "admin/customers/form.html.jinja",
            context,
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        )
```

### Pattern 2: Database Constraint Violations

**Scenario**: Unique constraint violation (duplicate email)

**Pattern**:
```python
from sqlalchemy.exc import IntegrityError

@router.post("/customers")
async def create_customer(
    request: Request,
    current_superuser: CurrentSuperuser,
    db: DBSession,
    # ... form parameters
):
    """Create customer."""
    try:
        customer_in = CustomerCreate(...)
        customer = await repo.create(customer_in)
        await db.commit()
        
        return build_redirect_response(
            url="/admin/customers",
            message="Customer created successfully",
        )
        
    except IntegrityError as ie:
        await db.rollback()
        
        # Extract user-friendly message
        if "unique constraint" in str(ie).lower():
            if "email" in str(ie).lower():
                error_msg = "A customer with this email already exists"
            else:
                error_msg = "This customer already exists"
        else:
            error_msg = "Database error occurred"
        
        return build_redirect_response(
            url="/admin/customers/new",
            message=error_msg,
            message_type="error",
        )
```

### Pattern 3: Not Found Errors

**Scenario**: Resource not found

**Pattern**:
```python
from fastapi import HTTPException, status

@router.get("/customers/{customer_id}")
async def view_customer(
    request: Request,
    customer_id: int,
    current_superuser: CurrentSuperuser,
    db: DBSession,
    customer_repo: CustomerRepo,
):
    """View customer details."""
    customer = await customer_repo.get(customer_id)
    
    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Customer with ID {customer_id} not found",
        )
    
    context = get_admin_context(
        request,
        current_superuser,
        active_page="customers",
        customer=customer,
    )
    
    return templates.TemplateResponse(
        "admin/customers/detail.html.jinja",
        context,
    )
```

### Pattern 4: Unexpected Errors

**Scenario**: Unexpected exception

**Pattern**:
```python
import logging

logger = logging.getLogger(__name__)

@router.post("/customers")
async def create_customer(
    request: Request,
    current_superuser: CurrentSuperuser,
    db: DBSession,
    # ... form parameters
):
    """Create customer."""
    try:
        customer_in = CustomerCreate(...)
        customer = await repo.create(customer_in)
        await db.commit()
        
        return build_redirect_response(
            url="/admin/customers",
            message="Customer created successfully",
        )
        
    except ValidationError as ve:
        # Handle validation errors
        # ...
        
    except IntegrityError as ie:
        # Handle database errors
        # ...
        
    except Exception as e:
        # Log unexpected errors
        logger.exception(f"Unexpected error creating customer: {e}")
        await db.rollback()
        
        return build_redirect_response(
            url="/admin/customers/new",
            message="An unexpected error occurred. Please try again.",
            message_type="error",
        )
```

### Pattern 5: Feature Flag Disabled

**Scenario**: Feature flag is disabled

**Pattern**:
```python
@router.get("/customers")
async def list_customers(
    request: Request,
    current_superuser: CurrentSuperuser,
):
    """List customers page."""
    settings = get_settings()
    
    if not settings.windx.experimental_customers_page:
        return build_redirect_response(
            url="/admin/dashboard",
            message="Customers module is currently disabled",
            message_type="warning",
        )
    
    # Continue with implementation
    # ...
```

---

## Feature Flag Usage

### Available Feature Flags

**Customer Management**:
```python
settings.windx.experimental_customers_page: bool
```

**Order Management**:
```python
settings.windx.experimental_orders_page: bool
```

### Checking Feature Flags

**Method 1: Using `check_feature_flag()`**:
```python
@router.get("/customers")
async def list_customers(
    request: Request,
    current_superuser: CurrentSuperuser,
):
    """List customers page."""
    # Raises 404 if disabled
    check_feature_flag("experimental_customers_page")
    
    # Continue with implementation
    # ...
```

**Method 2: Manual Check with Redirect**:
```python
@router.get("/customers")
async def list_customers(
    request: Request,
    current_superuser: CurrentSuperuser,
):
    """List customers page."""
    settings = get_settings()
    
    if not settings.windx.experimental_customers_page:
        return build_redirect_response(
            url="/admin/dashboard",
            message="Customers module is currently disabled",
            message_type="warning",
        )
    
    # Continue with implementation
    # ...
```

### Feature Flag in Templates

Feature flags are automatically included in admin context:

```jinja2
{# admin/base.html.jinja #}
<nav>
    <a href="/admin/dashboard">Dashboard</a>
    
    {% if enable_customers %}
    <a href="/admin/customers">Customers</a>
    {% endif %}
    
    {% if enable_orders %}
    <a href="/admin/orders">Orders</a>
    {% endif %}
</nav>
```

### Enabling/Disabling Feature Flags

**Via Environment Variables**:
```bash
# .env file
WINDX__EXPERIMENTAL_CUSTOMERS_PAGE=true
WINDX__EXPERIMENTAL_ORDERS_PAGE=true
```

**Via Configuration**:
```python
# app/core/config.py
class WindxSettings(BaseSettings):
    experimental_customers_page: bool = Field(
        default=False,
        description="Enable experimental customers page",
    )
    experimental_orders_page: bool = Field(
        default=False,
        description="Enable experimental orders page",
    )
```

---

## Troubleshooting Guide

### Issue 1: Feature Flag Not Working

**Symptoms**:
- Feature flag is set to `true` but page still redirects
- Feature flag changes don't take effect

**Solutions**:

1. **Check environment variable format**:
   ```bash
   # ✅ CORRECT
   WINDX__EXPERIMENTAL_CUSTOMERS_PAGE=true
   
   # ❌ WRONG
   WINDX_EXPERIMENTAL_CUSTOMERS_PAGE=true  # Single underscore
   experimental_customers_page=true  # Missing prefix
   ```

2. **Restart application**:
   ```bash
   # Environment variables are loaded at startup
   # Restart the application to pick up changes
   ```

3. **Check settings loading**:
   ```python
   from app.core.config import get_settings
   
   settings = get_settings()
   print(f"Customers page enabled: {settings.windx.experimental_customers_page}")
   ```

### Issue 2: Validation Errors Not Displaying

**Symptoms**:
- Form submission fails but no error messages shown
- Validation errors not appearing in template

**Solutions**:

1. **Check template has error display**:
   ```jinja2
   {% if validation_errors %}
   <div class="alert alert-danger">
       <ul>
       {% for error in validation_errors %}
           <li>{{ error }}</li>
       {% endfor %}
       </ul>
   </div>
   {% endif %}
   ```

2. **Verify errors are passed to context**:
   ```python
   except ValidationError as ve:
       errors = format_validation_errors(ve)
       context = get_admin_context(
           request,
           current_superuser,
           validation_errors=errors,  # ← Make sure this is included
       )
   ```

3. **Check error formatting**:
   ```python
   # Test error formatting
   from pydantic import ValidationError
   
   try:
       CustomerCreate(email="invalid")
   except ValidationError as ve:
       errors = format_validation_errors(ve)
       print(errors)  # Should show formatted messages
   ```

### Issue 3: Form Data Not Preserved

**Symptoms**:
- Form submission fails and user has to re-enter all data
- Form fields are empty after validation error

**Solutions**:

1. **Pass form data to context**:
   ```python
   except ValidationError as ve:
       context = get_admin_context(
           request,
           current_superuser,
           validation_errors=errors,
           form_data={
               "company_name": company_name,
               "email": email,
               # ... all form fields
           },
       )
   ```

2. **Use form data in template**:
   ```jinja2
   <input 
       type="text" 
       name="company_name" 
       value="{{ form_data.company_name if form_data else '' }}"
   >
   ```

### Issue 4: Database Connection Errors

**Symptoms**:
- "Connection refused" errors
- "Too many connections" errors
- Slow query performance

**Solutions**:

1. **Check database is running**:
   ```bash
   # Check PostgreSQL status
   pg_isready -h localhost -p 5432
   ```

2. **Check connection pool settings**:
   ```python
   # app/core/database.py
   engine = create_async_engine(
       settings.database_url,
       pool_size=5,  # Adjust based on load
       max_overflow=10,
       pool_pre_ping=True,  # Verify connections
   )
   ```

3. **Check for connection leaks**:
   ```python
   # Always use async context manager
   async with get_db() as db:
       # Use db
       pass
   # Connection automatically returned to pool
   ```

### Issue 5: Authorization Errors

**Symptoms**:
- 403 Forbidden errors
- Regular users accessing admin pages
- Superusers unable to access pages

**Solutions**:

1. **Check user role**:
   ```python
   # Verify user is superuser
   print(f"User: {current_user.email}")
   print(f"Is superuser: {current_user.is_superuser}")
   ```

2. **Check dependency injection**:
   ```python
   # ✅ CORRECT - Requires superuser
   async def endpoint(
       current_superuser: CurrentSuperuser,
   ):
       pass
   
   # ❌ WRONG - Only requires authentication
   async def endpoint(
       current_user: CurrentUser,
   ):
       pass
   ```

3. **Check authentication token**:
   ```python
   # Verify token is valid
   from app.core.security import decode_access_token
   
   token = request.cookies.get("access_token")
   payload = decode_access_token(token)
   print(f"Token payload: {payload}")
   ```

### Issue 6: Template Not Found

**Symptoms**:
- "Template not found" errors
- 500 errors when rendering pages

**Solutions**:

1. **Check template path**:
   ```python
   # ✅ CORRECT - Relative to templates directory
   return templates.TemplateResponse(
       "admin/customers/list.html.jinja",
       context,
   )
   
   # ❌ WRONG - Absolute path
   return templates.TemplateResponse(
       "/app/templates/admin/customers/list.html.jinja",
       context,
   )
   ```

2. **Verify template exists**:
   ```bash
   # Check file exists
   ls app/templates/admin/customers/list.html.jinja
   ```

3. **Check template configuration**:
   ```python
   # app/main.py
   templates = Jinja2Templates(directory="app/templates")
   ```

---

## Common Patterns

### Pattern 1: List Page with Filtering

```python
@router.get("/customers")
async def list_customers(
    request: Request,
    current_superuser: CurrentSuperuser,
    db: DBSession,
    customer_repo: CustomerRepo,
    page: PageQuery = 1,
    page_size: PageSizeQuery = 50,
    search: SearchQuery = None,
    is_active: IsActiveQuery = None,
):
    """List customers with filtering."""
    # Check feature flag
    check_feature_flag("experimental_customers_page")
    
    # Get filtered customers
    customers = await customer_repo.get_multi(
        skip=(page - 1) * page_size,
        limit=page_size,
        search=search,
        is_active=is_active,
    )
    
    # Get total count for pagination
    total = await customer_repo.count(
        search=search,
        is_active=is_active,
    )
    
    # Build context
    context = get_admin_context(
        request,
        current_superuser,
        active_page="customers",
        customers=customers,
        total=total,
        page=page,
        page_size=page_size,
        pages=(total + page_size - 1) // page_size,
        search=search,
        is_active=is_active,
    )
    
    return templates.TemplateResponse(
        "admin/customers/list.html.jinja",
        context,
    )
```

### Pattern 2: Create Form (GET + POST)

```python
@router.get("/customers/new")
async def new_customer_form(
    request: Request,
    current_superuser: CurrentSuperuser,
):
    """Show customer creation form."""
    check_feature_flag("experimental_customers_page")
    
    context = get_admin_context(
        request,
        current_superuser,
        active_page="customers",
    )
    
    return templates.TemplateResponse(
        "admin/customers/form.html.jinja",
        context,
    )

@router.post("/customers")
async def create_customer(
    request: Request,
    current_superuser: CurrentSuperuser,
    db: DBSession,
    customer_repo: CustomerRepo,
    company_name: OptionalStrForm = None,
    email: RequiredStrForm = ...,
    # ... other form fields
):
    """Create customer from form."""
    check_feature_flag("experimental_customers_page")
    
    try:
        # Normalize optional fields
        company_name = FormDataProcessor.normalize_optional_string(company_name)
        
        # Create customer
        customer_in = CustomerCreate(
            company_name=company_name,
            email=email,
            # ...
        )
        customer = await customer_repo.create(customer_in)
        await db.commit()
        
        return build_redirect_response(
            url="/admin/customers",
            message="Customer created successfully",
        )
        
    except ValidationError as ve:
        errors = format_validation_errors(ve)
        context = get_admin_context(
            request,
            current_superuser,
            active_page="customers",
            validation_errors=errors,
            form_data={"company_name": company_name, "email": email},
        )
        return templates.TemplateResponse(
            "admin/customers/form.html.jinja",
            context,
            status_code=422,
        )
```

### Pattern 3: Detail Page with Related Data

```python
@router.get("/customers/{customer_id}")
async def view_customer(
    request: Request,
    customer_id: int,
    current_superuser: CurrentSuperuser,
    db: DBSession,
    customer_repo: CustomerRepo,
):
    """View customer details."""
    check_feature_flag("experimental_customers_page")
    
    # Get customer with related data
    customer = await customer_repo.get_with_relations(
        customer_id,
        load_configurations=True,
        load_quotes=True,
        load_orders=True,
    )
    
    if not customer:
        raise HTTPException(
            status_code=404,
            detail=f"Customer {customer_id} not found",
        )
    
    context = get_admin_context(
        request,
        current_superuser,
        active_page="customers",
        customer=customer,
        configurations=customer.configurations,
        quotes=customer.quotes,
        orders=customer.orders,
    )
    
    return templates.TemplateResponse(
        "admin/customers/detail.html.jinja",
        context,
    )
```

---

## Summary

### Key Takeaways

1. **Use Shared Utilities**: Leverage `get_admin_context()`, `build_redirect_response()`, etc.
2. **Consistent Error Handling**: Follow established patterns for validation, database, and unexpected errors
3. **Feature Flags**: Always check feature flags at the start of endpoints
4. **User-Friendly Messages**: Convert technical errors to user-friendly messages
5. **Preserve Form Data**: Always preserve form data on validation errors
6. **Logging**: Log unexpected errors for debugging

### Quick Reference

| Utility | Purpose | Usage |
|---------|---------|-------|
| `get_admin_context()` | Build template context | `context = get_admin_context(request, user, ...)` |
| `check_feature_flag()` | Verify feature enabled | `check_feature_flag("experimental_customers_page")` |
| `build_redirect_response()` | Create redirect with message | `return build_redirect_response(url, message)` |
| `format_validation_errors()` | Format Pydantic errors | `errors = format_validation_errors(ve)` |
| `FormDataProcessor` | Process form data | `FormDataProcessor.normalize_optional_string(value)` |

---

## Additional Resources

- [FastAPI Error Handling](https://fastapi.tiangolo.com/tutorial/handling-errors/)
- [Jinja2 Templates](https://jinja.palletsprojects.com/)
- [Pydantic Validation](https://docs.pydantic.dev/latest/concepts/validators/)
- [SQLAlchemy Error Handling](https://docs.sqlalchemy.org/en/20/core/exceptions.html)
