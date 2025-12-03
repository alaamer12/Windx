"""Pytest configuration for E2E tests.

Provides fixtures for Playwright browser automation and admin authentication.
"""

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


@pytest_asyncio.fixture(scope="session")
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
async def admin_user(db_session: AsyncSession) -> User:
    """Create admin user for E2E tests.
    
    Args:
        db_session: Database session
        
    Returns:
        User: Created admin user
    """
    admin = User(
        email="admin@e2e.test",
        username="e2e_admin",
        full_name="E2E Admin User",
        hashed_password=get_password_hash("AdminPassword123!"),
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
) -> AsyncGenerator[Page, None]:
    """Create authenticated page with admin login.
    
    Args:
        page: Browser page
        base_url: Base URL for application
        admin_user: Admin user fixture
        
    Yields:
        Page: Authenticated browser page
    """
    # Navigate to login page
    await page.goto(f"{base_url}/api/v1/admin/auth/login")
    
    # Wait for page to load
    await page.wait_for_load_state("networkidle")
    
    # Fill login form
    await page.fill('input[name="username"]', "e2e_admin")
    await page.fill('input[name="password"]', "AdminPassword123!")
    
    # Submit form
    await page.click('button[type="submit"]')
    
    # Wait for redirect to dashboard
    await page.wait_for_url(f"{base_url}/api/v1/admin/", timeout=5000)
    
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
