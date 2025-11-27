---
inclusion: always
---

# Project Coding Standards and Patterns

This document defines the coding standards, patterns, and best practices for this FastAPI backend project.

## Architecture Patterns

### Layered Architecture
- **ALWAYS** follow the layered architecture pattern
- **API Layer** → **Service Layer** → **Repository Layer** → **Database Layer**
- Each layer has specific responsibilities
- Never skip layers or mix concerns

```
API Layer (HTTP) → Service Layer (Business Logic) → Repository Layer (Data Access) → Database Layer
```

### Repository Pattern
- **ALWAYS** use repository pattern for database operations
- **NEVER** access SQLAlchemy models directly in endpoints
- Create custom repository methods for complex queries
- Inherit from `BaseRepository` for standard CRUD operations
- Repositories only handle data access, no business logic

```python
# ✅ CORRECT - Repository with data access only
class UserRepository(BaseRepository[User, UserCreate, UserUpdate]):
    async def get_by_email(self, email: str) -> User | None:
        result = await self.db.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()

# ❌ WRONG - Business logic in repository
class UserRepository(BaseRepository):
    async def create_user(self, user_in: UserCreate) -> User:
        if await self.get_by_email(user_in.email):  # Business logic!
            raise ValueError("Email exists")
        return await self.create(user_in)
```

### Service Pattern
- **ALWAYS** implement business logic in service layer
- **NEVER** put business logic in endpoints or repositories
- Services orchestrate multiple repositories
- Services manage transactions (commit/rollback)
- Services raise domain exceptions

```python
# ✅ CORRECT - Business logic in service
class UserService(BaseService):
    async def create_user(self, user_in: UserCreate) -> User:
        # Business logic: Check uniqueness
        if await self.user_repo.get_by_email(user_in.email):
            raise ConflictException("Email already exists")
        
        # Business logic: Hash password
        hashed_password = get_password_hash(user_in.password)
        
        # Data access via repository
        user = await self.user_repo.create({
            **user_in.model_dump(exclude={"password"}),
            "hashed_password": hashed_password,
        })
        
        # Transaction management
        await self.commit()
        return user

# ❌ WRONG - Business logic in endpoint
@router.post("/users")
async def create_user(user_in: UserCreate, user_repo: UserRepo):
    if await user_repo.get_by_email(user_in.email):  # Business logic in endpoint!
        raise HTTPException(400, "Email exists")
    hashed = get_password_hash(user_in.password)  # Business logic in endpoint!
    return await user_repo.create(...)
```

### API Layer Pattern
- **ALWAYS** keep endpoints thin (HTTP handling only)
- **NEVER** put business logic in endpoints
- Call service layer methods
- Handle HTTP-specific concerns (status codes, headers)
- Return Pydantic schemas

```python
# ✅ CORRECT - Thin endpoint calling service
@router.post("/users", response_model=UserSchema, status_code=201)
async def create_user(user_in: UserCreate, db: DBSession) -> User:
    """Create new user."""
    user_service = UserService(db)
    return await user_service.create_user(user_in)

# ❌ WRONG - Business logic in endpoint
@router.post("/users")
async def create_user(user_in: UserCreate, user_repo: UserRepo):
    # Validation, hashing, checking - all business logic!
    if await user_repo.get_by_email(user_in.email):
        raise HTTPException(400, "Email exists")
    hashed = get_password_hash(user_in.password)
    return await user_repo.create(...)
```

### Dependency Injection
- Use FastAPI's `Depends()` for all dependencies
- Use `Annotated` for type hints with dependencies
- Create reusable dependencies in `app/api/deps.py`

```python
# ✅ CORRECT
async def get_user(
    user_id: PositiveInt,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> User:
    pass
```

## Type Hinting Standards

### Full Type Hinting Required
- **ALL** functions, methods, and variables must have type hints
- Use `Annotated` for FastAPI dependencies and Pydantic fields
- Use union types with `|` (not `Union`)
- Use `None` instead of `Optional`

```python
# ✅ CORRECT
def get_user(user_id: int) -> User | None:
    pass

# ❌ WRONG
def get_user(user_id):  # Missing types
    pass
```

### Pydantic Semantic Types
- **ALWAYS** use Pydantic semantic types instead of primitives with manual validation
- Use `PositiveInt` instead of `int` with `gt=0`
- Use `EmailStr` for email fields
- Use `AnyHttpUrl` for URLs
- Use `SecretStr` for sensitive strings

```python
# ✅ CORRECT
class UserCreate(BaseModel):
    age: PositiveInt
    email: EmailStr

# ❌ WRONG
class UserCreate(BaseModel):
    age: Annotated[int, Field(gt=0)]  # Use PositiveInt instead
    email: str  # Use EmailStr instead
```

### Annotated Types
- Use `Annotated` for all Pydantic fields with `Field()`
- Use `Annotated` for FastAPI dependencies
- Use `Annotated` for SQLAlchemy mapped columns when needed

```python
# ✅ CORRECT
email: Annotated[
    EmailStr,
    Field(
        description="User email address",
        examples=["user@example.com"],
    ),
]
```

## SQLAlchemy Standards

### Mapped Columns
- **ALWAYS** use `Mapped[type]` with `mapped_column()`
- Use SQLAlchemy 2.0 style (not legacy)
- Define relationships with proper type hints

