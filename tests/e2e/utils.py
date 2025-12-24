"""Utility functions for E2E tests.

Provides helper functions for common E2E testing patterns.
"""

from playwright.async_api import Page, expect


async def wait_for_success_message(page: Page, message: str | None = None) -> None:
    """Wait for success alert to appear.

    Args:
        page: Playwright page
        message: Optional specific message to check for
    """
    success_alert = page.locator(".alert-success")
    await expect(success_alert).to_be_visible(timeout=5000)

    if message:
        await expect(success_alert).to_contain_text(message)


async def wait_for_error_message(page: Page, message: str | None = None) -> None:
    """Wait for error alert to appear.

    Args:
        page: Playwright page
        message: Optional specific message to check for
    """
    error_alert = page.locator(".alert-danger, .alert-error")
    await expect(error_alert).to_be_visible(timeout=5000)

    if message:
        await expect(error_alert).to_contain_text(message)


async def fill_form_field(page: Page, field_name: str, value: str) -> None:
    """Fill a form field by name.

    Args:
        page: Playwright page
        field_name: Name attribute of the field
        value: Value to fill
    """
    field = page.locator(f'input[name="{field_name}"], textarea[name="{field_name}"]')
    await field.fill(value)


async def select_dropdown_option(page: Page, field_name: str, value: str) -> None:
    """Select dropdown option by name.

    Args:
        page: Playwright page
        field_name: Name attribute of the select element
        value: Value to select
    """
    select = page.locator(f'select[name="{field_name}"]')
    await select.select_option(value)


async def click_button_with_text(page: Page, text: str) -> None:
    """Click button containing specific text.

    Args:
        page: Playwright page
        text: Text content of the button
    """
    button = page.locator(f'button:has-text("{text}"), a:has-text("{text}")')
    await button.click()


async def verify_element_visible(page: Page, selector: str) -> None:
    """Verify element is visible.

    Args:
        page: Playwright page
        selector: CSS selector for the element
    """
    element = page.locator(selector)
    await expect(element).to_be_visible()


async def verify_element_not_visible(page: Page, selector: str) -> None:
    """Verify element is not visible.

    Args:
        page: Playwright page
        selector: CSS selector for the element
    """
    element = page.locator(selector)
    await expect(element).not_to_be_visible()


async def verify_text_present(page: Page, text: str) -> None:
    """Verify text is present on the page.

    Args:
        page: Playwright page
        text: Text to search for
    """
    element = page.locator(f'text="{text}"')
    await expect(element).to_be_visible()


async def accept_confirmation_dialog(page: Page) -> None:
    """Set up handler to accept confirmation dialogs.

    Args:
        page: Playwright page
    """
    page.on("dialog", lambda dialog: dialog.accept())


async def dismiss_confirmation_dialog(page: Page) -> None:
    """Set up handler to dismiss confirmation dialogs.

    Args:
        page: Playwright page
    """
    page.on("dialog", lambda dialog: dialog.dismiss())


async def take_screenshot(page: Page, name: str) -> None:
    """Take a screenshot for debugging.

    Args:
        page: Playwright page
        name: Name for the screenshot file
    """
    await page.screenshot(path=f"test-results/{name}.png")


async def wait_for_navigation(page: Page, url_pattern: str, timeout: int = 5000) -> None:
    """Wait for navigation to URL matching pattern.

    Args:
        page: Playwright page
        url_pattern: URL pattern to match (can include wildcards)
        timeout: Timeout in milliseconds
    """
    await page.wait_for_url(url_pattern, timeout=timeout)
