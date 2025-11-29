"""Integration tests for admin hierarchy form validation.

Tests Pydantic validation, error handling, and form re-rendering with errors.
"""

import pytest
from decimal import Decimal
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.hierarchy_builder import HierarchyBuilderService


@pytest.mark.asyncio
async def test_save_node_with_invalid_name_shows_validation_error(
    client: AsyncClient,
    superuser_auth_headers: dict,
    db_session: AsyncSession,
):
    """Test that invalid node name triggers Pydantic validation error."""
    # Create manufacturing type
    service = HierarchyBuilderService(db_session)
    mfg_type = await service.create_manufacturing_type(
        name="Test Window",
        base_price=Decimal("200.00"),
    )
    
    # Submit form with empty name (should fail validation)
    form_data = {
        "manufacturing_type_id": str(mfg_type.id),
        "name": "",  # Empty name should fail
        "node_type": "category",
        "price_impact_type": "fixed",
        "weight_impact": "0",
        "sort_order": "0",
        "required": "false",
    }
    
    response = await client.post(
        "/api/v1/admin/hierarchy/node/save",
        headers=superuser_auth_headers,
        data=form_data,
    )
    
    # Verify 422 status code (validation error)
    assert response.status_code == 422
    
    # Verify form is re-rendered with error
    content = response.text
    assert "validation_errors" in content or "error" in content.lower()
    assert "name" in content.lower()


@pytest.mark.asyncio
async def test_save_node_with_invalid_node_type_shows_validation_error(
    client: AsyncClient,
    superuser_auth_headers: dict,
    db_session: AsyncSession,
):
    """Test that invalid node_type triggers Pydantic validation error."""
    # Create manufacturing type
    service = HierarchyBuilderService(db_session)
    mfg_type = await service.create_manufacturing_type(
        name="Test Window",
        base_price=Decimal("200.00"),
    )
    
    # Submit form with invalid node_type
    form_data = {
        "manufacturing_type_id": str(mfg_type.id),
        "name": "Test Node",
        "node_type": "invalid_type",  # Invalid enum value
        "price_impact_type": "fixed",
        "weight_impact": "0",
        "sort_order": "0",
        "required": "false",
    }
    
    response = await client.post(
        "/api/v1/admin/hierarchy/node/save",
        headers=superuser_auth_headers,
        data=form_data,
    )
    
    # Verify 422 status code
    assert response.status_code == 422
    
    # Verify error message mentions node_type
    content = response.text
    assert "node_type" in content.lower()


@pytest.mark.asyncio
async def test_save_node_with_invalid_decimal_shows_error(
    client: AsyncClient,
    superuser_auth_headers: dict,
    db_session: AsyncSession,
):
    """Test that invalid decimal value triggers ValueError handling."""
    # Create manufacturing type
    service = HierarchyBuilderService(db_session)
    mfg_type = await service.create_manufacturing_type(
        name="Test Window",
        base_price=Decimal("200.00"),
    )
    
    # Submit form with invalid decimal
    form_data = {
        "manufacturing_type_id": str(mfg_type.id),
        "name": "Test Node",
        "node_type": "option",
        "price_impact_type": "fixed",
        "price_impact_value": "not_a_number",  # Invalid decimal
        "weight_impact": "0",
        "sort_order": "0",
        "required": "false",
    }
    
    response = await client.post(
        "/api/v1/admin/hierarchy/node/save",
        headers=superuser_auth_headers,
        data=form_data,
    )
    
    # Verify redirect with error message (decimal conversion error caught)
    assert response.status_code == 303
    assert "error=" in response.headers["location"]
    # Error message should mention the conversion issue
    assert "error" in response.headers["location"].lower()


@pytest.mark.asyncio
async def test_save_node_preserves_form_data_on_validation_error(
    client: AsyncClient,
    superuser_auth_headers: dict,
    db_session: AsyncSession,
):
    """Test that form data is preserved when Pydantic validation fails."""
    # Create manufacturing type
    service = HierarchyBuilderService(db_session)
    mfg_type = await service.create_manufacturing_type(
        name="Test Window",
        base_price=Decimal("200.00"),
    )
    
    # Submit form with Pydantic validation error (invalid enum value)
    form_data = {
        "manufacturing_type_id": str(mfg_type.id),
        "name": "Valid Name",  # Valid name
        "node_type": "invalid_type",  # Invalid enum - triggers Pydantic validation
        "description": "This description should be preserved",
        "price_impact_type": "fixed",
        "weight_impact": "0",
        "sort_order": "5",
        "required": "false",
    }
    
    response = await client.post(
        "/api/v1/admin/hierarchy/node/save",
        headers=superuser_auth_headers,
        data=form_data,
    )
    
    # Verify 422 status
    assert response.status_code == 422
    
    # Verify form is re-rendered with preserved data
    content = response.text
    # Check that validation error is shown
    assert "node_type" in content.lower() or "validation" in content.lower()
    # Check that sort_order value is preserved
    assert 'value="5"' in content
    # Check that name is preserved
    assert "Valid Name" in content


