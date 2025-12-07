"""Pytest configuration for E2E tests.

Provides fixtures for Playwright browser automation and admin authentication.
"""

__all__ = [
    # Configuration Fixtures
    "base_url",
    # Browser Fixtures
    "browser",
    "context",
    "page",
    # User Fixtures
    "admin_user",
    # Authenticated Fixtures
    "authenticated_page",
    "hierarchy_page",
    # Cleanup Fixtures
    "cleanup_e2e_data",
]

import asyncio
import os
from collections.abc import AsyncGenerator

import pytest
import pytest_asyncio
from playwright.async_api import Browser, BrowserContext, Page, async_playwright
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_password_hash
from app.models.user import User


@pytest.fixture(scope="session")
def base_url() -> str:
    """Get base URL for E2E tests.
    
    Returns:
        str: Base URL (default: http://localhost:8000)
    """
    return os.getenv("E2E_BASE_URL", "http://localhost:8000")


@pytest_asyncio.fixture(scope="function")
async def browser() -> AsyncGenerator[Browser, None]:
    """Create Playwright browser instance.
    
    Yields:
        Browser: Chromium browser instance
    """
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,  # Set to False for debugging
            args=["--disable-dev-shm-usage"],  # Prevent crashes in CI
        )
        yield browser
        await browser.close()

# Another way to do it if you need "session" scope
# The problem with the function above is bad timing which leads to "The test is hanging during collection"
# @pytest_asyncio.fixture(scope="session")
# async def browser() -> AsyncGenerator[Browser, None]:
#     # 1. Start playwright (engine)
#     p = await async_playwright().start()

#     # 2. Launch browser after engine is ready
#     browser = await p.chromium.launch(
#         headless=True,
#         args=["--disable-dev-shm-usage"],
#     )

#     # 3. Give the browser to tests
#     yield browser

#     # 4. Cleanup when all tests finish
#     await browser.close()
#     await p.stop()


@pytest_asyncio.fixture
async def context(browser: Browser) -> AsyncGenerator[BrowserContext, None]:
    """Create browser context with viewport settings.
    
    Args:
        browser: Playwright browser instance
        
    Yields:
        BrowserContext: Browser context with configured viewport
    """
    context = await browser.new_context(
        viewport={"width": 1920, "height": 1080},
        locale="en-US",
    )
    yield context
    await context.close()


@pytest_asyncio.fixture
async def page(context: BrowserContext) -> AsyncGenerator[Page, None]:
    """Create new page in browser context.
    
    Args:
        context: Browser context
        
    Yields:
        Page: New browser page
    """
    page = await context.new_page()
    yield page
    await page.close()


@pytest_asyncio.fixture
async def admin_user(db_session: AsyncSession, test_settings) -> User:
    """Create admin user for E2E tests.
    
    Args:
        db_session: Database session
        test_settings: Test settings with credentials
        
    Returns:
        User: Created admin user
    """
    from sqlalchemy import select
    
    from tests.config import TestSettings
    
    settings = test_settings if test_settings else TestSettings()
    
    # Check if user already exists
    result = await db_session.execute(
        select(User).where(User.email == "admin@e2e.test")
    )
    existing_user = result.scalar_one_or_none()
    
    if existing_user:
        # Update password in case it changed
        existing_user.hashed_password = get_password_hash(settings.test_admin_password)
        existing_user.is_active = True
        existing_user.is_superuser = True
        await db_session.commit()
        await db_session.refresh(existing_user)
        return existing_user
    
    # Create new user
    admin = User(
        email="admin@e2e.test",
        username="e2e_admin",
        full_name="E2E Admin User",
        hashed_password=get_password_hash(settings.test_admin_password),
        is_active=True,
        is_superuser=True,
    )
    db_session.add(admin)
    await db_session.commit()
    await db_session.refresh(admin)
    return admin


@pytest_asyncio.fixture
async def authenticated_page(
    page: Page,
    base_url: str,
    admin_user: User,
    test_settings,
) -> AsyncGenerator[Page, None]:
    """Create authenticated page with admin login.
    
    Args:
        page: Browser page
        base_url: Base URL for application
        admin_user: Admin user fixture
        test_settings: Test settings with credentials
        
    Yields:
        Page: Authenticated browser page
    """
    from tests.config import TestSettings
    
    settings = test_settings if test_settings else TestSettings()
    
    # Navigate to login page
    await page.goto(f"{base_url}/api/v1/admin/login")
    
    # Wait for page to load
    await page.wait_for_load_state("networkidle")
    
    # Fill login form (admin login uses form data, not JSON)
    await page.fill('input[name="username"]', "e2e_admin")
    await page.fill('input[name="password"]', settings.test_admin_password)
    
    # Submit form and wait for navigation
    try:
        async with page.expect_navigation(timeout=15000):
            await page.click('button[type="submit"]')
    except Exception as e:
        # Get page content for debugging
        content = await page.content()
        print(f"\n❌ Login failed. Page content length: {len(content)}")
        print(f"Current URL: {page.url}")
        # Check for error messages
        error_alert = page.locator('.alert-error, .alert-danger, .error')
        if await error_alert.count() > 0:
            error_text = await error_alert.first.text_content()
            print(f"Error message: {error_text}")
        raise Exception(f"Login navigation failed: {e}")
    
    # Verify we're on the dashboard
    current_url = page.url
    if "/api/v1/admin/dashboard" not in current_url:
        raise Exception(f"Expected to be on dashboard, but got: {current_url}")
    
    print(f"✅ Successfully authenticated. Current URL: {current_url}")
    
    yield page


@pytest_asyncio.fixture
async def hierarchy_page(
    authenticated_page: Page,
    base_url: str,
) -> AsyncGenerator[Page, None]:
    """Navigate to hierarchy management page.
    
    Args:
        authenticated_page: Authenticated browser page
        base_url: Base URL for application
        
    Yields:
        Page: Page on hierarchy management dashboard
    """
    await authenticated_page.goto(f"{base_url}/api/v1/admin/hierarchy/")
    await authenticated_page.wait_for_load_state("networkidle")
    yield authenticated_page


@pytest_asyncio.fixture
async def cleanup_e2e_data(db_session: AsyncSession):
    """Clean up E2E test data before and after tests.
    
    This fixture removes all test data created by E2E tests to ensure
    a clean state for each test run.
    
    Args:
        db_session: Database session
        
    Yields:
        None
    """
    from sqlalchemy import delete, select
    
    from app.models.attribute_node import AttributeNode
    from app.models.manufacturing_type import ManufacturingType
    
    async def cleanup():
        """Remove all E2E test data."""
        # Delete manufacturing types that start with "E2E"
        result = await db_session.execute(
            select(ManufacturingType).where(ManufacturingType.name.like("E2E%"))
        )
        mfg_types = result.scalars().all()
        
        for mfg_type in mfg_types:
            # Delete associated attribute nodes (cascade should handle this, but be explicit)
            await db_session.execute(
                delete(AttributeNode).where(
                    AttributeNode.manufacturing_type_id == mfg_type.id
                )
            )
            await db_session.delete(mfg_type)
        
        await db_session.commit()
    
    # Cleanup before test
    await cleanup()
    
    yield
    
    # Cleanup after test
    await cleanup()
