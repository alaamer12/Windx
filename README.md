# Backend API Project

Professional backend API-first architecture using FastAPI, PostgreSQL (Supabase), and repository pattern.

## Features

- ✅ **Dual Database Support**: Seamlessly switch between Supabase (development) and PostgreSQL (production)
- ✅ **Repository Pattern**: Clean data access layer
- ✅ **Full Type Hints**: Type-safe with Annotated types
- ✅ **Type Aliases**: Reusable dependency type aliases for clean code
- ✅ **JWT Authentication**: Secure token-based auth
- ✅ **Connection Pooling**: Optimized for each database provider
- ✅ **Auto Migrations**: Alembic database migrations
- ✅ **API Versioning**: `/api/v1/` prefix for future compatibility
- ✅ **Modern Tooling**: uv for fast dependency management, hatchling for builds
- ✅ **Performance Optimized**: Redis caching, rate limiting, and pagination
- ✅ **Production Ready**: Comprehensive monitoring and error handling

## Prerequisites

- Python 3.11 or higher
- [uv](https://github.com/astral-sh/uv) - Fast Python package installer

### Install uv

```bash
# Windows
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh
```

## Setup

### 1. Install Dependencies
```bash
# Install all dependencies
uv sync

# Install with dev dependencies
uv sync --extra dev
```

### 3. Start Redis (for caching and rate limiting)

```bash
# Using Docker (recommended)
docker-compose up -d redis

# Or install Redis locally
# Windows: https://redis.io/docs/getting-started/installation/install-redis-on-windows/
# Mac: brew install redis
# Linux: sudo apt install redis
```

### 4. Configure Environment

#### Development (Supabase)
```bash
copy .env.development .env
# Edit .env with your Supabase and Redis credentials
```

#### Production (PostgreSQL)
```bash
copy .env.production .env
# Edit .env with your production database credentials
```

### 4. Run the Application

#### Development
```bash
# Using uv
uv run uvicorn app.main:app --reload --env-file .env.development

# Or activate virtual environment first
source .venv/bin/activate  # Linux/Mac
.venv\Scripts\activate     # Windows
uvicorn app.main:app --reload --env-file .env.development
```

#### Production
```bash
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 --env-file .env.production
```

## Database Configuration

### Supabase (Development)
```env
DATABASE_PROVIDER=supabase
DATABASE_HOST=db.xxxxx.supabase.co
DATABASE_PORT=5432
DATABASE_USER=postgres
DATABASE_PASSWORD=your-password
DATABASE_NAME=postgres
DATABASE_POOL_SIZE=3
DATABASE_MAX_OVERFLOW=5
```

### PostgreSQL (Production)
```env
DATABASE_PROVIDER=postgresql
DATABASE_HOST=your-db-host.com
DATABASE_PORT=5432
DATABASE_USER=your_user
DATABASE_PASSWORD=your_password
DATABASE_NAME=your_database
DATABASE_POOL_SIZE=10
DATABASE_MAX_OVERFLOW=20
```

## Project Structure

- `app/core/` - Core functionality (config, database, security)
- `app/models/` - SQLAlchemy ORM models
- `app/schemas/` - Pydantic schemas for validation
- `app/repositories/` - Repository pattern for data access
- `app/api/v1/endpoints/` - API endpoints

## API Documentation

Once running, visit:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
- Health Check: http://localhost:8000/health

## Database Migrations

### Create Migration
```bash
alembic revision --autogenerate -m "description"
```

### Apply Migrations
```bash
alembic upgrade head
```

### Rollback Migration
```bash
alembic downgrade -1
```

## Switching Between Databases

Simply change the `DATABASE_PROVIDER` in your `.env` file:

```env
# For Supabase
DATABASE_PROVIDER=supabase

# For PostgreSQL
DATABASE_PROVIDER=postgresql
```

The application automatically optimizes connection pooling based on the provider.
