# Application Architecture

## Overview

This application follows a **layered architecture** with clear separation of concerns, implementing the **Repository Pattern** with a **Service Layer** for business logic.

## Architecture Layers

```
┌─────────────────────────────────────────────────────────────┐
│                      API Layer (HTTP)                        │
│  - Endpoints (FastAPI routes)                               │
│  - Request/Response handling                                │
│  - HTTP status codes                                        │
│  - OpenAPI documentation                                    │
└──────────────────────┬──────────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────────┐
│                    Service Layer                             │
│  - Business logic                                           │
│  - Transaction management                                   │
│  - Validation rules                                         │
│  - Complex operations                                       │
└──────────────────────┬──────────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────────┐
│                  Repository Layer                            │
│  - Data access only                                         │
│  - CRUD operations                                          │
│  - Custom queries                                           │
│  - No business logic                                        │
└──────────────────────┬──────────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────────┐
│                   Database Layer                             │
│  - Connection management                                    │
│  - Session lifecycle                                        │
│  - ORM models                                               │
│  - Migrations                                               │
└─────────────────────────────────────────────────────────────┘
```

## Directory Structure

```
app/
├── api/                    # API Layer
│   ├── deps.py            # FastAPI dependencies
│   ├── types.py           # Type aliases for dependencies
│   └── v1/                # API version 1
│       ├── endpoints/     # Route handlers
│       │   ├── auth.py    # Authentication endpoints
│       │   └── users.py   # User endpoints
│       └── router.py      # API router configuration
│
├── services/              # Service Layer (Business Logic)
│   ├── __init__.py
│   ├── base.py           # Base service class
│   ├── auth.py           # Authentication service
│   ├── user.py           # User service
│   └── session.py        # Session service
│
├── repositories/          # Repository Layer (Data Access)
│   ├── __init__.py
│   ├── base.py           # Base repository class
│   ├── user.py           # User repository
│   └── session.py        # Session repository
│
├── database/              # Database Layer
│   ├── __init__.py
│   ├── base.py           # Declarative base
│   ├── connection.py     # Connection & session management
│   └── utils.py          # Database utilities
│
├── models/                # ORM Models
│   ├── __init__.py
│   ├── user.py           # User model
│   └── session.py        # Session model
│
├── schemas/               # Pydantic Schemas
│   ├── __init__.py
│   ├── user.py           # User schemas
│   └── session.py        # Session schemas
│
├── core/                  # Core Functionality
│   ├── config.py         # Configuration
│   ├── security.py       # Security utilities
│   ├── exceptions.py     # Exception handling
│   ├── middleware.py     # Middleware
│   ├── cache.py          # Caching
│   ├── limiter.py        # Rate limiting
│   └── pagination.py     # Pagination
│
└── main.py               # Application entry point
```

## Layer Responsibilities

### 1. API Layer (`app/api/`)

**Purpose**: Handle HTTP requests and responses

**Responsibilities**:
- Route definition and HTTP method handling
- Request validation (via Pydantic)
- Response formatting
- HTTP status codes
- OpenAPI documentation
- Dependency injection

**Rules**:
- ✅ Call service layer methods
- ✅ Handle HTTP-specific concerns
- ✅ Return Pydantic schemas
- ❌ No business logic
- ❌ No direct database access
- ❌ No direct repository calls

**Example**:
```python
@router.post("/users", response_model=UserSchema, status_code=201)
async def create_user(
    user_in: UserCreate,
    db: DBSession,
) -> User:
    """Create new user endpoint."""
    user_service = UserService(db)
    return await user_service.create_user(user_in)
```

### 2. Service Layer (`app/services/`)

**Purpose**: Implement business logic and orchestrate operations

**Responsibilities**:
- Business logic implementation
- Transaction management
- Validation rules
- Complex operations across multiple repositories
- Error handling with domain exceptions

**Rules**:
- ✅ Use repositories for data access
- ✅ Implement business rules
- ✅ Manage transactions
- ✅ Raise domain exceptions
- ❌ No HTTP concerns
- ❌ No direct SQL queries
- ❌ No Pydantic schemas in method signatures (use models)

**Example**:
```python
class UserService(BaseService):
    async def create_user(self, user_in: UserCreate) -> User:
        """Create user with validation."""
        # Business logic: Check uniqueness
        if await self.user_repo.get_by_email(user_in.email):
            raise ConflictException("Email already exists")
        
        # Business logic: Hash password
        hashed_password = get_password_hash(user_in.password)
        
        # Data access: Create user
        user = await self.user_repo.create({
            **user_in.model_dump(exclude={"password"}),
            "hashed_password": hashed_password,
        })
        
        # Transaction management
        await self.commit()
        return user
```

### 3. Repository Layer (`app/repositories/`)

