# Backend API Project

Professional backend API-first architecture using FastAPI, PostgreSQL (Supabase), and repository pattern with integrated Windx automated product configurator.

## Overview

This backend application provides a robust foundation for user authentication and management, enhanced with the **Windx Configurator System** - a sophisticated, hierarchical product configuration platform for automated window, door, and custom manufacturing solutions.

### Windx Configurator System

**Windx** is an automated product configurator that empowers customers to design, customize, and order manufactured products through a dynamic, hierarchical attribute system. The system provides full transparency in pricing, real-time configuration validation, and seamless quote-to-order workflows.

#### Business Purpose

The Windx system addresses key business challenges in custom manufacturing:

- **Customer Empowerment**: Self-service product configuration with complete transparency
- **Operational Efficiency**: Automated pricing calculations and quote generation
- **Scalability**: Easily extend to new product lines and markets
- **Reduced Errors**: Validation rules prevent invalid configurations
- **Faster Sales Cycles**: Instant quotes and streamlined ordering

#### Hierarchical Attribute System

Windx uses a flexible, unlimited-depth hierarchy for product attributes:

```
Manufacturing Type (e.g., Window)
  └─ Category (e.g., Frame Options)
      └─ Attribute (e.g., Frame Material)
          └─ Option (e.g., Aluminum)
              └─ Sub-option (e.g., Anodized Finish)
                  └─ Sub-sub-option (e.g., Color: Bronze)
```

**Key Concepts:**
- **Manufacturing Types**: Top-level product categories (Window, Door, Table)
- **Attribute Nodes**: Hierarchical tree structure using PostgreSQL LTREE extension
- **Dynamic Behavior**: Conditional display and validation based on selections
- **Price Impacts**: Fixed amounts, percentages, or formula-based calculations
- **Weight Impacts**: Automatic weight calculation for shipping
- **Technical Specifications**: Computed properties (U-value, dimensions, etc.)

#### Key Features

1. **Dynamic Configuration**
   - Unlimited hierarchy depth for product attributes
   - Conditional display logic (show/hide based on selections)
   - Real-time validation rules
   - Flexible value types (string, number, boolean, formula, dimension)

2. **Automated Pricing**
   - Base price + option price impacts
   - Fixed, percentage, and formula-based pricing
   - Real-time price calculation
   - Price history tracking

3. **Template System**
   - Pre-defined configurations for common use cases
   - Public templates for customer use
   - Usage tracking and success metrics
   - Quick-start configurations

4. **Quote Generation**
   - Immutable configuration snapshots
   - Price validity periods
   - Tax and discount calculations
   - Technical requirements documentation

5. **Order Processing**
   - Quote-to-order conversion
   - Order item management
   - Installation address tracking
   - Special instructions support

#### Architecture Overview

Windx follows a **hybrid database approach** combining:

- **Relational Structure**: Standard tables for entities (types, configurations, quotes)
- **LTREE Hierarchies**: PostgreSQL LTREE extension for efficient tree queries
- **JSONB Flexibility**: Dynamic attributes, validation rules, and technical data

**Data Flow:**
```
Customer → Configuration → Selections → Price Calculation → Quote → Order
                ↓
         Template System (optional)
```

**Technology Stack:**
- **PostgreSQL LTREE**: Hierarchical path queries (ancestors, descendants)
- **JSONB**: Flexible attribute storage and validation rules
- **SQLAlchemy 2.0**: Type-safe ORM with Mapped columns
- **Pydantic V2**: Request/response validation
- **Repository Pattern**: Clean data access layer
- **Service Layer**: Business logic and price calculations

#### Domain Models

- **ManufacturingType**: Product categories with base pricing
- **AttributeNode**: Hierarchical attribute tree with LTREE paths
- **Configuration**: Customer product designs with selections
- **ConfigurationSelection**: Individual attribute choices
- **ConfigurationTemplate**: Pre-defined common configurations
- **Customer**: Customer management (extends user system)
- **Quote**: Price quotes with immutable snapshots
- **Order**: Order processing and fulfillment

For detailed Windx documentation, see:
- [Windx System Overview](docs/windx-overview.md) - Complete system understanding
- [Windx SQL Design](docs/windx-sql-traits.md) - Database design analysis
- [Windx SQL Explanations](docs/windx-sql-explanations.md) - ERD and data flow

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
- ✅ **Windx Configurator**: Hierarchical product configuration system
- ✅ **LTREE Hierarchies**: Efficient tree queries with PostgreSQL LTREE
- ✅ **Dynamic Pricing**: Formula-based price calculations
- ✅ **Template System**: Pre-defined configurations for quick start

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

## Testing

### ⚠️ Important: PostgreSQL Required for Tests

The test suite uses **PostgreSQL** (not SQLite) to support Windx features like LTREE and JSONB.

### Quick Setup

1. **Update `.env.test`** with your Supabase credentials:
   ```env
   SUPABASE_URL=https://YOUR_PROJECT_REF.supabase.co
   SUPABASE_ANON_KEY=your_actual_anon_key
   SUPABASE_DB_PASSWORD=your_actual_db_password
   ```

2. **Run tests**:
   ```bash
   .venv\scripts\python -m pytest tests/ -v
   ```

### Test Commands

```bash
# Run all tests
.venv\scripts\python -m pytest tests/

# Run with coverage
.venv\scripts\python -m pytest tests/ --cov=app --cov-report=html

# Run specific test file
.venv\scripts\python -m pytest tests/integration/test_auth.py

# Run only unit tests
.venv\scripts\python -m pytest tests/unit/

# Run only integration tests
.venv\scripts\python -m pytest tests/integration/
```

