"""User repository for database operations.

This module implements the repository pattern for User model with
custom query methods for user management.

Public Classes:
    UserRepository: Repository for User CRUD operations

Features:
    - User lookup by email and username
    - Active user filtering
    - Inherits base CRUD operations
    - Type-safe async operations
"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.repositories.base import BaseRepository
from app.schemas.user import UserCreate, UserUpdate

__all__ = ["UserRepository"]


class UserRepository(BaseRepository[User, UserCreate, UserUpdate]):
    """Repository for User model operations."""

    def __init__(self, db: AsyncSession) -> None:
        """Initialize user repository.

        Args:
            db (AsyncSession): Database session
        """
        super().__init__(User, db)

    async def get_by_email(self, email: str) -> User | None:
        """Get user by email address.

        Args:
            email (str): User email address

        Returns:
            User | None: User instance or None if not found
        """
        result = await self.db.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()

    async def get_by_username(self, username: str) -> User | None:
        """Get user by username.

        Args:
            username (str): Username

        Returns:
            User | None: User instance or None if not found
        """
        result = await self.db.execute(select(User).where(User.username == username))
        return result.scalar_one_or_none()

    async def get_active_users(self, skip: int = 0, limit: int = 100) -> list[User]:
        """Get all active users.

        Args:
            skip (int): Number of records to skip
            limit (int): Maximum number of records to return

        Returns:
            list[User]: List of active users
        """
        result = await self.db.execute(
            select(User).where(User.is_active == True).offset(skip).limit(limit)
        )
        return list(result.scalars().all())
