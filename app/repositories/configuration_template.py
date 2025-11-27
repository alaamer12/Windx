"""Repository for ConfigurationTemplate operations.

This module provides the repository implementation for ConfigurationTemplate
model with custom query methods.

Public Classes:
    ConfigurationTemplateRepository: Repository for template operations

Features:
    - Standard CRUD operations via BaseRepository
    - Get public templates
    - Get by manufacturing type
    - Increment usage count
"""

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.configuration_template import ConfigurationTemplate
from app.repositories.base import BaseRepository
from app.schemas.configuration_template import (
    ConfigurationTemplateCreate,
    ConfigurationTemplateUpdate,
)

__all__ = ["ConfigurationTemplateRepository"]


class ConfigurationTemplateRepository(
    BaseRepository[
        ConfigurationTemplate,
        ConfigurationTemplateCreate,
        ConfigurationTemplateUpdate,
    ]
):
    """Repository for ConfigurationTemplate operations.

    Provides data access methods for configuration templates including
    filtering by visibility, manufacturing type, and usage tracking.

    Attributes:
        model: ConfigurationTemplate model class
        db: Database session
    """

    def __init__(self, db: AsyncSession) -> None:
        """Initialize repository with ConfigurationTemplate model.

        Args:
            db (AsyncSession): Database session
        """
        super().__init__(ConfigurationTemplate, db)

    async def get_public_templates(self) -> list[ConfigurationTemplate]:
        """Get all public templates.

        Returns only templates where is_public is True and is_active is True,
        ordered by usage count (most popular first).

        Returns:
            list[ConfigurationTemplate]: List of public templates

        Example:
            ```python
            public_templates = await repo.get_public_templates()
            ```
        """
        result = await self.db.execute(
            select(ConfigurationTemplate)
            .where(ConfigurationTemplate.is_public == True)
            .where(ConfigurationTemplate.is_active == True)
            .order_by(ConfigurationTemplate.usage_count.desc())
        )
        return list(result.scalars().all())

    async def get_by_manufacturing_type(
        self, manufacturing_type_id: int
    ) -> list[ConfigurationTemplate]:
        """Get templates by manufacturing type.

        Returns all active templates for the specified manufacturing type,
        ordered by usage count (most popular first).

        Args:
            manufacturing_type_id (int): Manufacturing type ID

        Returns:
            list[ConfigurationTemplate]: List of templates

        Example:
            ```python
            window_templates = await repo.get_by_manufacturing_type(1)
            ```
        """
        result = await self.db.execute(
            select(ConfigurationTemplate)
            .where(
                ConfigurationTemplate.manufacturing_type_id == manufacturing_type_id
            )
            .where(ConfigurationTemplate.is_active == True)
            .order_by(ConfigurationTemplate.usage_count.desc())
        )
        return list(result.scalars().all())

    async def increment_usage_count(self, template_id: int) -> None:
        """Increment the usage count for a template.

        Atomically increments the usage_count field by 1.
        This is called when a template is applied to create a configuration.

        Args:
            template_id (int): Template ID

        Example:
            ```python
            await repo.increment_usage_count(42)
            ```
        """
        await self.db.execute(
            update(ConfigurationTemplate)
            .where(ConfigurationTemplate.id == template_id)
            .values(usage_count=ConfigurationTemplate.usage_count + 1)
        )
        await self.db.commit()
