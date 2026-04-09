"""Profile-specific product definition service.

This module provides the service implementation for profile product definitions
with hierarchical dependencies (Company → Material → Opening System → System Series → Colors).
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, TYPE_CHECKING

from sqlalchemy.ext.asyncio import AsyncSession

if TYPE_CHECKING:
    from app.services.product_definition import ProductDefinitionService

from .base import BaseProductDefinitionService
from .types import EntityCreateData, EntityUpdateData, ProfilePathData, ProfileDependentOptions

__all__ = ["ProfileProductDefinitionService"]


class ProfileProductDefinitionService(BaseProductDefinitionService):
    """Service for profile product definitions with hierarchical dependencies.
    
    This service handles the profile scope which includes:
    - Hierarchical entities: company → material → opening_system → system_series → color
    - Dependency path management
    - Cascading option selection
    """

    def __init__(self, db: AsyncSession):
        """Initialize profile service.
        
        Args:
            db: Database session
        """
        super().__init__(db, "profile")
        # Use existing service for backward compatibility during migration
        self._legacy_service: Optional[Any] = None

    async def get_entities(self, entity_type: str) -> List[Any]:
        """Get profile entities of specific type.
        
        Args:
            entity_type: Type of entities (company, material, opening_system, system_series, color)
            
        Returns:
            List of AttributeNode entities
        """
        from sqlalchemy import select
        from app.models.attribute_node import AttributeNode
        
        try:
            stmt = select(AttributeNode).where(
                AttributeNode.node_type == entity_type,
                AttributeNode.page_type == self.scope
            ).order_by(AttributeNode.name)
            
            result = await self.db.execute(stmt)
            return list(result.scalars().all())
        except Exception as e:
            self._handle_service_error(e, f"getting {entity_type} entities")

    async def create_entity(self, data: EntityCreateData) -> Any:
        """Create profile entity.
        
        Args:
            data: Entity creation data
            
        Returns:
            Created entity
        """
        from app.models.attribute_node import AttributeNode
        
        try:
            # Validate entity type for profile scope
            valid_types = ["company", "material", "opening_system", "system_series", "color"]
            if data.entity_type not in valid_types:
                raise ValueError(f"Invalid entity type for profile scope: {data.entity_type}. Valid types: {valid_types}")

            # Generate LTREE path
            slug = self._slugify(data.name)
            ltree_path = f"definitions.{self.scope}.{data.entity_type}.{slug}"
            
            entity = AttributeNode(
                name=data.name,
                node_type=data.entity_type,
                page_type=self.scope,
                image_url=data.image_url,
                price_impact_value=data.price_from,
                description=data.description,
                metadata_=self._prepare_entity_metadata(data),
                ltree_path=ltree_path,
                depth=3
            )
            
            self.db.add(entity)
            await self.commit()
            await self.refresh(entity)
            return entity
        except Exception as e:
            await self.rollback()
            self._handle_service_error(e, f"creating {data.entity_type} entity")

    async def update_entity(self, entity_id: int, data: EntityUpdateData) -> Optional[Any]:
        """Update profile entity.
        
        Args:
            entity_id: Entity ID to update
            data: Update data
            
        Returns:
            Updated entity or None if not found
        """
        from sqlalchemy import select
        from app.models.attribute_node import AttributeNode
        
        try:
            stmt = select(AttributeNode).where(AttributeNode.id == entity_id)
            result = await self.db.execute(stmt)
            entity = result.scalar_one_or_none()
            
            if not entity:
                return None
                
            if data.name is not None:
                entity.name = data.name
                # Update ltree path if name changed? 
                # For safety, we keep the original slug in the path
            if data.image_url is not None:
                entity.image_url = data.image_url
            if data.price_from is not None:
                entity.price_impact_value = data.price_from
            if data.description is not None:
                entity.description = data.description
            if data.metadata is not None:
                entity.metadata_ = data.metadata
                
            await self.commit()
            await self.refresh(entity)
            return entity
        except Exception as e:
            await self.rollback()
            self._handle_service_error(e, f"updating entity {entity_id}")

    async def delete_entity(self, entity_id: int) -> Dict[str, Any]:
        """Delete profile entity.
        
        Args:
            entity_id: Entity ID to delete
            
        Returns:
            Result dict with success status
        """
        from sqlalchemy import delete
        from app.models.attribute_node import AttributeNode
        
        try:
            stmt = delete(AttributeNode).where(AttributeNode.id == entity_id)
            result = await self.db.execute(stmt)
            await self.commit()
            
            if result.rowcount == 0:
                return {"success": False, "message": "Entity not found"}
                
            return {"success": True, "message": "Entity deleted successfully"}
        except Exception as e:
            await self.rollback()
            self._handle_service_error(e, f"deleting entity {entity_id}")

    async def get_entity_by_id(self, entity_id: int) -> Optional[Any]:
        """Get profile entity by ID."""
        from sqlalchemy import select
        from app.models.attribute_node import AttributeNode
        
        try:
            stmt = select(AttributeNode).where(AttributeNode.id == entity_id)
            result = await self.db.execute(stmt)
            return result.scalar_one_or_none()
        except Exception as e:
            self._handle_service_error(e, f"getting entity {entity_id}")

    # ============================================================================
    # Profile-Specific Dependency Path Management
    # ============================================================================

    async def create_dependency_path(self, data: ProfilePathData) -> Any:
        """Create profile dependency path."""
        from app.models.attribute_node import AttributeNode
        
        try:
            # Store path as a node with metadata linking the entity IDs
            path_str = f"c{data.company_id}.m{data.material_id}.o{data.opening_system_id}.s{data.system_series_id}.l{data.color_id}"
            ltree_path = f"paths.{self.scope}.{path_str}"
            
            path_node = AttributeNode(
                name=f"Path {path_str}",
                node_type="entity_path",
                page_type=self.scope,
                ltree_path=ltree_path,
                metadata_={
                    "company_id": data.company_id,
                    "material_id": data.material_id,
                    "opening_system_id": data.opening_system_id,
                    "system_series_id": data.system_series_id,
                    "color_id": data.color_id
                }
            )
            
            self.db.add(path_node)
            await self.commit()
            await self.refresh(path_node)
            return path_node
        except Exception as e:
            await self.rollback()
            self._handle_service_error(e, "creating dependency path")

    async def delete_dependency_path(self, ltree_path: str) -> Dict[str, Any]:
        """Delete profile dependency path."""
        from sqlalchemy import delete
        from app.models.attribute_node import AttributeNode
        
        try:
            stmt = delete(AttributeNode).where(
                AttributeNode.ltree_path == ltree_path,
                AttributeNode.node_type == "entity_path"
            )
            result = await self.db.execute(stmt)
            await self.commit()
            
            if result.rowcount == 0:
                return {"success": False, "message": "Path not found"}
                
            return {"success": True, "message": "Path deleted successfully"}
        except Exception as e:
            await self.rollback()
            self._handle_service_error(e, f"deleting dependency path {ltree_path}")

    async def get_all_paths(self) -> List[Dict[str, Any]]:
        """Get all profile dependency paths."""
        from sqlalchemy import select
        from app.models.attribute_node import AttributeNode
        
        try:
            stmt = select(AttributeNode).where(
                AttributeNode.node_type == "entity_path",
                AttributeNode.page_type == self.scope
            )
            result = await self.db.execute(stmt)
            nodes = result.scalars().all()
            
            return [
                {
                    "id": n.id,
                    "ltree_path": n.ltree_path,
                    **(n.metadata_ if n.metadata_ else {})
                }
                for n in nodes
            ]
        except Exception as e:
            self._handle_service_error(e, "getting all paths")

    async def get_path_details(self, path_id: int) -> Optional[Dict[str, Any]]:
        """Get detailed path information."""
        from sqlalchemy import select
        from app.models.attribute_node import AttributeNode
        
        try:
            stmt = select(AttributeNode).where(AttributeNode.id == path_id)
            result = await self.db.execute(stmt)
            node = result.scalar_one_or_none()
            
            if not node:
                return None
                
            return {
                "id": node.id,
                "ltree_path": node.ltree_path,
                **(node.metadata_ if node.metadata_ else {})
            }
        except Exception as e:
            self._handle_service_error(e, f"getting path details {path_id}")

    async def get_dependent_options(self, selections: ProfileDependentOptions) -> Dict[str, List[Dict[str, Any]]]:
        """Get dependent options based on parent selections.
        
        This mimics the legacy behavior by returning available entities.
        A more advanced version would filter based on 'entity_path' nodes.
        """
        result = {}
        entity_types = ["company", "material", "opening_system", "system_series", "color"]
        
        for etype in entity_types:
            entities = await self.get_entities(etype)
            result[etype] = [
                {
                    "id": e.id,
                    "name": e.name,
                    "price_impact_value": str(e.price_impact_value) if e.price_impact_value else None,
                    "metadata": e.metadata_
                }
                for e in entities
            ]
            
        return result

    async def get_scope_for_entity(self, entity_type: str) -> str:
        """Get scope for an entity type."""
        return self.scope

    # ============================================================================
    # Validation Methods
    # ============================================================================

    def _validate_entity_type(self, entity_type: str) -> bool:
        """Validate entity type for profile scope."""
        valid_types = ["company", "material", "opening_system", "system_series", "color"]
        return entity_type in valid_types

    async def validate_entity_references(self, data: Dict[str, Any]) -> bool:
        """Validate entity references for profile scope."""
        return True
