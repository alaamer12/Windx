"""Pydantic schemas for AttributeNode model."""

from datetime import datetime
from decimal import Decimal
from typing import Annotated, Any

from pydantic import BaseModel, ConfigDict, Field, field_validator


class DisplayCondition(BaseModel):
    """Conditional display logic for attribute nodes."""

    operator: Annotated[str, Field(description="Operator: equals, contains, gt, lt, gte, lte, exists, and, or")]
    field: Annotated[str | None, Field(default=None, description="Field to check")]
    value: Annotated[Any | None, Field(default=None, description="Value to compare")]
    conditions: Annotated[list["DisplayCondition"] | None, Field(default=None, description="Nested conditions")]

    model_config = ConfigDict(from_attributes=True)


class ValidationRule(BaseModel):
    """Validation rule definition for attribute inputs."""

    rule_type: Annotated[str, Field(description="Type: required, min, max, range, pattern, custom, length")]
    value: Annotated[Any | None, Field(default=None, description="Rule value")]
    min: Annotated[float | None, Field(default=None, description="Minimum value for range")]
    max: Annotated[float | None, Field(default=None, description="Maximum value for range")]
    pattern: Annotated[str | None, Field(default=None, description="Regex pattern for validation")]
    message: Annotated[str, Field(description="Error message to display")]

    model_config = ConfigDict(from_attributes=True)


class AttributeNodeBase(BaseModel):
    """Base schema for AttributeNode with common fields."""

    name: Annotated[str, Field(max_length=200, description="Display name of the attribute")]
    node_type: Annotated[str, Field(description="Node type: category, attribute, option, component, technical_spec")]
    data_type: Annotated[str | None, Field(default=None, description="Data type: string, number, boolean, formula, dimension, selection")]
    display_condition: Annotated[dict | None, Field(default=None, description="Conditional display logic (JSONB)")]
    validation_rules: Annotated[dict | None, Field(default=None, description="Input validation rules (JSONB)")]
    required: Annotated[bool, Field(default=False, description="Whether this attribute must be selected")]
    price_impact_type: Annotated[str, Field(default="fixed", description="How it affects price: fixed, percentage, formula")]
    price_impact_value: Annotated[Decimal | None, Field(default=None, ge=0, decimal_places=2, description="Fixed price adjustment amount")]
    price_formula: Annotated[str | None, Field(default=None, description="Dynamic price calculation formula")]
    weight_impact: Annotated[Decimal, Field(default=Decimal("0"), ge=0, decimal_places=2, description="Fixed weight addition in kg")]
    weight_formula: Annotated[str | None, Field(default=None, description="Dynamic weight calculation formula")]
    technical_property_type: Annotated[str | None, Field(default=None, max_length=50, description="Type of technical property")]
    technical_impact_formula: Annotated[str | None, Field(default=None, description="Technical calculation formula")]
    sort_order: Annotated[int, Field(default=0, description="Display order among siblings")]
    ui_component: Annotated[str | None, Field(default=None, max_length=50, description="UI control type")]
    description: Annotated[str | None, Field(default=None, description="Help text for users")]
    help_text: Annotated[str | None, Field(default=None, description="Additional guidance for users")]

    @field_validator("node_type")
    @classmethod
    def validate_node_type(cls, v: str) -> str:
        """Validate node_type is one of the allowed values."""
        allowed = {"category", "attribute", "option", "component", "technical_spec"}
        if v not in allowed:
            raise ValueError(f"node_type must be one of {allowed}, got '{v}'")
        return v

    @field_validator("data_type")
    @classmethod
    def validate_data_type(cls, v: str | None) -> str | None:
        """Validate data_type is one of the allowed values."""
        if v is None:
            return v
        allowed = {"string", "number", "boolean", "formula", "dimension", "selection"}
        if v not in allowed:
            raise ValueError(f"data_type must be one of {allowed}, got '{v}'")
        return v

    @field_validator("price_impact_type")
    @classmethod
    def validate_price_impact_type(cls, v: str) -> str:
        """Validate price_impact_type is one of the allowed values."""
        allowed = {"fixed", "percentage", "formula"}
        if v not in allowed:
            raise ValueError(f"price_impact_type must be one of {allowed}, got '{v}'")
        return v



