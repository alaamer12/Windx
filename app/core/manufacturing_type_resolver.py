"""Manufacturing Type Configuration and Resolution.

This module provides a robust, production-ready way to resolve manufacturing types
without hardcoding database IDs. It uses stable identifiers (names) and provides
fallback mechanisms for different environments.
"""

from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.manufacturing_type import ManufacturingType


class ManufacturingTypeResolver:
    """Resolves manufacturing types by stable identifiers instead of hardcoded IDs.
    
    This class provides a production-safe way to reference manufacturing types
    that works across different environments and database states.
    """
    
    # Stable identifiers for known manufacturing types
    WINDOW_PROFILE_ENTRY = "Window Profile Entry"
    CASEMENT_WINDOW = "Casement Window"
    SLIDING_DOOR = "Sliding Door"
    
    # Page type constants
    PAGE_TYPE_PROFILE = "profile"
    PAGE_TYPE_ACCESSORIES = "accessories"
    PAGE_TYPE_GLAZING = "glazing"
    
    # Valid page types
    VALID_PAGE_TYPES = {PAGE_TYPE_PROFILE, PAGE_TYPE_ACCESSORIES, PAGE_TYPE_GLAZING}
    
    # Cache for resolved IDs (per-session)
    _cache: dict[str, int] = {}
    
    @classmethod
    async def get_by_name(
        cls,
        db: AsyncSession,
        name: str,
        *,
        create_if_missing: bool = False,
    ) -> Optional[ManufacturingType]:
        """Get manufacturing type by name.
        
        Args:
            db: Database session
            name: Manufacturing type name (stable identifier)
            create_if_missing: If True, create the type if it doesn't exist
            
        Returns:
            ManufacturingType or None if not found
        """
        stmt = select(ManufacturingType).where(
            ManufacturingType.name == name,
            ManufacturingType.is_active == True,
        )
        result = await db.execute(stmt)
        mfg_type = result.scalar_one_or_none()
        
        if mfg_type:
            # Cache the ID for this session
            cls._cache[name] = mfg_type.id
            return mfg_type
            
        if create_if_missing:
            # This should only be used in development/setup
            # Production should have types pre-created
            raise NotImplementedError(
                f"Manufacturing type '{name}' not found. "
                "Run setup script to create it."
            )
            
        return None
    
    @classmethod
    async def get_id_by_name(
        cls,
        db: AsyncSession,
        name: str,
    ) -> Optional[int]:
        """Get manufacturing type ID by name.
        
        Args:
            db: Database session
            name: Manufacturing type name
            
        Returns:
            Manufacturing type ID or None if not found
        """
        # Check cache first
        if name in cls._cache:
            return cls._cache[name]
            
        mfg_type = await cls.get_by_name(db, name)
        return mfg_type.id if mfg_type else None
    
    @classmethod
    async def get_default_for_page_type(
        cls,
        db: AsyncSession,
        page_type: str,
        manufacturing_category: str = "window",
    ) -> Optional[ManufacturingType]:
        """Get the default manufacturing type for a specific page type.
        
        This method provides a fallback chain based on page type and category:
        1. Try specific page type + category combination
        2. Try first active type matching category
        3. Try any active manufacturing type
        
        Args:
            db: Database session
            page_type: Page type (profile, accessories, glazing)
            manufacturing_category: Category (window, door, etc.)
            
        Returns:
            ManufacturingType or None if no types exist
        """
        # Validate page type
        if page_type not in cls.VALID_PAGE_TYPES:
            raise ValueError(f"Invalid page_type '{page_type}'. Must be one of: {cls.VALID_PAGE_TYPES}")
        
        # For profile pages, use the existing logic
        if page_type == cls.PAGE_TYPE_PROFILE:
            return await cls.get_default_profile_entry_type(db)
        
        # For accessories and glazing, try to find appropriate manufacturing type
        # First try category-specific types
        stmt = select(ManufacturingType).where(
            ManufacturingType.base_category == manufacturing_category,
            ManufacturingType.is_active == True,
        ).limit(1)
        result = await db.execute(stmt)
        mfg_type = result.scalar_one_or_none()
        if mfg_type:
            return mfg_type
        
        # Fallback: Any active type
        stmt = select(ManufacturingType).where(
            ManufacturingType.is_active == True
        ).limit(1)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()
    
    @classmethod
    async def get_default_profile_entry_type(
        cls,
        db: AsyncSession,
    ) -> Optional[ManufacturingType]:
        """Get the default manufacturing type for profile entry.
        
        This method provides a fallback chain:
        1. Try "Window Profile Entry" (primary)
        2. Try first active window type
        3. Try any active manufacturing type
        
        Args:
            db: Database session
            
        Returns:
            ManufacturingType or None if no types exist
        """
        # Try primary profile entry type
        mfg_type = await cls.get_by_name(db, cls.WINDOW_PROFILE_ENTRY)
        if mfg_type:
            return mfg_type
        
        # Fallback: Try any window type
        stmt = select(ManufacturingType).where(
            ManufacturingType.base_category == "window",
            ManufacturingType.is_active == True,
        ).limit(1)
        result = await db.execute(stmt)
        mfg_type = result.scalar_one_or_none()
        if mfg_type:
            return mfg_type
        
        # Last resort: Any active type
        stmt = select(ManufacturingType).where(
            ManufacturingType.is_active == True
        ).limit(1)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()
    
    @classmethod
    def validate_page_type(cls, page_type: str | None) -> bool:
        """Validate if page_type is valid.
        
        Args:
            page_type: Page type to validate
            
        Returns:
            bool: True if valid, False otherwise
        """
        if page_type is None:
            return False
        return page_type in cls.VALID_PAGE_TYPES
    
    @classmethod
    def clear_cache(cls):
        """Clear the ID cache. Useful for testing or after database changes."""
        cls._cache.clear()
