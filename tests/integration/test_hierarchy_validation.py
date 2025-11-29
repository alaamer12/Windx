"""Integration tests for hierarchy validation in HierarchyBuilderService.

This module tests the validation logic for node creation and hierarchy management.
"""

import pytest
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import (
    NotFoundException,
    ValidationException,
    ConflictException,
)
from app.services.hierarchy_builder import HierarchyBuilderService


@pytest.mark.asyncio
async def test_create_node_validates_manufacturing_type_exists(
    db_session: AsyncSession,
):
    """Test that create_node raises NotFoundException for invalid manufacturing type."""
    service = HierarchyBuilderService(db_session)
    
    with pytest.raises(NotFoundException) as exc_info:
        await service.create_node(
            manufacturing_type_id=99999,  # Non-existent ID
            name="Test Node",
            node_type="category",
        )
    
    assert "Manufacturing type with id 99999 not found" in str(exc_info.value)


@pytest.mark.asyncio
async def test_create_node_validates_parent_exists(
    db_session: AsyncSession,
):
    """Test that create_node raises NotFoundException for invalid parent."""
    service = HierarchyBuilderService(db_session)
    
    # Create manufacturing type first
    mfg_type = await service.create_manufacturing_type(
        name="Test Window",
        base_price=Decimal("100.00"),
    )
    
    with pytest.raises(NotFoundException) as exc_info:
        await service.create_node(
            manufacturing_type_id=mfg_type.id,
            name="Test Node",
            node_type="category",
            parent_node_id=99999,  # Non-existent parent
        )
    
    assert "Parent node with id 99999 not found" in str(exc_info.value)


@pytest.mark.asyncio
async def test_create_node_validates_node_type(
    db_session: AsyncSession,
):
    """Test that create_node raises ValidationException for invalid node_type."""
    service = HierarchyBuilderService(db_session)
    
    # Create manufacturing type first
    mfg_type = await service.create_manufacturing_type(
        name="Test Window",
        base_price=Decimal("100.00"),
    )
    
    with pytest.raises(ValidationException) as exc_info:
        await service.create_node(
            manufacturing_type_id=mfg_type.id,
            name="Test Node",
            node_type="invalid_type",  # Invalid node type
        )
    
    assert "Invalid node_type 'invalid_type'" in str(exc_info.value)


@pytest.mark.asyncio
async def test_create_node_detects_duplicate_names_at_same_level(
    db_session: AsyncSession,
):
    """Test that create_node raises ConflictException for duplicate names at same level."""
    service = HierarchyBuilderService(db_session)
    
    # Create manufacturing type
    mfg_type = await service.create_manufacturing_type(
        name="Test Window",
        base_price=Decimal("100.00"),
    )
    
    # Create first node
    await service.create_node(
        manufacturing_type_id=mfg_type.id,
        name="Frame Material",
        node_type="category",
    )
    
    # Try to create duplicate at same level (root)
    with pytest.raises(ConflictException) as exc_info:
        await service.create_node(
            manufacturing_type_id=mfg_type.id,
            name="Frame Material",  # Duplicate name
            node_type="category",
        )
    
    assert "already exists at root level" in str(exc_info.value)


@pytest.mark.asyncio
async def test_create_node_allows_same_name_at_different_levels(
    db_session: AsyncSession,
):
    """Test that nodes with same name are allowed at different levels."""
    service = HierarchyBuilderService(db_session)
    
    # Create manufacturing type
    mfg_type = await service.create_manufacturing_type(
        name="Test Window",
        base_price=Decimal("100.00"),
    )
    
    # Create parent node
    parent = await service.create_node(
        manufacturing_type_id=mfg_type.id,
        name="Options",
        node_type="category",
    )
    
    # Create child node with same name as parent (should be allowed)
    child = await service.create_node(
        manufacturing_type_id=mfg_type.id,
        name="Options",  # Same name as parent
        node_type="attribute",
        parent_node_id=parent.id,
    )
    
    assert child.name == "Options"
    assert child.parent_node_id == parent.id


