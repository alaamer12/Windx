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

## References

- [Repository Pattern](https://martinfowler.com/eaaCatalog/repository.html)
- [Service Layer Pattern](https://martinfowler.com/eaaCatalog/serviceLayer.html)
- [Clean Architecture](https://blog.cleancoder.com/uncle-bob/2012/08/13/the-clean-architecture.html)
- [FastAPI Best Practices](https://fastapi.tiangolo.com/tutorial/)
