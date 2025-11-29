"""Integration tests for admin hierarchy management endpoints.

Tests the admin dashboard endpoints for managing hierarchical attribute data.
"""

import pytest
from decimal import Decimal
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.hierarchy_builder import HierarchyBuilderService


@pytest.mark.asyncio
async def test_hierarchy_dashboard_no_type_selected(
    client: AsyncClient,
    superuser_auth_headers: dict,
    db_session: AsyncSession,
):
    """Test dashboard renders with no manufacturing type selected."""
    # Create a manufacturing type for the selector
    service = HierarchyBuilderService(db_session)
    await service.create_manufacturing_type(
        name="Test Window",
        description="Test window type",
        base_price=Decimal("200.00"),
    )
    
    # Request dashboard without type selection
    response = await client.get(
        "/api/v1/admin/hierarchy/",
        headers=superuser_auth_headers,
    )
    
    # Verify response
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    
    # Verify content contains expected elements
    content = response.text
    assert "Hierarchy Management Dashboard" in content
    assert "Test Window" in content
    assert "Select a Manufacturing Type" in content


@pytest.mark.asyncio
async def test_hierarchy_dashboard_with_type_selected(
    client: AsyncClient,
    superuser_auth_headers: dict,
    db_session: AsyncSession,
):
    """Test dashboard renders with manufacturing type selected."""
    # Create manufacturing type and hierarchy
    service = HierarchyBuilderService(db_session)
    mfg_type = await service.create_manufacturing_type(
        name="Test Window",
        description="Test window type",
        base_price=Decimal("200.00"),
    )
    
    # Create simple hierarchy
    root = await service.create_node(
        manufacturing_type_id=mfg_type.id,
        name="Frame Options",
        node_type="category",
    )
    
    child = await service.create_node(
        manufacturing_type_id=mfg_type.id,
        name="Material Type",
        node_type="attribute",
        parent_node_id=root.id,
    )
    
    # Request dashboard with type selection
    response = await client.get(
        f"/api/v1/admin/hierarchy/?manufacturing_type_id={mfg_type.id}",
        headers=superuser_auth_headers,
    )
    
    # Verify response
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    
    # Verify content contains tree data
    content = response.text
    assert "Frame Options" in content
    assert "Material Type" in content
    assert "Attribute Tree" in content


@pytest.mark.asyncio
async def test_hierarchy_dashboard_shows_ascii_tree(
    client: AsyncClient,
    superuser_auth_headers: dict,
    db_session: AsyncSession,
):
    """Test dashboard includes ASCII tree visualization."""
    # Create manufacturing type and hierarchy
    service = HierarchyBuilderService(db_session)
    mfg_type = await service.create_manufacturing_type(
        name="Test Window",
        base_price=Decimal("200.00"),
    )
    
    root = await service.create_node(
        manufacturing_type_id=mfg_type.id,
        name="Frame Options",
        node_type="category",
    )
    
    child = await service.create_node(
        manufacturing_type_id=mfg_type.id,
        name="Aluminum",
        node_type="option",
        parent_node_id=root.id,
        price_impact_value=Decimal("50.00"),
    )
    
    # Request dashboard
    response = await client.get(
        f"/api/v1/admin/hierarchy/?manufacturing_type_id={mfg_type.id}",
        headers=superuser_auth_headers,
    )
    
    # Verify ASCII tree is present
    assert response.status_code == 200
    content = response.text
    assert "ASCII Tree Visualization" in content
    assert "Frame Options [category]" in content
    assert "Aluminum [option]" in content


@pytest.mark.asyncio
async def test_hierarchy_dashboard_requires_superuser(
    client: AsyncClient,
    db_session: AsyncSession,
):
    """Test dashboard requires superuser authentication."""
    # Create manufacturing type
    service = HierarchyBuilderService(db_session)
    mfg_type = await service.create_manufacturing_type(
        name="Test Window",
        base_price=Decimal("200.00"),
    )
    
    # Request without authentication
    response = await client.get(
        f"/api/v1/admin/hierarchy/?manufacturing_type_id={mfg_type.id}",
    )
    
    # Verify unauthorized
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_hierarchy_dashboard_with_empty_tree(
    client: AsyncClient,
    superuser_auth_headers: dict,
    db_session: AsyncSession,
):
    """Test dashboard handles manufacturing type with no nodes."""
    # Create manufacturing type with no nodes
    service = HierarchyBuilderService(db_session)
    mfg_type = await service.create_manufacturing_type(
        name="Empty Type",
        base_price=Decimal("100.00"),
    )
    
    # Request dashboard
    response = await client.get(
        f"/api/v1/admin/hierarchy/?manufacturing_type_id={mfg_type.id}",
        headers=superuser_auth_headers,
    )
    
    # Verify response
    assert response.status_code == 200
    content = response.text
    assert "Empty Type" in content
    # Should show empty state message
    assert "No attribute nodes found" in content or "Empty tree" in content


