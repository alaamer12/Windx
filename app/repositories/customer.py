"""Repository for Customer operations.

This module provides the repository implementation for Customer
model with custom query methods.

Public Classes:
    CustomerRepository: Repository for customer operations

Features:
    - Standard CRUD operations via BaseRepository
    - Get by email lookup
    - Get active customers
"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.customer import Customer
from app.repositories.base import BaseRepository
from app.schemas.customer import CustomerCreate, CustomerUpdate

__all__ = ["CustomerRepository"]


class CustomerRepository(BaseRepository[Customer, CustomerCreate, CustomerUpdate]):
    """Repository for Customer operations.

    Provides data access methods for customers including
    lookups by email and active status filtering.

    Attributes:
        model: Customer model class
        db: Database session
    """

    def __init__(self, db: AsyncSession) -> None:
        """Initialize repository with Customer model.

        Args:
            db (AsyncSession): Database session
        """
        super().__init__(Customer, db)

    async def get_by_email(self, email: str) -> Customer | None:
        """Get customer by email address.

        Args:
            email (str): Customer email address

        Returns:
            Customer | None: Customer or None if not found

        Example:
            ```python
            customer = await repo.get_by_email("john@example.com")
            ```
        """
        result = await self.db.execute(
            select(Customer).where(Customer.email == email)
        )
        return result.scalar_one_or_none()

    async def get_active(self) -> list[Customer]:
        """Get all active customers.

        Returns only customers where is_active is True,
        ordered by company name or email.

        Returns:
            list[Customer]: List of active customers

        Example:
            ```python
            active_customers = await repo.get_active()
            ```
        """
        result = await self.db.execute(
            select(Customer)
            .where(Customer.is_active == True)
            .order_by(Customer.company_name, Customer.email)
        )
        return list(result.scalars().all())
