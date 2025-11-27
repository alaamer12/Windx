"""Repository for Order operations.

This module provides the repository implementation for Order
model with custom query methods and eager loading support.

Public Classes:
    OrderRepository: Repository for order operations

Features:
    - Standard CRUD operations via BaseRepository
    - Get by order number
    - Get by quote
    - Eager loading of order items
"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.order import Order
from app.repositories.base import BaseRepository
from app.schemas.order import OrderCreate, OrderUpdate

__all__ = ["OrderRepository"]


class OrderRepository(BaseRepository[Order, OrderCreate, OrderUpdate]):
    """Repository for Order operations.

    Provides data access methods for orders including
    lookups by order number, quote, and eager loading of items.

    Attributes:
        model: Order model class
        db: Database session
    """

    def __init__(self, db: AsyncSession) -> None:
        """Initialize repository with Order model.

        Args:
            db (AsyncSession): Database session
        """
        super().__init__(Order, db)

    async def get_by_order_number(self, order_number: str) -> Order | None:
        """Get order by order number.

        Args:
            order_number (str): Unique order number

        Returns:
            Order | None: Order or None if not found

        Example:
            ```python
            order = await repo.get_by_order_number("ORD-2024-001")
            ```
        """
        result = await self.db.execute(
            select(Order).where(Order.order_number == order_number)
        )
        return result.scalar_one_or_none()

    async def get_by_quote(self, quote_id: int) -> Order | None:
        """Get order by quote ID.

        Returns the order created from the specified quote.

        Args:
            quote_id (int): Quote ID

        Returns:
            Order | None: Order or None if not found

        Example:
            ```python
            order = await repo.get_by_quote(501)
            ```
        """
        result = await self.db.execute(
            select(Order).where(Order.quote_id == quote_id)
        )
        return result.scalar_one_or_none()

    async def get_with_items(self, order_id: int) -> Order | None:
        """Get order with eager-loaded items.

        Loads the order along with all its items in a single query
        to prevent N+1 query problems. Also loads related configurations
        for each item.

        Args:
            order_id (int): Order ID

        Returns:
            Order | None: Order with items or None if not found

        Example:
            ```python
            # Get order with all items loaded
            order = await repo.get_with_items(42)
            if order:
                for item in order.items:
                    print(f"{item.configuration.name}: {item.quantity}x @ ${item.unit_price}")
            ```
        """
        result = await self.db.execute(
            select(Order)
            .where(Order.id == order_id)
            .options(
                selectinload(Order.items).selectinload(
                    Order.items.property.mapper.class_.configuration
                )
            )
        )
        return result.scalar_one_or_none()
