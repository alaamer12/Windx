# GitHub Actions Workflows

This directory contains CI/CD workflows for automated testing and deployment.

## Available Workflows

### 1. `tests.yml` - Simple Test Runner ⚡
**Recommended for most projects**

Runs on every push to `main` and on pull requests.

**Features:**
- Fast execution with `uv` package manager
- Linting with Ruff
- Full test suite execution
- Test summary in GitHub UI

**Usage:**
```bash
# Triggered automatically on:
# - Push to main branch
# - Pull requests to main branch
```

---

### 2. `tests-with-coverage.yml` - Tests with Coverage 📊

Extended version with code coverage reporting.

**Features:**
- Everything from `tests.yml`
- Code coverage calculation
- Coverage upload to Codecov
- Coverage badge generation
- Detailed coverage report
- **Excludes**: E2E tests and Redis-dependent tests

**Test Markers:**
```bash
-m "not e2e and not redis"
```

**Setup Required:**
1. Sign up at [codecov.io](https://codecov.io)
2. Add `CODECOV_TOKEN` to repository secrets
3. Enable this workflow

---

### 3. `redis-tests.yml` - Redis Tests (Cache & Rate Limiting) 🔴

Runs tests that require Redis for caching and rate limiting.

**Features:**
- Redis service container
- Cache health check tests
- Rate limiter tests
- Caching behavior validation
- Connection cleanup tests

**Test Markers:**
```bash
-m redis
```

**Services:**
- PostgreSQL 15
- Redis 7

**Tests Included:**
- `test_health_check_cache_when_enabled`
- `test_health_check_rate_limiter_when_enabled`
- `test_health_check_redis_cache_failure`
- `test_health_check_redis_limiter_failure`
- `test_health_check_redis_connection_cleanup`
- `test_get_stats_caching_behavior`
- `test_get_stats_cache_performance`

---

### 4. `e2e-tests.yml` - End-to-End Tests 🎭

Runs browser-based E2E tests using Playwright.

**Features:**
- Playwright with Chromium
- Full application testing
- Screenshot/video capture on failure
- Real browser automation

**Test Markers:**
```bash
-m e2e
```

**Services:**
- PostgreSQL 15
- FastAPI server (background)

---

### 5. `ci-cd.yml` - Full CI/CD Pipeline 🚀

Complete pipeline with linting, testing, and deployment.

**Features:**
- Separate lint and test jobs
- Multi-version Python testing (3.11, 3.12)
- Docker image building
- Automatic deployment on main branch
- Pipeline summary dashboard

**Setup Required:**
1. Add Docker Hub credentials to secrets:
   - `DOCKER_USERNAME`
   - `DOCKER_PASSWORD`
2. (Optional) Add `CODECOV_TOKEN` for coverage

**Jobs:**
1. **Lint** - Code quality checks
2. **Test** - Run tests on multiple Python versions
3. **Build** - Build and push Docker image (main branch only)
4. **Summary** - Generate pipeline results

---

## Configuration

### Required Secrets

Add these in: `Settings` → `Secrets and variables` → `Actions`

| Secret            | Required For       | Description               |
|-------------------|--------------------|---------------------------|
| `CODECOV_TOKEN`   | Coverage workflows | Token from codecov.io     |
| `DOCKER_USERNAME` | CI/CD pipeline     | Docker Hub username       |
| `DOCKER_PASSWORD` | CI/CD pipeline     | Docker Hub password/token |

### Environment Variables

The workflows automatically create a `.env.test` file with:

```env
TESTING=true
DATABASE_PROVIDER=sqlite
DATABASE_URL=sqlite+aiosqlite:///./test.db
SECRET_KEY=test-secret-key-for-ci-cd-only
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
CORS_ORIGINS=["http://localhost:3000"]
CACHE_ENABLED=false
LIMITER_ENABLED=false
```

---

## Test Markers

Tests are organized using pytest markers defined in `pyproject.toml`:

| Marker | Description | Example |
|--------|-------------|---------|
| `unit` | Fast, isolated unit tests | `pytest -m unit` |
| `integration` | Full-stack integration tests | `pytest -m integration` |
| `e2e` | Browser-based end-to-end tests | `pytest -m e2e` |
| `redis` | Tests requiring Redis (cache/rate limiting) | `pytest -m redis` |
| `slow` | Slow-running tests | `pytest -m slow` |
| `auth` | Authentication tests | `pytest -m auth` |
| `users` | User management tests | `pytest -m users` |
| `services` | Service layer tests | `pytest -m services` |
| `repositories` | Repository layer tests | `pytest -m repositories` |

---

## Choosing a Workflow

### Use `tests.yml` if:
- ✅ You want simple, fast CI
- ✅ You don't need coverage reports
- ✅ You're just getting started

### Use `tests-with-coverage.yml` if:
- ✅ You want to track code coverage
- ✅ You have Codecov set up
- ✅ You want detailed test reports
- ✅ You don't need Redis or E2E tests

### Use `redis-tests.yml` if:
- ✅ You need to test caching behavior
- ✅ You need to test rate limiting
- ✅ You have Redis available

### Use `e2e-tests.yml` if:
- ✅ You need browser-based testing
- ✅ You want to test full user workflows
- ✅ You need visual regression testing

### Use `ci-cd.yml` if:
- ✅ You need full CI/CD pipeline
- ✅ You want to test multiple Python versions
- ✅ You want automatic Docker builds
- ✅ You're ready for production deployment

---

## Local Testing

Test the workflow locally before pushing:

```bash
# Install dependencies
uv sync

# Run linter
uv run ruff check app/ tests/

# Run formatter check
uv run ruff format --check app/ tests/

# Run all tests (except E2E and Redis)
uv run pytest tests/ -v -m "not e2e and not redis"

# Run only Redis tests (requires Redis running locally)
# Start Redis first:
docker run -d --name redis-test -p 6379:6379 redis:7-alpine
# Then run tests:
uv run pytest tests/ -v -m redis
# Stop Redis after:
docker stop redis-test && docker rm redis-test

# Run only E2E tests (requires app running)
uv run pytest tests/ -v -m e2e

# Run tests with coverage
uv run pytest tests/ --cov=app --cov-report=term -m "not e2e and not redis"

# Run specific marker
uv run pytest tests/ -v -m integration
```

---

## Workflow Status Badges

Add these to your README.md:

### Simple Tests
```markdown
![Tests](https://github.com/yourusername/yourrepo/actions/workflows/tests.yml/badge.svg)
```

### Tests with Coverage
```markdown
![Tests](https://github.com/yourusername/yourrepo/actions/workflows/tests-with-coverage.yml/badge.svg)
[![codecov](https://codecov.io/gh/yourusername/yourrepo/branch/main/graph/badge.svg)](https://codecov.io/gh/yourusername/yourrepo)
```

### Full CI/CD
```markdown
![CI/CD](https://github.com/yourusername/yourrepo/actions/workflows/ci-cd.yml/badge.svg)
```

---

## Troubleshooting

### Tests fail in CI but pass locally
- Check Python version matches (3.11)
- Verify `.env.test` is created correctly
- Check for environment-specific issues

### Coverage upload fails
- Verify `CODECOV_TOKEN` is set correctly
- Check Codecov repository is configured
- Ensure coverage.xml is generated

### Docker build fails
- Verify Docker credentials are correct
- Check Dockerfile exists and is valid
- Ensure Docker Hub repository exists

### uv sync fails
- Check `pyproject.toml` is valid
- Verify all dependencies are available
- Try clearing cache: delete `.github/workflows/.uv-cache`

---

## Performance Tips

1. **Enable caching** - Already enabled for `uv` dependencies
2. **Parallel jobs** - CI/CD workflow runs lint and test in parallel
3. **Fail fast** - Tests stop on first failure (can be disabled)
4. **Selective runs** - Use path filters to skip unnecessary runs

Example path filter:
```yaml
on:
  push:
    branches:
      - main
    paths:
      - 'app/**'
      - 'tests/**'
      - 'pyproject.toml'
```

---

## Next Steps

1. Choose the workflow that fits your needs
2. Delete the others (or keep them disabled)
3. Add required secrets to repository settings
4. Push to main branch to trigger the workflow
5. Check the Actions tab for results

For more information, see:
- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [uv Documentation](https://docs.astral.sh/uv/)
- [Codecov Documentation](https://docs.codecov.com/)
