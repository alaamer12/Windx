"""Repository for AttributeNode operations with hierarchy support.

This module provides the repository implementation for AttributeNode
model with hierarchical query methods using LTREE.

Public Classes:
    AttributeNodeRepository: Repository for attribute node operations

Features:
    - Hierarchical queries via HierarchicalRepository
    - Get by manufacturing type
    - Get root nodes
    - LTREE pattern matching
    - Efficient tree traversal
"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.attribute_node import AttributeNode
from app.repositories.windx_base import HierarchicalRepository
from app.schemas.attribute_node import AttributeNodeCreate, AttributeNodeUpdate

__all__ = ["AttributeNodeRepository"]


class AttributeNodeRepository(
    HierarchicalRepository[AttributeNode, AttributeNodeCreate, AttributeNodeUpdate]
):
    """Repository for AttributeNode operations with hierarchy support.

    Extends HierarchicalRepository to provide LTREE-based hierarchical
    queries for attribute nodes. Includes methods for filtering by
    manufacturing type and pattern matching.

    Attributes:
        model: AttributeNode model class
        db: Database session
    """

    def __init__(self, db: AsyncSession) -> None:
        """Initialize repository with AttributeNode model.

        Args:
            db (AsyncSession): Database session
        """
        super().__init__(AttributeNode, db)

    async def get_by_manufacturing_type(
        self, manufacturing_type_id: int
    ) -> list[AttributeNode]:
        """Get all attribute nodes for a manufacturing type.

        Returns all nodes in the attribute tree for the specified
        manufacturing type, ordered by ltree_path for hierarchical display.

        Args:
            manufacturing_type_id (int): Manufacturing type ID

        Returns:
            list[AttributeNode]: List of attribute nodes ordered by path

        Example:
            ```python
            # Get all attributes for Window type
            window_attrs = await repo.get_by_manufacturing_type(1)
            ```
        """
        result = await self.db.execute(
            select(AttributeNode)
            .where(AttributeNode.manufacturing_type_id == manufacturing_type_id)
            .order_by(AttributeNode.ltree_path)
        )
        return list(result.scalars().all())

    async def get_root_nodes(
        self, manufacturing_type_id: int | None = None
    ) -> list[AttributeNode]:
        """Get root nodes (top-level nodes with no parent).

        Returns nodes at the top of the hierarchy. Can optionally filter
        by manufacturing type.

        Args:
            manufacturing_type_id (int | None): Optional manufacturing type filter

        Returns:
            list[AttributeNode]: List of root nodes ordered by sort_order and name

        Example:
            ```python
            # Get all root nodes
            roots = await repo.get_root_nodes()
            
            # Get root nodes for specific manufacturing type
            window_roots = await repo.get_root_nodes(manufacturing_type_id=1)
            ```
        """
        query = select(AttributeNode).where(AttributeNode.parent_node_id.is_(None))

        if manufacturing_type_id is not None:
            query = query.where(
                AttributeNode.manufacturing_type_id == manufacturing_type_id
            )

        query = query.order_by(AttributeNode.sort_order, AttributeNode.name)

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def search_by_path_pattern(self, pattern: str) -> list[AttributeNode]:
        """Search attribute nodes using LTREE lquery pattern.

        Uses PostgreSQL LTREE lquery syntax for pattern matching.
        Supports wildcards and complex path patterns.

        Args:
            pattern (str): LTREE lquery pattern

        Returns:
            list[AttributeNode]: List of matching nodes ordered by path

        Example:
            ```python
            # Find all nodes with 'material' in path
            materials = await repo.search_by_path_pattern('*.material.*')
            
            # Find nodes at specific depth (3 levels)
            level3 = await repo.search_by_path_pattern('*{3}')
            
            # Find specific path pattern
            frames = await repo.search_by_path_pattern('window.frame.*')
            ```

        Pattern Syntax:
            - `*`: Match any single label
            - `*{n}`: Match exactly n labels
            - `*{n,}`: Match n or more labels
            - `*{,n}`: Match up to n labels
            - `*{n,m}`: Match between n and m labels
            - `label1|label2`: Match either label1 or label2
        """
        result = await self.db.execute(
            select(AttributeNode)
            .where(AttributeNode.ltree_path.lquery(pattern))
            .order_by(AttributeNode.ltree_path)
        )
        return list(result.scalars().all())
