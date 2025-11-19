"""User service for business logic.

This module implements business logic for user management including
user creation, updates, validation, and complex operations.

Public Classes:
    UserService: User management business logic

Features:
    - User creation with validation
    - User updates with business rules
    - User deletion with cleanup
    - Complex user queries
    - Password management
"""

from typing import Any

from pydantic import PositiveInt
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictException, NotFoundException
from app.core.security import get_password_hash
from app.models.user import User
from app.repositories.user import UserRepository
from app.schemas.user import UserCreate, UserUpdate
from app.services.base import BaseService

__all__ = ["UserService"]


class UserService(BaseService):
    """User service for business logic.

    Handles user management operations including creation, updates,
    deletion, and complex business logic.

    Attributes:
        db: Database session
        user_repo: User repository for data access
    """

    def __init__(self, db: AsyncSession) -> None:
        """Initialize user service.

        Args:
            db (AsyncSession): Database session
        """
        super().__init__(db)
        self.user_repo = UserRepository(db)

    async def create_user(self, user_in: UserCreate) -> User:
        """Create new user with validation.

        Validates that email and username are unique before creating user.
        Hashes password before storing.

        Args:
            user_in (UserCreate): User creation data

        Returns:
            User: Created user instance

        Raises:
            ConflictException: If email or username already exists
        """
        # Check if email already exists
        existing_user = await self.user_repo.get_by_email(user_in.email)
        if existing_user:
            raise ConflictException(
                message="Email already registered",
                details={"email": user_in.email},
            )

        # Check if username already exists
        existing_user = await self.user_repo.get_by_username(user_in.username)
        if existing_user:
            raise ConflictException(
                message="Username already taken",
                details={"username": user_in.username},
            )

        # Hash password
        hashed_password = get_password_hash(user_in.password)

        # Create user data with hashed password
        user_data = user_in.model_dump(exclude={"password"})
        user_data["hashed_password"] = hashed_password

        # Create user
        user = await self.user_repo.create(user_data)
        await self.commit()
        await self.refresh(user)

        return user

    async def get_user(self, user_id: PositiveInt) -> User:
        """Get user by ID.

        Args:
            user_id (PositiveInt): User ID

        Returns:
            User: User instance

        Raises:
            NotFoundException: If user not found
        """
        user = await self.user_repo.get(user_id)
        if not user:
            raise NotFoundException(
                resource="User",
                details={"user_id": user_id},
            )
        return user

    async def get_user_by_email(self, email: str) -> User | None:
        """Get user by email.

        Args:
            email (str): User email

        Returns:
            User | None: User instance or None if not found
        """
        return await self.user_repo.get_by_email(email)

    async def get_user_by_username(self, username: str) -> User | None:
        """Get user by username.

        Args:
            username (str): Username

        Returns:
            User | None: User instance or None if not found
        """
        return await self.user_repo.get_by_username(username)

    async def update_user(
        self,
        user_id: PositiveInt,
        user_update: UserUpdate,
        current_user: User,
    ) -> User:
        """Update user with validation.

        Validates permissions and uniqueness constraints before updating.

        Args:
            user_id (PositiveInt): User ID to update
            user_update (UserUpdate): Update data
            current_user (User): Current authenticated user

        Returns:
            User: Updated user instance

        Raises:
            NotFoundException: If user not found
            ConflictException: If email or username conflicts
            AuthorizationException: If user lacks permission
        """
        from app.core.exceptions import AuthorizationException

        # Get user
        user = await self.get_user(user_id)

        # Check permissions (users can only update themselves unless superuser)
        if user.id != current_user.id and not current_user.is_superuser:
            raise AuthorizationException(
                message="You can only update your own profile",
                details={"user_id": user_id, "current_user_id": current_user.id},
            )

        # Validate email uniqueness if changing
        if user_update.email and user_update.email != user.email:
            existing_user = await self.user_repo.get_by_email(user_update.email)
            if existing_user:
                raise ConflictException(
                    message="Email already registered",
                    details={"email": user_update.email},
                )

        # Validate username uniqueness if changing
        if user_update.username and user_update.username != user.username:
            existing_user = await self.user_repo.get_by_username(user_update.username)
            if existing_user:
                raise ConflictException(
                    message="Username already taken",
                    details={"username": user_update.username},
                )

        # Hash password if provided
        update_data = user_update.model_dump(exclude_unset=True)
        if "password" in update_data:
            update_data["hashed_password"] = get_password_hash(update_data.pop("password"))

        # Update user
        updated_user = await self.user_repo.update(user, update_data)
        await self.commit()
        await self.refresh(updated_user)

        return updated_user

    async def delete_user(
        self,
        user_id: PositiveInt,
        current_user: User,
    ) -> None:
        """Delete user with validation.

        Only superusers can delete users. Performs cleanup of related data.

        Args:
            user_id (PositiveInt): User ID to delete
            current_user (User): Current authenticated user

        Raises:
            NotFoundException: If user not found
            AuthorizationException: If user is not superuser
        """
        from app.core.exceptions import AuthorizationException

        # Check permissions (only superusers can delete)
        if not current_user.is_superuser:
            raise AuthorizationException(
                message="Only superusers can delete users",
                details={"current_user_id": current_user.id},
            )

        # Get user
        user = await self.get_user(user_id)

        # Delete user (cascade will handle sessions)
        await self.user_repo.delete(user.id)
        await self.commit()

    async def list_users(
        self,
        skip: int = 0,
        limit: int = 100,
        active_only: bool = False,
    ) -> list[User]:
        """List users with pagination.

        Args:
            skip (int): Number of records to skip
            limit (int): Maximum number of records to return
            active_only (bool): Only return active users

        Returns:
            list[User]: List of users
        """
        if active_only:
            return await self.user_repo.get_active_users(skip=skip, limit=limit)
        return await self.user_repo.get_multi(skip=skip, limit=limit)

    async def activate_user(self, user_id: PositiveInt) -> User:
        """Activate user account.

        Args:
            user_id (PositiveInt): User ID

        Returns:
            User: Updated user instance

        Raises:
            NotFoundException: If user not found
        """
        user = await self.get_user(user_id)
        user.is_active = True
        await self.commit()
        await self.refresh(user)
        return user

    async def deactivate_user(self, user_id: PositiveInt) -> User:
        """Deactivate user account.

        Args:
            user_id (PositiveInt): User ID

        Returns:
            User: Updated user instance

        Raises:
            NotFoundException: If user not found
        """
        user = await self.get_user(user_id)
        user.is_active = False
        await self.commit()
        await self.refresh(user)
        return user

    async def get_user_with_permission_check(
        self,
        user_id: PositiveInt,
        current_user: User,
    ) -> User:
        """Get user by ID with permission check.

        Users can only view their own profile unless they're superuser.

        Args:
            user_id (PositiveInt): User ID to retrieve
            current_user (User): Current authenticated user

        Returns:
            User: User instance

        Raises:
            AuthorizationException: If user lacks permission
            NotFoundException: If user not found
        """
        from app.core.exceptions import AuthorizationException

        # Check permissions
        if user_id != current_user.id and not current_user.is_superuser:
            raise AuthorizationException(
                message="You can only view your own profile",
                details={"user_id": user_id, "current_user_id": current_user.id},
            )

        return await self.get_user(user_id)