**Purpose**: Data access and persistence

**Responsibilities**:
- CRUD operations
- Custom queries
- Data retrieval and storage
- Query optimization

**Rules**:
- ✅ Use SQLAlchemy ORM
- ✅ Return ORM models
- ✅ Implement custom queries
- ❌ No business logic
- ❌ No validation
- ❌ No transaction management (handled by service)
- ❌ No password hashing or security logic

**Example**:
```python
class UserRepository(BaseRepository[User, UserCreate, UserUpdate]):
    async def get_by_email(self, email: str) -> User | None:
        """Get user by email."""
        result = await self.db.execute(
            select(User).where(User.email == email)
        )
        return result.scalar_one_or_none()
```

### 4. Database Layer (`app/database/`)

**Purpose**: Database configuration and connection management

**Responsibilities**:
- Database connection setup
- Session lifecycle management
- Engine configuration
- Connection pooling
- Database utilities

**Rules**:
- ✅ Configure database connections
- ✅ Manage session lifecycle
- ✅ Provide database utilities
- ❌ No business logic
- ❌ No data access logic

**Example**:
```python
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Database session dependency."""
    session_maker = get_session_maker()
    async with session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
```

## Data Flow

### Create User Flow

```
1. HTTP Request
   POST /api/v1/users
   Body: {"email": "user@example.com", "password": "secret"}
   
2. API Layer (endpoints/users.py)
   - Validate request with Pydantic
   - Call UserService.create_user()
   
3. Service Layer (services/user.py)
   - Check email uniqueness (business rule)
   - Hash password (business logic)
   - Call UserRepository.create()
   - Commit transaction
   
4. Repository Layer (repositories/user.py)
   - Execute INSERT query
   - Return User model
   
5. Database Layer
   - Manage session
   - Execute SQL
   
6. Response
   - Service returns User model
   - API converts to UserSchema
   - Return HTTP 201 with user data
```

### Authentication Flow

```
1. HTTP Request
   POST /api/v1/auth/login
   Body: {"email": "user@example.com", "password": "secret"}
   
2. API Layer (endpoints/auth.py)
   - Validate request
   - Call AuthService.login()
   
3. Service Layer (services/auth.py)
   - Authenticate user (business logic)
   - Verify password
   - Create JWT token
   - Create session via SessionRepository
   - Commit transaction
   
4. Repository Layer
   - UserRepository.get_by_email()
   - SessionRepository.create()
   
5. Response
   - Return access token
```

## Benefits of This Architecture

### 1. Separation of Concerns
- Each layer has a single responsibility
- Easy to understand and maintain
- Changes in one layer don't affect others

### 2. Testability
- Service layer can be tested without HTTP
- Repository layer can be tested with test database
- Easy to mock dependencies

### 3. Reusability
- Services can be called from multiple endpoints
- Repositories can be used by multiple services
- Business logic is centralized

### 4. Maintainability
- Clear structure makes code easy to find
- Consistent patterns across the application
- Easy to onboard new developers

### 5. Scalability
- Easy to add new features
- Can extract services to microservices
- Clear boundaries for refactoring

## Design Patterns

### Repository Pattern
- Abstracts data access
- Provides clean API for data operations
- Easy to swap implementations

### Service Pattern
- Encapsulates business logic
- Orchestrates multiple repositories
- Manages transactions

### Dependency Injection
- Loose coupling between layers
- Easy to test with mocks
- FastAPI's Depends() system

### Unit of Work
- Transaction management in services
- Commit/rollback handling
- Ensures data consistency

## Best Practices

### API Layer
```python
# ✅ CORRECT
@router.post("/users")
async def create_user(user_in: UserCreate, db: DBSession):
    service = UserService(db)
    return await service.create_user(user_in)

# ❌ WRONG - Business logic in endpoint
@router.post("/users")
async def create_user(user_in: UserCreate, db: DBSession):
    if await user_repo.get_by_email(user_in.email):  # Business logic!
        raise HTTPException(400, "Email exists")
    hashed = get_password_hash(user_in.password)  # Business logic!
    return await user_repo.create(...)
```

### Service Layer
```python
# ✅ CORRECT
class UserService(BaseService):
    async def create_user(self, user_in: UserCreate) -> User:
        # Business logic here
        if await self.user_repo.get_by_email(user_in.email):
            raise ConflictException("Email exists")
        user = await self.user_repo.create(...)
        await self.commit()
        return user

# ❌ WRONG - No business logic
class UserService(BaseService):
    async def create_user(self, user_in: UserCreate) -> User:
        return await self.user_repo.create(user_in)  # Just passing through!
```

