# Database Setup Guide

This guide explains how to set up and switch between Supabase (development) and PostgreSQL (production) databases.

## Overview

The application supports two database providers:
- **Supabase**: Fast setup for development with managed PostgreSQL
- **PostgreSQL**: Self-hosted or managed PostgreSQL for production

Both use the same PostgreSQL implementation, so switching is seamless.

## Architecture

### Connection Management
- **Engine**: Single cached instance per application lifecycle
- **Connection Pool**: Optimized per provider (smaller for Supabase, larger for production)
- **Session Management**: Automatic commit/rollback with FastAPI dependencies
- **Health Checks**: Pre-ping enabled to detect stale connections

### Configuration
All database settings are in `.env` files with provider-specific optimizations:

```python
# Supabase (Development)
DATABASE_PROVIDER=supabase
DATABASE_POOL_SIZE=3
DATABASE_MAX_OVERFLOW=5

# PostgreSQL (Production)
DATABASE_PROVIDER=postgresql
DATABASE_POOL_SIZE=10
DATABASE_MAX_OVERFLOW=20
```

## Setup Instructions

### 1. Supabase (Development)

#### Create Supabase Project
1. Go to [supabase.com](https://supabase.com)
2. Create a new project
3. Wait for database provisioning
4. Get connection details from Settings > Database

#### Configure Environment
```bash
# Copy development template
copy .env.development .env

# Edit .env with your Supabase credentials
DATABASE_PROVIDER=supabase
DATABASE_HOST=db.xxxxx.supabase.co
DATABASE_PORT=5432
DATABASE_USER=postgres
DATABASE_PASSWORD=your-supabase-password
DATABASE_NAME=postgres
```

#### Connection String Format
```
postgresql+asyncpg://postgres:[PASSWORD]@db.[PROJECT-REF].supabase.co:5432/postgres
```

#### Supabase Optimizations
- Smaller connection pool (3-5 connections)
- Pre-ping enabled for connection health
- Automatic reconnection on connection loss

### 2. PostgreSQL (Production)

#### Setup Options

**Option A: Managed PostgreSQL**
- AWS RDS
- Google Cloud SQL
- Azure Database for PostgreSQL
- DigitalOcean Managed Databases

**Option B: Self-Hosted**
- Docker container
- VM installation
- Kubernetes deployment

#### Configure Environment
```bash
# Copy production template
copy .env.production .env

# Edit .env with your PostgreSQL credentials
DATABASE_PROVIDER=postgresql
DATABASE_HOST=your-db-host.com
DATABASE_PORT=5432
DATABASE_USER=your_db_user
DATABASE_PASSWORD=your_secure_password
DATABASE_NAME=your_database
```

#### Connection String Format
```
postgresql+asyncpg://[USER]:[PASSWORD]@[HOST]:[PORT]/[DATABASE]
```

#### Production Optimizations
- Larger connection pool (10-20 connections)
- Connection pooling with overflow
- Pre-ping for reliability

## Switching Between Databases

### Method 1: Environment Files (Recommended)

```bash
# Development
uvicorn app.main:app --reload --env-file .env.development

# Production
uvicorn app.main:app --host 0.0.0.0 --port 8000 --env-file .env.production
```

### Method 2: Environment Variable

```bash
# Windows
set DATABASE_PROVIDER=supabase
uvicorn app.main:app --reload

set DATABASE_PROVIDER=postgresql
uvicorn app.main:app --reload

# Linux/Mac
export DATABASE_PROVIDER=supabase
uvicorn app.main:app --reload

export DATABASE_PROVIDER=postgresql
uvicorn app.main:app --reload
```

### Method 3: Edit .env File

Simply change the `DATABASE_PROVIDER` value in your `.env` file:

```env
# For Supabase
DATABASE_PROVIDER=supabase

# For PostgreSQL
DATABASE_PROVIDER=postgresql
```

## Database Migrations

### Initial Setup

```bash
# 1. Initialize database connection
python scripts/init_db.py

# 2. Create initial migration
alembic revision --autogenerate -m "Initial migration"

# 3. Apply migration
alembic upgrade head
```

### Development Workflow

```bash
# 1. Make changes to models in app/models/

# 2. Create migration
alembic revision --autogenerate -m "Add new field to User"

# 3. Review generated migration in alembic/versions/

# 4. Apply migration
alembic upgrade head
```

### Production Deployment

```bash
# 1. Test migrations in development first
alembic upgrade head

# 2. Backup production database
pg_dump -h your-host -U your-user -d your-db > backup.sql

# 3. Apply migrations to production
# Set production environment
export DATABASE_PROVIDER=postgresql
alembic upgrade head

# 4. Verify application
curl http://your-domain/health
```

### Rollback Migrations

```bash
# Rollback one migration
alembic downgrade -1

# Rollback to specific revision
alembic downgrade <revision_id>

# Rollback all migrations
alembic downgrade base
```

## Connection Pool Configuration

### Supabase Limits
- Free tier: 60 connections max
- Pro tier: 200 connections max
- Recommended pool size: 3-5 per instance

### PostgreSQL Limits
- Default: 100 connections
- Recommended pool size: 10-20 per instance
- Formula: `(max_connections - superuser_reserved) / num_instances`

### Configuration Parameters

```env
# Connection pool size (active connections)
DATABASE_POOL_SIZE=5

# Additional connections when pool is full
DATABASE_MAX_OVERFLOW=10

# Test connections before use
DATABASE_POOL_PRE_PING=True

# Log SQL queries (development only)
DATABASE_ECHO=True
```

## Monitoring and Troubleshooting

### Health Check Endpoint

```bash
curl http://localhost:8000/health
```

Response:
```json
{
  "status": "healthy",
  "app_name": "My API",
  "version": "1.0.0",
  "database": {
    "provider": "supabase",
    "host": "db.xxxxx.supabase.co",
    "connected": true
  }
}
```

### Common Issues

#### Connection Refused
```
sqlalchemy.exc.OperationalError: connection refused
```

**Solutions:**
- Check database host and port
- Verify firewall rules
- Ensure database is running
- Check credentials

#### Too Many Connections
```
FATAL: remaining connection slots are reserved
```

**Solutions:**
- Reduce `DATABASE_POOL_SIZE`
- Reduce `DATABASE_MAX_OVERFLOW`
- Close idle connections
- Increase database max_connections

#### Connection Timeout
```
asyncpg.exceptions.ConnectionDoesNotExistError
```

**Solutions:**
- Enable `DATABASE_POOL_PRE_PING=True`
- Check network connectivity
- Verify database is accessible
- Check connection string

### Logging

Enable SQL query logging for debugging:

```env
# Development
DATABASE_ECHO=True
DEBUG=True

# Production
DATABASE_ECHO=False
DEBUG=False
```

## Security Best Practices

### Development
- Use separate Supabase project for development
- Don't commit `.env` files
- Use weak passwords (they're not production)
- Enable query logging for debugging

### Production
- Use strong, generated passwords
- Enable SSL/TLS connections
- Restrict database access by IP
- Use connection pooling
- Monitor connection usage
- Regular backups
- Rotate credentials periodically

### Environment Variables

```env
# ❌ NEVER commit these
DATABASE_PASSWORD=actual-password
SECRET_KEY=actual-secret-key

# ✅ Use placeholders in .env.example
DATABASE_PASSWORD=your-password-here
SECRET_KEY=your-secret-key-here
```

## Performance Optimization

### Supabase
- Use connection pooling (built-in)
- Enable pre-ping for reliability
- Keep pool size small (3-5)
- Use read replicas for scaling

### PostgreSQL
- Tune `shared_buffers` and `work_mem`
- Enable query caching
- Use connection pooling (PgBouncer)
- Add indexes on frequently queried columns
- Monitor slow queries

### Application Level
- Use `select()` for queries (not legacy API)
- Use `joinedload()` for eager loading
- Implement pagination
- Cache frequently accessed data
- Use database indexes

## Testing

### Test Database Connection

```python
# scripts/test_connection.py
import asyncio
from app.database import init_db

async def test():
    try:
        await init_db()
        print("✓ Connection successful")
    except Exception as e:
        print(f"❌ Connection failed: {e}")

asyncio.run(test())
```

### Run Tests

```bash
# Test with development database
python scripts/test_connection.py

# Test with production database
export DATABASE_PROVIDER=postgresql
python scripts/test_connection.py
```

## Backup and Recovery

### Backup Supabase

```bash
# Using Supabase CLI
supabase db dump -f backup.sql

# Using pg_dump
pg_dump -h db.xxxxx.supabase.co -U postgres -d postgres > backup.sql
```

### Backup PostgreSQL

```bash
# Full backup
pg_dump -h your-host -U your-user -d your-db > backup.sql

# Compressed backup
pg_dump -h your-host -U your-user -d your-db | gzip > backup.sql.gz

# Schema only
pg_dump -h your-host -U your-user -d your-db --schema-only > schema.sql
```

### Restore Database

```bash
# Restore from backup
psql -h your-host -U your-user -d your-db < backup.sql

# Restore compressed backup
gunzip -c backup.sql.gz | psql -h your-host -U your-user -d your-db
```

## Migration Between Providers

### From Supabase to PostgreSQL

```bash
# 1. Backup Supabase database
pg_dump -h db.xxxxx.supabase.co -U postgres -d postgres > supabase_backup.sql

# 2. Create production database
createdb -h your-prod-host -U your-user your-database

# 3. Restore to production
psql -h your-prod-host -U your-user -d your-database < supabase_backup.sql

# 4. Update .env to use production database
DATABASE_PROVIDER=postgresql
DATABASE_HOST=your-prod-host

# 5. Test connection
python scripts/test_connection.py

# 6. Deploy application
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### From PostgreSQL to Supabase

```bash
# 1. Backup production database
pg_dump -h your-prod-host -U your-user -d your-db > prod_backup.sql

# 2. Restore to Supabase
psql -h db.xxxxx.supabase.co -U postgres -d postgres < prod_backup.sql

# 3. Update .env to use Supabase
DATABASE_PROVIDER=supabase
DATABASE_HOST=db.xxxxx.supabase.co

# 4. Test connection
python scripts/test_connection.py
```

## Conclusion

The application is designed to work seamlessly with both Supabase and PostgreSQL. Simply update your environment configuration and restart the application to switch between providers.

For questions or issues, refer to:
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/)
- [Supabase Documentation](https://supabase.com/docs)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