```python
# ✅ CORRECT
class User(Base):
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    sessions: Mapped[list["Session"]] = relationship("Session", back_populates="user")

# ❌ WRONG - Legacy style
class User(Base):
    id = Column(Integer, primary_key=True)  # Don't use Column
```

### Async Operations
- **ALL** database operations must be async
- Use `AsyncSession` for database sessions
- Use `async with` for session management
- Use `await` for all database queries

```python
# ✅ CORRECT
async def get_user(self, id: int) -> User | None:
    result = await self.db.execute(select(User).where(User.id == id))
    return result.scalar_one_or_none()
```

## Pydantic Schema Standards

### Composed Schemas
- **NEVER** create monolithic schema classes
- **ALWAYS** compose schemas (Base, Create, Update, Response, InDB)
- Use inheritance for schema composition
- Keep schemas focused and single-purpose

```python
# ✅ CORRECT - Composed schemas
class UserBase(BaseModel):
    email: EmailStr
    username: str

class UserCreate(UserBase):
    password: str

class User(UserBase):
    id: PositiveInt
    is_active: bool
    created_at: datetime

class UserInDB(User):
    hashed_password: str

# ❌ WRONG - Monolithic schema
class User(BaseModel):
    id: int | None = None
    email: str
    username: str
    password: str | None = None
    hashed_password: str | None = None
    is_active: bool = True
```

### Schema Configuration
- Use `model_config = ConfigDict(from_attributes=True)` for ORM models
- Use `Field()` for all field metadata
- Include descriptions and examples

## Documentation Standards

### Google-Style Docstrings
- **ALL** modules, classes, functions, and methods must have Google-style docstrings
- Module docstrings must include: description, public classes, public functions, features
- Function docstrings must include: Args (with types), Returns (with types), Raises
- Class docstrings must include: Attributes

```python
# ✅ CORRECT - Module docstring
"""User repository for database operations.

This module implements the repository pattern for User model with
custom query methods for user management.

Public Classes:
    UserRepository: Repository for User CRUD operations

Public Functions:
    None

Features:
    - User lookup by email and username
    - Active user filtering
    - Inherits base CRUD operations
"""

# ✅ CORRECT - Function docstring
async def get_by_email(self, email: str) -> User | None:
    """Get user by email address.

    Args:
        email (str): User email address

    Returns:
        User | None: User instance or None if not found
    """

# ✅ CORRECT - Class docstring
class User(Base):
    """User model for authentication and user management.
    
    Attributes:
        id: Primary key
        email: Unique email address
        username: Unique username
        hashed_password: Bcrypt hashed password
        is_active: Account active status
    """
```

### __all__ Variable
- **EVERY** module must define `__all__`
- List all public classes, functions, and variables
- Place after imports, before code

```python
# ✅ CORRECT
"""Module docstring."""

from typing import Annotated

__all__ = ["UserRepository", "SessionRepository"]

class UserRepository:
    pass
```

## Configuration Standards

### Settings with lru_cache
- Use `@lru_cache` decorator for `get_settings()`
- Compose settings into logical groups (DatabaseSettings, SecuritySettings)
- Use `pydantic-settings` for environment variables
- Use nested settings with `env_nested_delimiter`

```python
# ✅ CORRECT
@lru_cache
def get_settings() -> Settings:
    """Get cached application settings.

    Returns:
        Settings: Application settings instance (cached singleton)
    """
    return Settings()
```

### Environment Variables
- Use `.env` file for local development
- Provide `.env.example` with all required variables
- Use type-safe settings with Pydantic validation
- Use descriptive field names with proper prefixes

## Security Standards

### Password Hashing
- **ALWAYS** use bcrypt for password hashing
- Use `passlib` with `CryptContext`
- Never store plain text passwords
- Hash passwords before storing in database

```python
# ✅ CORRECT
hashed_password = get_password_hash(user_in.password)
```

### JWT Tokens
- Use `python-jose` for JWT operations
- Store secret key in environment variables
- Use configurable token expiration
- Validate tokens on every protected endpoint

### Authentication
- Use HTTP Bearer token authentication
- Implement `get_current_user` dependency
- Implement `get_current_active_superuser` for admin endpoints
- Return proper HTTP status codes (401, 403)

## API Endpoint Standards

### Endpoint Organization
- Organize endpoints by feature domain (auth, users, etc.)
- Use API versioning (`/api/v1/`)
- Use plural nouns for resource endpoints (`/users`, not `/user`)
- Use proper HTTP methods (GET, POST, PATCH, DELETE)

### Router Configuration
- **ALWAYS** configure router with tags and common responses
- Use descriptive tags for OpenAPI grouping
- Include common error responses at router level

```python
# ✅ CORRECT - Router with configuration
from app.schemas.responses import get_common_responses

router = APIRouter(
    tags=["Users"],
    responses=get_common_responses(401, 403, 500),
)

# ❌ WRONG - No configuration
router = APIRouter()
```

### Endpoint Documentation
- **ALWAYS** include `summary`, `description`, `response_description`, `operation_id`
- **ALWAYS** provide response examples for success cases
- **ALWAYS** include common error responses with `**get_common_responses()`

