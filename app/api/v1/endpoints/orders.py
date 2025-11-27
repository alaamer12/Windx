"""Order management endpoints.

This module provides REST API endpoints for managing orders.

Public Variables:
    router: FastAPI router for order endpoints

Features:
    - List user's orders with pagination
    - Get order with items
    - Create order from quote
    - Authorization checks (users see only their own)
    - OpenAPI documentation with examples
"""

from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from pydantic import PositiveInt

from app.api.types import CurrentUser, DBSession
from app.core.pagination import Page, PaginationParams, create_pagination_params
from app.models.order import Order
from app.schemas.order import Order as OrderSchema
from app.schemas.order import OrderCreate, OrderWithItems
from app.schemas.responses import get_common_responses

__all__ = ["router"]

router = APIRouter(
    tags=["Orders"],
    responses=get_common_responses(401, 500),
)


@router.get(
    "/",
    response_model=Page[OrderSchema],
    summary="List Orders",
    description="List user's orders with pagination. Superusers can see all orders.",
    response_description="Paginated list of orders",
    operation_id="listOrders",
    responses={
        200: {
            "description": "Successfully retrieved orders",
        },
        **get_common_responses(401, 500),
    },
)
async def list_orders(
    current_user: CurrentUser,
    params: Annotated[PaginationParams, Depends(create_pagination_params)],
    db: DBSession,
    status_filter: Annotated[
        str | None,
        Query(alias="status", description="Filter by status (confirmed, production, shipped, installed)"),
    ] = None,
) -> Page[Order]:
    """List user's orders with filtering.

    Regular users see only their own orders.
    Superusers can see all orders.

    Args:
        current_user (User): Current authenticated user
        params (PaginationParams): Pagination parameters
        db (AsyncSession): Database session
        status_filter (str | None): Filter by status

    Returns:
        Page[Order]: Paginated list of orders

    Example:
        GET /api/v1/orders?status=production
    """
    from app.core.pagination import paginate
    from app.repositories.order import OrderRepository
    from app.repositories.quote import QuoteRepository

    order_repo = OrderRepository(db)
    quote_repo = QuoteRepository(db)

    # Build filtered query with authorization
    if current_user.is_superuser:
        query = order_repo.get_filtered(status=status_filter)
    else:
        # Get user's quotes to filter orders
        user_quote_ids = await quote_repo.get_user_quote_ids(current_user.id)
        query = order_repo.get_filtered_by_quotes(
            quote_ids=user_quote_ids,
            status=status_filter,
        )

    return await paginate(db, query, params)


@router.get(
    "/{order_id}",
    response_model=OrderWithItems,
    summary="Get Order",
    description="Get an order with all its items",
    response_description="Order with items",
    operation_id="getOrder",
    responses={
        200: {
            "description": "Successfully retrieved order",
        },
        403: {
            "description": "Not authorized to access this order",
        },
        404: {
            "description": "Order not found",
        },
        **get_common_responses(401, 500),
    },
)
async def get_order(
    order_id: PositiveInt,
    current_user: CurrentUser,
    db: DBSession,
) -> Order:
    """Get order with items.

    Users can only access their own orders unless they are superusers.

    Args:
        order_id (PositiveInt): Order ID
        current_user (User): Current authenticated user
        db (AsyncSession): Database session

    Returns:
        Order: Order with items

    Raises:
        NotFoundException: If order not found
        AuthorizationException: If user lacks permission
    """
    from app.core.exceptions import AuthorizationException, NotFoundException
    from app.repositories.order import OrderRepository
    from app.repositories.quote import QuoteRepository

    order_repo = OrderRepository(db)
    quote_repo = QuoteRepository(db)

    order = await order_repo.get_with_items(order_id)
    if not order:
        raise NotFoundException("Order not found")

    # Authorization check
    if not current_user.is_superuser:
        quote = await quote_repo.get(order.quote_id)
        if not quote or quote.customer_id != current_user.id:
            raise AuthorizationException(
                "You do not have permission to access this order"
            )

    return order


@router.post(
    "/",
    response_model=OrderSchema,
    status_code=status.HTTP_201_CREATED,
    summary="Create Order",
    description="Create an order from a quote",
    response_description="Created order",
    operation_id="createOrder",
    responses={
        201: {
            "description": "Order successfully created",
        },
        403: {
            "description": "Not authorized to create order for this quote",
        },
        404: {
            "description": "Quote not found",
        },
        **get_common_responses(401, 422, 500),
    },
)
async def create_order(
    order_in: OrderCreate,
    current_user: CurrentUser,
    db: DBSession,
) -> Order:
    """Create an order from a quote.

    Users can only create orders for their own quotes unless they are superusers.

    Args:
        order_in (OrderCreate): Order creation data
        current_user (User): Current authenticated user
        db (AsyncSession): Database session

    Returns:
        Order: Created order

    Raises:
        NotFoundException: If quote not found
        AuthorizationException: If user lacks permission

    Example:
        POST /api/v1/orders
        {
            "quote_id": 1,
            "required_date": "2024-02-15",
            "special_instructions": "Call before delivery",
            "installation_address": {
                "street": "123 Main St",
                "city": "Springfield",
                "state": "IL",
                "zip": "62701"
            }
        }
    """
    from app.core.exceptions import AuthorizationException, NotFoundException
    from app.repositories.order import OrderRepository
    from app.repositories.quote import QuoteRepository

    order_repo = OrderRepository(db)
    quote_repo = QuoteRepository(db)

    # Get quote and check authorization
    quote = await quote_repo.get(order_in.quote_id)
    if not quote:
        raise NotFoundException("Quote not found")

    # Authorization check
    if not current_user.is_superuser and quote.customer_id != current_user.id:
        raise AuthorizationException(
            "You do not have permission to create an order for this quote"
        )

    # Create order
    order = await order_repo.create(order_in)
    await db.commit()
    await db.refresh(order)

    return order
