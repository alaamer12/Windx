# Backend API Architecture

## Overview

Professional backend API-first architecture using FastAPI, PostgreSQL (Supabase), and repository pattern.

## Project Structure

```
app/
├── __init__.py              # Main package with Google-style docstring
├── main.py                  # FastAPI application entry point
├── core/                    # Core functionality
│   ├── __init__.py
│   ├── config.py           # Settings with lru_cache, composed Pydantic models
│   ├── database.py         # Database connection, session management
│   └── security.py         # Password hashing, JWT tokens
├── models/                  # SQLAlchemy ORM models
│   ├── __init__.py
│   ├── user.py             # User model with Mapped columns
│   └── session.py          # Session model with Mapped columns
├── schemas/                 # Pydantic schemas (composed)
│   ├── __init__.py
│   ├── user.py             # User schemas with semantic types
│   └── session.py          # Session schemas
├── repositories/            # Repository pattern
│   ├── __init__.py
│   ├── base.py             # Generic base repository
│   ├── user.py             # User repository
│   └── session.py          # Session repository
└── api/                     # API layer
    ├── __init__.py
    ├── deps.py             # Dependency injection
    └── v1/
        ├── __init__.py
        ├── router.py       # API router
        └── endpoints/
            ├── __init__.py
            ├── auth.py     # Authentication endpoints
            └── users.py    # User management endpoints
```

## Key Features

### ✅ Repository Pattern
- Clean separation of data access logic
- Generic base repository with CRUD operations
- Type-safe async operations

### ✅ Full Type Hinting
- Using `Annotated` with FastAPI, SQLAlchemy, Pydantic
- All functions, methods, and classes fully typed
- Type parameters in docstrings

### ✅ Pydantic Semantic Types
- `PositiveInt` instead of `int` with manual validation
- `EmailStr` for email validation
- Custom field validators

### ✅ Composed Pydantic Models
- Separate Base/Create/Update/InDB schemas
- No monolithic classes
- Reusable schema composition

### ✅ SQLAlchemy Mapped Columns
- Modern SQLAlchemy 2.0 style
- Type-safe column definitions
- Relationship management

### ✅ Google-style Docstrings
- Module docstrings with description, public classes, public functions, features
- Function/method docstrings with Args, Returns, Raises
- Class docstrings with Attributes
- Type information in docstrings

### ✅ Settings with lru_cache
- `get_settings()` cached globally
- Composed settings (DatabaseSettings, SecuritySettings)
- Environment variable loading

### ✅ __all__ Variables
- Every module defines `__all__`
- Explicit public API

### ✅ Supabase PostgreSQL
- Async PostgreSQL with asyncpg
- Connection pooling
- Session management

### ✅ User & Session Models
- Complete auth system foundation
- JWT token management
- Session tracking

## API Endpoints

### Authentication (`/api/v1/auth`)
- `POST /register` - Register new user
- `POST /login` - Login and get JWT token
- `POST /logout` - Logout (deactivate session)
- `GET /me` - Get current user info

### Users (`/api/v1/users`)
- `GET /` - List all users (superuser only)
- `GET /{user_id}` - Get user by ID
- `PATCH /{user_id}` - Update user
- `DELETE /{user_id}` - Delete user (superuser only)

## Setup Instructions

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Configure environment:
```bash
copy .env.example .env
# Edit .env with your Supabase credentials
```

3. Run the application:
```bash
uvicorn app.main:app --reload
```

4. Access API documentation:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Code Standards

- **Docstrings**: Google style for all modules, classes, functions, methods
- **Type Hints**: Full type hinting with `Annotated` types
- **Async/Await**: All database operations are async
- **Repository Pattern**: Data access through repositories only
- **Dependency Injection**: FastAPI dependencies for auth and DB
- **Error Handling**: HTTPException with proper status codes
- **Security**: Bcrypt password hashing, JWT tokens
