"""Pydantic schemas module.

This module contains all Pydantic schemas for data validation,
serialization, and API request/response handling.

Public Classes:
    User: User response schema
    UserCreate: User creation schema
    UserUpdate: User update schema
    UserInDB: User database schema with password
    Session: Session response schema
    SessionCreate: Session creation schema
    SessionInDB: Session database schema with token
    LoginRequest: Login request schema
    Token: Token response schema

Features:
    - Composed schemas (not monolithic)
    - Semantic types (EmailStr, PositiveInt)
    - Field validation with constraints
    - Type-safe with Annotated types
    - ORM mode support
"""

from app.schemas.auth import LoginRequest, Token
from app.schemas.session import Session, SessionCreate, SessionInDB
from app.schemas.user import User, UserCreate, UserInDB, UserUpdate

__all__ = [
    "User",
    "UserCreate",
    "UserUpdate",
    "UserInDB",
    "Session",
    "SessionCreate",
    "SessionInDB",
    "LoginRequest",
    "Token",
]
