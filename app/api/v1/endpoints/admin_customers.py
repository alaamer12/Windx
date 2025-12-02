"""Admin customers endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Request, status
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import ValidationError
from sqlalchemy import func, or_, select

from app.api.admin_utils import (
    FormDataProcessor,
    build_redirect_response,
    check_feature_flag,
    format_validation_errors,
)
from app.api.deps import get_admin_context
from app.api.types import (
    CurrentSuperuser,
    CustomerRepo,
    DBSession,
    OptionalBoolForm,
    OptionalStrForm,
    PageQuery,
    SearchQuery,
)
from app.core.config import get_settings
from app.models.customer import Customer
from app.schemas.customer import CustomerCreate, CustomerUpdate
from app.schemas.responses import get_common_responses

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


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
            "content": {"text/html": {"example": "<html>...</html>"}},
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
    customer_repo: CustomerRepo,
    page: PageQuery = 1,
    search: SearchQuery = None,
    type: str | None = None,
    status_filter: str | None = None,
):
    """List all customers with filtering and pagination.

    Displays a paginated list of customers with optional filtering by
    customer type, active status, and search across multiple fields.

    Args:
        request: FastAPI request object
        current_superuser: Current authenticated superuser
        db: Database session
        customer_repo: Customer repository
        page: Page number (1-indexed)
        search: Search term for company name, contact person, or email
        type: Filter by customer type (residential, commercial, contractor)
        status_filter: Filter by status (active, inactive)

    Returns:
        HTMLResponse: Rendered customer list template
        RedirectResponse: Redirect to dashboard if feature is disabled
    """
    settings = get_settings()
    if not settings.windx.experimental_customers_page:
        return build_redirect_response(
            url="/api/v1/admin/dashboard",
            message="Customers module is currently disabled",
            message_type="error",
        )

    # Build query filters
    is_active = None
    if status_filter == "active":
        is_active = True
    elif status_filter == "inactive":
        is_active = False

    # Get filtered query
    query = customer_repo.get_filtered(is_active=is_active, customer_type=type)

    # Apply search if provided
    if search:
        search_term = f"%{search}%"
        query = query.where(
            or_(
                Customer.company_name.ilike(search_term),
                Customer.contact_person.ilike(search_term),
                Customer.email.ilike(search_term),
            )
        )

    # Pagination
    page_size = 20
    skip = (page - 1) * page_size

    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    total_count = await db.scalar(count_query) or 0
    total_pages = (total_count + page_size - 1) // page_size

    # Get page items
    result = await db.execute(query.offset(skip).limit(page_size))
    customers = result.scalars().all()

    return templates.TemplateResponse(
        request=request,
        name="admin/customers_list.html.jinja",
        context=get_admin_context(
            request,
            current_superuser,
            active_page="customers",
            customers=customers,
            page=page,
            total_pages=total_pages,
            search=search,
            type_filter=type,
            status_filter=status_filter,
        ),
    )


@router.get(
    "/new",
    response_class=HTMLResponse,
    summary="New Customer Form",
    description="Display form for creating a new customer",
    response_description="HTML page with customer creation form",
    operation_id="newCustomerForm",
    responses={
        200: {
            "description": "Successfully rendered customer form",
            "content": {"text/html": {"example": "<html>...</html>"}},
        },
        302: {
            "description": "Redirect if feature is disabled",
        },
        **get_common_responses(401, 403, 500),
    },
)
async def new_customer_form(
    request: Request,
    current_superuser: CurrentSuperuser,
):
    """Show create customer form.

    Displays an empty form for creating a new customer.
    Requires superuser authentication.

    Args:
        request: FastAPI request object
        current_superuser: Current authenticated superuser

    Returns:
        HTMLResponse: Rendered customer form template
        RedirectResponse: Redirect to dashboard if feature is disabled
    """
    settings = get_settings()
    if not settings.windx.experimental_customers_page:
        return build_redirect_response(
            url="/api/v1/admin/dashboard",
            message="Customers module is currently disabled",
            message_type="error",
        )

    return templates.TemplateResponse(
        request=request,
        name="admin/customer_form.html.jinja",
        context=get_admin_context(
            request,
            current_superuser,
            active_page="customers",
            action="create",
        ),
    )


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
            "content": {"text/html": {"example": "<html>...</html>"}},
        },
        **get_common_responses(401, 403, 404, 500),
    },
)
async def create_customer(
    request: Request,
    current_superuser: CurrentSuperuser,
    db: DBSession,
    customer_repo: CustomerRepo,
    company_name: OptionalStrForm = None,
    contact_person: OptionalStrForm = None,
    email: OptionalStrForm = None,
    phone: OptionalStrForm = None,
    customer_type: OptionalStrForm = None,
    tax_id: OptionalStrForm = None,
    payment_terms: OptionalStrForm = None,
    street: OptionalStrForm = None,
    city: OptionalStrForm = None,
    state: OptionalStrForm = None,
    zip_code: OptionalStrForm = None,
    country: OptionalStrForm = None,
    notes: OptionalStrForm = None,
    is_active: OptionalBoolForm = True,
):
    """Create new customer from form data.

    Validates form data, creates a new customer record, and redirects
    to the customer list on success or re-renders the form with errors.

    Args:
        request: FastAPI request object
        current_superuser: Current authenticated superuser
        db: Database session
        customer_repo: Customer repository
        company_name: Company name (optional for residential)
        contact_person: Primary contact person name
        email: Contact email address
        phone: Contact phone number
        customer_type: Type (residential, commercial, contractor)
        tax_id: Tax identification number
        payment_terms: Payment terms (net_30, net_15, etc.)
        street: Street address
        city: City
        state: State/province
        zip_code: ZIP/postal code
        country: Country
        notes: Internal notes
        is_active: Active status (default True)

    Returns:
        RedirectResponse: Redirect to customer list on success
        HTMLResponse: Re-rendered form with validation errors on failure
    """
    check_feature_flag("experimental_customers_page")

    # Build address dict
    address = {}
    if street:
        address["street"] = street
    if city:
        address["city"] = city
    if state:
        address["state"] = state
    if zip_code:
        address["zip"] = zip_code
    if country:
        address["country"] = country

    try:
        customer_in = CustomerCreate(
            company_name=FormDataProcessor.normalize_optional_string(company_name),
            contact_person=FormDataProcessor.normalize_optional_string(contact_person),
            email=FormDataProcessor.normalize_optional_string(email),
            phone=FormDataProcessor.normalize_optional_string(phone),
            customer_type=customer_type,
            tax_id=FormDataProcessor.normalize_optional_string(tax_id),
            payment_terms=FormDataProcessor.normalize_optional_string(payment_terms),
            address=address if address else None,
            notes=FormDataProcessor.normalize_optional_string(notes),
        )

        # Create customer (this commits internally)
        customer = await customer_repo.create(customer_in)

        # Update is_active if needed (customer_repo.create already committed)
        if not is_active:
            customer.is_active = is_active
            db.add(customer)
            await db.commit()

        return build_redirect_response(
            url="/api/v1/admin/customers",
            message="Customer created successfully",
            message_type="success",
        )

    except ValidationError as ve:
        validation_errors = format_validation_errors(ve)
        return templates.TemplateResponse(
            request=request,
            name="admin/customer_form.html.jinja",
            context=get_admin_context(
                request,
                current_superuser,
                active_page="customers",
                action="create",
                validation_errors=validation_errors,
                form_data={
                    "company_name": company_name,
                    "contact_person": contact_person,
                    "email": email,
                    "phone": phone,
                    "customer_type": customer_type,
                    "tax_id": tax_id,
                    "payment_terms": payment_terms,
                    "address": address,
                    "notes": notes,
                    "is_active": is_active,
                },
            ),
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
        )

    except Exception as e:
        # Rollback any pending transaction
        try:
            await db.rollback()
        except Exception:
            pass  # Ignore rollback errors

        # Check for duplicate email error
        error_msg = str(e)
        if "ix_customers_email" in error_msg or "duplicate key" in error_msg.lower():
            error_msg = f"A customer with email '{email}' already exists"
            # For duplicate email, redirect instead of rendering template
            # to avoid session issues after rollback
            return build_redirect_response(
                url="/api/v1/admin/customers/new",
                message=error_msg,
                message_type="error",
            )

        return templates.TemplateResponse(
            request=request,
            name="admin/customer_form.html.jinja",
            context=get_admin_context(
                request,
                current_superuser,
                active_page="customers",
                action="create",
                error=error_msg,
                form_data={
                    "company_name": company_name,
                    "contact_person": contact_person,
                    "email": email,
                    "phone": phone,
                    "customer_type": customer_type,
                    "tax_id": tax_id,
                    "payment_terms": payment_terms,
                    "address": address,
                    "notes": notes,
                    "is_active": is_active,
                },
            ),
            status_code=status.HTTP_400_BAD_REQUEST,
        )


@router.get(
    "/{id}",
    response_class=HTMLResponse,
    summary="View Customer",
    description="Display detailed customer information",
    response_description="HTML page with customer details",
    operation_id="viewCustomer",
    responses={
        200: {
            "description": "Successfully retrieved customer details",
            "content": {"text/html": {"example": "<html>...</html>"}},
        },
        302: {
            "description": "Redirect if customer not found or feature disabled",
        },
        **get_common_responses(401, 403, 404, 500),
    },
)
async def view_customer(
    request: Request,
    id: int,
    current_superuser: CurrentSuperuser,
    customer_repo: CustomerRepo,
):
    """View customer details.

    Displays complete customer information including configurations,
    quotes, and orders.

    Args:
        request: FastAPI request object
        id: Customer ID
        current_superuser: Current authenticated superuser
        customer_repo: Customer repository

    Returns:
        HTMLResponse: Rendered customer detail template
        RedirectResponse: Redirect to customer list if not found
    """
    check_feature_flag("experimental_customers_page")

    customer = await customer_repo.get_with_full_details(id)

    if not customer:
        return build_redirect_response(
            url="/api/v1/admin/customers",
            message="Customer not found",
            message_type="error",
        )

    return templates.TemplateResponse(
        request=request,
        name="admin/customer_detail.html.jinja",
        context=get_admin_context(
            request,
            current_superuser,
            active_page="customers",
            customer=customer,
        ),
    )


@router.get(
    "/{id}/edit",
    response_class=HTMLResponse,
    summary="Edit Customer Form",
    description="Display form for editing an existing customer",
    response_description="HTML page with pre-filled customer form",
    operation_id="editCustomerForm",
    responses={
        200: {
            "description": "Successfully rendered customer edit form",
            "content": {"text/html": {"example": "<html>...</html>"}},
        },
        302: {
            "description": "Redirect if customer not found or feature disabled",
        },
        **get_common_responses(401, 403, 404, 500),
    },
)
async def edit_customer_form(
    request: Request,
    id: int,
    current_superuser: CurrentSuperuser,
    customer_repo: CustomerRepo,
):
    """Show edit customer form.

    Displays a form pre-filled with existing customer data for editing.

    Args:
        request: FastAPI request object
        id: Customer ID
        current_superuser: Current authenticated superuser
        customer_repo: Customer repository

    Returns:
        HTMLResponse: Rendered customer form template with existing data
        RedirectResponse: Redirect to customer list if not found
    """
    check_feature_flag("experimental_customers_page")

    customer = await customer_repo.get(id)

    if not customer:
        return build_redirect_response(
            url="/api/v1/admin/customers",
            message="Customer not found",
            message_type="error",
        )

    return templates.TemplateResponse(
        request=request,
        name="admin/customer_form.html.jinja",
        context=get_admin_context(
            request,
            current_superuser,
            active_page="customers",
            action="edit",
            customer=customer,
        ),
    )


@router.post(
    "/{id}/edit",
    response_class=HTMLResponse,
    summary="Update Customer",
    description="Update an existing customer from form submission",
    response_description="Redirect to customer detail or form with errors",
    operation_id="updateCustomer",
    responses={
        302: {
            "description": "Redirect to customer detail on success",
        },
        400: {
            "description": "Validation error, re-render form with errors",
            "content": {"text/html": {"example": "<html>...</html>"}},
        },
        **get_common_responses(401, 403, 404, 500),
    },
)
async def update_customer(
    request: Request,
    id: int,
    current_superuser: CurrentSuperuser,
    db: DBSession,
    customer_repo: CustomerRepo,
    company_name: OptionalStrForm = None,
    contact_person: OptionalStrForm = None,
    email: OptionalStrForm = None,
    phone: OptionalStrForm = None,
    customer_type: OptionalStrForm = None,
    tax_id: OptionalStrForm = None,
    payment_terms: OptionalStrForm = None,
    street: OptionalStrForm = None,
    city: OptionalStrForm = None,
    state: OptionalStrForm = None,
    zip_code: OptionalStrForm = None,
    country: OptionalStrForm = None,
    notes: OptionalStrForm = None,
    is_active: OptionalBoolForm = False,  # Checkbox sends nothing if unchecked
):
    """Update customer from form data.

    Validates form data, updates the customer record, and redirects
    to the customer detail page on success or re-renders the form with errors.

    Args:
        request: FastAPI request object
        id: Customer ID
        current_superuser: Current authenticated superuser
        db: Database session
        customer_repo: Customer repository
        company_name: Company name (optional for residential)
        contact_person: Primary contact person name
        email: Contact email address
        phone: Contact phone number
        customer_type: Type (residential, commercial, contractor)
        tax_id: Tax identification number
        payment_terms: Payment terms (net_30, net_15, etc.)
        street: Street address
        city: City
        state: State/province
        zip_code: ZIP/postal code
        country: Country
        notes: Internal notes
        is_active: Active status

    Returns:
        RedirectResponse: Redirect to customer detail on success
        HTMLResponse: Re-rendered form with validation errors on failure
    """
    check_feature_flag("experimental_customers_page")

    customer = await customer_repo.get(id)

    if not customer:
        return build_redirect_response(
            url="/api/v1/admin/customers",
            message="Customer not found",
            message_type="error",
        )

    # Build address dict
    address = {}
    if street:
        address["street"] = street
    if city:
        address["city"] = city
    if state:
        address["state"] = state
    if zip_code:
        address["zip"] = zip_code
    if country:
        address["country"] = country

    try:
        customer_in = CustomerUpdate(
            company_name=FormDataProcessor.normalize_optional_string(company_name),
            contact_person=FormDataProcessor.normalize_optional_string(contact_person),
            email=FormDataProcessor.normalize_optional_string(email),
            phone=FormDataProcessor.normalize_optional_string(phone),
            customer_type=customer_type,
            tax_id=FormDataProcessor.normalize_optional_string(tax_id),
            payment_terms=FormDataProcessor.normalize_optional_string(payment_terms),
            address=address if address else None,
            notes=FormDataProcessor.normalize_optional_string(notes),
            is_active=is_active,
        )

        await customer_repo.update(customer, customer_in)
        await db.commit()

        return build_redirect_response(
            url=f"/api/v1/admin/customers/{id}",
            message="Customer updated successfully",
            message_type="success",
        )

    except ValidationError as ve:
        validation_errors = format_validation_errors(ve)
        return templates.TemplateResponse(
            request=request,
            name="admin/customer_form.html.jinja",
            context=get_admin_context(
                request,
                current_superuser,
                active_page="customers",
                action="edit",
                customer=customer,
                validation_errors=validation_errors,
            ),
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
        )

    except Exception as e:
        return templates.TemplateResponse(
            request=request,
            name="admin/customer_form.html.jinja",
            context=get_admin_context(
                request,
                current_superuser,
                active_page="customers",
                action="edit",
                customer=customer,
                error=str(e),
            ),
            status_code=status.HTTP_400_BAD_REQUEST,
        )


@router.post(
    "/{id}/delete",
    response_class=HTMLResponse,
    summary="Delete Customer",
    description="Delete a customer record",
    response_description="Redirect to customer list with success or error message",
    operation_id="deleteCustomer",
    responses={
        302: {
            "description": "Redirect to customer list after deletion attempt",
        },
        **get_common_responses(401, 403, 404, 500),
    },
)
async def delete_customer(
    request: Request,
    id: int,
    current_superuser: CurrentSuperuser,
    db: DBSession,
    customer_repo: CustomerRepo,
):
    """Delete customer.

    Removes a customer record from the database. This is a permanent
    deletion and cannot be undone.

    Args:
        request: FastAPI request object
        id: Customer ID
        current_superuser: Current authenticated superuser
        db: Database session
        customer_repo: Customer repository

    Returns:
        RedirectResponse: Redirect to customer list with success or error message
    """
    check_feature_flag("experimental_customers_page")

    customer = await customer_repo.get(id)

    if not customer:
        return build_redirect_response(
            url="/api/v1/admin/customers",
            message="Customer not found",
            message_type="error",
        )

    try:
        # Note: delete() method commits internally
        await customer_repo.delete(id)

        return build_redirect_response(
            url="/api/v1/admin/customers",
            message="Customer deleted successfully",
            message_type="success",
        )

    except Exception as e:
        await db.rollback()
        return build_redirect_response(
            url="/api/v1/admin/customers",
            message=f"Error deleting customer: {str(e)}",
            message_type="error",
        )