```python
# ✅ CORRECT - Complete OpenAPI documentation
@router.post(
    "/users",
    response_model=UserSchema,
    status_code=status.HTTP_201_CREATED,
    summary="Create New User",
    description="Create a new user account with email and password.",
    response_description="Successfully created user",
    operation_id="createUser",
    responses={
        201: {
            "description": "User successfully created",
            "content": {
                "application/json": {
                    "example": {
                        "id": 1,
                        "email": "user@example.com",
                        "username": "john_doe"
                    }
                }
            }
        },
        409: {
            "description": "Email already exists",
            "content": {
                "application/json": {
                    "example": {
                        "message": "Email already registered",
                        "details": [{"detail": "Email is already in use"}]
                    }
                }
            }
        },
        **get_common_responses(422, 500)
    }
)
async def create_user(user_in: UserCreate, db: DBSession) -> User:
    """Create a new user."""
    pass

# ❌ WRONG - No documentation
@router.post("/users")
async def create_user(user_in: UserCreate):
    pass
```

### Response Models
- **ALWAYS** specify `response_model` in decorators
- Use proper status codes (`status.HTTP_201_CREATED`, etc.)
- Return consistent response structures
- Use Pydantic schemas for responses

```python
# ✅ CORRECT
@router.post("/", response_model=UserSchema, status_code=status.HTTP_201_CREATED)
async def create_user(user_in: UserCreate) -> User:
    pass
```

### Error Handling
- Use domain exceptions (not HTTPException directly)
- Include descriptive error messages
- Use proper HTTP status codes
- Errors are handled by global exception handlers

```python
# ✅ CORRECT - Use domain exceptions
from app.core.exceptions import NotFoundException, ConflictException

if not user:
    raise NotFoundException(resource="User", details={"user_id": user_id})

if await user_repo.get_by_email(email):
    raise ConflictException(message="Email already exists", details={"email": email})

# ❌ WRONG - Direct HTTPException
raise HTTPException(status_code=404, detail="User not found")
```

## File Organization

### Module Structure
```
app/
├── core/           # Core functionality (config, database, security)
├── models/         # SQLAlchemy ORM models
├── schemas/        # Pydantic schemas
├── repositories/   # Repository pattern implementations
├── api/
│   ├── deps.py    # Shared dependencies
│   └── v1/
│       ├── router.py
│       └── endpoints/  # Feature-based endpoints
└── main.py        # Application entry point
```

### Import Order
1. Standard library imports
2. Third-party imports
3. Local application imports
4. Blank line between groups

```python
# ✅ CORRECT
from datetime import datetime
from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User
```

## Testing Standards (Future)

### Test Organization
- Mirror application structure in tests
- Use pytest for testing
- Use async test fixtures
- Mock external dependencies

### Test Coverage
- Aim for 80%+ code coverage
- Test all repository methods
- Test all API endpoints
- Test error cases

## Database Standards

### Migrations
- Use Alembic for database migrations
- Create migration for every model change
- Review migrations before applying
- Never edit applied migrations

### Naming Conventions
- Tables: plural snake_case (`users`, `sessions`)
- Columns: snake_case (`created_at`, `is_active`)
- Indexes: `ix_{table}_{column}`
- Foreign keys: `fk_{table}_{column}`

## Performance Standards

### Query Optimization
- Use `select()` for queries (not legacy query API)
- Use `joinedload()` for eager loading relationships
- Use pagination for list endpoints
- Add indexes on frequently queried columns

### Caching
- Use `@lru_cache` for expensive computations
- Cache settings globally
- Consider Redis for distributed caching (future)

## Code Quality

### Linting and Formatting
- Use Ruff for linting and formatting
- Follow PEP 8 style guide
- Maximum line length: 100 characters
- Use trailing commas in multi-line structures

### Code Review Checklist
- [ ] All functions have type hints
- [ ] All functions have Google-style docstrings
- [ ] All modules have `__all__` defined
- [ ] Repository pattern used for database access
- [ ] Pydantic semantic types used
- [ ] Composed schemas (not monolithic)
- [ ] SQLAlchemy Mapped columns used
- [ ] Async/await used for database operations
- [ ] Proper error handling with HTTPException
- [ ] Tests written (when applicable)

## Common Patterns

### Creating a New Endpoint
1. Define Pydantic schemas (Base, Create, Update, Response)
2. Create/update SQLAlchemy model with Mapped columns
3. Create/update repository with custom methods
4. Create endpoint in appropriate router
5. Add authentication/authorization dependencies
6. Write tests

### Adding a New Model
1. Create model in `app/models/` with Mapped columns
2. Create schemas in `app/schemas/` (composed)
3. Create repository in `app/repositories/`
4. Add to `__init__.py` files with `__all__`
5. Create Alembic migration
6. Create endpoints in `app/api/v1/endpoints/`

## Anti-Patterns to Avoid

### ❌ Don't Do This
- Direct database queries in endpoints
- Monolithic Pydantic schemas
- Missing type hints
- Missing docstrings
- Using `Optional[T]` instead of `T | None`
- Using `Union[A, B]` instead of `A | B`
- Legacy SQLAlchemy `Column()` instead of `Mapped`
- Synchronous database operations
- Plain `int` with validation instead of `PositiveInt`
- Missing `__all__` in modules
- PEP 257 style docstrings instead of Google style

