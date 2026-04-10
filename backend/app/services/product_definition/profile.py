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
        """Get profile entities of specific type."""
        from sqlalchemy import select
        from app.models.attribute_node import AttributeNode
        
        try:
            stmt = select(AttributeNode).where(
                AttributeNode.node_type == entity_type,
                AttributeNode.page_type == self.scope
            ).order_by(AttributeNode.name)
            
            result = await self.db.execute(stmt)
            entities = list(result.scalars().all())

            # Enrich system_series with parent information from paths for dynamic autofill
            if entity_type == "system_series":
                # Get all paths to find parents
                path_stmt = select(AttributeNode).where(
                    AttributeNode.node_type == "entity_path",
                    AttributeNode.page_type == self.scope
                )
                path_result = await self.db.execute(path_stmt)
                paths = path_result.scalars().all()

                # Build a lookup for parents by series_id
                # Since multiple paths might exist for one series (different colors), 
                # we just need any one path to find the parents
                series_to_parents = {}
                for path in paths:
                    pm = path.metadata_ or {}
                    sid = pm.get("system_series_id")
                    if sid and sid not in series_to_parents:
                        series_to_parents[sid] = {
                            "company_id": pm.get("company_id"),
                            "material_id": pm.get("material_id"),
                            "opening_system_id": pm.get("opening_system_id")
                        }

                # Get names for all referenced parent IDs to avoid N+1
                all_parent_ids = set()
                for p in series_to_parents.values():
                    all_parent_ids.update([v for v in p.values() if v])
                
                parent_map = {}
                if all_parent_ids:
                    p_stmt = select(AttributeNode).where(AttributeNode.id.in_(all_parent_ids))
                    p_res = await self.db.execute(p_stmt)
                    for p_node in p_res.scalars().all():
                        parent_map[p_node.id] = p_node.name

                # Inject parent names into series metadata
                for entity in entities:
                    parents = series_to_parents.get(entity.id)
                    if parents:
                        if not entity.metadata_:
                            entity.metadata_ = {}
                        
                        # Add parent names to metadata for frontend dependency engine
                        entity.metadata_["company"] = parent_map.get(parents["company_id"])
                        entity.metadata_["material"] = parent_map.get(parents["material_id"])
                        entity.metadata_["opening_system"] = parent_map.get(parents["opening_system_id"])

            return entities
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
            
            metadata = self._prepare_entity_metadata(data)
            validation_rules = metadata.pop("validation_rules", None)
            
            entity = AttributeNode(
                name=data.name,
                node_type=data.entity_type,
                page_type=self.scope,
                image_url=data.image_url,
                price_impact_value=data.price_from,
                description=data.description,
                metadata_=metadata,
                validation_rules=validation_rules,
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
                # Extract validation rules if present in metadata dictionary
                metadata = data.metadata.copy()
                if "validation_rules" in metadata:
                    entity.validation_rules = metadata.pop("validation_rules")
                
                # Use remaining metadata for metadata_ column
                entity.metadata_ = metadata
                
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
        """Get detailed path information including enriched entity data."""
        from sqlalchemy import select
        from app.models.attribute_node import AttributeNode
        
        try:
            stmt = select(AttributeNode).where(AttributeNode.id == path_id)
            result = await self.db.execute(stmt)
            node = result.scalar_one_or_none()
            
            if not node:
                return None
            
            # Basic details from path node
            details = {
                "id": node.id,
                "ltree_path": node.ltree_path,
                "name": node.name,
                "created_at": node.created_at.isoformat() if node.created_at else None,
                **(node.metadata_ if node.metadata_ else {})
            }
            
            # Enrich with actual entity objects
            entity_ids = {
                "company": details.get("company_id"),
                "material": details.get("material_id"),
                "opening_system": details.get("opening_system_id"),
                "system_series": details.get("system_series_id"),
                "color": details.get("color_id")
            }
            
            entities = {}
            for etype, eid in entity_ids.items():
                if eid:
                    estmt = select(AttributeNode).where(AttributeNode.id == eid)
                    eresult = await self.db.execute(estmt)
                    enode = eresult.scalar_one_or_none()
                    if enode:
                        entities[etype] = {
                            "id": enode.id,
                            "name": enode.name,
                            "node_type": enode.node_type,
                            "description": enode.description,
                            "image_url": enode.image_url,
                            "price_impact_value": str(enode.price_impact_value) if enode.price_impact_value else "0",
                            "metadata_": enode.metadata_,
                            "validation_rules": enode.validation_rules
                        }
            
            details["entities"] = entities
            
            # Fetch scope metadata for definitions
            scope_metadata = await self.get_scope_metadata()
            details["definitions"] = scope_metadata.get("entities", {})
            
            # Construct display path from entity names
            path_names = [
                entities.get("company", {}).get("name"),
                entities.get("material", {}).get("name"),
                entities.get("opening_system", {}).get("name"),
                entities.get("system_series", {}).get("name"),
                entities.get("color", {}).get("name")
            ]
            details["display_path"] = " → ".join([n for n in path_names if n])
            
            return details
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
