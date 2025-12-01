"""Admin Orders Management Endpoints."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Form, HTTPException, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from app.api.deps import get_current_active_superuser, get_db
from app.api.types import DBSession
from app.core.config import get_settings
from app.models.user import User
from app.repositories.order import OrderRepository
from app.schemas.order import OrderUpdate

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

CurrentActiveSuperuser = Annotated[User, Depends(get_current_active_superuser)]
DB = Annotated[DBSession, Depends(get_db)]


def get_admin_context(request: Request, current_user: User, active_page: str = "orders", **kwargs):
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
    """Check if orders page feature flag is enabled."""
    settings = get_settings()
    if not settings.windx.experimental_orders_page:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Orders module is currently disabled"
        )


@router.get("", response_class=HTMLResponse)
async def list_orders(
    request: Request,
    current_superuser: CurrentActiveSuperuser,
    db: DB,
    page: int = 1,
    search: str | None = None,
    status: str | None = None,
):
    """List all orders with filtering and pagination."""
    settings = get_settings()
    if not settings.windx.experimental_orders_page:
        return RedirectResponse(
            url="/api/v1/admin/dashboard?error=Orders module is currently disabled",
            status_code=status.HTTP_302_FOUND,
        )

    OrderRepository(db)

    # Build query
    # Note: OrderRepository might need a custom filter method similar to CustomerRepository
    # For now, we'll use get_multi or implement a custom query here

    from sqlalchemy import or_, select
    from sqlalchemy.orm import selectinload

    from app.models.customer import Customer
    from app.models.order import Order

    query = select(Order).options(selectinload(Order.customer)).order_by(Order.order_date.desc())

    if status:
        query = query.where(Order.status == status)

    if search:
        search_term = f"%{search}%"
        query = query.join(Order.customer, isouter=True).where(
            or_(
                Order.order_number.ilike(search_term),
                Customer.company_name.ilike(search_term),
                Customer.contact_person.ilike(search_term),
                Customer.email.ilike(search_term),
            )
        )

    # Pagination
    page_size = 20
    skip = (page - 1) * page_size

    # Get total count
    from sqlalchemy import func

    count_query = select(func.count()).select_from(query.subquery())
    total_count = await db.scalar(count_query) or 0
    total_pages = (total_count + page_size - 1) // page_size

    # Get page items
    result = await db.execute(query.offset(skip).limit(page_size))
    orders = result.scalars().all()

    return templates.TemplateResponse(
        "admin/orders_list.html.jinja",
        get_admin_context(
            request,
            current_superuser,
            orders=orders,
            page=page,
            total_pages=total_pages,
            search=search,
            status_filter=status,
        ),
    )


@router.get("/{id}", response_class=HTMLResponse)
async def view_order(
    request: Request,
    id: int,
    current_superuser: CurrentActiveSuperuser,
    db: DB,
):
    """View order details."""
    await check_feature_flag()
    repo = OrderRepository(db)

    # Use get_with_full_details if available, or manually load
    # Checking repo... it has get_with_full_details
    order = await repo.get_with_full_details(id)

    if not order:
        return RedirectResponse(
            url="/api/v1/admin/orders?error=Order not found", status_code=status.HTTP_302_FOUND
        )

    return templates.TemplateResponse(
        "admin/order_detail.html.jinja",
        get_admin_context(
            request,
            current_superuser,
            order=order,
        ),
    )


@router.post("/{id}/status", response_class=HTMLResponse)
async def update_order_status(
    request: Request,
    id: int,
    current_superuser: CurrentActiveSuperuser,
    db: DB,
    status: str = Form(...),
):
    """Update order status."""
    await check_feature_flag()
    repo = OrderRepository(db)
    order = await repo.get(id)

    if not order:
        return RedirectResponse(
            url="/api/v1/admin/orders?error=Order not found", status_code=status.HTTP_302_FOUND
        )

    try:
        # Validate status
        new_status = OrderStatus(status)

        # Update
        order_update = OrderUpdate(status=new_status)
        await repo.update(order, order_update)

        return RedirectResponse(
            url=f"/api/v1/admin/orders/{id}?success=Order status updated to {status}",
            status_code=status.HTTP_302_FOUND,
        )
    except ValueError:
        return RedirectResponse(
            url=f"/api/v1/admin/orders/{id}?error=Invalid status value",
            status_code=status.HTTP_302_FOUND,
        )
    except Exception as e:
        return RedirectResponse(
            url=f"/api/v1/admin/orders/{id}?error={str(e)}", status_code=status.HTTP_302_FOUND
        )
