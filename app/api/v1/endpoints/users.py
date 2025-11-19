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

from app.api.types import CurrentSuperuser, CurrentUser, DBSession
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
    current_superuser: CurrentSuperuser,
    params: PaginationParams,
    db: DBSession,
) -> Page[User]:
    """List all users with pagination (superuser only).

    Args:
        current_superuser (User): Current superuser
        params (PaginationParams): Pagination parameters
        db (AsyncSession): Database session

    Returns:
        Page[User]: Paginated list of users

    Note:
        This endpoint uses direct pagination for simplicity since it's
        a straightforward query with no business logic.
    """
    from sqlalchemy import select

    from app.core.pagination import paginate

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
    current_user: CurrentUser,
    db: DBSession,
) -> User:
    """Get user by ID with caching.

    Rate limit: 20 requests per minute.
    Cache TTL: 5 minutes.

    Args:
        user_id (PositiveInt): User ID
        current_user (User): Current authenticated user
        db (AsyncSession): Database session

    Returns:
        User: User data

    Raises:
        AuthorizationException: If user lacks permission
        NotFoundException: If user not found
    """
    from app.services.user import UserService

    user_service = UserService(db)
    return await user_service.get_user_with_permission_check(user_id, current_user)


@router.patch(
    "/{user_id}",
    response_model=UserSchema,
    dependencies=[Depends(rate_limit(times=10, seconds=60))],
)
async def update_user(
    user_id: PositiveInt,
    user_update: UserUpdate,
    current_user: CurrentUser,
    db: DBSession,
) -> User:
    """Update user information.

    Args:
        user_id (PositiveInt): User ID
        user_update (UserUpdate): User update data
        current_user (User): Current authenticated user
        db (AsyncSession): Database session

    Returns:
        User: Updated user data

    Raises:
        AuthorizationException: If user lacks permission
        NotFoundException: If user not found
        ConflictException: If email/username conflicts
    """
    from app.services.user import UserService

    user_service = UserService(db)
    updated_user = await user_service.update_user(user_id, user_update, current_user)

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
    current_superuser: CurrentSuperuser,
    db: DBSession,
) -> None:
    """Delete user (superuser only).

    Args:
        user_id (PositiveInt): User ID
        current_superuser (User): Current superuser
        db (AsyncSession): Database session

    Raises:
        NotFoundException: If user not found
        AuthorizationException: If user is not superuser
    """
    from app.services.user import UserService

    user_service = UserService(db)
    await user_service.delete_user(user_id, current_superuser)