## Type Aliases for Dependencies

### Reusable Type Aliases
- **ALWAYS** use type aliases from `app/api/types` for common dependencies
- **NEVER** repeat `Annotated[Type, Depends(func)]` in endpoints
- Create new type aliases for frequently used dependencies
- Include comprehensive docstrings with usage examples

```python
# ✅ CORRECT - Use type aliases
from app.api.types import DBSession, CurrentUser, UserRepo

@router.get("/users/{user_id}")
async def get_user(
    user_id: int,
    user_repo: UserRepo,
    current_user: CurrentUser,
) -> User:
    return await user_repo.get(user_id)

# ❌ WRONG - Repeat dependency annotations
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

@router.get("/users/{user_id}")
async def get_user(
    user_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> User:
    user_repo = UserRepository(db)
    return await user_repo.get(user_id)
```

### Available Type Aliases

**Database:**
- `DBSession`: Database session dependency
  ```python
  async def endpoint(db: DBSession): ...
  ```

**Authentication:**
- `CurrentUser`: Current authenticated user
  ```python
  async def endpoint(current_user: CurrentUser): ...
  ```
- `CurrentSuperuser`: Current superuser
  ```python
  async def endpoint(current_superuser: CurrentSuperuser): ...
  ```

**Repositories:**
- `UserRepo`: User repository dependency
  ```python
  async def endpoint(user_repo: UserRepo): ...
  ```
- `SessionRepo`: Session repository dependency
  ```python
  async def endpoint(session_repo: SessionRepo): ...
  ```

### Creating New Type Aliases

When creating new type aliases in `app/api/types.py`:

1. Add factory function for repository dependencies
2. Create type alias with `Annotated`
3. Include comprehensive docstring with:
   - Description
   - Usage example
   - Available methods (for repositories)
4. Add to `__all__`

```python
# ✅ CORRECT - New type alias
def get_product_repository(db: DBSession) -> ProductRepository:
    """Get product repository instance.
    
    Args:
        db (AsyncSession): Database session
    
    Returns:
        ProductRepository: Product repository instance
    """
    return ProductRepository(db)

ProductRepo = Annotated[ProductRepository, Depends(get_product_repository)]
"""Product repository dependency.

Provides access to product data access layer.

Usage:
    ```python
    @router.get("/products/{product_id}")
    async def get_product(
        product_id: int,
        product_repo: ProductRepo,
    ):
        return await product_repo.get(product_id)
    ```

Available Methods:
    - get(id): Get product by ID
    - get_by_sku(sku): Get product by SKU
    - create(obj_in): Create new product
"""
```

### Benefits of Type Aliases

1. **Reduced Boilerplate**: Less code repetition
2. **Better Readability**: Clear, concise parameter names
3. **IDE Support**: Full autocomplete and type checking
4. **Consistency**: Same pattern across all endpoints
5. **Documentation**: Docstrings provide inline help
6. **Maintainability**: Change dependency in one place

## Performance Optimization

### Caching with fastapi-cache2

- **ALWAYS** cache read-only endpoints that don't change frequently
- Use appropriate TTL (Time To Live) based on data volatility
- Invalidate cache when data is updated
- Use Redis for distributed caching

```python
# ✅ CORRECT - Cache read operations
from fastapi_cache.decorator import cache

@router.get("/users/{user_id}")
@cache(expire=300)  # Cache for 5 minutes
async def get_user(user_id: int, user_repo: UserRepo) -> User:
    return await user_repo.get(user_id)

# ✅ CORRECT - Invalidate cache on update
@router.patch("/users/{user_id}")
async def update_user(user_id: int, user_update: UserUpdate, user_repo: UserRepo):
    user = await user_repo.update(user_id, user_update)
    await invalidate_cache(f"*get_user*{user_id}*")
    return user

# ❌ WRONG - Don't cache write operations
@router.post("/users")
@cache(expire=300)  # Wrong!
async def create_user(user_in: UserCreate):
    pass
```

### Rate Limiting with fastapi-limiter

- **ALWAYS** add rate limiting to public endpoints
- Use stricter limits for sensitive operations (login, register)
- Use per-user rate limiting when possible
- Configure appropriate time windows

```python
# ✅ CORRECT - Rate limit sensitive endpoints
from app.core.limiter import rate_limit

@router.post(
    "/login",
    dependencies=[Depends(rate_limit(times=10, seconds=300))]  # 10 per 5 min
)
async def login(login_data: LoginRequest):
    pass

@router.post(
    "/register",
    dependencies=[Depends(rate_limit(times=5, seconds=3600))]  # 5 per hour
)
async def register(user_in: UserCreate):
    pass

# ✅ CORRECT - Rate limit read endpoints
@router.get(
    "/users/{user_id}",
    dependencies=[Depends(rate_limit(times=20, seconds=60))]  # 20 per minute
)
async def get_user(user_id: int):
    pass

# ❌ WRONG - No rate limiting on public endpoint
@router.post("/login")
async def login(login_data: LoginRequest):  # Vulnerable to brute force!
    pass
```

### Pagination with fastapi-pagination

