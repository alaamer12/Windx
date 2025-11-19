"""Authentication endpoints.

This module provides REST API endpoints for user authentication including
registration, login, logout, and current user information.

Public Classes:
    Token: Token response schema
    LoginRequest: Login request schema

Public Variables:
    router: FastAPI router for authentication endpoints

Features:
    - User registration
    - User login with JWT token generation
    - User logout
    - Get current user information
    - Session management
"""

from datetime import datetime, timedelta, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.database import get_db
from app.core.security import create_access_token, get_password_hash, verify_password
from app.models.user import User
from app.repositories.session import SessionRepository
from app.repositories.user import UserRepository
from app.schemas.session import SessionCreate
from app.schemas.user import User as UserSchema
from app.schemas.user import UserCreate

__all__ = ["router", "Token", "LoginRequest"]

router = APIRouter()


class Token(BaseModel):
    """Token response schema.
    
    Attributes:
        access_token: JWT access token
        token_type: Token type (bearer)
    """

    access_token: Annotated[str, Field(description="JWT access token")]
    token_type: Annotated[str, Field(description="Token type", examples=["bearer"])]


class LoginRequest(BaseModel):
    """Login request schema.
    
    Attributes:
        username: Username or email
        password: User password
    """

    username: Annotated[str, Field(description="Username or email")]
    password: Annotated[str, Field(description="User password")]


@router.post("/register", response_model=UserSchema, status_code=status.HTTP_201_CREATED)
async def register(
    user_in: UserCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> User:
    """Register a new user.

    Args:
        user_in (UserCreate): User registration data
        db (AsyncSession): Database session

    Returns:
        User: Created user

    Raises:
        HTTPException: If username or email already exists
    """
    user_repo = UserRepository(db)

    # Check if user exists
    existing_user = await user_repo.get_by_email(user_in.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )

    existing_user = await user_repo.get_by_username(user_in.username)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already taken",
        )

    # Create user with hashed password
    user_dict = user_in.model_dump()
    user_dict["hashed_password"] = get_password_hash(user_dict.pop("password"))

    # Create user using repository
    from app.schemas.user import UserInDB

    user_create = UserInDB(**user_dict, id=0, is_active=True, is_superuser=False, created_at=datetime.now(timezone.utc), updated_at=datetime.now(timezone.utc))
    db_user = User(**user_dict)
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)

    return db_user


@router.post("/login", response_model=Token)
async def login(
    login_data: LoginRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> Token:
    """Login and get access token.

    Args:
        login_data (LoginRequest): Login credentials
        db (AsyncSession): Database session

    Returns:
        Token: Access token

    Raises:
        HTTPException: If credentials are invalid
    """
    user_repo = UserRepository(db)

    # Try to find user by username or email
    user = await user_repo.get_by_username(login_data.username)
    if not user:
        user = await user_repo.get_by_email(login_data.username)

    if not user or not verify_password(login_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user",
        )

    # Create access token
    access_token = create_access_token(subject=user.id)

    # Create session record
    session_repo = SessionRepository(db)
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=30)
    session_create = SessionCreate(
        user_id=user.id,
        token=access_token,
        expires_at=expires_at,
    )
    await session_repo.create(session_create)

    return Token(access_token=access_token, token_type="bearer")


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> None:
    """Logout current user (deactivate session).

    Args:
        current_user (User): Current authenticated user
        db (AsyncSession): Database session
    """
    # In a real implementation, you'd deactivate the current session
    # For now, this is a placeholder
    pass


@router.get("/me", response_model=UserSchema)
async def get_current_user_info(
    current_user: Annotated[User, Depends(get_current_user)],
) -> User:
    """Get current user information.

    Args:
        current_user (User): Current authenticated user

    Returns:
        User: Current user data
    """
    return current_user
