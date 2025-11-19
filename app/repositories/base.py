"""Base repository with common CRUD operations.

This module provides a generic base repository class implementing the
repository pattern for database operations with type safety.

Public Classes:
    BaseRepository: Generic repository with CRUD operations

Features:
    - Generic type-safe repository pattern
    - Common CRUD operations (Create, Read, Update, Delete)
    - Pagination support
    - Async SQLAlchemy operations
    - Pydantic schema integration
"""

from typing import Any, Generic, TypeVar

from pydantic import BaseModel, PositiveInt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.base import Base

ModelType = TypeVar("ModelType", bound=Base)
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)

__all__ = ["BaseRepository", "ModelType", "CreateSchemaType", "UpdateSchemaType"]


class BaseRepository(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    """Base repository class with common CRUD operations.
    
    Attributes:
        model: SQLAlchemy model class
        db: Database session
    """

    def __init__(self, model: type[ModelType], db: AsyncSession) -> None:
        """Initialize repository.

        Args:
            model (type[ModelType]): SQLAlchemy model class
            db (AsyncSession): Database session
        """
        self.model = model
        self.db = db

    async def get(self, id: PositiveInt) -> ModelType | None:
        """Get a single record by ID.

        Args:
            id (PositiveInt): Record ID

        Returns:
            ModelType | None: Model instance or None if not found
        """
        result = await self.db.execute(select(self.model).where(self.model.id == id))
        return result.scalar_one_or_none()

    async def get_multi(
        self,
        skip: int = 0,
        limit: int = 100,
    ) -> list[ModelType]:
        """Get multiple records with pagination.

        Args:
            skip (int): Number of records to skip
            limit (int): Maximum number of records to return

        Returns:
            list[ModelType]: List of model instances
        """
        result = await self.db.execute(select(self.model).offset(skip).limit(limit))
        return list(result.scalars().all())

    async def create(self, obj_in: CreateSchemaType) -> ModelType:
        """Create a new record.

        Args:
            obj_in (CreateSchemaType): Schema with data for creation

        Returns:
            ModelType: Created model instance
        """
        obj_data = obj_in.model_dump()
        db_obj = self.model(**obj_data)
        self.db.add(db_obj)
        await self.db.commit()
        await self.db.refresh(db_obj)
        return db_obj

    async def update(
        self,
        db_obj: ModelType,
        obj_in: UpdateSchemaType | dict[str, Any],
    ) -> ModelType:
        """Update an existing record.

        Args:
            db_obj (ModelType): Existing model instance
            obj_in (UpdateSchemaType | dict[str, Any]): Schema or dict with update data

        Returns:
            ModelType: Updated model instance
        """
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.model_dump(exclude_unset=True)

        for field, value in update_data.items():
            setattr(db_obj, field, value)

        self.db.add(db_obj)
        await self.db.commit()
        await self.db.refresh(db_obj)
        return db_obj

    async def delete(self, id: PositiveInt) -> ModelType | None:
        """Delete a record by ID.

        Args:
            id (PositiveInt): Record ID

        Returns:
            ModelType | None: Deleted model instance or None if not found
        """
        db_obj = await self.get(id)
        if db_obj:
            await self.db.delete(db_obj)
            await self.db.commit()
        return db_obj