- **ALWAYS** paginate list endpoints
- Use `Page[T]` response model for paginated responses
- Set reasonable default and maximum page sizes
- Use `PaginationParams` dependency

```python
# ✅ CORRECT - Paginated list endpoint
from app.core.pagination import Page, PaginationParams

@router.get("/users", response_model=Page[UserSchema])
async def list_users(
    params: Annotated[PaginationParams, Depends(create_pagination_params)],
    db: DBSession,
) -> Page[User]:
    query = select(User).order_by(User.created_at.desc())
    return await paginate(query, params)

# Response:
# {
#   "items": [...],
#   "total": 100,
#   "page": 1,
#   "size": 50,
#   "pages": 2
# }

# ❌ WRONG - No pagination on list endpoint
@router.get("/users", response_model=list[UserSchema])
async def list_users(user_repo: UserRepo) -> list[User]:
    return await user_repo.get_multi()  # Could return thousands!
```

### Cache Configuration

```python
# Cache settings in .env
CACHE_ENABLED=True
CACHE_REDIS_HOST=localhost
CACHE_REDIS_PORT=6379
CACHE_REDIS_DB=0
CACHE_PREFIX=myapi:cache
CACHE_DEFAULT_TTL=300  # 5 minutes

# Different TTLs for different data
@cache(expire=60)    # 1 minute - frequently changing
@cache(expire=300)   # 5 minutes - moderate
@cache(expire=3600)  # 1 hour - rarely changing
```

### Rate Limit Configuration

```python
# Rate limiter settings in .env
LIMITER_ENABLED=True
LIMITER_REDIS_HOST=localhost
LIMITER_REDIS_PORT=6379
LIMITER_REDIS_DB=1
LIMITER_PREFIX=myapi:limiter

# Different limits for different operations
rate_limit(times=5, seconds=3600)    # Registration: 5 per hour
rate_limit(times=10, seconds=300)    # Login: 10 per 5 minutes
rate_limit(times=20, seconds=60)     # Read: 20 per minute
rate_limit(times=10, seconds=60)     # Write: 10 per minute
```

### Performance Best Practices

1. **Cache Read Operations**: Cache GET endpoints with appropriate TTL
2. **Invalidate on Write**: Clear cache when data changes
3. **Rate Limit All Endpoints**: Protect against abuse
4. **Paginate Lists**: Never return unbounded lists
5. **Use Redis**: For distributed caching and rate limiting
6. **Monitor Performance**: Track cache hit rates and rate limit violations

## Database Provider Switching

### Configuration
- Support both Supabase (development) and PostgreSQL (production)
- Use `DATABASE_PROVIDER` environment variable to switch
- Optimize connection pooling per provider
- Use `@lru_cache` for engine and session maker

```python
# ✅ CORRECT - Provider-aware configuration
class DatabaseSettings(BaseSettings):
    provider: Literal["supabase", "postgresql"] = "supabase"
    host: str
    port: int = 5432
    
    @computed_field
    @property
    def is_supabase(self) -> bool:
        return self.provider == "supabase"
```

### Connection Pooling
- Supabase: Smaller pool (3-5 connections)
- PostgreSQL: Larger pool (10-20 connections)
- Always enable `pool_pre_ping` for reliability

```python
# ✅ CORRECT - Provider-specific optimization
if settings.database.is_supabase:
    engine_kwargs["pool_size"] = min(settings.database.pool_size, 5)
    engine_kwargs["max_overflow"] = min(settings.database.max_overflow, 5)
```

### Environment Files
- `.env.development` - Supabase configuration
- `.env.production` - PostgreSQL configuration
- `.env.example` - Template with both options

### Migrations
- Use Alembic for database migrations
- Test migrations in development first
- Always backup before production migrations
- Support both providers in `alembic/env.py`

## Pydantic V2 Best Practices

### Use SecretStr for Sensitive Data

- **ALWAYS** use `SecretStr` for passwords, API keys, tokens
- **NEVER** use plain `str` for sensitive data
- Access with `.get_secret_value()` when needed

```python
# ✅ CORRECT
from pydantic import SecretStr

class SecuritySettings(BaseSettings):
    secret_key: SecretStr
    api_key: SecretStr

# Usage
secret = settings.secret_key.get_secret_value()

# ❌ WRONG
class SecuritySettings(BaseSettings):
    secret_key: str  # Will be exposed in logs!
```

### Use Computed Fields

- Use `@computed_field` for derived values
- Mark as `@property` for read-only access
- Include return type hint

```python
# ✅ CORRECT
from pydantic import computed_field

class DatabaseSettings(BaseSettings):
    host: str
    port: int
    
    @computed_field
    @property
    def url(self) -> PostgresDsn:
        return PostgresDsn(f"postgresql://{self.host}:{self.port}")

# ❌ WRONG - Don't store derived values
class DatabaseSettings(BaseSettings):
    host: str
    port: int
    url: str  # Should be computed!
```

### Use Model Validators

- Use `@model_validator(mode="after")` for cross-field validation
- Return `self` from validator
- Raise `ValueError` for validation errors

