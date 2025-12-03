# End-to-End Tests

This directory contains browser-based end-to-end tests using Playwright.

## Setup

### Install Dependencies

```bash
# Install Python dependencies (including playwright)
.venv\Scripts\python -m pip install -e ".[dev]"

# Install Playwright browsers
.venv\Scripts\python -m playwright install
```

### Environment Setup

E2E tests require a running application instance. You can either:

1. **Run tests against local development server:**
   ```bash
   # Terminal 1: Start the application
   .venv\Scripts\python -m uvicorn main:app --reload
   
   # Terminal 2: Run E2E tests
   .venv\Scripts\python -m pytest tests/e2e/ -v
   ```

2. **Set custom base URL:**
   ```bash
   E2E_BASE_URL=http://localhost:8000 .venv\Scripts\python -m pytest tests/e2e/ -v
   ```

## Running Tests

### Run all E2E tests
```bash
.venv\Scripts\python -m pytest tests/e2e/ -v
```

### Run specific test file
```bash
.venv\Scripts\python -m pytest tests/e2e/test_admin_hierarchy.py -v
```

### Run specific test
```bash
.venv\Scripts\python -m pytest tests/e2e/test_admin_hierarchy.py::test_create_attribute_node_workflow -v
```

### Run with headed browser (see what's happening)
```bash
.venv\Scripts\python -m pytest tests/e2e/ -v --headed
```

### Run with slow motion (for debugging)
```bash
.venv\Scripts\python -m pytest tests/e2e/ -v --headed --slowmo 1000
```

## Test Structure

### Fixtures (conftest.py)

- `browser`: Playwright browser instance (session-scoped)
- `context`: Browser context with viewport settings
- `page`: New browser page
- `admin_user`: Admin user for authentication
- `authenticated_page`: Pre-authenticated page
- `hierarchy_page`: Page navigated to hierarchy dashboard

### Test Files

- `test_basic_pages.py`: Simple tests for basic page loading (no auth required) - **START HERE**
- `test_admin_hierarchy.py`: Tests for attribute node CRUD operations (requires auth)

## Writing E2E Tests

### Basic Pattern

```python
@pytest.mark.asyncio
async def test_my_workflow(
    authenticated_page: Page,
    base_url: str,
    db_session: AsyncSession,
):
    """Test description."""
    # Setup test data
    # ...
    
    # Navigate to page
    await authenticated_page.goto(f"{base_url}/path")
    
    # Interact with page
    await authenticated_page.click('button#my-button')
    
    # Verify results
    await expect(authenticated_page.locator('.success')).to_be_visible()
```

### Best Practices

1. **Use semantic selectors**: Prefer text content and ARIA labels over CSS classes
2. **Wait for network idle**: Use `wait_for_load_state("networkidle")` after navigation
3. **Use expect assertions**: Use Playwright's `expect()` for automatic retries
4. **Clean up test data**: Use fixtures to create and clean up test data
5. **Isolate tests**: Each test should be independent and not rely on others

### Common Patterns

#### Filling Forms
```python
await page.fill('input[name="username"]', "testuser")
await page.select_option('select[name="type"]', "option_value")
await page.check('input[type="checkbox"]')
```

#### Clicking Elements
```python
await page.click('button:has-text("Submit")')
await page.locator('#my-button').click()
```

#### Waiting for Elements
```python
await page.wait_for_selector('.success-message')
await expect(page.locator('.alert')).to_be_visible()
```

#### Handling Dialogs
```python
page.on("dialog", lambda dialog: dialog.accept())
await page.click('button.delete')
```

## Debugging

### Visual Debugging

Run tests with headed browser to see what's happening:
```bash
.venv\Scripts\python -m pytest tests/e2e/ -v --headed --slowmo 500
```

### Screenshots on Failure

Playwright automatically captures screenshots on failure. Find them in:
```
test-results/
```

### Trace Viewer

Enable tracing for detailed debugging:
```python
await context.tracing.start(screenshots=True, snapshots=True)
# ... run test ...
await context.tracing.stop(path="trace.zip")
```

View trace:
```bash
.venv\Scripts\python -m playwright show-trace trace.zip
```

## CI/CD Integration

E2E tests can run in CI/CD pipelines:

```yaml
# Example GitHub Actions workflow
- name: Install Playwright
  run: |
    python -m pip install -e ".[dev]"
    python -m playwright install --with-deps

- name: Run E2E tests
  run: python -m pytest tests/e2e/ -v
  env:
    E2E_BASE_URL: http://localhost:8000
```

## Troubleshooting

### Browser not found
```bash
.venv\Scripts\python -m playwright install chromium
```

### Connection refused
Ensure the application is running before running E2E tests.

### Timeout errors
Increase timeout in test:
```python
await page.wait_for_selector('.element', timeout=10000)
```

### Element not found
Use Playwright Inspector:
```bash
PWDEBUG=1 .venv\Scripts\python -m pytest tests/e2e/test_admin_hierarchy.py::test_name
```
