"""Repository for Quote operations.

This module provides the repository implementation for Quote
model with custom query methods.

Public Classes:
    QuoteRepository: Repository for quote operations

Features:
    - Standard CRUD operations via BaseRepository
    - Get by quote number
    - Get by customer
    - Get by configuration
"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.quote import Quote
from app.repositories.base import BaseRepository
from app.schemas.quote import QuoteCreate, QuoteUpdate

__all__ = ["QuoteRepository"]


class QuoteRepository(BaseRepository[Quote, QuoteCreate, QuoteUpdate]):
    """Repository for Quote operations.

    Provides data access methods for quotes including
    lookups by quote number, customer, and configuration.

    Attributes:
        model: Quote model class
        db: Database session
    """

    def __init__(self, db: AsyncSession) -> None:
        """Initialize repository with Quote model.

        Args:
            db (AsyncSession): Database session
        """
        super().__init__(Quote, db)

    async def get_by_quote_number(self, quote_number: str) -> Quote | None:
        """Get quote by quote number.

        Args:
            quote_number (str): Unique quote number

        Returns:
            Quote | None: Quote or None if not found

        Example:
            ```python
            quote = await repo.get_by_quote_number("Q-2024-001")
            ```
        """
        result = await self.db.execute(
            select(Quote).where(Quote.quote_number == quote_number)
        )
        return result.scalar_one_or_none()

    async def get_by_customer(self, customer_id: int) -> list[Quote]:
        """Get all quotes for a customer.

        Returns all quotes for the specified customer,
        ordered by creation date (newest first).

        Args:
            customer_id (int): Customer ID

        Returns:
            list[Quote]: List of quotes

        Example:
            ```python
            customer_quotes = await repo.get_by_customer(42)
            ```
        """
        result = await self.db.execute(
            select(Quote)
            .where(Quote.customer_id == customer_id)
            .order_by(Quote.created_at.desc())
        )
        return list(result.scalars().all())

    async def get_by_configuration(self, configuration_id: int) -> list[Quote]:
        """Get all quotes for a configuration.

        Returns all quotes generated for the specified configuration,
        ordered by creation date (newest first).

        Args:
            configuration_id (int): Configuration ID

        Returns:
            list[Quote]: List of quotes

        Example:
            ```python
            config_quotes = await repo.get_by_configuration(123)
            ```
        """
        result = await self.db.execute(
            select(Quote)
            .where(Quote.configuration_id == configuration_id)
            .order_by(Quote.created_at.desc())
        )
        return list(result.scalars().all())