```python
# ✅ CORRECT
from pydantic import model_validator

class Settings(BaseSettings):
    debug: bool
    cors_origins: list[str]
    
    @model_validator(mode="after")
    def validate_settings(self) -> "Settings":
        if not self.debug and not self.cors_origins:
            raise ValueError("CORS origins required in production")
        return self

# ❌ WRONG - No cross-field validation
class Settings(BaseSettings):
    debug: bool
    cors_origins: list[str]  # No validation!
```

### Configure SettingsConfigDict Properly

- Enable `validate_default=True`
- Enable `validate_assignment=True`
- Enable `str_strip_whitespace=True`
- Enable `use_attribute_docstrings=True`

```python
# ✅ CORRECT
model_config = SettingsConfigDict(
    env_file=".env",
    env_file_encoding="utf-8",
    case_sensitive=False,
    env_nested_delimiter="__",
    str_strip_whitespace=True,
    validate_default=True,
    validate_assignment=True,
    use_attribute_docstrings=True,
    extra="ignore",
)

# ❌ WRONG - Missing important settings
model_config = SettingsConfigDict(
    env_file=".env",
)
```

### Use Semantic Types

- Use Pydantic's built-in semantic types
- Don't use plain types with manual validation

```python
# ✅ CORRECT
from pydantic import EmailStr, PositiveInt, AnyHttpUrl

class User(BaseModel):
    email: EmailStr
    age: PositiveInt
    website: AnyHttpUrl

# ❌ WRONG
class User(BaseModel):
    email: str  # Use EmailStr
    age: Annotated[int, Field(gt=0)]  # Use PositiveInt
    website: str  # Use AnyHttpUrl
```

## SQLAlchemy 2.0 Best Practices

### Use Mapped Columns with Full Configuration

- **ALWAYS** use `Mapped[T]` with `mapped_column()`
- Add `doc` parameter for documentation
- Add `sort_order` for important columns
- Add indexes strategically

```python
# ✅ CORRECT
from sqlalchemy.orm import Mapped, mapped_column

class User(Base):
    id: Mapped[int] = mapped_column(
        primary_key=True,
        index=True,
        autoincrement=True,
        sort_order=-100,
        doc="Primary key identifier",
    )
    
    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        index=True,
        nullable=False,
        doc="User email address (unique)",
    )

# ❌ WRONG - Legacy style
class User(Base):
    id = Column(Integer, primary_key=True)
    email = Column(String(255), unique=True)
```

### Add Strategic Indexes

- Index primary keys (automatic)
- Index foreign keys
- Index frequently filtered columns
- Index frequently sorted columns

```python
# ✅ CORRECT
class User(Base):
    email: Mapped[str] = mapped_column(String(255), index=True)  # Lookups
    is_active: Mapped[bool] = mapped_column(default=True, index=True)  # Filtering
    created_at: Mapped[datetime] = mapped_column(default=..., index=True)  # Sorting

# ❌ WRONG - No indexes
class User(Base):
    email: Mapped[str] = mapped_column(String(255))  # Slow lookups!
```

### Use TYPE_CHECKING for Relationships

- Import related models in `if TYPE_CHECKING` block
- Use string references in `Mapped[]`
- Prevents circular imports

```python
# ✅ CORRECT
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.session import Session

class User(Base):
    sessions: Mapped[list["Session"]] = relationship(...)

# ❌ WRONG - Circular import
from app.models.session import Session

class User(Base):
    sessions: Mapped[list[Session]] = relationship(...)
```

### Document Columns

- Add `doc` parameter to all columns
- Describe purpose and constraints
- Include format information

```python
# ✅ CORRECT
email: Mapped[str] = mapped_column(
    String(255),
    unique=True,
    doc="User email address (unique, max 255 chars)",
)

# ❌ WRONG - No documentation
email: Mapped[str] = mapped_column(String(255), unique=True)
```

## Exception Handling

### Local try/except for Business Logic

- Use `try/except` in endpoints for **specific, recoverable failures**
- Wrap unexpected errors in domain exceptions
- Always rollback database transactions on error
- Re-raise domain exceptions (let global handlers format them)

```python
# ✅ CORRECT - Local error handling
from app.core.exceptions import NotFoundException, DatabaseException

@router.get("/users/{user_id}")
async def get_user(user_id: int, user_repo: UserRepo) -> User:
    try:
        user = await user_repo.get(user_id)
    except Exception as e:
        raise DatabaseException(
            message="Failed to fetch user",
            details={"user_id": user_id, "error": str(e)},
        )
    
    if not user:
        raise NotFoundException(resource="User", details={"user_id": user_id})
    
    return user

# ❌ WRONG - Generic HTTPException
@router.get("/users/{user_id}")
async def get_user(user_id: int, user_repo: UserRepo) -> User:
    user = await user_repo.get(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Not found")  # Too generic!
    return user
```

### Global Exception Handlers

- Global handlers are configured in `app/main.py`
- Provide consistent error format across all endpoints
- Automatic logging with request context
- Never expose internal details to clients

```python
# Configured automatically
setup_exception_handlers(app)

# Handles:
# - AppException and all subclasses
# - RequestValidationError (Pydantic)
# - IntegrityError (SQLAlchemy)
# - OperationalError (SQLAlchemy)
# - Exception (catch-all)
```

### Custom Exception Classes

Use specific exception classes for different error types:

```python
# ✅ CORRECT - Specific exceptions
from app.core.exceptions import (
    NotFoundException,
    ConflictException,
    AuthenticationException,
    AuthorizationException,
    DatabaseException,
)

# Not found
raise NotFoundException(resource="User", details={"user_id": 123})

# Conflict (duplicate)
raise ConflictException(message="Email already exists", details={"email": email})

# Authentication failed
raise AuthenticationException(message="Invalid credentials")

# Authorization failed
raise AuthorizationException(message="Admin access required")

# Database error
raise DatabaseException(message="Query failed", details={"query": "..."})

# ❌ WRONG - Generic exceptions
raise HTTPException(status_code=404, detail="Not found")
raise Exception("Something went wrong")
```

### Error Response Format

All errors return consistent JSON:

```json
{
  "error": "not_found_error",
  "message": "User not found",
  "details": [
    {
      "type": "not_found_error",
      "message": "User not found",
      "field": null
    }
  ],
  "request_id": "abc-123"
}
```

### Exception Handling Pattern

```python
# Standard pattern for endpoints
@router.post("/endpoint")
async def endpoint(data: Data, repo: Repo, db: DBSession):
    try:
        # 1. Validate business rules
        if not await repo.check_exists(data.id):
            raise NotFoundException(resource="Resource")
        
        # 2. Check conflicts
        if await repo.get_by_name(data.name):
            raise ConflictException(message="Name already exists")
        
        # 3. Perform operation
        result = await repo.create(data)
        await db.commit()
        
        return result
    
    except (NotFoundException, ConflictException):
        # Re-raise domain exceptions
        raise
    except Exception as e:
        # Wrap unexpected errors
        await db.rollback()
        raise DatabaseException(
            message="Operation failed",
            details={"error": str(e)},
        )
```

### Best Practices

1. **Use specific exception classes** - Not generic HTTPException
2. **Include context in details** - Help with debugging
3. **Re-raise domain exceptions** - Let global handlers format
4. **Rollback on database errors** - Maintain consistency
5. **Don't expose internals** - Keep error messages generic
6. **Log with context** - Include request info
7. **Test error cases** - Verify error handling works

## Middleware Best Practices

### Middleware Order

- **ALWAYS** maintain proper middleware order for security
- First middleware = last to execute
- Last middleware = first to execute

```python
# ✅ CORRECT - Proper order
def setup_middleware(app: FastAPI, settings: Settings):
    app.add_middleware(RequestSizeLimitMiddleware)  # 1. Check size first
    app.add_middleware(TrustedHostMiddleware)       # 2. Validate host
    app.add_middleware(HTTPSRedirectMiddleware)     # 3. Force HTTPS
    app.add_middleware(CORSMiddleware)              # 4. Handle CORS
    app.add_middleware(SecurityHeadersMiddleware)   # 5. Add headers
    app.add_middleware(GZipMiddleware)              # 6. Compress
    app.add_middleware(RequestIDMiddleware)         # 7. Track requests
    app.add_middleware(LoggingMiddleware)           # 8. Log everything

# ❌ WRONG - Random order
app.add_middleware(LoggingMiddleware)
app.add_middleware(RequestSizeLimitMiddleware)  # Should be first!
```

### Custom Middleware

- Inherit from `BaseHTTPMiddleware` for simple middleware
- Use `__init__` for configuration
- Use `dispatch` method for request/response handling
- Always call `await call_next(request)`

```python
# ✅ CORRECT
class CustomMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp, *, config: str) -> None:
        super().__init__(app)
        self.config = config
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Pre-processing
        request.state.custom = self.config
        
        # Process request
        response = await call_next(request)
        
        # Post-processing
        response.headers["X-Custom"] = self.config
        
        return response

# ❌ WRONG - Missing await
async def dispatch(self, request: Request, call_next: Callable) -> Response:
    response = call_next(request)  # Missing await!
    return response
```

### Security Headers

- **ALWAYS** add OWASP security headers
- Use HSTS in production
- Customize CSP for your needs
- Never disable security headers

```python
# ✅ CORRECT
app.add_middleware(
    SecurityHeadersMiddleware,
    hsts_max_age=31536000,  # 1 year
)

# ❌ WRONG - No security headers
# Missing security middleware entirely
```

### Request Tracking

- **ALWAYS** use Request ID middleware
- Access via `request.state.request_id`
- Include in logs and errors
- Return in response headers

```python
# ✅ CORRECT
@router.get("/endpoint")
async def endpoint(request: Request):
    request_id = request.state.request_id
    logger.info(f"Processing {request_id}")
    return {"request_id": request_id}

# ❌ WRONG - No request tracking
@router.get("/endpoint")
async def endpoint():
    logger.info("Processing request")  # No correlation ID!
```

## Separation of Concerns

### Schemas Must Be in app/schemas/
- **NEVER** define Pydantic schemas in endpoints
- **ALWAYS** create schemas in `app/schemas/` directory
- Import schemas from `app.schemas` in endpoints

```python
# ❌ WRONG - Schema in endpoint
# app/api/v1/endpoints/auth.py
class LoginRequest(BaseModel):
    username: str
    password: str

# ✅ CORRECT - Schema in schemas directory
# app/schemas/auth.py
class LoginRequest(BaseModel):
    username: str
    password: str

# app/api/v1/endpoints/auth.py
from app.schemas.auth import LoginRequest
```

