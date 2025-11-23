# Design Document

## Overview

This design document outlines the technical implementation for performance optimizations to the FastAPI backend application. The optimizations are organized into three phases based on priority and impact: Critical (Phase 1), High Priority (Phase 2), and Nice to Have (Phase 3). The implementation follows the existing project architecture patterns including layered architecture, repository pattern, service pattern, and proper separation of concerns.

## Architecture

### System Components

The performance optimizations will touch the following layers of the application:

1. **API Layer** (`app/api/v1/endpoints/`)
   - Dashboard stats endpoint modifications
   - User list endpoint enhancements
   - New metrics endpoints

2. **Service Layer** (`app/services/`)
   - Optimized dashboard statistics service method
   - Enhanced user service with filtering capabilities

3. **Repository Layer** (`app/repositories/`)
   - New repository methods for filtered queries
   - Optimized aggregation queries

4. **Model Layer** (`app/models/`)
   - Index additions to User model

5. **Middleware Layer** (`app/core/middleware.py`)
   - New TimeoutMiddleware implementation

6. **Database Layer** (`alembic/versions/`)
   - Migration for adding indexes

### Performance Impact

| Optimization | Current Performance | Target Performance | Impact |
|--------------|-------------------|-------------------|---------|
| Dashboard Stats | 500ms+ (10k users) | <50ms | 10-100x |
| User Queries | 200ms+ | <20ms | 10x |
| Request Hangs | Indefinite | 30s max | Prevents DoS |
| Health Check | Basic | Comprehensive | Better monitoring |

## Components and Interfaces

### 1. Dashboard Statistics Optimization

#### Service Layer Enhancement

**File:** `app/services/dashboard.py` (new file)

```python
class DashboardService(BaseService):
    """Dashboard service for statistics and metrics."""
    
    async def get_dashboard_stats_optimized(self) -> dict:
        """Get dashboard statistics using database aggregation.
        
        Returns:
            dict: Dashboard statistics with counts and timestamp
        """
```

**Key Design Decisions:**
- Create dedicated DashboardService to separate concerns from UserService
- Use SQLAlchemy `func.count()` with filters for aggregation
- Single query execution for all statistics
- Return ISO formatted timestamp for cache validation

#### Endpoint Modification

**File:** `app/api/v1/endpoints/dashboard.py`

- Replace in-memory list comprehension with service call
- Add `@cache(expire=60)` decorator for 1-minute caching
- Maintain existing response format for backward compatibility

### 2. Database Index Implementation

#### Model Enhancement

**File:** `app/models/user.py`

```python
is_active: Mapped[bool] = mapped_column(
    default=True,
    nullable=False,
    index=True,  # Add index
    doc="Account active status",
)

is_superuser: Mapped[bool] = mapped_column(
    default=False,
    nullable=False,
    index=True,  # Add index
    doc="Superuser privileges flag",
)

created_at: Mapped[datetime] = mapped_column(
    TIMESTAMP(timezone=True),
    default=lambda: datetime.now(UTC),
    server_default=func.now(),
    nullable=False,
    index=True,  # Add index
    doc="Account creation timestamp (UTC)",
)
```

#### Migration

**File:** `alembic/versions/XXXX_add_user_indexes.py`

```python
def upgrade():
    op.create_index('ix_users_is_active', 'users', ['is_active'])
    op.create_index('ix_users_is_superuser', 'users', ['is_superuser'])
    op.create_index('ix_users_created_at', 'users', ['created_at'])

def downgrade():
    op.drop_index('ix_users_created_at', 'users')
    op.drop_index('ix_users_is_superuser', 'users')
    op.drop_index('ix_users_is_active', 'users')
```

**Key Design Decisions:**
- Add indexes directly in model definition for clarity
- Use standard naming convention: `ix_{table}_{column}`
- Drop indexes in reverse order during downgrade
- Indexes improve WHERE clause and ORDER BY performance

### 3. Request Timeout Middleware

#### Middleware Implementation

**File:** `app/core/middleware.py`

```python
class TimeoutMiddleware(BaseHTTPMiddleware):
    """Add timeout to all requests to prevent hanging."""
    
    def __init__(self, app: ASGIApp, *, timeout: float = 30.0) -> None:
        """Initialize timeout middleware.
        
        Args:
            app: ASGI application
            timeout: Request timeout in seconds (default: 30)
        """
        super().__init__(app)
        self.timeout = timeout
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request with timeout enforcement."""
```

**Key Design Decisions:**
- Use `asyncio.wait_for()` for timeout enforcement
- Return HTTP 504 Gateway Timeout on timeout
- Configurable timeout duration (default 30 seconds)
- Add early in middleware stack (after request size limit)
- Include timeout duration in error message

#### Middleware Stack Order