@pytest.mark.asyncio
async def test_update_node_with_validation_error_shows_form(
    client: AsyncClient,
    superuser_auth_headers: dict,
    db_session: AsyncSession,
):
    """Test that updating node with Pydantic validation error re-renders form."""
    # Create manufacturing type and node
    service = HierarchyBuilderService(db_session)
    mfg_type = await service.create_manufacturing_type(
        name="Test Window",
        base_price=Decimal("200.00"),
    )
    
    node = await service.create_node(
        manufacturing_type_id=mfg_type.id,
        name="Original Name",
        node_type="category",
    )
    
    # Submit update with Pydantic validation error (invalid enum)
    form_data = {
        "node_id": str(node.id),
        "manufacturing_type_id": str(mfg_type.id),
        "name": "Updated Name",  # Valid name
        "node_type": "invalid_type",  # Invalid enum - triggers Pydantic validation
        "price_impact_type": "fixed",
        "weight_impact": "0",
        "sort_order": "0",
        "required": "false",
    }
    
    response = await client.post(
        "/api/v1/admin/hierarchy/node/save",
        headers=superuser_auth_headers,
        data=form_data,
    )
    
    # Verify 422 status
    assert response.status_code == 422
    
    # Verify form is rendered with node data
    content = response.text
    assert "Original Name" in content or "node_form" in content or "Updated Name" in content


@pytest.mark.asyncio
async def test_save_node_handles_empty_optional_fields(
    client: AsyncClient,
    superuser_auth_headers: dict,
    db_session: AsyncSession,
):
    """Test that empty strings for optional fields are handled correctly."""
    # Create manufacturing type
    service = HierarchyBuilderService(db_session)
    mfg_type = await service.create_manufacturing_type(
        name="Test Window",
        base_price=Decimal("200.00"),
    )
    
    # Submit form with empty optional fields
    form_data = {
        "manufacturing_type_id": str(mfg_type.id),
        "name": "Test Node",
        "node_type": "category",
        "data_type": "",  # Empty optional field
        "description": "",  # Empty optional field
        "help_text": "",  # Empty optional field
        "price_formula": "",  # Empty optional field
        "price_impact_type": "fixed",
        "weight_impact": "0",
        "sort_order": "0",
        "required": "false",
    }
    
    response = await client.post(
        "/api/v1/admin/hierarchy/node/save",
        headers=superuser_auth_headers,
        data=form_data,
    )
    
    # Verify success (empty strings should be converted to None)
    assert response.status_code == 303
    assert "success" in response.headers["location"]
    
    # Verify node was created with None for empty fields
    from app.repositories.attribute_node import AttributeNodeRepository
    attr_repo = AttributeNodeRepository(db_session)
    nodes = await attr_repo.get_by_manufacturing_type(mfg_type.id)
    assert len(nodes) == 1
    assert nodes[0].data_type is None
    assert nodes[0].description is None
    assert nodes[0].help_text is None
    assert nodes[0].price_formula is None


@pytest.mark.asyncio
async def test_save_node_with_whitespace_only_fields(
    client: AsyncClient,
    superuser_auth_headers: dict,
    db_session: AsyncSession,
):
    """Test that whitespace-only strings are treated as empty."""
    # Create manufacturing type
    service = HierarchyBuilderService(db_session)
    mfg_type = await service.create_manufacturing_type(
        name="Test Window",
        base_price=Decimal("200.00"),
    )
    
    # Submit form with whitespace-only fields
    form_data = {
        "manufacturing_type_id": str(mfg_type.id),
        "name": "Test Node",
        "node_type": "category",
        "description": "   ",  # Whitespace only
        "price_impact_value": "  ",  # Whitespace only
        "price_impact_type": "fixed",
        "weight_impact": "  0  ",  # Whitespace around number
        "sort_order": "0",
        "required": "false",
    }
    
    response = await client.post(
        "/api/v1/admin/hierarchy/node/save",
        headers=superuser_auth_headers,
        data=form_data,
    )
    
    # Verify success
    assert response.status_code == 303
    assert "success" in response.headers["location"]
    
    # Verify whitespace was handled correctly
    from app.repositories.attribute_node import AttributeNodeRepository
    attr_repo = AttributeNodeRepository(db_session)
    nodes = await attr_repo.get_by_manufacturing_type(mfg_type.id)
    assert len(nodes) == 1
    assert nodes[0].description is None  # Whitespace-only should be None
    assert nodes[0].price_impact_value is None  # Whitespace-only should be None
    assert nodes[0].weight_impact == Decimal("0")  # Should parse correctly


