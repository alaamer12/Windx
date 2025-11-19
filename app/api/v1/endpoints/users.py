"""User management endpoints.

This module provides REST API endpoints for user management including
listing, retrieving, updating, and deleting users.

Public Variables:
    router: FastAPI router for user endpoints

Features:
    - List all users with pagination (superuser only)
    - Get user by ID with caching
    - Update user information
    - Delete user (superuser only)
    - Permission-based access control
    - Rate limiting on all endpoints
    - Caching for read operations
"""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi_cache.decorator import cache
from pydantic import PositiveInt

from app.api.types import CurrentSuperuser, CurrentUser, DBSession, UserRepo
from app.core.cache import get_cache_namespace
from app.core.limiter import rate_limit
from app.core.pagination import Page, PaginationParams, create_pagination_params

# Add pagination params dependency
PaginationParams = Annotated[PaginationParams, Depends(create_pagination_params)]
from app.models.user import User
from app.schemas.user import User as UserSchema
from app.schemas.user import UserUpdate

__all__ = ["router"]

router = APIRouter()


@router.get("/", response_model=Page[UserSchema])
async def list_users(
    user_repo: UserRepo,
    current_superuser: CurrentSuperuser,
    params: PaginationParams,
    db: DBSession,
) -> Page[User]:
    """List all users with pagination (superuser only).

    Args:
        user_repo (UserRepository): User repository
        current_superuser (User): Current superuser
        params (PaginationParams): Pagination parameters
        db (AsyncSession): Database session

    Returns:
        Page[User]: Paginated list of users
    """
    from sqlalchemy import select

    from app.core.pagination import paginate
    from app.models.user import User

    query = select(User).order_by(User.created_at.desc())
    return await paginate(query, params)


@router.get(
    "/{user_id}",
    response_model=UserSchema,
    dependencies=[Depends(rate_limit(times=20, seconds=60))],
)
@cache(expire=300)  # Cache for 5 minutes
async def get_user(
    user_id: PositiveInt,
    user_repo: UserRepo,
    current_user: CurrentUser,
) -> User:
    """Get user by ID with caching.

    Rate limit: 20 requests per minute.
    Cache TTL: 5 minutes.

    Args:
        user_id (PositiveInt): User ID
        user_repo (UserRepository): User repository
        current_user (User): Current authenticated user

    Returns:
        User: User data

    Raises:
        HTTPException: If user not found or no permission
    """
    # Users can only view their own profile unless they're superuser
    if user_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )

    user = await user_repo.get(user_id)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    return user


@router.patch(
    "/{user_id}",
    response_model=UserSchema,
    dependencies=[Depends(rate_limit(times=10, seconds=60))],
)
async def update_user(
    user_id: PositiveInt,
    user_update: UserUpdate,
    user_repo: UserRepo,
    current_user: CurrentUser,
) -> User:
    """Update user information.

    Args:
        user_id (PositiveInt): User ID
        user_update (UserUpdate): User update data
        user_repo (UserRepository): User repository
        current_user (User): Current authenticated user

    Returns:
        User: Updated user data

    Raises:
        HTTPException: If user not found or no permission
    """
    # Users can only update their own profile unless they're superuser
    if user_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )

    user = await user_repo.get(user_id)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    # Handle password update
    update_data = user_update.model_dump(exclude_unset=True)
    if "password" in update_data:
        from app.core.security import get_password_hash

        update_data["hashed_password"] = get_password_hash(update_data.pop("password"))

    updated_user = await user_repo.update(user, update_data)

    # Invalidate cache for this user
    from app.core.cache import invalidate_cache

    await invalidate_cache(f"*get_user*{user_id}*")

    return updated_user


@router.delete(
    "/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(rate_limit(times=5, seconds=60))],
)
async def delete_user(
    user_id: PositiveInt,
    user_repo: UserRepo,
    current_superuser: CurrentSuperuser,
) -> None:
    """Delete user (superuser only).

    Args:
        user_id (PositiveInt): User ID
        user_repo (UserRepository): User repository
        current_superuser (User): Current superuser

    Raises:
        HTTPException: If user not found
    """
    user = await user_repo.delete(user_id)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