```
1. RequestSizeLimitMiddleware (check size first)
2. TimeoutMiddleware (NEW - prevent hangs)
3. TrustedHostMiddleware (validate host)
4. HTTPSRedirectMiddleware (force HTTPS)
5. CORSMiddleware (handle CORS)
6. SecurityHeadersMiddleware (add headers)
7. GZipMiddleware (compress)
8. RequestIDMiddleware (track requests)
9. LoggingMiddleware (log everything)
```

### 4. Enhanced Health Check

#### Health Check Enhancement

**File:** `main.py`

```python
@app.get("/health")
async def health_check(
    settings: Annotated[Settings, Depends(get_settings)],
    db: DBSession,
) -> dict:
    """Enhanced health check with dependency verification."""
```

**Response Structure:**

```json
{
  "status": "healthy",
  "app_name": "Backend API",
  "version": "1.0.0",
  "checks": {
    "database": {
      "status": "healthy",
      "provider": "supabase"
    },
    "cache": {
      "status": "healthy"
    },
    "rate_limiter": {
      "status": "healthy"
    }
  }
}
```

**Key Design Decisions:**
- Check database with `SELECT 1` query
- Check Redis cache and rate limiter with `ping()` command
- Properly close Redis connections after checking
- Set overall status to "unhealthy" if any check fails
- Include error messages in failed checks
- Only check enabled services (cache/limiter)

### 5. Query Filters for User List Endpoint

#### Repository Enhancement

**File:** `app/repositories/user.py`

```python
async def get_filtered_users(
    self,
    is_active: bool | None = None,
    is_superuser: bool | None = None,
    search: str | None = None,
    sort_by: str = "created_at",
    sort_order: str = "desc",
) -> Select:
    """Build filtered query for users.
    
    Returns:
        Select: SQLAlchemy select statement
    """
```

**Key Design Decisions:**
- Return Select statement for pagination compatibility
- Use dynamic query building with conditional filters
- Use `ilike()` for case-insensitive search
- Use `or_()` for multi-column search
- Use `getattr()` for dynamic column access in sorting
- Validate sort_by and sort_order at API layer

#### Endpoint Enhancement

**File:** `app/api/v1/endpoints/users.py`

```python
@router.get("/", response_model=Page[UserSchema])
async def list_users(
    current_superuser: CurrentSuperuser,
    params: PaginationParams,
    is_active: bool | None = None,
    is_superuser: bool | None = None,
    search: str | None = None,
    sort_by: Literal["created_at", "username", "email"] = "created_at",
    sort_order: Literal["asc", "desc"] = "desc",
    db: DBSession,
) -> Page[User]:
    """List users with filtering and sorting."""
```

### 6. Dashboard Statistics Caching

#### Caching Strategy

**Implementation:**
- Add `@cache(expire=60)` decorator to stats endpoint
- Use existing fastapi-cache2 infrastructure
- 60-second TTL balances freshness and performance
- Cache key automatically generated from endpoint path

**Cache Invalidation:**
- No explicit invalidation needed (stats are aggregate)
- 1-minute staleness is acceptable for dashboard metrics
- Cache automatically expires and refreshes

**Key Design Decisions:**
- Short TTL (60s) for reasonable freshness
- No cache invalidation complexity needed
- Reduces database load by 60x for frequent dashboard access
- Works with existing Redis cache configuration

### 7. Database Connection Pool Monitoring

#### Metrics Endpoint

**File:** `app/api/v1/endpoints/metrics.py` (new file)

```python
@router.get("/database")
async def database_metrics(
    current_superuser: CurrentSuperuser,
) -> dict:
    """Get database connection pool metrics.
    
    Returns:
        dict: Connection pool statistics
    """
```

**Response Structure:**

```json
{
  "pool_size": 5,
  "checked_in": 3,
  "checked_out": 2,
  "overflow": 0,
  "total_connections": 5
}
```

**Key Design Decisions:**
- Superuser-only access for security
- Access engine pool directly via `get_engine()`
- Return all relevant pool metrics
- No caching (real-time metrics needed)
- Useful for debugging connection issues

### 8. Bulk User Creation Endpoint

#### Service Enhancement

**File:** `app/services/user.py`

```python
async def create_users_bulk(
    self,
    users_in: list[UserCreate],
) -> list[User]:
    """Create multiple users in a single transaction.
    
    Args:
        users_in: List of user creation schemas
        
    Returns:
        list[User]: List of created users
        
    Raises:
        ConflictException: If any email/username conflicts
        DatabaseException: If transaction fails
    """
```

**Key Design Decisions:**
- Process all users in single transaction
- Rollback entire transaction on any failure
- Validate each user individually
- Return list of created users
- Superuser-only access
- Use existing create_user logic for consistency

#### Endpoint Implementation