### Repository Layer
```python
# ✅ CORRECT
class UserRepository(BaseRepository):
    async def get_by_email(self, email: str) -> User | None:
        result = await self.db.execute(
            select(User).where(User.email == email)
        )
        return result.scalar_one_or_none()

# ❌ WRONG - Business logic in repository
class UserRepository(BaseRepository):
    async def create_user(self, user_in: UserCreate) -> User:
        if await self.get_by_email(user_in.email):  # Business logic!
            raise ValueError("Email exists")
        hashed = get_password_hash(user_in.password)  # Business logic!
        return await self.create(...)
```

## Migration from Old Structure

### Before (Mixed Concerns)
```python
# Endpoint with business logic
@router.post("/users")
async def create_user(user_in: UserCreate, user_repo: UserRepo):
    # Business logic in endpoint!
    if await user_repo.get_by_email(user_in.email):
        raise HTTPException(400, "Email exists")
    hashed = get_password_hash(user_in.password)
    return await user_repo.create(...)
```

### After (Proper Separation)
```python
# Endpoint (HTTP only)
@router.post("/users")
async def create_user(user_in: UserCreate, db: DBSession):
    service = UserService(db)
    return await service.create_user(user_in)

# Service (Business logic)
class UserService:
    async def create_user(self, user_in: UserCreate) -> User:
        if await self.user_repo.get_by_email(user_in.email):
            raise ConflictException("Email exists")
        hashed = get_password_hash(user_in.password)
        user = await self.user_repo.create({...})
        await self.commit()
        return user

# Repository (Data access only)
class UserRepository:
    async def get_by_email(self, email: str) -> User | None:
        result = await self.db.execute(...)
        return result.scalar_one_or_none()
```

## Testing Strategy

### Unit Tests
- Test services with mocked repositories
- Test repositories with test database
- Test endpoints with mocked services

### Integration Tests
- Test full flow from endpoint to database
- Use test database
- Verify transactions

### Example
```python
# Test service with mocked repository
async def test_create_user_duplicate_email():
    mock_repo = Mock(UserRepository)
    mock_repo.get_by_email.return_value = User(...)
    
    service = UserService(mock_db)
    service.user_repo = mock_repo
    
    with pytest.raises(ConflictException):
        await service.create_user(user_in)
```

## Performance Optimizations

### Overview

The application implements several performance optimizations to ensure scalability and responsiveness under load. These optimizations focus on reducing database queries, implementing caching, adding strategic indexes, and preventing resource exhaustion.

### DashboardService

**Purpose**: Optimize dashboard statistics calculation using database aggregation

**Implementation**:
- Located in `app/services/dashboard.py`
- Uses SQLAlchemy `func.count()` with filters for aggregation
- Calculates all statistics in a single database query
- Returns results with ISO timestamp

**Performance Impact**:
- Before: 500ms+ with 10k users (loads all records into memory)
- After: <50ms with 10k users (database aggregation)
- 10-100x performance improvement

**Usage**:
```python
dashboard_service = DashboardService(db)
stats = await dashboard_service.get_dashboard_stats_optimized()
# Returns: {
#   "total_users": 10000,
#   "active_users": 9500,
#   "inactive_users": 500,
#   "superusers": 10,
#   "new_users_today": 25,
#   "new_users_week": 150,
#   "timestamp": "2024-01-15T10:30:00Z"
# }
```

### TimeoutMiddleware

**Purpose**: Prevent long-running requests from blocking resources

**Implementation**:
- Located in `app/core/middleware.py`
- Uses `asyncio.wait_for()` to enforce timeout
- Default timeout: 30 seconds (configurable)
- Returns HTTP 504 Gateway Timeout on timeout

**Configuration**:
```python
app.add_middleware(TimeoutMiddleware, timeout=30.0)
```

**Error Response**:
```json
{
  "error": "request_timeout",
  "message": "Request exceeded 30.0s timeout",
  "details": [],
  "request_id": "uuid"
}
```

### Enhanced Health Check

**Purpose**: Comprehensive dependency verification for monitoring

**Implementation**:
- Located in `main.py` at `/health` endpoint
- Verifies database connectivity with `SELECT 1`
- Verifies Redis cache connectivity (if enabled)
- Verifies Redis rate limiter connectivity (if enabled)
- Returns overall status and individual check results

**Response Format**:
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

### Query Filters and Sorting

**Purpose**: Efficient data retrieval with filtering and sorting

**Implementation**:
- User list endpoint supports filtering by `is_active`, `is_superuser`
- Search functionality across `username`, `email`, `full_name`
- Sorting by `created_at`, `username`, or `email`
- Sort order: `asc` or `desc`

**Repository Method**:
```python
# app/repositories/user.py
async def get_filtered_users(
    self,
    is_active: bool | None = None,
    is_superuser: bool | None = None,
    search: str | None = None,
    sort_by: str = "created_at",
    sort_order: str = "desc",
) -> Select:
    """Build filtered query for users."""
```

