"""Base service class for product definitions.

This module provides the foundation for scope-specific product definition services
with common functionality and abstract methods for scope-specific implementations.
"""

from __future__ import annotations

import re
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.services.base import BaseService
from .types import EntityData, EntityCreateData, EntityUpdateData

__all__ = ["BaseProductDefinitionService"]


class BaseProductDefinitionService(BaseService, ABC):
    """Base service for product definitions with common functionality.
    
    This abstract class provides the foundation for implementing
    scope-specific product definition services (profile, glazing, etc.).
    """

    def __init__(self, db: AsyncSession, scope: str):
        """Initialize base service.
        
        Args:
            db: Database session
            scope: The scope name (e.g., 'profile', 'glazing')
        """
        super().__init__(db)
        self.scope = scope
        self._scope_metadata_cache: Optional[Dict[str, Any]] = None

    # ============================================================================
    # Abstract Methods (must be implemented by subclasses)
    # ============================================================================

    @abstractmethod
    async def get_entities(self, entity_type: str) -> List[Any]:
        """Get entities of specific type for this scope.
        
        Args:
            entity_type: Type of entities to retrieve
            
        Returns:
            List of entities
        """
        pass

    async def get_entities_by_type(self, entity_type: str) -> List[Any]:
        """Alias for get_entities for backward compatibility.
        
        Args:
            entity_type: Type of entities to retrieve
            
        Returns:
            List of entities
        """
        return await self.get_entities(entity_type)

    @abstractmethod
    async def create_entity(self, data: EntityCreateData) -> Any:
        """Create entity for this scope.
        
        Args:
            data: Entity creation data
            
        Returns:
            Created entity
        """
        pass

    @abstractmethod
    async def update_entity(self, entity_id: int, data: EntityUpdateData) -> Optional[Any]:
        """Update entity for this scope.
        
        Args:
            entity_id: Entity ID to update
            data: Update data
            
        Returns:
            Updated entity or None if not found
        """
        pass

    @abstractmethod
    async def delete_entity(self, entity_id: int) -> Dict[str, Any]:
        """Delete entity for this scope.
        
        Args:
            entity_id: Entity ID to delete
            
        Returns:
            Result dict with success status
        """
        pass

    # ============================================================================
    # Common Methods (shared by all scopes)
    # ============================================================================

    async def get_scope_metadata(self) -> Dict[str, Any]:
        """Get metadata for this scope, merging YAML configuration with database extensions.
        
        Returns:
        	Scope metadata dictionary
        """
        if self._scope_metadata_cache is not None:
            return self._scope_metadata_cache

        # 1. Load from YAML (Core Configuration)
        metadata = await self._load_scope_metadata_from_yaml()
        
        # 2. Merge with Database (Dynamic Extensions)
        db_metadata = await self._load_scope_metadata_from_db()
        if db_metadata:
            # Handle legacy 'dependencies' key in DB which conflicts with new form 'dependencies'
            # If the DB metadata has 'dependencies' with parent/child structure, move it to 'relations'
            if "dependencies" in db_metadata:
                deps = db_metadata["dependencies"]
                if isinstance(deps, list) and len(deps) > 0 and "parent" in deps[0]:
                    # This is legacy relation data, move it to 'relations' to avoid schema conflicts
                    db_metadata["relations"] = deps
                    del db_metadata["dependencies"]
            
            # Merge logic: favor DB metadata for keys that exist in both, but combine lists if appropriate
            # For now, we'll continue with update() but after the key fix
            metadata.update(db_metadata)
            
        self._scope_metadata_cache = metadata
        return metadata

    async def get_definition_scopes(self) -> Dict[str, Any]:
        """Get definition scopes.
        
        Returns:
            Dict mapping scope name to its metadata
        """
        metadata = await self.get_scope_metadata()
        return {self.scope: metadata}

    async def _load_scope_metadata_from_yaml(self) -> Dict[str, Any]:
        """Load scope metadata from YAML configuration file."""
        import yaml
        from pathlib import Path
        
        # Try to find the YAML file in the config directory
        config_path = Path("backend/config/product_definition") / f"{self.scope}.yaml"
        
        # Fallback for different working directories
        if not config_path.exists():
             config_path = Path(__file__).resolve().parent.parent.parent.parent / "config" / "product_definition" / f"{self.scope}.yaml"

        if config_path.exists():
            try:
                with open(config_path, "r", encoding="utf-8") as f:
                    return yaml.safe_load(f)
            except Exception as e:
                print(f"[WARNING] Failed to load YAML metadata for {self.scope}: {e}")
        
        # Default fallback if YAML not found
        return {
            "scope": self.scope,
            "label": self.scope.title(),
            "entities": {},
            "hierarchy": {},
            "dependencies": []
        }

    async def _load_scope_metadata_from_db(self) -> Dict[str, Any]:
        """Load scope metadata from database."""
        from sqlalchemy import select
        from app.models.attribute_node import AttributeNode
        
        try:
            stmt = select(AttributeNode).where(
                AttributeNode.node_type == "scope_metadata",
                AttributeNode.page_type == self.scope
            )
            result = await self.db.execute(stmt)
            node = result.scalar_one_or_none()
            
            if node and node.metadata_:
                return node.metadata_
        except Exception as e:
            print(f"[WARNING] Failed to load DB metadata for {self.scope}: {e}")
            
        return {}

    def clear_scope_metadata_cache(self) -> None:
        """Clear the cached scope metadata to force reload from database."""
        self._scope_metadata_cache = None

    def _slugify(self, name: str) -> str:
        """Convert name to LTREE-safe slug.
        
        Args:
            name: Entity name
            
        Returns:
            LTREE-safe slug (lowercase, underscores, no special chars)
        """
        # Convert to lowercase
        slug = name.lower()
        # Replace spaces and hyphens with underscores
        slug = re.sub(r"[\s\-]+", "_", slug)
        # Remove any characters that aren't alphanumeric or underscore
        slug = re.sub(r"[^a-z0-9_]", "", slug)
        # Remove leading/trailing underscores
        slug = slug.strip("_")
        # Ensure it doesn't start with a number (LTREE requirement)
        if slug and slug[0].isdigit():
            slug = "n" + slug
        return slug or "unnamed"

    def _validate_entity_type(self, entity_type: str) -> bool:
        """Validate that entity type is supported by this scope.
        
        Args:
            entity_type: Type of entity to validate
            
        Returns:
            True if valid, False otherwise
        """
        # This is a placeholder - in a real implementation, this would
        # check against the scope's configured entity types
        return bool(entity_type and isinstance(entity_type, str))

    def _prepare_entity_metadata(self, data: EntityCreateData) -> Dict[str, Any]:
        """Prepare metadata for entity creation.
        
        Args:
            data: Entity creation data
            
        Returns:
            Prepared metadata dictionary
        """
        metadata = data.metadata or {}
        
        # Add scope-specific metadata
        metadata.update({
            "scope": self.scope,
            "entity_type": data.entity_type,
            "created_by_service": self.__class__.__name__
        })
        
        return metadata

    async def get_entity_by_id(self, entity_id: int) -> Optional[Any]:
        """Get entity by ID.
        
        Args:
            entity_id: Entity ID
            
        Returns:
            Entity or None if not found
        """
        # This is a placeholder - subclasses should implement this
        # or use a common repository pattern
        raise NotImplementedError("Subclasses must implement get_entity_by_id")

    async def validate_entity_references(self, data: Dict[str, Any]) -> bool:
        """Validate that referenced entities exist.
        
        Args:
            data: Data containing entity references
            
        Returns:
            True if all references are valid
        """
        # This is a placeholder - subclasses can override for specific validation
        return True

    def _handle_service_error(self, error: Exception, operation: str) -> None:
        """Handle service-level errors with logging.
        
        Args:
            error: The exception that occurred
            operation: Description of the operation that failed
        """
        error_msg = str(error)
        print(f"[ERROR] {self.__class__.__name__} - {operation}: {error_msg}")
        
        # Re-raise the error for the caller to handle
        raise error

    # ============================================================================
    # Utility Methods
    # ============================================================================

    def get_service_info(self) -> Dict[str, Any]:
        """Get information about this service instance.
        
        Returns:
            Service information dictionary
        """
        return {
            "service_class": self.__class__.__name__,
            "scope": self.scope,
            "database_connected": self.db is not None,
            "metadata_cached": self._scope_metadata_cache is not None
        }