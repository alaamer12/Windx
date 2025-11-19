# Quick Start Guide

Get up and running in 5 minutes!

## 1. Install Dependencies

```bash
pip install -r requirements.txt
```

## 2. Choose Your Database

### Option A: Supabase (Recommended for Development)

1. Create account at [supabase.com](https://supabase.com)
2. Create new project
3. Copy connection details from Settings > Database

```bash
copy .env.development .env
```

Edit `.env`:
```env
DATABASE_PROVIDER=supabase
DATABASE_HOST=db.xxxxx.supabase.co
DATABASE_PASSWORD=your-supabase-password
```

### Option B: Local PostgreSQL

```bash
# Install PostgreSQL
# Windows: Download from postgresql.org
# Mac: brew install postgresql
# Linux: sudo apt install postgresql

# Create database
createdb myapi

copy .env.development .env
```

Edit `.env`:
```env
DATABASE_PROVIDER=postgresql
DATABASE_HOST=localhost
DATABASE_USER=postgres
DATABASE_PASSWORD=your-password
DATABASE_NAME=myapi
```

## 3. Initialize Database

```bash
# Create initial migration
alembic revision --autogenerate -m "Initial migration"

# Apply migration
alembic upgrade head
```

## 4. Run Application

```bash
uvicorn app.main:app --reload
```

## 5. Test It!

Open browser to:
- API Docs: http://localhost:8000/docs
- Health Check: http://localhost:8000/health

### Register a User

```bash
curl -X POST "http://localhost:8000/api/v1/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "username": "testuser",
    "password": "testpass123"
  }'
```

### Login

```bash
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "password": "testpass123"
  }'
```

## Switching Databases

### Development → Production

```bash
# 1. Backup development data
pg_dump -h db.xxxxx.supabase.co -U postgres -d postgres > backup.sql

# 2. Update .env
DATABASE_PROVIDER=postgresql
DATABASE_HOST=your-production-host.com

# 3. Restore data (optional)
psql -h your-production-host.com -U your-user -d your-db < backup.sql

# 4. Run migrations
alembic upgrade head

# 5. Restart application
uvicorn app.main:app --reload
```

## Common Commands

```bash
# Run with specific env file
uvicorn app.main:app --reload --env-file .env.development

# Create migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Rollback migration
alembic downgrade -1

# View migration history
alembic history

# Check current migration
alembic current
```

## Troubleshooting

### Connection Refused
- Check database is running
- Verify host and port in `.env`
- Check firewall rules

### Too Many Connections
- Reduce `DATABASE_POOL_SIZE` in `.env`
- Close other database connections

### Migration Errors
- Check model definitions in `app/models/`
- Verify database connection
- Review generated migration in `alembic/versions/`

## Next Steps

- Read [DATABASE_SETUP.md](docs/DATABASE_SETUP.md) for detailed configuration
- Read [ARCHITECTURE.md](ARCHITECTURE.md) for project structure
- Check [coding-standards.md](.kiro/steering/coding-standards.md) for development guidelines

## Need Help?

- Check health endpoint: http://localhost:8000/health
- View API docs: http://localhost:8000/docs
- Check logs for error messages
