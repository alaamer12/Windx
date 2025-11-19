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
from fastapi_cache.decorator import cache
from pydantic import BaseModel, Field

from app.api.types import CurrentUser, DBSession, SessionRepo, UserRepo
from app.core.limiter import rate_limit
from app.core.security import create_access_token, get_password_hash, verify_password
from app.models.user import User
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


@router.post(
    "/register",
    response_model=UserSchema,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(rate_limit(times=5, seconds=3600))],  # 5 per hour
)
async def register(
    user_in: UserCreate,
    user_repo: UserRepo,
    db: DBSession,
) -> User:
    """Register a new user.

    Args:
        user_in (UserCreate): User registration data
        user_repo (UserRepository): User repository
        db (AsyncSession): Database session

    Returns:
        User: Created user

    Raises:
        ConflictException: If username or email already exists
        DatabaseException: If database operation fails
    """
    from app.core.exceptions import ConflictException, DatabaseException

    try:
        # Check if user exists
        existing_user = await user_repo.get_by_email(user_in.email)
        if existing_user:
            raise ConflictException(
                message="Email already registered",
                details={"email": user_in.email},
            )

        existing_user = await user_repo.get_by_username(user_in.username)
        if existing_user:
            raise ConflictException(
                message="Username already taken",
                details={"username": user_in.username},
            )

        # Create user with hashed password
        user_dict = user_in.model_dump()
        user_dict["hashed_password"] = get_password_hash(user_dict.pop("password"))

        # Create user
        db_user = User(**user_dict)
        db.add(db_user)
        await db.commit()
        await db.refresh(db_user)

        return db_user

    except ConflictException:
        # Re-raise conflict exceptions
        raise
    except Exception as e:
        # Wrap unexpected errors
        await db.rollback()
        raise DatabaseException(
            message="Failed to create user",
            details={"error": str(e)},
        )


@router.post(
    "/login",
    response_model=Token,
    dependencies=[Depends(rate_limit(times=10, seconds=300))],  # 10 per 5 minutes
)
async def login(
    login_data: LoginRequest,
    user_repo: UserRepo,
    session_repo: SessionRepo,
) -> Token:
    """Login and get access token.

    Args:
        login_data (LoginRequest): Login credentials
        user_repo (UserRepository): User repository
        session_repo (SessionRepository): Session repository

    Returns:
        Token: Access token

    Raises:
        AuthenticationException: If credentials are invalid
        DatabaseException: If database operation fails
    """
    from app.core.exceptions import AuthenticationException, DatabaseException

    try:
        # Try to find user by username or email
        user = await user_repo.get_by_username(login_data.username)
        if not user:
            user = await user_repo.get_by_email(login_data.username)

        if not user or not verify_password(login_data.password, user.hashed_password):
            raise AuthenticationException(
                message="Incorrect username or password",
                details={"username": login_data.username},
            )

        if not user.is_active:
            raise AuthenticationException(
                message="Account is inactive",
                details={"user_id": user.id},
            )

        # Create access token
        access_token = create_access_token(subject=user.id)

        # Create session record
        expires_at = datetime.now(timezone.utc) + timedelta(minutes=30)
        session_create = SessionCreate(
            user_id=user.id,
            token=access_token,
            expires_at=expires_at,
        )
        await session_repo.create(session_create)

        return Token(access_token=access_token, token_type="bearer")

    except AuthenticationException:
        # Re-raise authentication exceptions
        raise
    except Exception as e:
        # Wrap unexpected errors
        raise DatabaseException(
            message="Login failed due to system error",
            details={"error": str(e)},
        )


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    current_user: CurrentUser,
    session_repo: SessionRepo,
) -> None:
    """Logout current user (deactivate session).

    Args:
        current_user (User): Current authenticated user
        session_repo (SessionRepository): Session repository
    """
    # In a real implementation, you'd deactivate the current session
    # For now, this is a placeholder
    pass


@router.get(
    "/me",
    response_model=UserSchema,
    dependencies=[Depends(rate_limit(times=30, seconds=60))],
)
@cache(expire=60)  # Cache for 1 minute
async def get_current_user_info(
    current_user: CurrentUser,
) -> User:
    """Get current user information.

    Args:
        current_user (User): Current authenticated user

    Returns:
        User: Current user data
    """
    return current_user
