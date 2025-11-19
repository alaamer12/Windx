"""User management endpoints.

This module provides REST API endpoints for user management including
listing, retrieving, updating, and deleting users.

Public Variables:
    router: FastAPI router for user endpoints

Features:
    - List all users (superuser only)
    - Get user by ID
    - Update user information
    - Delete user (superuser only)
    - Permission-based access control
"""

from fastapi import APIRouter, HTTPException, status
from pydantic import PositiveInt

from app.api.types import CurrentSuperuser, CurrentUser, UserRepo
from app.models.user import User
from app.schemas.user import User as UserSchema
from app.schemas.user import UserUpdate

__all__ = ["router"]

router = APIRouter()


@router.get("/", response_model=list[UserSchema])
async def list_users(
    user_repo: UserRepo,
    current_superuser: CurrentSuperuser,
    skip: int = 0,
    limit: int = 100,
) -> list[User]:
    """List all users (superuser only).

    Args:
        user_repo (UserRepository): User repository
        current_superuser (User): Current superuser
        skip (int): Number of records to skip
        limit (int): Maximum number of records to return

    Returns:
        list[User]: List of users
    """
    return await user_repo.get_multi(skip=skip, limit=limit)


@router.get("/{user_id}", response_model=UserSchema)
async def get_user(
    user_id: PositiveInt,
    user_repo: UserRepo,
    current_user: CurrentUser,
) -> User:
    """Get user by ID.

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


@router.patch("/{user_id}", response_model=UserSchema)
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

    return await user_repo.update(user, update_data)


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
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
