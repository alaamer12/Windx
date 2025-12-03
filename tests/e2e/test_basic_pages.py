"""Basic E2E tests for simple page loading.

Tests that verify the application is running and basic pages load correctly.
These tests don't require authentication or complex setup.
"""

import pytest
from playwright.async_api import Page, expect

# Mark all tests in this module as e2e tests
pytestmark = pytest.mark.e2e


@pytest.mark.asyncio
async def test_homepage_loads(page: Page, base_url: str):
    """Test that the homepage loads and displays welcome message.
    
    This is the simplest possible test - just verify the server is running
    and the root endpoint returns the expected content.
    """
    # Navigate to homepage
    await page.goto(base_url)
    
    # Wait for page to load
    await page.wait_for_load_state("networkidle")
    
    # Check that page contains welcome message
    content = await page.content()
    assert "Welcome to WindX Product Configurator API" in content
    
    # Verify the JSON response contains expected keys
    # The root endpoint returns JSON, so we can check the text content
    assert "version" in content
    assert "docs" in content
    assert "health" in content


@pytest.mark.asyncio
async def test_health_endpoint_loads(page: Page, base_url: str):
    """Test that the health check endpoint loads and returns status.
    
    Verifies the /health endpoint is accessible and returns health information.
    """
    # Navigate to health endpoint
    await page.goto(f"{base_url}/health")
    
    # Wait for page to load
    await page.wait_for_load_state("networkidle")
    
    # Check that page contains health status
    content = await page.content()
    assert "status" in content
    assert "app_name" in content
    assert "version" in content


@pytest.mark.asyncio
async def test_docs_page_loads(page: Page, base_url: str):
    """Test that the API documentation page loads.
    
    Verifies the Swagger UI documentation is accessible.
    """
    # Navigate to docs page
    await page.goto(f"{base_url}/docs")
    
    # Wait for page to load
    await page.wait_for_load_state("networkidle")
    
    # Check that Swagger UI loaded
    # Swagger UI has a specific title
    title = await page.title()
    assert "FastAPI" in title or "Swagger" in title or "WindX" in title
    
    # Check for Swagger UI elements
    swagger_ui = page.locator(".swagger-ui")
    await expect(swagger_ui).to_be_visible(timeout=10000)


@pytest.mark.asyncio
async def test_page_title_and_metadata(page: Page, base_url: str):
    """Test that pages have proper titles and metadata.
    
    Verifies basic HTML structure and metadata.
    """
    # Navigate to docs page (has proper HTML)
    await page.goto(f"{base_url}/docs")
    
    # Wait for page to load
    await page.wait_for_load_state("networkidle")
    
    # Check page title exists
    title = await page.title()
    assert len(title) > 0
    
    # Check that page has proper HTML structure
    html = page.locator("html")
    await expect(html).to_be_visible()