class AttributeNodeCreate(AttributeNodeBase):
    """Schema for creating a new AttributeNode."""

    manufacturing_type_id: Annotated[int | None, Field(default=None, gt=0, description="Manufacturing type ID (null for root nodes)")]
    parent_node_id: Annotated[int | None, Field(default=None, gt=0, description="Parent node ID (null for root nodes)")]


class AttributeNodeUpdate(BaseModel):
    """Schema for updating an AttributeNode."""

    name: Annotated[str | None, Field(default=None, max_length=200)]
    node_type: Annotated[str | None, Field(default=None)]
    data_type: Annotated[str | None, Field(default=None)]
    display_condition: Annotated[dict | None, Field(default=None)]
    validation_rules: Annotated[dict | None, Field(default=None)]
    required: Annotated[bool | None, Field(default=None)]
    price_impact_type: Annotated[str | None, Field(default=None)]
    price_impact_value: Annotated[Decimal | None, Field(default=None, ge=0, decimal_places=2)]
    price_formula: Annotated[str | None, Field(default=None)]
    weight_impact: Annotated[Decimal | None, Field(default=None, ge=0, decimal_places=2)]
    weight_formula: Annotated[str | None, Field(default=None)]
    technical_property_type: Annotated[str | None, Field(default=None, max_length=50)]
    technical_impact_formula: Annotated[str | None, Field(default=None)]
    parent_node_id: Annotated[int | None, Field(default=None, gt=0)]
    sort_order: Annotated[int | None, Field(default=None)]
    ui_component: Annotated[str | None, Field(default=None, max_length=50)]
    description: Annotated[str | None, Field(default=None)]
    help_text: Annotated[str | None, Field(default=None)]

    @field_validator("node_type")
    @classmethod
    def validate_node_type(cls, v: str | None) -> str | None:
        """Validate node_type is one of the allowed values."""
        if v is None:
            return v
        allowed = {"category", "attribute", "option", "component", "technical_spec"}
        if v not in allowed:
            raise ValueError(f"node_type must be one of {allowed}, got '{v}'")
        return v

    @field_validator("data_type")
    @classmethod
    def validate_data_type(cls, v: str | None) -> str | None:
        """Validate data_type is one of the allowed values."""
        if v is None:
            return v
        allowed = {"string", "number", "boolean", "formula", "dimension", "selection"}
        if v not in allowed:
            raise ValueError(f"data_type must be one of {allowed}, got '{v}'")
        return v

    @field_validator("price_impact_type")
    @classmethod
    def validate_price_impact_type(cls, v: str | None) -> str | None:
        """Validate price_impact_type is one of the allowed values."""
        if v is None:
            return v
        allowed = {"fixed", "percentage", "formula"}
        if v not in allowed:
            raise ValueError(f"price_impact_type must be one of {allowed}, got '{v}'")
        return v



class AttributeNode(AttributeNodeBase):
    """Schema for AttributeNode response."""

    id: Annotated[int, Field(gt=0, description="Attribute node ID")]
    manufacturing_type_id: Annotated[int | None, Field(default=None, description="Manufacturing type ID")]
    parent_node_id: Annotated[int | None, Field(default=None, description="Parent node ID")]
    ltree_path: Annotated[str, Field(description="Hierarchical path (LTREE)")]
    depth: Annotated[int, Field(ge=0, description="Nesting level in the tree")]
    created_at: Annotated[datetime, Field(description="Creation timestamp")]
    updated_at: Annotated[datetime, Field(description="Last update timestamp")]

    model_config = ConfigDict(from_attributes=True)


class AttributeNodeTree(AttributeNode):
    """Schema for AttributeNode with children for tree representation."""

    children: Annotated[list["AttributeNodeTree"], Field(default_factory=list, description="Child nodes in the hierarchy")]

    model_config = ConfigDict(from_attributes=True)


class AttributeNodeWithParent(AttributeNode):
    """Schema for AttributeNode with parent information."""

    parent: Annotated[AttributeNode | None, Field(default=None, description="Parent node information")]

    model_config = ConfigDict(from_attributes=True)
