"""Authentication endpoints.

This module provides REST API endpoints for user authentication including
registration, login, logout, and current user information.

Public Variables:
    router: FastAPI router for authentication endpoints

Features:
    - User registration
    - User login with JWT token generation
    - User logout
    - Get current user information
    - Session management
"""

from fastapi import APIRouter, Depends, status
from fastapi_cache.decorator import cache

from app.api.types import CurrentUser, DBSession
from app.core.limiter import rate_limit
from app.models.user import User
from app.schemas.auth import LoginRequest, Token
from app.schemas.user import User as UserSchema
from app.schemas.user import UserCreate

__all__ = ["router"]

router = APIRouter()


@router.post(
    "/register",
    response_model=UserSchema,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(rate_limit(times=5, seconds=3600))],  # 5 per hour
)
async def register(
    user_in: UserCreate,
    db: DBSession,
) -> User:
    """Register a new user.

    Args:
        user_in (UserCreate): User registration data
        db (AsyncSession): Database session

    Returns:
        User: Created user

    Raises:
        ConflictException: If username or email already exists
        DatabaseException: If database operation fails
    """
    from app.services.user import UserService

    user_service = UserService(db)
    return await user_service.create_user(user_in)


@router.post(
    "/login",
    response_model=Token,
    dependencies=[Depends(rate_limit(times=10, seconds=300))],  # 10 per 5 minutes
)
async def login(
    login_data: LoginRequest,
    db: DBSession,
) -> Token:
    """Login and get access token.

    Args:
        login_data (LoginRequest): Login credentials
        db (AsyncSession): Database session

    Returns:
        Token: Access token

    Raises:
        AuthenticationException: If credentials are invalid
        DatabaseException: If database operation fails
    """
    from app.services.auth import AuthService

    auth_service = AuthService(db)
    access_token, _ = await auth_service.login(login_data.username, login_data.password)
    return Token(access_token=access_token, token_type="bearer")


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    current_user: CurrentUser,
    db: DBSession,
) -> None:
    """Logout current user (deactivate session).

    Args:
        current_user (User): Current authenticated user
        db (AsyncSession): Database session
    """
    from app.services.session import SessionService

    session_service = SessionService(db)
    # Deactivate all active sessions for the user
    await session_service.deactivate_all_user_sessions(current_user.id)


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
