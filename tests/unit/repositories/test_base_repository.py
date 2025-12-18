"""Unit tests for BaseRepository methods.

Tests the new utility methods added to BaseRepository:
- get_by_field: Get record by any field name
- exists: Check if record exists by ID
- count: Count records with optional filters
"""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.repositories.base import BaseRepository


@pytest.mark.asyncio
class TestBaseRepositoryGetByField:
    """Test get_by_field method."""

    async def test_get_by_field_finds_existing_record(self, db_session: AsyncSession):
        """Test get_by_field returns record when it exists."""
        # Arrange
        repo = BaseRepository(User, db_session)
        user = User(
            email="test@example.com",
            username="testuser",
            hashed_password="$2b$12$test",
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        # Act
        found = await repo.get_by_field("email", "test@example.com")

        # Assert
        assert found is not None
        assert found.email == "test@example.com"
        assert found.username == "testuser"

    async def test_get_by_field_returns_none_when_not_found(self, db_session: AsyncSession):
        """Test get_by_field returns None when record doesn't exist."""
        # Arrange
        repo = BaseRepository(User, db_session)

        # Act
        found = await repo.get_by_field("email", "nonexistent@example.com")

        # Assert
        assert found is None

    async def test_get_by_field_with_username(self, db_session: AsyncSession):
        """Test get_by_field works with different field names."""
        # Arrange
        repo = BaseRepository(User, db_session)
        user = User(
            email="test@example.com",
            username="uniqueuser",
            hashed_password="$2b$12$test",
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        # Act
        found = await repo.get_by_field("username", "uniqueuser")

        # Assert
        assert found is not None
        assert found.username == "uniqueuser"

    async def test_get_by_field_raises_error_for_invalid_field(self, db_session: AsyncSession):
        """Test get_by_field raises ValueError for invalid field name."""
        # Arrange
        repo = BaseRepository(User, db_session)

        # Act & Assert
        with pytest.raises(ValueError, match="Invalid field name: nonexistent_field"):
            await repo.get_by_field("nonexistent_field", "value")


@pytest.mark.asyncio
class TestBaseRepositoryExists:
    """Test exists method."""

    async def test_exists_returns_true_for_existing_id(self, db_session: AsyncSession):
        """Test exists returns True when record exists."""
        # Arrange
        repo = BaseRepository(User, db_session)
        user = User(
            email="test@example.com",
            username="testuser",
            hashed_password="$2b$12$test",
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        # Act
        result = await repo.exists(user.id)

        # Assert
        assert result is True

    async def test_exists_returns_false_for_nonexistent_id(self, db_session: AsyncSession):
        """Test exists returns False when record doesn't exist."""
        # Arrange
        repo = BaseRepository(User, db_session)

        # Act
        result = await repo.exists(99999)

        # Assert
        assert result is False


@pytest.mark.asyncio
class TestBaseRepositoryCount:
    """Test count method."""

    async def test_count_returns_total_without_filters(self, db_session: AsyncSession):
        """Test count returns total count when no filters provided."""
        # Arrange
        repo = BaseRepository(User, db_session)
        user1 = User(
            email="user1@example.com",
            username="user1",
            hashed_password="$2b$12$test",
            is_active=True,
        )
        user2 = User(
            email="user2@example.com",
            username="user2",
            hashed_password="$2b$12$test",
            is_active=False,
        )
        db_session.add_all([user1, user2])
        await db_session.commit()

        # Act
        count = await repo.count()

        # Assert
        assert count == 2

    async def test_count_with_single_filter(self, db_session: AsyncSession):
        """Test count returns correct count with single filter."""
        # Arrange
        repo = BaseRepository(User, db_session)
        user1 = User(
            email="user1@example.com",
            username="user1",
            hashed_password="$2b$12$test",
            is_active=True,
        )
        user2 = User(
            email="user2@example.com",
            username="user2",
            hashed_password="$2b$12$test",
            is_active=False,
        )
        db_session.add_all([user1, user2])
        await db_session.commit()

        # Act
        active_count = await repo.count({"is_active": True})

        # Assert
        assert active_count == 1

    async def test_count_with_multiple_filters(self, db_session: AsyncSession):
        """Test count returns correct count with multiple filters."""
        # Arrange
        repo = BaseRepository(User, db_session)
        user1 = User(
            email="user1@example.com",
            username="user1",
            hashed_password="$2b$12$test",
            is_active=True,
            is_superuser=True,
        )
        user2 = User(
            email="user2@example.com",
            username="user2",
            hashed_password="$2b$12$test",
            is_active=True,
            is_superuser=False,
        )
        user3 = User(
            email="user3@example.com",
            username="user3",
            hashed_password="$2b$12$test",
            is_active=False,
            is_superuser=True,
        )
        db_session.add_all([user1, user2, user3])
        await db_session.commit()

        # Act
        count = await repo.count({"is_active": True, "is_superuser": True})

        # Assert
        assert count == 1

    async def test_count_returns_zero_when_no_matches(self, db_session: AsyncSession):
        """Test count returns 0 when no records match filters."""
        # Arrange
        repo = BaseRepository(User, db_session)
        user = User(
            email="user@example.com",
            username="user",
            hashed_password="$2b$12$test",
            is_active=True,
        )
        db_session.add(user)
        await db_session.commit()

        # Act
        count = await repo.count({"is_active": False})

        # Assert
        assert count == 0

    async def test_count_raises_error_for_invalid_field(self, db_session: AsyncSession):
        """Test count raises ValueError for invalid field name."""
        # Arrange
        repo = BaseRepository(User, db_session)

        # Act & Assert
        with pytest.raises(ValueError, match="Invalid field name: nonexistent_field"):
            await repo.count({"nonexistent_field": "value"})
