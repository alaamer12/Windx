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

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import PositiveInt
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_active_superuser, get_current_user
from app.core.database import get_db
from app.models.user import User
from app.repositories.user import UserRepository
from app.schemas.user import User as UserSchema
from app.schemas.user import UserUpdate

__all__ = ["router"]

router = APIRouter()


@router.get("/", response_model=list[UserSchema])
async def list_users(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_superuser)],
    skip: int = 0,
    limit: int = 100,
) -> list[User]:
    """List all users (superuser only).

    Args:
        db (AsyncSession): Database session
        current_user (User): Current superuser
        skip (int): Number of records to skip
        limit (int): Maximum number of records to return

    Returns:
        list[User]: List of users
    """
    user_repo = UserRepository(db)
    users = await user_repo.get_multi(skip=skip, limit=limit)
    return users


@router.get("/{user_id}", response_model=UserSchema)
async def get_user(
    user_id: PositiveInt,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> User:
    """Get user by ID.

    Args:
        user_id (PositiveInt): User ID
        db (AsyncSession): Database session
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

    user_repo = UserRepository(db)
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
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> User:
    """Update user information.

    Args:
        user_id (PositiveInt): User ID
        user_update (UserUpdate): User update data
        db (AsyncSession): Database session
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

    user_repo = UserRepository(db)
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
    return updated_user


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: PositiveInt,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_superuser)],
) -> None:
    """Delete user (superuser only).

    Args:
        user_id (PositiveInt): User ID
        db (AsyncSession): Database session
        current_user (User): Current superuser

    Raises:
        HTTPException: If user not found
    """
    user_repo = UserRepository(db)
    user = await user_repo.delete(user_id)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
