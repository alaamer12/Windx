"""Repository pattern implementation module.

This module contains all repository implementations following the
repository pattern for clean data access layer separation.

Public Classes:
    UserRepository: Repository for User operations
    SessionRepository: Repository for Session operations

Features:
    - Repository pattern implementation
    - Generic base repository with CRUD
    - Type-safe async operations
    - Custom query methods per repository
    - Clean separation of concerns
"""

from app.repositories.session import SessionRepository
from app.repositories.user import UserRepository

__all__ = ["UserRepository", "SessionRepository"]
