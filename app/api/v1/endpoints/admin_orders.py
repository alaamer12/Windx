"""Admin Orders Management Endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import func, or_, select
from sqlalchemy.orm import selectinload

from app.api.admin_utils import build_redirect_response, check_feature_flag
from app.api.deps import get_admin_context
from app.api.types import (
    CurrentSuperuser,
    DBSession,
    OrderRepo,
    PageQuery,
    RequiredStrForm,
    SearchQuery,
)
from app.core.config import get_settings
from app.models.customer import Customer
from app.models.order import Order
from app.schemas.order import OrderUpdate
from app.schemas.responses import get_common_responses

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

# Valid order status values
VALID_ORDER_STATUSES = {"confirmed", "production", "shipped", "installed"}


@router.get(
    "",
    response_class=HTMLResponse,
    summary="List Orders",
    description="List all orders with optional filtering by status and search term. Supports pagination.",
    response_description="HTML page with order list",
    operation_id="listOrders",
    responses={
        200: {
            "description": "Successfully retrieved orders page",
            "content": {"text/html": {"example": "<html>...</html>"}},
        },
        302: {
            "description": "Redirect if feature is disabled",
        },
        **get_common_responses(401, 403, 500),
    },
)
async def list_orders(
    request: Request,
    current_superuser: CurrentSuperuser,
    db: DBSession,
    page: PageQuery = 1,
    search: SearchQuery = None,
    status_filter: str | None = None,
):
    """List all orders with filtering and pagination.

    Displays a paginated list of orders with optional filtering by
    order status and search across order number and customer fields.

    Args:
        request: FastAPI request object
        current_superuser: Current authenticated superuser
        db: Database session
        page: Page number (1-indexed)
        search: Search term for order number, customer name, or email
        status_filter: Filter by order status (confirmed, production, shipped, installed)

    Returns:
        HTMLResponse: Rendered order list template
        RedirectResponse: Redirect to dashboard if feature is disabled
    """
    settings = get_settings()
    if not settings.windx.experimental_orders_page:
        return build_redirect_response(
            url="/api/v1/admin/dashboard",
            message="Orders module is currently disabled",
            message_type="error",
        )

    # Build query with customer relationship and items
    query = (
        select(Order)
        .options(selectinload(Order.quote), selectinload(Order.items))
        .order_by(Order.order_date.desc())
    )

    # Apply status filter
    if status_filter and status_filter in VALID_ORDER_STATUSES:
        query = query.where(Order.status == status_filter)

    # Apply search if provided
    if search:
        search_term = f"%{search}%"
        # Join with quote to access customer
        query = (
            query.join(Order.quote)
            .join(Customer, Customer.id == Order.quote.property.mapper.class_.customer_id)
            .where(
                or_(
                    Order.order_number.ilike(search_term),
                    Customer.company_name.ilike(search_term),
                    Customer.contact_person.ilike(search_term),
                    Customer.email.ilike(search_term),
                )
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
    orders = result.scalars().all()

    return templates.TemplateResponse(
        request=request,
        name="admin/orders_list.html.jinja",
        context=get_admin_context(
            request,
            current_superuser,
            active_page="orders",
            orders=orders,
            page=page,
            total_pages=total_pages,
            search=search,
            status_filter=status_filter,
            valid_statuses=VALID_ORDER_STATUSES,
        ),
    )


@router.get(
    "/{id}",
    response_class=HTMLResponse,
    summary="View Order",
    description="Display detailed order information including customer, items, and quote",
    response_description="HTML page with order details",
    operation_id="viewOrder",
    responses={
        200: {
            "description": "Successfully retrieved order details",
            "content": {"text/html": {"example": "<html>...</html>"}},
        },
        302: {
            "description": "Redirect if order not found or feature disabled",
        },
        **get_common_responses(401, 403, 404, 500),
    },
)
async def view_order(
    request: Request,
    id: int,
    current_superuser: CurrentSuperuser,
    order_repo: OrderRepo,
):
    """View order details.

    Displays complete order information including customer details,
    order items, quote information, and status.

    Args:
        request: FastAPI request object
        id: Order ID
        current_superuser: Current authenticated superuser
        order_repo: Order repository

    Returns:
        HTMLResponse: Rendered order detail template
        RedirectResponse: Redirect to order list if not found
    """
    check_feature_flag("experimental_orders_page")

    order = await order_repo.get_with_full_details(id)

    if not order:
        return build_redirect_response(
            url="/api/v1/admin/orders",
            message="Order not found",
            message_type="error",
        )

    return templates.TemplateResponse(
        request=request,
        name="admin/order_detail.html.jinja",
        context=get_admin_context(
            request,
            current_superuser,
            active_page="orders",
            order=order,
            valid_statuses=VALID_ORDER_STATUSES,
        ),
    )


@router.post(
    "/{id}/status",
    response_class=HTMLResponse,
    summary="Update Order Status",
    description="Update the status of an order (confirmed, production, shipped, installed)",
    response_description="Redirect to order detail with success or error message",
    operation_id="updateOrderStatus",
    responses={
        302: {
            "description": "Redirect to order detail after status update attempt",
        },
        **get_common_responses(401, 403, 404, 500),
    },
)
async def update_order_status(
    request: Request,
    id: int,
    current_superuser: CurrentSuperuser,
    db: DBSession,
    order_repo: OrderRepo,
    new_status: RequiredStrForm = ...,
):
    """Update order status.

    Updates the order status to a new value. Validates that the status
    is one of the allowed values (confirmed, production, shipped, installed).

    Args:
        request: FastAPI request object
        id: Order ID
        current_superuser: Current authenticated superuser
        db: Database session
        order_repo: Order repository
        new_status: New status value from form

    Returns:
        RedirectResponse: Redirect to order detail with success or error message

    Status Progression:
        confirmed → production → shipped → installed
    """
    check_feature_flag("experimental_orders_page")

    order = await order_repo.get(id)

    if not order:
        return build_redirect_response(
            url="/api/v1/admin/orders",
            message="Order not found",
            message_type="error",
        )

    # Validate status
    if new_status not in VALID_ORDER_STATUSES:
        return build_redirect_response(
            url=f"/api/v1/admin/orders/{id}",
            message=f"Invalid status value. Must be one of: {', '.join(VALID_ORDER_STATUSES)}",
            message_type="error",
        )

    try:
        # Update order status
        order_update = OrderUpdate(status=new_status)
        await order_repo.update(order, order_update)
        await db.commit()

        return build_redirect_response(
            url=f"/api/v1/admin/orders/{id}",
            message=f"Order status updated to {new_status}",
            message_type="success",
        )

    except Exception as e:
        return build_redirect_response(
            url=f"/api/v1/admin/orders/{id}",
            message=f"Error updating order status: {str(e)}",
            message_type="error",
        )