### No Business Logic in Endpoints
- **NEVER** put business logic in endpoints
- **ALWAYS** call service layer methods
- Endpoints should only handle HTTP concerns

```python
# ❌ WRONG - Business logic in endpoint
@router.post("/users")
async def create_user(user_in: UserCreate, user_repo: UserRepo):
    if await user_repo.get_by_email(user_in.email):  # Business logic!
        raise HTTPException(400, "Email exists")
    return await user_repo.create(user_in)

# ✅ CORRECT - Call service
@router.post("/users")
async def create_user(user_in: UserCreate, db: DBSession):
    user_service = UserService(db)
    return await user_service.create_user(user_in)
```

### No Business Logic in Repositories
- **NEVER** put business logic in repositories
- **ALWAYS** keep repositories for data access only
- Business logic belongs in services

```python
# ❌ WRONG - Business logic in repository
class UserRepository:
    async def create_user(self, user_in: UserCreate) -> User:
        if await self.get_by_email(user_in.email):  # Business logic!
            raise ValueError("Email exists")
        return await self.create(user_in)

# ✅ CORRECT - Pure data access
class UserRepository:
    async def get_by_email(self, email: str) -> User | None:
        result = await self.db.execute(...)
        return result.scalar_one_or_none()
```

## OpenAPI Response Models

### Use Standard Response Models
- **ALWAYS** use `get_common_responses()` for consistent error responses
- **ALWAYS** configure router with common responses
- **ALWAYS** add detailed OpenAPI documentation to endpoints

```python
# ✅ CORRECT - Router with common responses
from app.schemas.responses import get_common_responses

router = APIRouter(
    tags=["MyFeature"],
    responses=get_common_responses(401, 500),
)

# ✅ CORRECT - Endpoint with detailed OpenAPI docs
@router.get(
    "/endpoint",
    response_model=MySchema,
    summary="Short description",
    description="Detailed description of what this endpoint does.",
    response_description="What the response contains",
    operation_id="uniqueOperationId",
    responses={
        200: {
            "description": "Success case description",
            "content": {
                "application/json": {
                    "example": {
                        "id": 1,
                        "name": "Example"
                    }
                }
            }
        },
        **get_common_responses(401, 404, 500)
    }
)
async def my_endpoint():
    pass

# ❌ WRONG - No OpenAPI documentation
@router.get("/endpoint")
async def my_endpoint():
    pass
```

### Standard Error Response Format
- **ALWAYS** use `ErrorResponse` and `ErrorDetail` models
- Errors should include message, details, and request_id

```python
# ✅ CORRECT - Standard error format
{
    "message": "Validation Error",
    "details": [
        {
            "detail": "Field is required",
            "error_code": "VALUE_ERROR_MISSING",
            "field": "email"
        }
    ],
    "request_id": "550e8400-e29b-41d4-a716-446655440000"
}

# ❌ WRONG - Inconsistent error format
{
    "error": "Something went wrong"
}
```

## Testing Standards

### Use httpx for HTTP Testing
- **ALWAYS** use httpx AsyncClient for HTTP testing
- **NEVER** use FastAPI TestClient
- Use async/await for all test functions

```python
# ❌ WRONG - Using TestClient
from fastapi.testclient import TestClient

def test_endpoint():
    client = TestClient(app)
    response = client.get("/api/v1/users/")

# ✅ CORRECT - Using httpx
from httpx import AsyncClient

async def test_endpoint(client: AsyncClient):
    response = await client.get("/api/v1/users/")
```

### Test Organization
- **Unit tests** in `tests/unit/` - Test services, repositories in isolation
- **Integration tests** in `tests/integration/` - Test full HTTP → DB flow
- **Factories** in `tests/factories/` - Test data generation

### Test Naming
- Test files: `test_*.py`
- Test classes: `Test*`
- Test functions: `test_*`
- Use descriptive names: `test_login_with_invalid_password_returns_401`

### Test Structure (AAA Pattern)
```python
async def test_something(client, test_user):
    # Arrange - Set up test data
    user_data = {"email": "new@example.com"}
    
    # Act - Perform the action
    response = await client.post("/api/v1/users", json=user_data)
    
    # Assert - Verify the result
    assert response.status_code == 201
    assert response.json()["email"] == user_data["email"]
```

### Coverage Requirements
- Overall: 80%+
- Services: 90%+
- Repositories: 85%+
- Endpoints: 80%+

## Questions?

When in doubt:
1. Check existing code for patterns
2. Refer to this document
3. Follow FastAPI best practices
4. Follow SQLAlchemy 2.0 patterns
5. Follow Pydantic V2 patterns
6. Check `docs/ARCHITECTURE.md` for architecture patterns
7. Check `docs/SEPARATION_OF_CONCERNS.md` for layer responsibilities
8. Check `docs/TESTING.md` for testing best practices
9. Check `docs/DATABASE_SETUP.md` for database configuration
10. Check `docs/PYDANTIC_V2_ENHANCEMENTS.md` for advanced features
11. Check `docs/EXCEPTION_HANDLING.md` for error handling patterns
12. Check `docs/MIDDLEWARE_SECURITY.md` for middleware and security best practices
