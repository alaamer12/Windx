---
inclusion: always
---

# Project Coding Standards and Patterns

This document defines the coding standards, patterns, and best practices for this FastAPI backend project.

## Architecture Patterns

### Repository Pattern
- **ALWAYS** use repository pattern for database operations
- **NEVER** access SQLAlchemy models directly in endpoints
- Create custom repository methods for complex queries
- Inherit from `BaseRepository` for standard CRUD operations

```python
# ✅ CORRECT
class UserRepository(BaseRepository[User, UserCreate, UserUpdate]):
    async def get_by_email(self, email: str) -> User | None:
        result = await self.db.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()

# ❌ WRONG - Don't query directly in endpoints
@router.get("/users")
async def get_users(db: AsyncSession):
    result = await db.execute(select(User))  # Wrong!
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
- Use `HTTPException` for all errors
- Include descriptive error messages
- Use proper HTTP status codes
- Include `detail` parameter

```python
# ✅ CORRECT
raise HTTPException(
    status_code=status.HTTP_404_NOT_FOUND,
    detail="User not found",
)
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

from app.core.database import get_db
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

## Questions?

When in doubt:
1. Check existing code for patterns
2. Refer to this document
3. Follow FastAPI best practices
4. Follow SQLAlchemy 2.0 patterns
5. Follow Pydantic V2 patterns
6. Check `docs/DATABASE_SETUP.md` for database configuration
