# Environment Variables Guide

This document provides a comprehensive guide to all environment variables used in this application.

## Table of Contents

- [Application Configuration](#application-configuration)
- [Database Configuration](#database-configuration)
- [Supabase Configuration](#supabase-configuration)
- [Security Configuration](#security-configuration)
- [CORS Configuration](#cors-configuration)
- [Cache Configuration](#cache-configuration)
- [Rate Limiter Configuration](#rate-limiter-configuration)

---

## Application Configuration

### `APP_NAME`
- **Type**: String
- **Default**: `"Backend API"`
- **Description**: Application name displayed in API documentation and logs
- **Example**: `"My Awesome API"`

### `APP_VERSION`
- **Type**: String
- **Default**: `"1.0.0"`
- **Description**: Application version following semantic versioning
- **Example**: `"2.1.0"`

### `DEBUG`
- **Type**: Boolean
- **Default**: `False`
- **Description**: Enable debug mode for detailed error messages and SQL logging
- **Values**: `True` (development) or `False` (production)
- **⚠️ Warning**: Never set to `True` in production!

### `API_V1_PREFIX`
- **Type**: String
- **Default**: `"/api/v1"`
- **Description**: URL prefix for API version 1 endpoints
- **Example**: `"/api/v1"` → endpoints will be at `/api/v1/users`, etc.

---

## Database Configuration

### `DATABASE_PROVIDER`
- **Type**: String (Literal)
- **Required**: ✅ Yes
- **Default**: `"supabase"`
- **Values**: `"supabase"` or `"postgresql"`
- **Description**: Database provider type
  - `supabase`: Use Supabase hosted PostgreSQL (recommended for development)
  - `postgresql`: Use self-hosted PostgreSQL (recommended for production)

### `DATABASE_CONNECTION_MODE`
- **Type**: String (Literal)
- **Required**: No
- **Default**: `"transaction_pooler"`
- **Values**: `"direct"`, `"transaction_pooler"`, `"session_pooler"`
- **Description**: Connection mode for Supabase (ignored for PostgreSQL)
  - `transaction_pooler`: **Recommended**. Uses connection pooling, port 6543. Does not support PREPARE statements.
  - `session_pooler`: Uses connection pooling, port 5432. Supports all PostgreSQL features.
  - `direct`: Direct connection, port 5432. Requires IPv6 support.

**How to choose**:
- Use `transaction_pooler` for most applications (default)
- Use `session_pooler` if you need prepared statements or advisory locks
- Use `direct` only if you have IPv6 support and need direct database access

### `DATABASE_HOST`
- **Type**: String
- **Required**: ✅ Yes
- **Description**: Database server hostname or IP address

**For Supabase**:
- Transaction pooler: `aws-0-eu-west-3.pooler.supabase.com` (or your region)
- Session pooler: `aws-0-eu-west-3.pooler.supabase.com` (or your region)
- Direct: `db.xxxxx.supabase.co` (replace xxxxx with your project ref)

**How to get (Supabase)**:
1. Go to [Supabase Dashboard](https://supabase.com/dashboard)
2. Select your project
3. Go to **Settings** → **Database**
4. Scroll to **Connection string** section
5. Select the connection mode you want
6. Copy the host from the connection string

**For PostgreSQL**:
- Local: `localhost` or `127.0.0.1`
- Remote: Your server's IP or hostname

### `DATABASE_PORT`
- **Type**: Integer
- **Required**: No
- **Default**: `5432`
- **Description**: Database server port

**Port by connection mode**:
- Transaction pooler: `6543`
- Session pooler: `5432`
- Direct: `5432`
- PostgreSQL: `5432` (default)

### `DATABASE_USER`
- **Type**: String
- **Required**: ✅ Yes
- **Description**: Database username

**For Supabase**:
- Pooler connections: `postgres.your-project-ref` (e.g., `postgres.vglmnngcvcrdzvnaopde`)
- Direct connection: `postgres`

**How to get (Supabase)**:
1. Go to **Settings** → **Database**
2. Look at the **Connection string** section
3. The user is shown in the connection string

**For PostgreSQL**:
- Your database username (e.g., `myapp_user`)

### `DATABASE_PASSWORD`
- **Type**: String (Secret)
- **Required**: ✅ Yes
- **Description**: Database password
- **⚠️ Security**: Keep this secret! Never commit to version control.

**How to get (Supabase)**:
1. Go to [Supabase Dashboard](https://supabase.com/dashboard)
2. Select your project
3. Go to **Settings** → **Database**
4. Scroll to **Database Password** section
5. Click **Show** to reveal the password
6. If you forgot it, click **Reset Database Password**

**For PostgreSQL**:
- The password you set when creating the database user

### `DATABASE_NAME`
- **Type**: String
- **Required**: No
- **Default**: `"postgres"`
- **Description**: Database name to connect to

**For Supabase**: Always `postgres`
**For PostgreSQL**: Your database name (e.g., `myapp_db`)

### `DATABASE_POOL_SIZE`
- **Type**: Integer
- **Required**: No
- **Default**: `5`
- **Range**: 1-20
- **Description**: Number of database connections to maintain in the pool

**Recommendations**:
- Supabase: 3-5 (due to connection limits)
- PostgreSQL: 10-20 (depending on your server capacity)

### `DATABASE_MAX_OVERFLOW`
- **Type**: Integer
- **Required**: No
- **Default**: `10`
- **Range**: 0-50
- **Description**: Maximum number of connections that can be created beyond `pool_size`

### `DATABASE_POOL_PRE_PING`
- **Type**: Boolean
- **Required**: No
- **Default**: `True`
- **Description**: Test connections before using them
- **Recommendation**: Always `True` (especially for Supabase)

### `DATABASE_ECHO`
- **Type**: Boolean
- **Required**: No
- **Default**: `False`
- **Description**: Log all SQL queries to console
- **Usage**: Set to `True` for debugging, `False` in production

### `DATABASE_DISABLE_POOLER_WARNING`
- **Type**: Boolean
- **Required**: No
- **Default**: `False`
- **Description**: Disable the warning about PREPARE statements when using transaction pooler
- **Usage**: Set to `True` if you understand the limitation and want to suppress the warning

---

## Supabase Configuration

These are optional and only needed if you're using Supabase client features (Storage, Auth, etc.).

### `SUPABASE_URL`
- **Type**: String (URL)
- **Required**: No (only if using Supabase client features)
- **Description**: Your Supabase project URL

**How to get**:
1. Go to [Supabase Dashboard](https://supabase.com/dashboard)
2. Select your project
3. Go to **Settings** → **API**
4. Copy the **Project URL**

**Example**: `https://vglmnngcvcrdzvnaopde.supabase.co`

### `SUPABASE_ANON_KEY`
- **Type**: String (JWT)
- **Required**: No (only if using Supabase client features)
- **Description**: Supabase anonymous/public API key (safe to expose in client-side code)

**How to get**:
1. Go to **Settings** → **API**
2. Copy the **anon public** key from **Project API keys** section

### `SUPABASE_SERVICE_ROLE_KEY`
- **Type**: String (JWT)
- **Required**: No
- **Description**: Supabase service role key with admin privileges
- **⚠️ Security**: NEVER expose this in client-side code! Server-side only!

**How to get**:
1. Go to **Settings** → **API**
2. Copy the **service_role** key from **Project API keys** section

---

## Security Configuration

### `SECRET_KEY`
- **Type**: String (Secret)
- **Required**: ✅ Yes
- **Min Length**: 32 characters
- **Description**: Secret key for JWT token generation and encryption
- **⚠️ Security**: Must be unique and kept secret!

**How to generate**:
```bash
# Using OpenSSL
openssl rand -hex 32

# Using Python
python -c "import secrets; print(secrets.token_hex(32))"
```

### `ALGORITHM`
- **Type**: String
- **Required**: No
- **Default**: `"HS256"`
- **Description**: Algorithm for JWT encoding
- **Recommendation**: Use `"HS256"` (default)

### `ACCESS_TOKEN_EXPIRE_MINUTES`
- **Type**: Integer
- **Required**: No
- **Default**: `30`
- **Description**: JWT access token expiration time in minutes
- **Recommendations**:
  - Development: 30-60 minutes
  - Production: 15-30 minutes

---

## CORS Configuration

### `BACKEND_CORS_ORIGINS`
- **Type**: JSON Array or Comma-separated String
- **Required**: No
- **Default**: `[]`
- **Description**: List of allowed CORS origins (frontend URLs)

**Format**:
```bash
# JSON array (recommended)
BACKEND_CORS_ORIGINS=["http://localhost:3000","https://yourdomain.com"]

# Comma-separated
BACKEND_CORS_ORIGINS=http://localhost:3000,https://yourdomain.com
```

**Examples**:
- Development: `["http://localhost:3000","http://localhost:8000"]`
- Production: `["https://yourdomain.com","https://www.yourdomain.com"]`

---

## Cache Configuration

Requires Redis server.

### `CACHE_ENABLED`
- **Type**: Boolean
- **Required**: No
- **Default**: `False`
- **Description**: Enable caching with Redis
- **Recommendation**: `False` in development, `True` in production

### `CACHE_REDIS_HOST`
- **Type**: String
- **Required**: If caching is enabled
- **Default**: `"localhost"`
- **Description**: Redis server hostname

### `CACHE_REDIS_PORT`
- **Type**: Integer
- **Required**: No
- **Default**: `6379`
- **Description**: Redis server port

### `CACHE_REDIS_PASSWORD`
- **Type**: String (Secret)
- **Required**: If Redis requires authentication
- **Description**: Redis password (leave empty if no password)

### `CACHE_REDIS_DB`
- **Type**: Integer
- **Required**: No
- **Default**: `0`
- **Range**: 0-15
- **Description**: Redis database number

### `CACHE_PREFIX`
- **Type**: String
- **Required**: No
- **Default**: `"myapi:cache"`
- **Description**: Prefix for cache keys (prevents conflicts with other apps)

### `CACHE_DEFAULT_TTL`
- **Type**: Integer
- **Required**: No
- **Default**: `300`
- **Description**: Default cache TTL (Time To Live) in seconds
- **Example**: `300` = 5 minutes

---

## Rate Limiter Configuration

Requires Redis server.

### `LIMITER_ENABLED`
- **Type**: Boolean
- **Required**: No
- **Default**: `False`
- **Description**: Enable rate limiting with Redis
- **Recommendation**: `False` in development, `True` in production

### `LIMITER_REDIS_HOST`
- **Type**: String
- **Required**: If rate limiting is enabled
- **Default**: `"localhost"`
- **Description**: Redis server hostname

### `LIMITER_REDIS_PORT`
- **Type**: Integer
- **Required**: No
- **Default**: `6379`
- **Description**: Redis server port

### `LIMITER_REDIS_PASSWORD`
- **Type**: String (Secret)
- **Required**: If Redis requires authentication
- **Description**: Redis password (leave empty if no password)

### `LIMITER_REDIS_DB`
- **Type**: Integer
- **Required**: No
- **Default**: `1`
- **Range**: 0-15
- **Description**: Redis database number (use different from cache)

### `LIMITER_PREFIX`
- **Type**: String
- **Required**: No
- **Default**: `"myapi:limiter"`
- **Description**: Prefix for rate limiter keys

### `LIMITER_DEFAULT_TIMES`
- **Type**: Integer
- **Required**: No
- **Default**: `100`
- **Description**: Default number of requests allowed

### `LIMITER_DEFAULT_SECONDS`
- **Type**: Integer
- **Required**: No
- **Default**: `60`
- **Description**: Default time window in seconds
- **Example**: `LIMITER_DEFAULT_TIMES=100` and `LIMITER_DEFAULT_SECONDS=60` = 100 requests per minute

---

## Environment Files

### `.env`
- **Purpose**: Development environment
- **Usage**: Used by default when running locally
- **Git**: Should be in `.gitignore` (contains secrets)

### `.env.example`
- **Purpose**: Template for environment variables
- **Usage**: Copy to `.env` and fill in your values
- **Git**: Committed to repository (no secrets)

### `.env.production`
- **Purpose**: Production environment
- **Usage**: Used when deploying to production
- **Git**: Should be in `.gitignore` (contains secrets)

### `.env.test`
- **Purpose**: Testing environment
- **Usage**: Used when running tests
- **Git**: Can be committed (uses test values)

---

## Quick Start

1. **Copy the example file**:
   ```bash
   cp .env.example .env
   ```

2. **Fill in required values**:
   - `DATABASE_HOST`
   - `DATABASE_USER`
   - `DATABASE_PASSWORD`
   - `SECRET_KEY`

3. **For Supabase users**:
   - Set `DATABASE_PROVIDER=supabase`
   - Set `DATABASE_CONNECTION_MODE=transaction_pooler`
   - Get credentials from Supabase Dashboard

4. **For PostgreSQL users**:
   - Set `DATABASE_PROVIDER=postgresql`
   - Set `DATABASE_CONNECTION_MODE=direct`
   - Use your PostgreSQL credentials

5. **Test your configuration**:
   ```bash
   python test_config.py
   ```

---

## Troubleshooting

### "Field required" errors
- Make sure all required environment variables are set
- Check for typos in variable names
- Ensure `.env` file is in the project root

### Database connection fails
- Verify `DATABASE_HOST`, `DATABASE_PORT`, `DATABASE_USER`, `DATABASE_PASSWORD`
- For Supabase: Check connection mode matches the host and port
- For PostgreSQL: Ensure the database server is running

### IPv6 connection issues (Supabase direct mode)
- Use `transaction_pooler` or `session_pooler` instead
- These modes use IPv4 and work on all networks

### PREPARE statement errors (Supabase transaction pooler)
- This is expected behavior with transaction pooler
- Switch to `session_pooler` if you need PREPARE statements
- Or set `DATABASE_DISABLE_POOLER_WARNING=True` to suppress the warning

---

## Security Best Practices

1. **Never commit `.env` files** with real credentials
2. **Use strong, unique passwords** for production
3. **Rotate secrets regularly** (especially `SECRET_KEY`)
4. **Use different credentials** for each environment
5. **Enable rate limiting** in production
6. **Set `DEBUG=False`** in production
7. **Use HTTPS** for all production URLs
8. **Keep `SUPABASE_SERVICE_ROLE_KEY` secret** (server-side only)

---

## Need Help?

- Check the [Supabase Documentation](https://supabase.com/docs)
- Check the [FastAPI Documentation](https://fastapi.tiangolo.com/)
- Review the [PostgreSQL Documentation](https://www.postgresql.org/docs/)
