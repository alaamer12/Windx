# Docker Setup Guide

Run PostgreSQL locally using Docker for development without installing PostgreSQL.

## Prerequisites

- Docker Desktop installed
- Docker Compose installed (included with Docker Desktop)

## Quick Start

### 1. Start PostgreSQL

```bash
docker-compose up -d postgres
```

This starts:
- PostgreSQL 16 on port 5432
- Database: `myapi`
- User: `postgres`
- Password: `postgres`

### 2. Configure Application

```bash
copy .env.local .env
```

The `.env.local` file is already configured for Docker PostgreSQL.

### 3. Initialize Database

```bash
# Create initial migration
alembic revision --autogenerate -m "Initial migration"

# Apply migration
alembic upgrade head
```

### 4. Run Application

```bash
uvicorn app.main:app --reload
```

## Optional: PgAdmin

PgAdmin provides a web UI for database management.

### Start PgAdmin

```bash
docker-compose --profile tools up -d pgadmin
```

### Access PgAdmin

1. Open http://localhost:5050
2. Login:
   - Email: `admin@example.com`
   - Password: `admin`

3. Add Server:
   - Name: `Local PostgreSQL`
   - Host: `postgres` (or `host.docker.internal` on Windows/Mac)
   - Port: `5432`
   - Database: `myapi`
   - Username: `postgres`
   - Password: `postgres`

## Docker Commands

### Start Services

```bash
# Start PostgreSQL only
docker-compose up -d postgres

# Start PostgreSQL + PgAdmin
docker-compose --profile tools up -d
```

### Stop Services

```bash
# Stop all services
docker-compose down

# Stop and remove volumes (deletes data)
docker-compose down -v
```

### View Logs

```bash
# View PostgreSQL logs
docker-compose logs -f postgres

# View all logs
docker-compose logs -f
```

### Database Shell

```bash
# Connect to PostgreSQL
docker-compose exec postgres psql -U postgres -d myapi

# Run SQL commands
docker-compose exec postgres psql -U postgres -d myapi -c "SELECT * FROM users;"
```

## Backup and Restore

### Backup Database

```bash
# Backup to file
docker-compose exec postgres pg_dump -U postgres myapi > backup.sql

# Backup with compression
docker-compose exec postgres pg_dump -U postgres myapi | gzip > backup.sql.gz
```

### Restore Database

```bash
# Restore from file
docker-compose exec -T postgres psql -U postgres myapi < backup.sql

# Restore from compressed file
gunzip -c backup.sql.gz | docker-compose exec -T postgres psql -U postgres myapi
```

## Troubleshooting

### Port Already in Use

If port 5432 is already in use:

```yaml
# Edit docker-compose.yml
services:
  postgres:
    ports:
      - "5433:5432"  # Use different host port
```

Then update `.env`:
```env
DATABASE_PORT=5433
```

### Connection Refused

```bash
# Check if container is running
docker-compose ps

# Check container logs
docker-compose logs postgres

# Restart container
docker-compose restart postgres
```

### Reset Database

```bash
# Stop and remove volumes
docker-compose down -v

# Start fresh
docker-compose up -d postgres

# Re-run migrations
alembic upgrade head
```

## Production Deployment

For production, use managed PostgreSQL services:
- AWS RDS
- Google Cloud SQL
- Azure Database for PostgreSQL
- DigitalOcean Managed Databases

Docker is recommended for development only.

## Environment Comparison

| Environment | Provider | Use Case |
|------------|----------|----------|
| Local Docker | PostgreSQL | Local development without PostgreSQL installation |
| Supabase | PostgreSQL | Fast cloud development setup |
| Production | PostgreSQL | Production deployment |

## Next Steps

- Read [DATABASE_SETUP.md](DATABASE_SETUP.md) for detailed configuration
- Read [QUICK_START.md](../QUICK_START.md) for application setup
- Check [ARCHITECTURE.md](../ARCHITECTURE.md) for project structure