@pytest.mark.asyncio
async def test_hierarchy_dashboard_diagram_failure_graceful(
    client: AsyncClient,
    superuser_auth_headers: dict,
    db_session: AsyncSession,
    monkeypatch,
):
    """Test dashboard handles diagram generation failure gracefully."""
    # Create manufacturing type and hierarchy
    service = HierarchyBuilderService(db_session)
    mfg_type = await service.create_manufacturing_type(
        name="Test Window",
        base_price=Decimal("200.00"),
    )
    
    root = await service.create_node(
        manufacturing_type_id=mfg_type.id,
        name="Frame Options",
        node_type="category",
    )
    
    # Mock plot_tree to raise exception
    async def mock_plot_tree(*args, **kwargs):
        raise Exception("Matplotlib not available")
    
    monkeypatch.setattr(
        "app.services.hierarchy_builder.HierarchyBuilderService.plot_tree",
        mock_plot_tree
    )
    
    # Request dashboard (should not crash)
    response = await client.get(
        f"/api/v1/admin/hierarchy/?manufacturing_type_id={mfg_type.id}",
        headers=superuser_auth_headers,
    )
    
    # Verify response is still successful
    assert response.status_code == 200
    content = response.text
    assert "Frame Options" in content
    # Diagram should not be present, but page should still render
    assert "Diagram visualization will appear here" in content or "No diagram" in content


@pytest.mark.asyncio
async def test_hierarchy_dashboard_with_complex_tree(
    client: AsyncClient,
    superuser_auth_headers: dict,
    db_session: AsyncSession,
):
    """Test dashboard with complex multi-level hierarchy."""
    # Create manufacturing type
    service = HierarchyBuilderService(db_session)
    mfg_type = await service.create_manufacturing_type(
        name="Complex Window",
        base_price=Decimal("200.00"),
    )
    
    # Create complex hierarchy
    hierarchy = {
        "name": "Frame Options",
        "node_type": "category",
        "children": [
            {
                "name": "Material Type",
                "node_type": "attribute",
                "children": [
                    {
                        "name": "Aluminum",
                        "node_type": "option",
                        "price_impact_value": Decimal("50.00"),
                    },
                    {
                        "name": "Vinyl",
                        "node_type": "option",
                        "price_impact_value": Decimal("30.00"),
                    },
                ],
            },
            {
                "name": "Color",
                "node_type": "attribute",
                "children": [
                    {
                        "name": "White",
                        "node_type": "option",
                    },
                    {
                        "name": "Black",
                        "node_type": "option",
                        "price_impact_value": Decimal("25.00"),
                    },
                ],
            },
        ],
    }
    
    await service.create_hierarchy_from_dict(
        manufacturing_type_id=mfg_type.id,
        hierarchy_data=hierarchy,
    )
    
    # Request dashboard
    response = await client.get(
        f"/api/v1/admin/hierarchy/?manufacturing_type_id={mfg_type.id}",
        headers=superuser_auth_headers,
    )
    
    # Verify all nodes are present
    assert response.status_code == 200
    content = response.text
    assert "Frame Options" in content
    assert "Material Type" in content
    assert "Aluminum" in content
    assert "Vinyl" in content
    assert "Color" in content
    assert "White" in content
    assert "Black" in content


@pytest.mark.asyncio
async def test_hierarchy_dashboard_multiple_manufacturing_types(
    client: AsyncClient,
    superuser_auth_headers: dict,
    db_session: AsyncSession,
):
    """Test dashboard selector shows multiple manufacturing types."""
    # Create multiple manufacturing types
    service = HierarchyBuilderService(db_session)
    
    window = await service.create_manufacturing_type(
        name="Window Type",
        base_price=Decimal("200.00"),
    )
    
    door = await service.create_manufacturing_type(
        name="Door Type",
        base_price=Decimal("300.00"),
    )
    
    # Request dashboard
    response = await client.get(
        "/api/v1/admin/hierarchy/",
        headers=superuser_auth_headers,
    )
    
    # Verify both types are in selector
    assert response.status_code == 200
    content = response.text
    assert "Window Type" in content
    assert "Door Type" in content
    assert "Select a Manufacturing Type" in content
