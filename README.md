# Backend API Project

Professional backend API-first architecture using FastAPI, PostgreSQL (Supabase), and repository pattern.

## Features

- ✅ **Dual Database Support**: Seamlessly switch between Supabase (development) and PostgreSQL (production)
- ✅ **Repository Pattern**: Clean data access layer
- ✅ **Full Type Hints**: Type-safe with Annotated types
- ✅ **JWT Authentication**: Secure token-based auth
- ✅ **Connection Pooling**: Optimized for each database provider
- ✅ **Auto Migrations**: Alembic database migrations
- ✅ **API Versioning**: `/api/v1/` prefix for future compatibility

## Setup

### 1. Create Virtual Environment
```bash
python -m venv .venv
.venv\Scripts\activate  # Windows
source .venv/bin/activate  # Linux/Mac
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Configure Environment

#### Development (Supabase)
```bash
copy .env.development .env
# Edit .env with your Supabase credentials
```

#### Production (PostgreSQL)
```bash
copy .env.production .env
# Edit .env with your production database credentials
```

### 4. Run the Application

#### Development
```bash
uvicorn app.main:app --reload --env-file .env.development
```

#### Production
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --env-file .env.production
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
