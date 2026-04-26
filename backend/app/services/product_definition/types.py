"""Common types and interfaces for product definition services.

This module defines common types, protocols, and data structures
used across different product definition scopes.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Protocol, TypeVar
from decimal import Decimal
from pydantic import BaseModel, Field, field_validator

from app.core.config_loader import RuntimeConfigLoader

__all__ = [
    "EntityData",
    "EntityCreateData", 
    "EntityUpdateData",
    "ProfilePathData",
    "GlazingComponentData",
    "GlazingUnitData",
    "CalculationResult",
    "ServiceProtocol"
]


# ============================================================================
# Common Data Types
# ============================================================================

class EntityData(BaseModel):
    """Base data structure for entities."""
    
    id: int
    name: str
    description: Optional[str] = None
    image_url: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class EntityCreateData(BaseModel):
    """Data structure for creating entities."""
    
    entity_type: str
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    image_url: Optional[str] = None
    price_from: Optional[Decimal] = None
    metadata: Optional[Dict[str, Any]] = None


class EntityUpdateData(BaseModel):
    """Data structure for updating entities."""
    
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    image_url: Optional[str] = None
    price_from: Optional[Decimal] = None
    metadata: Optional[Dict[str, Any]] = None


# ============================================================================
# Profile-Specific Types
# ============================================================================

class ProfilePathData(BaseModel):
    """Data structure for profile dependency paths."""
    
    company_id: int = Field(..., gt=0)
    material_id: int = Field(..., gt=0)
    opening_system_id: int = Field(..., gt=0)
    system_series_id: int = Field(..., gt=0)
    color_id: int = Field(..., gt=0)


class ProfileDependentOptions(BaseModel):
    """Data structure for profile dependent options request."""
    
    company_id: Optional[int] = None
    material_id: Optional[int] = None
    opening_system_id: Optional[int] = None
    system_series_id: Optional[int] = None


# ============================================================================
# Glazing-Specific Types
# ============================================================================

class GlazingComponentData(BaseModel):
    """Data structure for glazing components."""

    component_type: str = Field(..., description="Component type")
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    price_per_sqm: Optional[Decimal] = None

    # Component-specific properties
    thickness: Optional[float] = None
    light_transmittance: Optional[float] = None
    u_value: Optional[float] = None
    material: Optional[str] = None
    thermal_conductivity: Optional[float] = None
    density: Optional[float] = None

    @field_validator("component_type")
    @classmethod
    def validate_component_type(cls, v: str) -> str:
        valid = RuntimeConfigLoader.get_entity_types("glazing")
        if valid and v not in valid:
            raise ValueError(f"Invalid component type '{v}'. Must be one of: {valid}")
        return v


class GlazingUnitData(BaseModel):
    """Data structure for glazing units."""

    name: str = Field(..., min_length=1, max_length=200)
    glazing_type: str = Field(..., description="Glazing unit type")
    description: Optional[str] = None

    # Component references
    outer_glass_id: Optional[int] = None
    middle_glass_id: Optional[int] = None
    inner_glass_id: Optional[int] = None
    spacer1_id: Optional[int] = None
    spacer2_id: Optional[int] = None
    gas_id: Optional[int] = None

    @field_validator("glazing_type")
    @classmethod
    def validate_glazing_type(cls, v: str) -> str:
        valid = RuntimeConfigLoader.get_glazing_types()
        if valid and v not in valid:
            raise ValueError(f"Invalid glazing type '{v}'. Must be one of: {valid}")
        return v


class CalculationResult(BaseModel):
    """Result of glazing unit calculations."""
    
    total_thickness: float
    u_value: float
    price_per_sqm: Decimal
    weight_per_sqm: float
    technical_properties: Dict[str, Any]


# ============================================================================
# Service Protocol
# ============================================================================

# Type variable for service implementations
ServiceType = TypeVar('ServiceType', bound='ServiceProtocol')


class ServiceProtocol(Protocol):
    """Protocol defining the interface for product definition services."""
    
    scope: str
    
    async def get_entities(self, entity_type: str) -> List[EntityData]:
        """Get entities of specific type for this scope."""
        ...
    
    async def create_entity(self, data: EntityCreateData) -> EntityData:
        """Create entity for this scope."""
        ...
    
    async def update_entity(self, entity_id: int, data: EntityUpdateData) -> Optional[EntityData]:
        """Update entity for this scope."""
        ...
    
    async def delete_entity(self, entity_id: int) -> Dict[str, Any]:
        """Delete entity for this scope."""
        ...
    
    async def get_scope_metadata(self) -> Dict[str, Any]:
        """Get metadata for this scope."""
        ...