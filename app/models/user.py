"""User database model.

This module defines the User ORM model for authentication and user management
using SQLAlchemy 2.0 with Mapped columns.

Public Classes:
    User: User model with authentication fields and relationships

Features:
    - Email and username uniqueness constraints
    - Password hashing support
    - Active/superuser status flags
    - Automatic timestamp management
    - One-to-many relationship with sessions
"""

from datetime import datetime, timezone
from typing import TYPE_CHECKING

from sqlalchemy import String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.session import Session

__all__ = ["User"]


class User(Base):
    """User model for authentication and user management.
    
    Attributes:
        id: Primary key
        email: Unique email address
        username: Unique username
        hashed_password: Bcrypt hashed password
        full_name: Optional full name
        is_active: Account active status
        is_superuser: Superuser privileges flag
        created_at: Account creation timestamp
        updated_at: Last update timestamp
        sessions: Related session records
    """

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    username: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)
    is_superuser: Mapped[bool] = mapped_column(default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
        nullable=False,
    )

    # Relationships
    sessions: Mapped[list["Session"]] = relationship(
        "Session",
        back_populates="user",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        """String representation of User.

        Returns:
            str: User representation with ID, email, and username
        """
        return f"<User(id={self.id}, email={self.email}, username={self.username})>"
