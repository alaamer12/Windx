"""End-to-end tests for admin hierarchy management.

Tests complete workflows for creating, editing, and deleting attribute nodes
through the admin UI using Playwright browser automation.
"""

from decimal import Decimal

import pytest
from playwright.async_api import Page, expect
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.hierarchy_builder import HierarchyBuilderService

# Mark all tests in this module as e2e tests
pytestmark = pytest.mark.e2e


@pytest.mark.asyncio
async def test_create_attribute_node_workflow(
    hierarchy_page: Page,
    base_url: str,
    db_session: AsyncSession,
):
    """Test creating an attribute node through admin UI.
    
    Validates:
    - Navigation to hierarchy page
    - Manufacturing type selection
    - Node creation form display
    - Form submission
    - Success message display
    - Node appears in tree
    """
    # Create manufacturing type for testing
    service = HierarchyBuilderService(db_session)
    mfg_type = await service.create_manufacturing_type(
        name="E2E Test Window",
        description="Window type for E2E testing",
        base_price=Decimal("200.00"),
    )
    
    # Navigate to hierarchy page with manufacturing type
    await hierarchy_page.goto(
        f"{base_url}/api/v1/admin/hierarchy/?manufacturing_type_id={mfg_type.id}"
    )
    await hierarchy_page.wait_for_load_state("networkidle")
    
    # Click "Create Node" button
    create_button = hierarchy_page.locator('a:has-text("Create Node")')
    await expect(create_button).to_be_visible()
    await create_button.click()
    
    # Wait for form to load
    await hierarchy_page.wait_for_url(
        f"{base_url}/api/v1/admin/hierarchy/node/create?manufacturing_type_id={mfg_type.id}"
    )
    
    # Fill node creation form
    await hierarchy_page.fill('input[name="name"]', "E2E Test Node")
    await hierarchy_page.fill('textarea[name="description"]', "Node created by E2E test")
    
    # Select node type
    await hierarchy_page.select_option('select[name="node_type"]', "category")
    
    # Submit form
    submit_button = hierarchy_page.locator('button[type="submit"]')
    await submit_button.click()
    
    # Wait for redirect back to hierarchy page
    await hierarchy_page.wait_for_url(
        f"{base_url}/api/v1/admin/hierarchy/?manufacturing_type_id={mfg_type.id}*",
        timeout=5000,
    )
    
    # Verify success message
    success_alert = hierarchy_page.locator('.alert-success')
    await expect(success_alert).to_be_visible()
    await expect(success_alert).to_contain_text("Node created successfully")
    
    # Verify node appears in tree
    node_in_tree = hierarchy_page.locator('text="E2E Test Node"')
    await expect(node_in_tree).to_be_visible()


@pytest.mark.asyncio
async def test_edit_attribute_node_workflow(
    hierarchy_page: Page,
    base_url: str,
    db_session: AsyncSession,
):
    """Test editing an attribute node through admin UI.
    
    Validates:
    - Node selection for editing
    - Edit form pre-population
    - Form modification
    - Update submission
    - Success message display
    - Updated values in tree
    """
    # Create manufacturing type and node
    service = HierarchyBuilderService(db_session)
    mfg_type = await service.create_manufacturing_type(
        name="E2E Edit Test Window",
        description="Window type for edit testing",
        base_price=Decimal("200.00"),
    )
    
    node = await service.create_node(
        manufacturing_type_id=mfg_type.id,
        name="Original Node Name",
        node_type="category",
        description="Original description",
    )
    
    # Navigate to hierarchy page
    await hierarchy_page.goto(
        f"{base_url}/api/v1/admin/hierarchy/?manufacturing_type_id={mfg_type.id}"
    )
    await hierarchy_page.wait_for_load_state("networkidle")
    
    # Find and click edit button for the node
    # Look for edit link/button associated with the node
    edit_link = hierarchy_page.locator(f'a[href*="/node/{node.id}/edit"]').first
    await expect(edit_link).to_be_visible()
    await edit_link.click()
    
    # Wait for edit form to load
    await hierarchy_page.wait_for_url(
        f"{base_url}/api/v1/admin/hierarchy/node/{node.id}/edit"
    )
    
    # Verify form is pre-populated
    name_input = hierarchy_page.locator('input[name="name"]')
    await expect(name_input).to_have_value("Original Node Name")
    
    # Update node name
    await name_input.fill("Updated Node Name")
    
    # Update description
    await hierarchy_page.fill('textarea[name="description"]', "Updated description")
    
    # Submit form
    submit_button = hierarchy_page.locator('button[type="submit"]')
    await submit_button.click()
    
    # Wait for redirect
    await hierarchy_page.wait_for_url(
        f"{base_url}/api/v1/admin/hierarchy/?manufacturing_type_id={mfg_type.id}*",
        timeout=5000,
    )
    
    # Verify success message
    success_alert = hierarchy_page.locator('.alert-success')
    await expect(success_alert).to_be_visible()
    await expect(success_alert).to_contain_text("Node updated successfully")
    
    # Verify updated name appears in tree
    updated_node = hierarchy_page.locator('text="Updated Node Name"')
    await expect(updated_node).to_be_visible()


