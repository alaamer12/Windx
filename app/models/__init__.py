"""Database models module.

This module contains all SQLAlchemy ORM models for database tables
using modern SQLAlchemy 2.0 with Mapped columns.

Public Classes:
    User: User model for authentication
    Session: Session model for tracking user sessions

Features:
    - SQLAlchemy 2.0 Mapped columns
    - Relationship management
    - Automatic timestamps
    - Type-safe model definitions
"""

from app.models.session import Session
from app.models.user import User

__all__ = ["User", "Session"]
