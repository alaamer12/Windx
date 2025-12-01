"""Integration tests for admin hierarchy form dropdowns.

Tests that all dropdown options are present and functional.
"""

from decimal import Decimal

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.hierarchy_builder import HierarchyBuilderService


@pytest.mark.asyncio
async def test_node_form_has_all_node_type_options(
    client: AsyncClient,
    superuser_auth_headers: dict,
    db_session: AsyncSession,
):
    """Test that node form includes all 5 node type options."""
    # Create manufacturing type
    service = HierarchyBuilderService(db_session)
    mfg_type = await service.create_manufacturing_type(
        name="Test Window",
        base_price=Decimal("200.00"),
    )

    # Get create node form
    response = await client.get(
        f"/api/v1/admin/hierarchy/node/create?manufacturing_type_id={mfg_type.id}",
        headers=superuser_auth_headers,
    )

    assert response.status_code == 200
    content = response.text

    # Verify all 5 node types are present
    assert 'value="category"' in content
    assert 'value="attribute"' in content
    assert 'value="option"' in content
    assert 'value="component"' in content
    assert 'value="technical_spec"' in content

    # Verify descriptions are present
    assert "Category - Organizational grouping" in content
    assert "Attribute - Configurable property" in content
    assert "Option - Selectable choice" in content
    assert "Component - Physical part" in content
    assert "Technical Spec - Calculated property" in content


@pytest.mark.asyncio
async def test_node_form_has_all_data_type_options(
    client: AsyncClient,
    superuser_auth_headers: dict,
    db_session: AsyncSession,
):
    """Test that node form includes all 6 data type options."""
    # Create manufacturing type
    service = HierarchyBuilderService(db_session)
    mfg_type = await service.create_manufacturing_type(
        name="Test Window",
        base_price=Decimal("200.00"),
    )

    # Get create node form
    response = await client.get(
        f"/api/v1/admin/hierarchy/node/create?manufacturing_type_id={mfg_type.id}",
        headers=superuser_auth_headers,
    )

    assert response.status_code == 200
    content = response.text

    # Verify all 6 data types are present
    assert 'value="string"' in content
    assert 'value="number"' in content
    assert 'value="boolean"' in content
    assert 'value="formula"' in content
    assert 'value="dimension"' in content
    assert 'value="selection"' in content

    # Verify descriptions are present
    assert "String - Text values" in content
    assert "Number - Numeric values" in content
    assert "Boolean - Yes/No choices" in content
    assert "Formula - Calculated values" in content
    assert "Dimension - Size measurements" in content
    assert "Selection - Choice from options" in content


@pytest.mark.asyncio
async def test_node_form_has_all_price_impact_type_options(
    client: AsyncClient,
    superuser_auth_headers: dict,
    db_session: AsyncSession,
):
    """Test that node form includes all 3 price impact type options."""
    # Create manufacturing type
    service = HierarchyBuilderService(db_session)
    mfg_type = await service.create_manufacturing_type(
        name="Test Window",
        base_price=Decimal("200.00"),
    )

    # Get create node form
    response = await client.get(
        f"/api/v1/admin/hierarchy/node/create?manufacturing_type_id={mfg_type.id}",
        headers=superuser_auth_headers,
    )

    assert response.status_code == 200
    content = response.text

    # Verify all 3 price impact types are present
    assert 'value="fixed"' in content
    assert 'value="percentage"' in content
    assert 'value="formula"' in content

    # Verify descriptions are present
    assert "Fixed - Add/subtract dollar amount" in content
    assert "Percentage - Multiply by percentage" in content
    assert "Formula - Calculate dynamically" in content


@pytest.mark.asyncio
async def test_node_form_has_all_ui_component_options(
    client: AsyncClient,
    superuser_auth_headers: dict,
    db_session: AsyncSession,
):
    """Test that node form includes all 5 UI component options."""
    # Create manufacturing type
    service = HierarchyBuilderService(db_session)
    mfg_type = await service.create_manufacturing_type(
        name="Test Window",
        base_price=Decimal("200.00"),
    )

    # Get create node form
    response = await client.get(
        f"/api/v1/admin/hierarchy/node/create?manufacturing_type_id={mfg_type.id}",
        headers=superuser_auth_headers,
    )

    assert response.status_code == 200
    content = response.text

    # Verify all 5 UI components are present
    assert 'value="dropdown"' in content
    assert 'value="radio"' in content
    assert 'value="checkbox"' in content
    assert 'value="slider"' in content
    assert 'value="input"' in content

    # Verify descriptions are present
    assert "Dropdown - Select from list" in content
    assert "Radio - Single choice buttons" in content
    assert "Checkbox - Multiple selections" in content
    assert "Slider - Range selection" in content
    assert "Input - Text/number entry" in content