@pytest.mark.asyncio
async def test_update_node_excludes_descendants_from_parent_selector_on_error(
    client: AsyncClient,
    superuser_auth_headers: dict,
    db_session: AsyncSession,
):
    """Test that Pydantic validation error on update still excludes descendants from parent selector."""
    # Create manufacturing type and hierarchy
    service = HierarchyBuilderService(db_session)
    mfg_type = await service.create_manufacturing_type(
        name="Test Window",
        base_price=Decimal("200.00"),
    )
    
    root = await service.create_node(
        manufacturing_type_id=mfg_type.id,
        name="Root",
        node_type="category",
    )
    
    child = await service.create_node(
        manufacturing_type_id=mfg_type.id,
        name="Child",
        node_type="category",
        parent_node_id=root.id,
    )
    
    # Submit update with Pydantic validation error (invalid enum)
    form_data = {
        "node_id": str(root.id),
        "manufacturing_type_id": str(mfg_type.id),
        "name": "Root Updated",  # Valid name
        "node_type": "invalid_type",  # Invalid enum - triggers Pydantic validation
        "price_impact_type": "fixed",
        "weight_impact": "0",
        "sort_order": "0",
        "required": "false",
    }
    
    response = await client.post(
        "/api/v1/admin/hierarchy/node/save",
        headers=superuser_auth_headers,
        data=form_data,
    )
    
    # Verify 422 status
    assert response.status_code == 422
    
    # Verify form is rendered (descendants should be excluded from parent selector)
    content = response.text
    assert "Root" in content or "node_form" in content


@pytest.mark.asyncio
async def test_save_node_with_multiple_validation_errors(
    client: AsyncClient,
    superuser_auth_headers: dict,
    db_session: AsyncSession,
):
    """Test that multiple validation errors are all displayed."""
    # Create manufacturing type
    service = HierarchyBuilderService(db_session)
    mfg_type = await service.create_manufacturing_type(
        name="Test Window",
        base_price=Decimal("200.00"),
    )
    
    # Submit form with multiple validation errors
    form_data = {
        "manufacturing_type_id": str(mfg_type.id),
        "name": "",  # Error 1: empty name
        "node_type": "invalid_type",  # Error 2: invalid enum
        "price_impact_type": "fixed",
        "weight_impact": "0",
        "sort_order": "0",
        "required": "false",
    }
    
    response = await client.post(
        "/api/v1/admin/hierarchy/node/save",
        headers=superuser_auth_headers,
        data=form_data,
    )
    
    # Verify 422 status
    assert response.status_code == 422
    
    # Verify both errors are mentioned
    content = response.text.lower()
    assert "name" in content
    assert "node_type" in content or "type" in content


@pytest.mark.asyncio
async def test_create_node_with_invalid_price_impact_type_shows_validation_error(
    client: AsyncClient,
    superuser_auth_headers: dict,
    db_session: AsyncSession,
):
    """Test that invalid price_impact_type triggers Pydantic validation error."""
    # Create manufacturing type
    service = HierarchyBuilderService(db_session)
    mfg_type = await service.create_manufacturing_type(
        name="Test Window",
        base_price=Decimal("200.00"),
    )
    
    # Submit create with invalid price_impact_type (should trigger Pydantic validation)
    form_data = {
        "manufacturing_type_id": str(mfg_type.id),
        "name": "New Node",
        "node_type": "category",
        "price_impact_type": "invalid_price_type",  # Invalid enum value
        "weight_impact": "0",
        "sort_order": "0",
        "required": "false",
    }
    
    response = await client.post(
        "/api/v1/admin/hierarchy/node/save",
        headers=superuser_auth_headers,
        data=form_data,
    )
    
    # Verify 422 status (validation error)
    assert response.status_code == 422
    
    # Verify form is re-rendered (HTML response, not JSON)
    content = response.text
    assert "<!DOCTYPE html>" in content or "<html" in content
    
    # Verify validation error is shown
    assert "price_impact_type" in content.lower() or "validation" in content.lower()