**File:** `app/api/v1/endpoints/users.py`

```python
@router.post(
    "/bulk",
    response_model=list[UserSchema],
    status_code=status.HTTP_201_CREATED,
)
async def create_users_bulk(
    users_in: list[UserCreate],
    current_superuser: CurrentSuperuser,
    db: DBSession,
) -> list[User]:
    """Create multiple users in a single transaction."""
```

## Data Models

### Dashboard Statistics Response

```python
{
    "total_users": int,
    "active_users": int,
    "inactive_users": int,
    "superusers": int,
    "new_users_today": int,
    "new_users_week": int,
    "timestamp": str  # ISO format
}
```

### Database Metrics Response

```python
{
    "pool_size": int,
    "checked_in": int,
    "checked_out": int,
    "overflow": int,
    "total_connections": int
}
```

### Enhanced Health Check Response

```python
{
    "status": "healthy" | "unhealthy",
    "app_name": str,
    "version": str,
    "checks": {
        "database": {
            "status": "healthy" | "unhealthy",
            "provider": str,
            "error": str  # Optional, only on failure
        },
        "cache": {
            "status": "healthy" | "unhealthy",
            "error": str  # Optional, only on failure
        },
        "rate_limiter": {
            "status": "healthy" | "unhealthy",
            "error": str  # Optional, only on failure
        }
    }
}
```

## Error Handling

### Timeout Errors

```python
{
    "error": "request_timeout",
    "message": "Request exceeded 30.0s timeout",
    "details": [],
    "request_id": "uuid"
}
```

### Bulk Creation Errors

- Use existing exception handling patterns
- ConflictException for duplicate email/username
- DatabaseException for transaction failures
- Return detailed error information for debugging

## Testing Strategy

### Unit Tests

1. **Dashboard Service Tests**
   - Test aggregation query correctness
   - Test date filtering logic
   - Test response format

2. **Repository Tests**
   - Test filtered query building
   - Test search functionality
   - Test sorting logic

3. **Middleware Tests**
   - Test timeout enforcement
   - Test timeout error response
   - Test normal request flow

### Integration Tests

1. **Dashboard Stats Endpoint**
   - Test with various user counts
   - Test caching behavior
   - Test performance benchmarks

2. **User List Endpoint**
   - Test filtering combinations
   - Test search functionality
   - Test sorting options
   - Test pagination with filters

3. **Health Check Endpoint**
   - Test with all services healthy
   - Test with database failure
   - Test with Redis failures
   - Test with disabled services

4. **Bulk Creation Endpoint**
   - Test successful bulk creation
   - Test transaction rollback on failure
   - Test validation errors

### Performance Tests

1. **Dashboard Stats Performance**
   - Benchmark with 1k, 10k, 100k users
   - Verify <50ms response time
   - Verify cache hit performance

2. **Indexed Query Performance**
   - Benchmark queries before/after indexes
   - Verify 10x improvement

3. **Timeout Middleware**
   - Test with slow endpoints
   - Verify timeout enforcement

## Implementation Phases

### Phase 1: Critical (Priority 1)

**Estimated Time:** 1 hour  
**Impact:** Massive performance improvement

1. Optimize dashboard stats query
2. Add database indexes
3. Add request timeout middleware

### Phase 2: High Priority (Priority 2)

**Estimated Time:** 2 hours  
**Impact:** Better monitoring and UX

1. Enhanced health check
2. Cache dashboard stats
3. Query filters for list endpoints

### Phase 3: Nice to Have (Priority 3)

**Estimated Time:** 3 hours  
**Impact:** Enhanced features

1. Connection pool monitoring
2. Bulk operations
3. Advanced metrics

## Security Considerations

1. **Metrics Endpoints:** Superuser-only access
2. **Bulk Operations:** Superuser-only access
3. **Health Check:** Public access (no sensitive data exposed)
4. **Timeout Middleware:** Prevents DoS attacks
5. **Query Filters:** No SQL injection (parameterized queries)

## Backward Compatibility

1. **Dashboard Stats:** Response format unchanged
2. **User List:** New parameters are optional
3. **Health Check:** Enhanced but maintains basic fields
4. **All Changes:** Non-breaking additions only

## Monitoring and Observability

1. **Performance Metrics:** Track response times before/after
2. **Cache Hit Rates:** Monitor cache effectiveness
3. **Connection Pool:** Monitor pool utilization
4. **Timeout Events:** Log timeout occurrences
5. **Health Check:** Use for uptime monitoring

## Rollback Plan

1. **Indexes:** Can be dropped via migration downgrade
2. **Middleware:** Can be disabled in setup_middleware()
3. **Endpoints:** Can be removed from router
4. **Service Methods:** Old methods remain available
5. **Cache:** Can be disabled via configuration