@pytest.mark.asyncio
async def test_delete_attribute_node_with_confirmation(
    hierarchy_page: Page,
    base_url: str,
    db_session: AsyncSession,
):
    """Test deleting an attribute node with confirmation dialog.
    
    Validates:
    - Delete button display
    - Confirmation dialog appears
    - Canceling deletion
    - Confirming deletion
    - Success message display
    - Node removed from tree
    """
    # Create manufacturing type and node
    service = HierarchyBuilderService(db_session)
    mfg_type = await service.create_manufacturing_type(
        name="E2E Delete Test Window",
        description="Window type for delete testing",
        base_price=Decimal("200.00"),
    )
    
    node = await service.create_node(
        manufacturing_type_id=mfg_type.id,
        name="Node To Delete",
        node_type="category",
        description="This node will be deleted",
    )
    
    # Navigate to hierarchy page
    await hierarchy_page.goto(
        f"{base_url}/api/v1/admin/hierarchy/?manufacturing_type_id={mfg_type.id}"
    )
    await hierarchy_page.wait_for_load_state("networkidle")
    
    # Verify node exists
    node_text = hierarchy_page.locator('text="Node To Delete"')
    await expect(node_text).to_be_visible()
    
    # Set up dialog handler to accept confirmation
    hierarchy_page.on("dialog", lambda dialog: dialog.accept())
    
    # Find and click delete button
    delete_button = hierarchy_page.locator(
        f'button[onclick*="deleteNode({node.id})"], '
        f'a[onclick*="deleteNode({node.id})"]'
    ).first
    
    await expect(delete_button).to_be_visible()
    await delete_button.click()
    
    # Wait for redirect after deletion
    await hierarchy_page.wait_for_url(
        f"{base_url}/api/v1/admin/hierarchy/?manufacturing_type_id={mfg_type.id}*",
        timeout=5000,
    )
    
    # Verify success message
    success_alert = hierarchy_page.locator('.alert-success')
    await expect(success_alert).to_be_visible()
    await expect(success_alert).to_contain_text("Node deleted successfully")
    
    # Verify node is removed from tree
    deleted_node = hierarchy_page.locator('text="Node To Delete"')
    await expect(deleted_node).not_to_be_visible()


@pytest.mark.asyncio
async def test_cancel_delete_attribute_node(
    hierarchy_page: Page,
    base_url: str,
    db_session: AsyncSession,
):
    """Test canceling node deletion keeps the node.
    
    Validates:
    - Delete button click
    - Confirmation dialog appears
    - Canceling keeps node
    - Node still visible in tree
    """
    # Create manufacturing type and node
    service = HierarchyBuilderService(db_session)
    mfg_type = await service.create_manufacturing_type(
        name="E2E Cancel Delete Test",
        description="Window type for cancel delete testing",
        base_price=Decimal("200.00"),
    )
    
    node = await service.create_node(
        manufacturing_type_id=mfg_type.id,
        name="Node To Keep",
        node_type="category",
        description="This node will not be deleted",
    )
    
    # Navigate to hierarchy page
    await hierarchy_page.goto(
        f"{base_url}/api/v1/admin/hierarchy/?manufacturing_type_id={mfg_type.id}"
    )
    await hierarchy_page.wait_for_load_state("networkidle")
    
    # Set up dialog handler to dismiss confirmation
    hierarchy_page.on("dialog", lambda dialog: dialog.dismiss())
    
    # Find and click delete button
    delete_button = hierarchy_page.locator(
        f'button[onclick*="deleteNode({node.id})"], '
        f'a[onclick*="deleteNode({node.id})"]'
    ).first
    
    await expect(delete_button).to_be_visible()
    await delete_button.click()
    
    # Wait a moment for any potential redirect (shouldn't happen)
    await hierarchy_page.wait_for_timeout(1000)
    
    # Verify node is still visible
    node_text = hierarchy_page.locator('text="Node To Keep"')
    await expect(node_text).to_be_visible()


