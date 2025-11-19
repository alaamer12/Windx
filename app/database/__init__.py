"""Database package for database configuration and utilities.

This package contains database configuration, connection management,
and database utilities.

Public Modules:
    connection: Database connection and session management
    base: Base model class
    utils: Database utilities

Features:
    - Database connection management
    - Session lifecycle management
    - Base model configuration
    - Database utilities
"""

from app.database.base import Base
from app.database.connection import close_db, get_db, init_db

__all__ = [
    "Base",
    "get_db",
    "init_db",
    "close_db",
]