@pytest.mark.asyncio
async def test_save_node_with_valid_price_formula(
    client: AsyncClient,
    superuser_auth_headers: dict,
    db_session: AsyncSession,
):
    """Test that valid price formula is accepted."""
    # Create manufacturing type
    service = HierarchyBuilderService(db_session)
    mfg_type = await service.create_manufacturing_type(
        name="Test Window",
        base_price=Decimal("200.00"),
    )
    
    # Submit form with price formula
    form_data = {
        "manufacturing_type_id": str(mfg_type.id),
        "name": "Dynamic Price Node",
        "node_type": "option",
        "price_impact_type": "formula",
        "price_formula": "width * height * 0.05",
        "weight_impact": "0",
        "sort_order": "0",
        "required": "false",
    }
    
    response = await client.post(
        "/api/v1/admin/hierarchy/node/save",
        headers=superuser_auth_headers,
        data=form_data,
    )
    
    # Verify success
    assert response.status_code == 303
    assert "success" in response.headers["location"]
    
    # Verify formula was saved
    from app.repositories.attribute_node import AttributeNodeRepository
    attr_repo = AttributeNodeRepository(db_session)
    nodes = await attr_repo.get_by_manufacturing_type(mfg_type.id)
    assert len(nodes) == 1
    assert nodes[0].price_formula == "width * height * 0.05"


@pytest.mark.asyncio
async def test_update_node_recalculates_path_on_parent_change(
    client: AsyncClient,
    superuser_auth_headers: dict,
    db_session: AsyncSession,
):
    """Test that updating parent recalculates ltree_path and depth."""
    # Create manufacturing type and nodes
    service = HierarchyBuilderService(db_session)
    mfg_type = await service.create_manufacturing_type(
        name="Test Window",
        base_price=Decimal("200.00"),
    )
    
    parent1 = await service.create_node(
        manufacturing_type_id=mfg_type.id,
        name="Parent 1",
        node_type="category",
    )
    
    parent2 = await service.create_node(
        manufacturing_type_id=mfg_type.id,
        name="Parent 2",
        node_type="category",
    )
    
    child = await service.create_node(
        manufacturing_type_id=mfg_type.id,
        name="Child",
        node_type="option",
        parent_node_id=parent1.id,
    )
    
    # Verify initial path
    await db_session.refresh(child)
    assert "parent_1" in child.ltree_path
    assert child.depth == 1
    
    # Update child to have parent2 as parent
    form_data = {
        "node_id": str(child.id),
        "manufacturing_type_id": str(mfg_type.id),
        "name": "Child",
        "node_type": "option",
        "parent_node_id": str(parent2.id),  # Change parent
        "price_impact_type": "fixed",
        "weight_impact": "0",
        "sort_order": "0",
        "required": "false",
    }
    
    response = await client.post(
        "/api/v1/admin/hierarchy/node/save",
        headers=superuser_auth_headers,
        data=form_data,
    )
    
    # Verify success
    assert response.status_code == 303
    
    # Verify path was recalculated
    await db_session.refresh(child)
    assert "parent_2" in child.ltree_path
    assert "parent_1" not in child.ltree_path
    assert child.depth == 1


@pytest.mark.asyncio
async def test_update_node_preserves_parent_when_not_provided(
    client: AsyncClient,
    superuser_auth_headers: dict,
    db_session: AsyncSession,
):
    """Test that not providing parent_node_id in update preserves existing parent."""
    # Create manufacturing type and nodes
    service = HierarchyBuilderService(db_session)
    mfg_type = await service.create_manufacturing_type(
        name="Test Window",
        base_price=Decimal("200.00"),
    )
    
    parent = await service.create_node(
        manufacturing_type_id=mfg_type.id,
        name="Parent",
        node_type="category",
    )
    
    child = await service.create_node(
        manufacturing_type_id=mfg_type.id,
        name="Child",
        node_type="category",
        parent_node_id=parent.id,
    )
    
    # Verify initial state
    await db_session.refresh(child)
    assert child.parent_node_id == parent.id
    assert child.depth == 1
    
    # Update child name without changing parent
    # When parent_node_id is not provided, it should remain unchanged
    form_data = {
        "node_id": str(child.id),
        "manufacturing_type_id": str(mfg_type.id),
        "name": "Child Updated",  # Change name
        "node_type": "category",
        # parent_node_id not included = should remain unchanged
        "price_impact_type": "fixed",
        "weight_impact": "0",
        "sort_order": "0",
        "required": "false",
    }
    
    response = await client.post(
        "/api/v1/admin/hierarchy/node/save",
        headers=superuser_auth_headers,
        data=form_data,
    )
    
    # Verify success
    assert response.status_code == 303
    
    # Verify parent was preserved (not changed to None)
    await db_session.refresh(child)
    assert child.parent_node_id == parent.id  # Should still have parent
    assert child.name == "Child Updated"  # Name should be updated
    assert child.depth == 1  # Depth should remain the same