@pytest.mark.asyncio
async def test_navigation_and_display(
    hierarchy_page: Page,
    base_url: str,
    db_session: AsyncSession,
):
    """Test navigation and display of hierarchy dashboard.
    
    Validates:
    - Dashboard loads correctly
    - Manufacturing type selector works
    - Tree visualization displays
    - Navigation elements present
    """
    # Create manufacturing type with hierarchy
    service = HierarchyBuilderService(db_session)
    mfg_type = await service.create_manufacturing_type(
        name="E2E Navigation Test",
        description="Window type for navigation testing",
        base_price=Decimal("200.00"),
    )
    
    root = await service.create_node(
        manufacturing_type_id=mfg_type.id,
        name="Root Category",
        node_type="category",
    )
    
    child = await service.create_node(
        manufacturing_type_id=mfg_type.id,
        name="Child Attribute",
        node_type="attribute",
        parent_node_id=root.id,
    )
    
    # Navigate to hierarchy page
    await hierarchy_page.goto(f"{base_url}/api/v1/admin/hierarchy/")
    await hierarchy_page.wait_for_load_state("networkidle")
    
    # Verify page title
    title = hierarchy_page.locator('h1, h2')
    await expect(title.first).to_contain_text("Hierarchy")
    
    # Verify manufacturing type selector exists
    type_selector = hierarchy_page.locator('select[name="manufacturing_type_id"]')
    await expect(type_selector).to_be_visible()
    
    # Select manufacturing type
    await type_selector.select_option(str(mfg_type.id))
    
    # Wait for page to reload with selected type
    await hierarchy_page.wait_for_url(
        f"{base_url}/api/v1/admin/hierarchy/?manufacturing_type_id={mfg_type.id}"
    )
    
    # Verify tree displays
    root_node = hierarchy_page.locator('text="Root Category"')
    await expect(root_node).to_be_visible()
    
    child_node = hierarchy_page.locator('text="Child Attribute"')
    await expect(child_node).to_be_visible()
    
    # Verify create button exists
    create_button = hierarchy_page.locator('a:has-text("Create Node")')
    await expect(create_button).to_be_visible()


@pytest.mark.asyncio
async def test_form_validation_errors_display(
    hierarchy_page: Page,
    base_url: str,
    db_session: AsyncSession,
):
    """Test that form validation errors are displayed correctly.
    
    Validates:
    - Submitting empty form shows errors
    - Error messages are visible
    - Form stays on page
    """
    # Create manufacturing type
    service = HierarchyBuilderService(db_session)
    mfg_type = await service.create_manufacturing_type(
        name="E2E Validation Test",
        description="Window type for validation testing",
        base_price=Decimal("200.00"),
    )
    
    # Navigate to create node form
    await hierarchy_page.goto(
        f"{base_url}/api/v1/admin/hierarchy/node/create?manufacturing_type_id={mfg_type.id}"
    )
    await hierarchy_page.wait_for_load_state("networkidle")
    
    # Submit empty form
    submit_button = hierarchy_page.locator('button[type="submit"]')
    await submit_button.click()
    
    # Wait for validation errors to appear
    await hierarchy_page.wait_for_timeout(1000)
    
    # Verify we're still on the form page (not redirected)
    current_url = hierarchy_page.url
    assert "/node/create" in current_url
    
    # Verify error messages are displayed
    # (Exact selectors depend on your form implementation)
    error_messages = hierarchy_page.locator('.alert-danger, .error, .invalid-feedback')
    await expect(error_messages.first).to_be_visible()