**Usage**:
```
GET /api/v1/users?is_active=true&search=john&sort_by=created_at&sort_order=desc
```

### Database Indexes

**Purpose**: Optimize query performance for frequently filtered columns

**Indexes Added**:
- `ix_users_is_active` - For filtering active/inactive users
- `ix_users_is_superuser` - For filtering superusers
- `ix_users_created_at` - For sorting by creation date

**Implementation**:
```python
# app/models/user.py
is_active: Mapped[bool] = mapped_column(
    default=True,
    nullable=False,
    index=True,  # Index for filtering
    doc="Account active status",
)
```

**Migration**:
```bash
alembic revision -m "add_user_indexes"
alembic upgrade head
```

**Performance Impact**:
- 10x improvement on filtered queries
- Faster sorting operations
- Reduced database load

### Caching Strategy

**Purpose**: Reduce database load for frequently accessed data

**Implementation**:
- Dashboard stats endpoint cached for 60 seconds
- Uses `fastapi-cache2` with Redis backend
- Automatic cache key generation
- TTL-based expiration (no manual invalidation needed)

**Usage**:
```python
from fastapi_cache.decorator import cache

@router.get("/stats")
@cache(expire=60)  # Cache for 1 minute
async def get_dashboard_stats(db: DBSession):
    dashboard_service = DashboardService(db)
    return await dashboard_service.get_dashboard_stats_optimized()
```

**Performance Impact**:
- 60x reduction in database queries for dashboard stats
- Sub-millisecond response time on cache hit
- Acceptable 1-minute staleness for aggregate statistics

### Metrics Endpoints

**Purpose**: Monitor database connection pool and system health

**Database Metrics**:
- Located at `/api/v1/metrics/database`
- Superuser-only access
- Returns connection pool statistics

**Response Format**:
```json
{
  "pool_size": 5,
  "checked_in": 3,
  "checked_out": 2,
  "overflow": 0,
  "total_connections": 5
}
```

**Usage**:
```python
# app/api/v1/endpoints/metrics.py
@router.get("/database")
async def database_metrics(current_superuser: CurrentSuperuser) -> dict:
    """Get database connection pool metrics."""
    engine = get_engine()
    pool = engine.pool
    return {
        "pool_size": pool.size(),
        "checked_in": pool.checkedin(),
        "checked_out": pool.checkedout(),
        "overflow": pool.overflow(),
        "total_connections": pool.size() + pool.overflow(),
    }
```

### Bulk Operations

**Purpose**: Efficient batch processing of multiple records

**Implementation**:
- Bulk user creation endpoint at `/api/v1/users/bulk`
- Processes all users in single transaction
- Automatic rollback on any failure
- Superuser-only access

**Usage**:
```python
POST /api/v1/users/bulk
[
  {"email": "user1@example.com", "username": "user1", "password": "pass1"},
  {"email": "user2@example.com", "username": "user2", "password": "pass2"}
]
```

**Service Method**:
```python
# app/services/user.py
async def create_users_bulk(
    self,
    users_in: list[UserCreate],
) -> list[User]:
    """Create multiple users in a single transaction."""
```

### Performance Best Practices

1. **Use Database Aggregation**: Calculate statistics in database, not in memory
2. **Add Strategic Indexes**: Index frequently filtered and sorted columns
3. **Implement Caching**: Cache read-only data with appropriate TTL
4. **Enforce Timeouts**: Prevent long-running requests from blocking resources
5. **Use Pagination**: Always paginate list endpoints
6. **Monitor Metrics**: Track connection pool usage and system health
7. **Batch Operations**: Use bulk endpoints for multiple records

### Monitoring Recommendations

1. **Health Check**: Monitor `/health` endpoint for dependency status
2. **Database Metrics**: Monitor `/api/v1/metrics/database` for connection pool usage
3. **Cache Hit Rate**: Monitor Redis cache hit/miss ratio
4. **Response Times**: Track endpoint response times
5. **Timeout Events**: Log and monitor timeout occurrences
6. **Query Performance**: Monitor slow query logs

### Performance Benchmarks

See `docs/PERFORMANCE.md` for detailed benchmarks and performance testing results.

## References

- [Repository Pattern](https://martinfowler.com/eaaCatalog/repository.html)
- [Service Layer Pattern](https://martinfowler.com/eaaCatalog/serviceLayer.html)
- [Clean Architecture](https://blog.cleancoder.com/uncle-bob/2012/08/13/the-clean-architecture.html)
- [FastAPI Best Practices](https://fastapi.tiangolo.com/tutorial/)
- [SQLAlchemy Performance](https://docs.sqlalchemy.org/en/20/faq/performance.html)
- [Redis Caching Strategies](https://redis.io/docs/manual/patterns/)