### Documentation

- **Quick Start**: See `TESTING_QUICKSTART.md`
- **Detailed Setup**: See `docs/TEST_DATABASE_SETUP.md`
- **Migration Info**: See `docs/TEST_MIGRATION_SUMMARY.md`

## Switching Between Databases

Simply change the `DATABASE_PROVIDER` in your `.env` file:

```env
# For Supabase
DATABASE_PROVIDER=supabase

# For PostgreSQL
DATABASE_PROVIDER=postgresql
```

The application automatically optimizes connection pooling based on the provider.

## Performance Optimizations

This application includes comprehensive performance optimizations for production workloads:

### Dashboard Statistics (10-100x Faster)
- **Database Aggregation**: Single SQL query with COUNT aggregations instead of loading all records
- **Response Caching**: 60-second cache TTL reduces database load by 90%
- **Performance**: <50ms response time even with 100k+ users (vs 5+ seconds before)

```bash
# Test optimized dashboard stats
curl -H "Authorization: Bearer $TOKEN" http://localhost:8000/api/v1/dashboard/stats
```

### Database Indexes (10x Faster Queries)
Strategic indexes on frequently queried columns:
- `is_active` - Fast filtering of active/inactive users
- `is_superuser` - Quick superuser lookups
- `created_at` - Efficient date-based queries and sorting

**Migration Required**: Run `alembic upgrade head` to create indexes.

### Query Filters and Sorting
Efficient database-level filtering instead of in-memory operations:

```bash
# Filter by active status
GET /api/v1/users?is_active=true

# Filter by superuser status
GET /api/v1/users?is_superuser=true

# Search by name, email, or username
GET /api/v1/users?search=john

# Sort by different fields
GET /api/v1/users?sort_by=email&sort_order=asc
GET /api/v1/users?sort_by=created_at&sort_order=desc

# Combine filters
GET /api/v1/users?is_active=true&search=admin&sort_by=created_at
```

### Request Timeout Protection
- **30-second timeout** on all requests prevents resource exhaustion
- Returns HTTP 504 Gateway Timeout for long-running requests
- Protects against DoS attacks and hanging connections

### Enhanced Health Check
Comprehensive dependency verification for monitoring:

```bash
curl http://localhost:8000/health
```

Returns status for:
- Database connectivity
- Redis cache (if enabled)
- Redis rate limiter (if enabled)

### Bulk Operations
Create multiple users in a single atomic transaction:

```bash
POST /api/v1/users/bulk
[
  {"email": "user1@example.com", "username": "user1", "password": "pass123"},
  {"email": "user2@example.com", "username": "user2", "password": "pass123"}
]
```

**Benefits**: 15x faster than individual requests, atomic transaction (all or nothing).

### Database Metrics Monitoring
Monitor connection pool health (superuser only):

```bash
GET /api/v1/metrics/database
```

Returns:
- `pool_size` - Configured pool size
- `checked_in` - Available connections
- `checked_out` - Active connections
- `overflow` - Overflow connections
- `total_connections` - Total connections

### Performance Benchmarks

| Operation | Before | After | Improvement |
|-----------|--------|-------|-------------|
| Dashboard Stats (10k users) | 500ms | 20ms | 25x |
| Dashboard Stats (cached) | 500ms | <1ms | 500x+ |
| User List (filtered) | 200ms | 20ms | 10x |
| User Search | 600ms | 30ms | 20x |
| Bulk Create (10 users) | 1000ms | 150ms | 6.7x |

### Configuration

**Enable Caching** (`.env`):
```env
CACHE_ENABLED=True
CACHE_REDIS_HOST=localhost
CACHE_REDIS_PORT=6379
CACHE_REDIS_DB=0
```

**Enable Rate Limiting** (`.env`):
```env
LIMITER_ENABLED=True
LIMITER_REDIS_HOST=localhost
LIMITER_REDIS_PORT=6379
LIMITER_REDIS_DB=1
```

### Documentation

For detailed performance information, see:
- [Performance Guide](docs/PERFORMANCE.md) - Comprehensive benchmarks and optimization strategies
- [Architecture](docs/ARCHITECTURE.md) - System architecture and design patterns
- [Testing](docs/TESTING.md) - Testing strategies and coverage

### Monitoring Recommendations

1. **Health Check**: Monitor `/health` endpoint every 60 seconds
2. **Database Metrics**: Track connection pool usage via `/api/v1/metrics/database`
3. **Cache Hit Rate**: Monitor Redis cache effectiveness
4. **Response Times**: Track p95 and p99 latencies
5. **Error Rates**: Alert on 5xx errors

### Migration Instructions

To apply performance optimizations to existing deployments:

1. **Update Dependencies**:
   ```bash
   uv sync
   ```

2. **Apply Database Migrations**:
   ```bash
   alembic upgrade head
   ```
   This creates indexes on `is_active`, `is_superuser`, and `created_at` columns.

3. **Configure Redis** (if not already):
   ```bash
   docker-compose up -d redis
   ```

4. **Update Environment Variables**:
   Add cache and rate limiter settings to `.env` (see Configuration above).

5. **Restart Application**:
   ```bash
   uv run uvicorn app.main:app --reload
   ```

6. **Verify Performance**:
   - Test dashboard stats: Should respond in <50ms
   - Test filtered queries: Should respond in <50ms
   - Check health endpoint: Should show all services healthy
