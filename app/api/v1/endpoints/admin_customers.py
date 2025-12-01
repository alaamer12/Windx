"""Admin customers endpoints."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Form, HTTPException, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_active_superuser, get_db
from app.core.config import get_settings
from app.models.user import User
from app.repositories.customer import CustomerRepository
from app.schemas.customer import CustomerCreate, CustomerUpdate

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

CurrentSuperuser = Annotated[User, Depends(get_current_active_superuser)]
DB = Annotated[AsyncSession, Depends(get_db)]


def get_admin_context(
    request: Request, current_user: User, active_page: str = "customers", **kwargs
):
    """Get common admin template context with feature flags."""
    settings = get_settings()
    context = {
        "request": request,
        "current_user": current_user,
        "active_page": active_page,
        "enable_customers": settings.windx.experimental_customers_page,
        "enable_orders": settings.windx.experimental_orders_page,
    }
    context.update(kwargs)
    return context


async def check_feature_flag():
    """Check if customers page feature flag is enabled."""
    settings = get_settings()
    if not settings.windx.experimental_customers_page:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Customers module is currently disabled"
        )


@router.get("", response_class=HTMLResponse)
async def list_customers(
    request: Request,
    current_superuser: CurrentSuperuser,
    db: DB,
    page: int = 1,
    search: str | None = None,
    type: str | None = None,
    status: str | None = None,
):
    """List all customers with filtering and pagination."""
    settings = get_settings()
    if not settings.windx.experimental_customers_page:
        return RedirectResponse(
            url="/api/v1/admin/dashboard?error=Customers module is currently disabled",
            status_code=status.HTTP_302_FOUND,
        )

    repo = CustomerRepository(db)

    # Build query filters
    is_active = None
    if status == "active":
        is_active = True
    elif status == "inactive":
        is_active = False

    # Get filtered query
    query = repo.get_filtered(is_active=is_active, customer_type=type)

    # Apply search if provided
    if search:
        from sqlalchemy import or_

        from app.models.customer import Customer

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

    # Execute query with pagination
    from sqlalchemy import func, select

    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    total_count = await db.scalar(count_query) or 0
    total_pages = (total_count + page_size - 1) // page_size

    # Get page items
    result = await db.execute(query.offset(skip).limit(page_size))
    customers = result.scalars().all()

    return templates.TemplateResponse(
        "admin/customers_list.html.jinja",
        get_admin_context(
            request,
            current_superuser,
            customers=customers,
            page=page,
            total_pages=total_pages,
            search=search,
            type_filter=type,
            status_filter=status,
        ),
    )


@router.get("/new", response_class=HTMLResponse)
async def new_customer_form(
    request: Request,
    current_superuser: CurrentSuperuser,
):
    """Show create customer form."""
    settings = get_settings()
    if not settings.windx.experimental_customers_page:
        return RedirectResponse(
            url="/api/v1/admin/dashboard?error=Customers module is currently disabled",
            status_code=status.HTTP_302_FOUND,
        )

    return templates.TemplateResponse(
        "admin/customer_form.html.jinja",
        get_admin_context(
            request,
            current_superuser,
            action="create",
        ),
    )


@router.post("", response_class=HTMLResponse)
async def create_customer(
    request: Request,
    current_superuser: CurrentSuperuser,
    db: DB,
    company_name: str | None = Form(None),
    contact_person: str | None = Form(None),
    email: str | None = Form(None),
    phone: str | None = Form(None),
    customer_type: str | None = Form(None),
    tax_id: str | None = Form(None),
    payment_terms: str | None = Form(None),
    street: str | None = Form(None),
    city: str | None = Form(None),
    state: str | None = Form(None),
    zip_code: str | None = Form(None),
    country: str | None = Form(None),
    notes: str | None = Form(None),
    is_active: bool = Form(True),
):
    """Create new customer."""
    await check_feature_flag()
    repo = CustomerRepository(db)

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
            company_name=company_name,
            contact_person=contact_person,
            email=email if email else None,
            phone=phone,
            customer_type=customer_type,
            tax_id=tax_id,
            payment_terms=payment_terms,
            address=address if address else None,
            notes=notes,
        )

        # Manually set is_active since it's not in CustomerCreate
        customer = await repo.create(customer_in)
        customer.is_active = is_active
        await db.commit()

        return RedirectResponse(
            url="/api/v1/admin/customers?success=Customer created successfully",
            status_code=status.HTTP_302_FOUND,
        )
    except Exception as e:
        return templates.TemplateResponse(
            "admin/customer_form.html.jinja",
            get_admin_context(
                request,
                current_superuser,
                action="create",
                error=str(e),
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


@router.get("/{id}", response_class=HTMLResponse)
async def view_customer(
    request: Request,
    id: int,
    current_superuser: CurrentSuperuser,
    db: DB,
):
    """View customer details."""
    await check_feature_flag()
    repo = CustomerRepository(db)
    customer = await repo.get_with_full_details(id)

    if not customer:
        return RedirectResponse(
            url="/api/v1/admin/customers?error=Customer not found",
            status_code=status.HTTP_302_FOUND,
        )

    return templates.TemplateResponse(
        "admin/customer_detail.html.jinja",
        get_admin_context(
            request,
            current_superuser,
            customer=customer,
        ),
    )


@router.get("/{id}/edit", response_class=HTMLResponse)
async def edit_customer_form(
    request: Request,
    id: int,
    current_superuser: CurrentSuperuser,
    db: DB,
):
    """Show edit customer form."""
    await check_feature_flag()
    repo = CustomerRepository(db)
    customer = await repo.get(id)

    if not customer:
        return RedirectResponse(
            url="/api/v1/admin/customers?error=Customer not found",
            status_code=status.HTTP_302_FOUND,
        )

    return templates.TemplateResponse(
        "admin/customer_form.html.jinja",
        get_admin_context(
            request,
            current_superuser,
            action="edit",
            customer=customer,
        ),
    )


@router.post("/{id}/edit", response_class=HTMLResponse)
async def update_customer(
    request: Request,
    id: int,
    current_superuser: CurrentSuperuser,
    db: DB,
    company_name: str | None = Form(None),
    contact_person: str | None = Form(None),
    email: str | None = Form(None),
    phone: str | None = Form(None),
    customer_type: str | None = Form(None),
    tax_id: str | None = Form(None),
    payment_terms: str | None = Form(None),
    street: str | None = Form(None),
    city: str | None = Form(None),
    state: str | None = Form(None),
    zip_code: str | None = Form(None),
    country: str | None = Form(None),
    notes: str | None = Form(None),
    is_active: bool = Form(False),  # Checkbox sends nothing if unchecked
):
    """Update customer."""
    await check_feature_flag()
    repo = CustomerRepository(db)
    customer = await repo.get(id)

    if not customer:
        return RedirectResponse(
            url="/api/v1/admin/customers?error=Customer not found",
            status_code=status.HTTP_302_FOUND,
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
            company_name=company_name,
            contact_person=contact_person,
            email=email if email else None,
            phone=phone,
            customer_type=customer_type,
            tax_id=tax_id,
            payment_terms=payment_terms,
            address=address if address else None,
            notes=notes,
            is_active=is_active,
        )

        await repo.update(customer, customer_in)

        return RedirectResponse(
            url=f"/api/v1/admin/customers/{id}?success=Customer updated successfully",
            status_code=status.HTTP_302_FOUND,
        )
    except Exception as e:
        return templates.TemplateResponse(
            "admin/customer_form.html.jinja",
            get_admin_context(
                request,
                current_superuser,
                action="edit",
                customer=customer,
                error=str(e),
            ),
            status_code=status.HTTP_400_BAD_REQUEST,
        )


@router.post("/{id}/delete", response_class=HTMLResponse)
async def delete_customer(
    request: Request,
    id: int,
    current_superuser: CurrentSuperuser,
    db: DB,
):
    """Delete customer."""
    await check_feature_flag()
    repo = CustomerRepository(db)
    customer = await repo.get(id)

    if not customer:
        return RedirectResponse(
            url="/api/v1/admin/customers?error=Customer not found",
            status_code=status.HTTP_302_FOUND,
        )

    try:
        await repo.remove(id)
        return RedirectResponse(
            url="/api/v1/admin/customers?success=Customer deleted successfully",
            status_code=status.HTTP_302_FOUND,
        )
    except Exception as e:
        return RedirectResponse(
            url=f"/api/v1/admin/customers?error=Error deleting customer: {str(e)}",
            status_code=status.HTTP_302_FOUND,
        )