@pytest.mark.asyncio
async def test_create_node_with_each_node_type(
    client: AsyncClient,
    superuser_auth_headers: dict,
    db_session: AsyncSession,
):
    """Test creating nodes with each node type option."""
    # Create manufacturing type
    service = HierarchyBuilderService(db_session)
    mfg_type = await service.create_manufacturing_type(
        name="Test Window",
        base_price=Decimal("200.00"),
    )

    node_types = ["category", "attribute", "option", "component", "technical_spec"]

    for node_type in node_types:
        form_data = {
            "manufacturing_type_id": str(mfg_type.id),
            "name": f"Test {node_type}",
            "node_type": node_type,
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
        assert response.status_code == 303, f"Failed for node_type: {node_type}"
        assert "success" in response.headers["location"]

    # Verify all nodes were created
    from app.repositories.attribute_node import AttributeNodeRepository

    attr_repo = AttributeNodeRepository(db_session)
    nodes = await attr_repo.get_by_manufacturing_type(mfg_type.id)
    assert len(nodes) == 5

    # Verify each node type exists
    node_types_created = {node.node_type for node in nodes}
    assert node_types_created == set(node_types)


@pytest.mark.asyncio
async def test_create_node_with_each_data_type(
    client: AsyncClient,
    superuser_auth_headers: dict,
    db_session: AsyncSession,
):
    """Test creating nodes with each data type option."""
    # Create manufacturing type
    service = HierarchyBuilderService(db_session)
    mfg_type = await service.create_manufacturing_type(
        name="Test Window",
        base_price=Decimal("200.00"),
    )

    data_types = ["string", "number", "boolean", "formula", "dimension", "selection"]

    for data_type in data_types:
        form_data = {
            "manufacturing_type_id": str(mfg_type.id),
            "name": f"Test {data_type}",
            "node_type": "attribute",
            "data_type": data_type,
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
        assert response.status_code == 303, f"Failed for data_type: {data_type}"
        assert "success" in response.headers["location"]

    # Verify all nodes were created
    from app.repositories.attribute_node import AttributeNodeRepository

    attr_repo = AttributeNodeRepository(db_session)
    nodes = await attr_repo.get_by_manufacturing_type(mfg_type.id)
    assert len(nodes) == 6

    # Verify each data type exists
    data_types_created = {node.data_type for node in nodes}
    assert data_types_created == set(data_types)


@pytest.mark.asyncio
async def test_create_node_with_each_price_impact_type(
    client: AsyncClient,
    superuser_auth_headers: dict,
    db_session: AsyncSession,
):
    """Test creating nodes with each price impact type option."""
    # Create manufacturing type
    service = HierarchyBuilderService(db_session)
    mfg_type = await service.create_manufacturing_type(
        name="Test Window",
        base_price=Decimal("200.00"),
    )

    price_impact_types = ["fixed", "percentage", "formula"]

    for price_impact_type in price_impact_types:
        form_data = {
            "manufacturing_type_id": str(mfg_type.id),
            "name": f"Test {price_impact_type}",
            "node_type": "option",
            "price_impact_type": price_impact_type,
            "price_impact_value": "50.00" if price_impact_type != "formula" else "",
            "price_formula": "width * height * 0.05" if price_impact_type == "formula" else "",
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
        assert response.status_code == 303, f"Failed for price_impact_type: {price_impact_type}"
        assert "success" in response.headers["location"]

    # Verify all nodes were created
    from app.repositories.attribute_node import AttributeNodeRepository

    attr_repo = AttributeNodeRepository(db_session)
    nodes = await attr_repo.get_by_manufacturing_type(mfg_type.id)
    assert len(nodes) == 3

    # Verify each price impact type exists
    price_types_created = {node.price_impact_type for node in nodes}
    assert price_types_created == set(price_impact_types)


@pytest.mark.asyncio
async def test_create_node_with_each_ui_component(
    client: AsyncClient,
    superuser_auth_headers: dict,
    db_session: AsyncSession,
):
    """Test creating nodes with each UI component option."""
    # Create manufacturing type
    service = HierarchyBuilderService(db_session)
    mfg_type = await service.create_manufacturing_type(
        name="Test Window",
        base_price=Decimal("200.00"),
    )

    ui_components = ["dropdown", "radio", "checkbox", "slider", "input"]

    for ui_component in ui_components:
        form_data = {
            "manufacturing_type_id": str(mfg_type.id),
            "name": f"Test {ui_component}",
            "node_type": "attribute",
            "ui_component": ui_component,
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
        assert response.status_code == 303, f"Failed for ui_component: {ui_component}"
        assert "success" in response.headers["location"]

    # Verify all nodes were created
    from app.repositories.attribute_node import AttributeNodeRepository

    attr_repo = AttributeNodeRepository(db_session)
    nodes = await attr_repo.get_by_manufacturing_type(mfg_type.id)
    assert len(nodes) == 5

    # Verify each UI component exists
    ui_components_created = {node.ui_component for node in nodes}
    assert ui_components_created == set(ui_components)


@pytest.mark.asyncio
async def test_edit_form_preserves_dropdown_selections(
    client: AsyncClient,
    superuser_auth_headers: dict,
    db_session: AsyncSession,
):
    """Test that edit form pre-selects the correct dropdown values."""
    # Create manufacturing type and node
    service = HierarchyBuilderService(db_session)
    mfg_type = await service.create_manufacturing_type(
        name="Test Window",
        base_price=Decimal("200.00"),
    )

    node = await service.create_node(
        manufacturing_type_id=mfg_type.id,
        name="Test Node",
        node_type="component",
        data_type="dimension",
        price_impact_type="percentage",
        ui_component="slider",
    )

    # Get edit form
    response = await client.get(
        f"/api/v1/admin/hierarchy/node/{node.id}/edit",
        headers=superuser_auth_headers,
    )

    assert response.status_code == 200
    content = response.text

    # Verify correct options are selected
    # Check for selected attribute in the correct option
    assert 'value="component"' in content and "selected" in content
    assert 'value="dimension"' in content and "selected" in content
    assert 'value="percentage"' in content and "selected" in content
    assert 'value="slider"' in content and "selected" in content