@pytest.mark.asyncio
async def test_move_node_detects_circular_reference(
    db_session: AsyncSession,
):
    """Test that move_node raises ValidationException for circular references."""
    service = HierarchyBuilderService(db_session)
    
    # Create manufacturing type
    mfg_type = await service.create_manufacturing_type(
        name="Test Window",
        base_price=Decimal("100.00"),
    )
    
    # Create hierarchy: A -> B -> C
    node_a = await service.create_node(
        manufacturing_type_id=mfg_type.id,
        name="Node A",
        node_type="category",
    )
    
    node_b = await service.create_node(
        manufacturing_type_id=mfg_type.id,
        name="Node B",
        node_type="category",
        parent_node_id=node_a.id,
    )
    
    node_c = await service.create_node(
        manufacturing_type_id=mfg_type.id,
        name="Node C",
        node_type="category",
        parent_node_id=node_b.id,
    )
    
    # Try to move A under C (would create cycle: A -> B -> C -> A)
    with pytest.raises(ValidationException) as exc_info:
        await service.move_node(node_a.id, node_c.id)
    
    assert "circular reference" in str(exc_info.value).lower()


@pytest.mark.asyncio
async def test_move_node_validates_parent_exists(
    db_session: AsyncSession,
):
    """Test that move_node raises NotFoundException for invalid parent."""
    service = HierarchyBuilderService(db_session)
    
    # Create manufacturing type and node
    mfg_type = await service.create_manufacturing_type(
        name="Test Window",
        base_price=Decimal("100.00"),
    )
    
    node = await service.create_node(
        manufacturing_type_id=mfg_type.id,
        name="Test Node",
        node_type="category",
    )
    
    # Try to move to non-existent parent
    with pytest.raises(NotFoundException) as exc_info:
        await service.move_node(node.id, 99999)
    
    assert "New parent node with id 99999 not found" in str(exc_info.value)


@pytest.mark.asyncio
async def test_move_node_validates_same_manufacturing_type(
    db_session: AsyncSession,
):
    """Test that move_node prevents moving to parent in different manufacturing type."""
    service = HierarchyBuilderService(db_session)
    
    # Create two manufacturing types
    mfg_type1 = await service.create_manufacturing_type(
        name="Window",
        base_price=Decimal("100.00"),
    )
    
    mfg_type2 = await service.create_manufacturing_type(
        name="Door",
        base_price=Decimal("150.00"),
    )
    
    # Create nodes in different types
    node1 = await service.create_node(
        manufacturing_type_id=mfg_type1.id,
        name="Window Node",
        node_type="category",
    )
    
    node2 = await service.create_node(
        manufacturing_type_id=mfg_type2.id,
        name="Door Node",
        node_type="category",
    )
    
    # Try to move node1 under node2 (different manufacturing types)
    with pytest.raises(ValueError) as exc_info:
        await service.move_node(node1.id, node2.id)
    
    assert "different manufacturing type" in str(exc_info.value)


@pytest.mark.asyncio
async def test_move_node_successfully_moves_node(
    db_session: AsyncSession,
):
    """Test that move_node successfully moves a node to a new parent."""
    service = HierarchyBuilderService(db_session)
    
    # Create manufacturing type
    mfg_type = await service.create_manufacturing_type(
        name="Test Window",
        base_price=Decimal("100.00"),
    )
    
    # Create nodes: A, B (both at root)
    node_a = await service.create_node(
        manufacturing_type_id=mfg_type.id,
        name="Node A",
        node_type="category",
    )
    
    node_b = await service.create_node(
        manufacturing_type_id=mfg_type.id,
        name="Node B",
        node_type="category",
    )
    
    # Move B under A
    moved_node = await service.move_node(node_b.id, node_a.id)
    
    assert moved_node.parent_node_id == node_a.id
    assert moved_node.ltree_path == f"{node_a.ltree_path}.node_b"
    assert moved_node.depth == 1
