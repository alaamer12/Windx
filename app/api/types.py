"""API type aliases and dependencies.

This module provides reusable type aliases for common dependencies used
throughout the API endpoints. Using these aliases improves code readability,
reduces boilerplate, and ensures consistency.

Public Type Aliases:
    DBSession: Database session dependency
    CurrentUser: Current authenticated user dependency
    CurrentSuperuser: Current superuser dependency
    UserRepo: User repository dependency
    SessionRepo: Session repository dependency

Features:
    - Type-safe dependencies with Annotated
    - Comprehensive docstrings for IDE support
    - Consistent dependency injection patterns
    - Reduced boilerplate in endpoints
"""

from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User
from app.repositories.session import SessionRepository
from app.repositories.user import UserRepository

__all__ = [
    "DBSession",
    "CurrentUser",
    "CurrentSuperuser",
    "UserRepo",
    "SessionRepo",
]


# ============================================================================
# Database Session Type Aliases
# ============================================================================

DBSession = Annotated[AsyncSession, Depends(get_db)]
"""Database session dependency.

Provides a SQLAlchemy async session for database operations.
Automatically handles session lifecycle (commit, rollback, close).

Usage:
    ```python
    @router.get("/items")
    async def list_items(db: DBSession):
        result = await db.execute(select(Item))
        return result.scalars().all()
    ```

Example:
    ```python
    from app.api.types import DBSession

    @router.post("/users", response_model=UserSchema)
    async def create_user(
        user_in: UserCreate,
        db: DBSession,
    ) -> User:
        user_repo = UserRepository(db)
        return await user_repo.create(user_in)
    ```
"""


# ============================================================================
# Authentication Type Aliases
# ============================================================================

def _get_current_user_dep():
    """Import dependency to avoid circular imports."""
    from app.api.deps import get_current_user

    return get_current_user


def _get_current_superuser_dep():
    """Import dependency to avoid circular imports."""
    from app.api.deps import get_current_active_superuser

    return get_current_active_superuser


CurrentUser = Annotated[User, Depends(_get_current_user_dep)]
"""Current authenticated user dependency.

Provides the currently authenticated user from JWT token.
Raises 401 if token is invalid or user not found.
Raises 400 if user is inactive.

Usage:
    ```python
    @router.get("/me")
    async def get_current_user_info(current_user: CurrentUser):
        return current_user
    ```

Example:
    ```python
    from app.api.types import CurrentUser, DBSession

    @router.patch("/me", response_model=UserSchema)
    async def update_current_user(
        user_update: UserUpdate,
        current_user: CurrentUser,
        db: DBSession,
    ) -> User:
        user_repo = UserRepository(db)
        return await user_repo.update(current_user, user_update)
    ```
"""

CurrentSuperuser = Annotated[User, Depends(_get_current_superuser_dep)]
"""Current superuser dependency.

Provides the currently authenticated superuser.
Raises 401 if token is invalid or user not found.
Raises 403 if user is not a superuser.

Usage:
    ```python
    @router.delete("/users/{user_id}")
    async def delete_user(
        user_id: int,
        current_superuser: CurrentSuperuser,
        db: DBSession,
    ):
        user_repo = UserRepository(db)
        await user_repo.delete(user_id)
    ```

Example:
    ```python
    from app.api.types import CurrentSuperuser, DBSession

    @router.get("/admin/users", response_model=list[UserSchema])
    async def list_all_users(
        current_superuser: CurrentSuperuser,
        db: DBSession,
        skip: int = 0,
        limit: int = 100,
    ) -> list[User]:
        user_repo = UserRepository(db)
        return await user_repo.get_multi(skip=skip, limit=limit)
    ```
"""


# ============================================================================
# Repository Type Aliases
# ============================================================================

def get_user_repository(db: DBSession) -> UserRepository:
    """Get user repository instance.

    Args:
        db (AsyncSession): Database session

    Returns:
        UserRepository: User repository instance
    """
    return UserRepository(db)


def get_session_repository(db: DBSession) -> SessionRepository:
    """Get session repository instance.

    Args:
        db (AsyncSession): Database session

    Returns:
        SessionRepository: Session repository instance
    """
    return SessionRepository(db)


UserRepo = Annotated[UserRepository, Depends(get_user_repository)]
"""User repository dependency.

Provides access to user data access layer with repository pattern.
Includes methods for user CRUD operations and custom queries.

Usage:
    ```python
    @router.get("/users/{user_id}")
    async def get_user(user_id: int, user_repo: UserRepo):
        return await user_repo.get(user_id)
    ```

Example:
    ```python
    from app.api.types import UserRepo, CurrentSuperuser

    @router.get("/users/email/{email}", response_model=UserSchema)
    async def get_user_by_email(
        email: str,
        user_repo: UserRepo,
        current_superuser: CurrentSuperuser,
    ) -> User:
        user = await user_repo.get_by_email(email)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return user
    ```

Available Methods:
    - get(id): Get user by ID
    - get_by_email(email): Get user by email
    - get_by_username(username): Get user by username
    - get_multi(skip, limit): Get multiple users with pagination
    - get_active_users(skip, limit): Get active users only
    - create(obj_in): Create new user
    - update(db_obj, obj_in): Update existing user
    - delete(id): Delete user by ID
"""

SessionRepo = Annotated[SessionRepository, Depends(get_session_repository)]
"""Session repository dependency.

Provides access to session data access layer with repository pattern.
Includes methods for session CRUD operations and token validation.

Usage:
    ```python
    @router.get("/sessions")
    async def list_sessions(
        session_repo: SessionRepo,
        current_user: CurrentUser,
    ):
        return await session_repo.get_user_sessions(current_user.id)
    ```

Example:
    ```python
    from app.api.types import SessionRepo, CurrentUser

    @router.delete("/sessions/{session_id}")
    async def delete_session(
        session_id: int,
        session_repo: SessionRepo,
        current_user: CurrentUser,
    ):
        session = await session_repo.get(session_id)
        if not session or session.user_id != current_user.id:
            raise HTTPException(status_code=404, detail="Session not found")
        await session_repo.delete(session_id)
        return {"message": "Session deleted"}
    ```

Available Methods:
    - get(id): Get session by ID
    - get_by_token(token): Get session by token
    - get_active_by_token(token): Get active session by token
    - get_user_sessions(user_id, active_only): Get all user sessions
    - deactivate_session(token): Deactivate a session
    - create(obj_in): Create new session
    - update(db_obj, obj_in): Update existing session
    - delete(id): Delete session by ID
"""
