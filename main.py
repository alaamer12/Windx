"""Main FastAPI application module.

This module initializes the FastAPI application with CORS middleware,
API routers, and health check endpoints.

Public Functions:
    root: Root endpoint
    health_check: Health check endpoint
    configure_cors: Configure CORS middleware

Features:
    - FastAPI application initialization
    - CORS middleware configuration
    - API v1 router integration
    - Health check endpoint
"""

from contextlib import asynccontextmanager
from typing import Annotated

from fastapi import Depends, FastAPI
from fastapi_pagination import add_pagination
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.router import api_router
from app.core.cache import close_cache, init_cache
from app.core.config import Settings, get_settings
from app.core.exceptions import setup_exception_handlers
from app.core.limiter import close_limiter, init_limiter
from app.core.middleware import setup_middleware
from app.database import close_db, get_db, init_db

__all__ = ["app", "root", "health_check", "lifespan"]


@asynccontextmanager
async def lifespan(application: FastAPI):
    """Application lifespan manager.

    Handles startup and shutdown events for the FastAPI application.
    Initializes database, cache, and rate limiter on startup.

    Args:
        application (FastAPI): FastAPI application instance

    Yields:
        None: Control back to FastAPI
    """
    # Startup
    print("[*] Starting application...")

    # Validate environment configuration
    try:
        settings = get_settings()
        print(f"[+] Configuration loaded: {settings.app_name} v{settings.app_version}")
        print(
            f"    Database: {settings.database.provider} @ {settings.database.host}:{settings.database.port}"
        )
        print(f"    Connection mode: {settings.database.connection_mode}")
    except Exception as e:
        print(f"[-] Configuration error: {e}")
        raise

    await init_db()
    await init_cache()
    await init_limiter()
    print("[+] Application started successfully")

    yield

    # Shutdown
    print("[*] Shutting down application...")
    await close_db()
    await close_cache()
    await close_limiter()
    print("[+] Application shutdown complete")


app = FastAPI(
    title="Backend API",
    description="Professional backend API with PostgreSQL/Supabase",
    version="1.0.0",
    lifespan=lifespan,
    swagger_ui_parameters={
        "persistAuthorization": True,
    },
)


@app.get("/")
async def root() -> dict[str, str]:
    """Root endpoint.

    Returns:
        dict[str, str]: Welcome message
    """
    return {"message": "Welcome to the API"}


@app.get(
    "/health",
    summary="Health Check",
    description="Comprehensive health check endpoint that verifies all system dependencies including database, cache, and rate limiter connectivity.",
    response_description="Health status with dependency checks",
    operation_id="healthCheck",
)
async def health_check(
    settings: Annotated[Settings, Depends(get_settings)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict[str, str | dict[str, str | bool | dict[str, str]]]:
    """Health check endpoint with dependency verification.

    Verifies connectivity to all critical system dependencies:
    - Database (PostgreSQL/Supabase)
    - Redis cache (if enabled)
    - Redis rate limiter (if enabled)

    Args:
        settings (Settings): Application settings
        db (AsyncSession): Database session

    Returns:
        dict: Health status with overall status and individual dependency checks

    Example Response:
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
    """
    from sqlalchemy import text

    overall_status = "healthy"
    checks: dict[str, dict[str, str]] = {}

    # Check database connectivity
    try:
        await db.execute(text("SELECT 1"))
        checks["database"] = {
            "status": "healthy",
            "provider": settings.database.provider,
        }
    except Exception as e:
        overall_status = "unhealthy"
        checks["database"] = {
            "status": "unhealthy",
            "provider": settings.database.provider,
            "error": str(e),
        }

    # Check Redis cache connectivity (if enabled)
    if settings.cache.enabled:
        redis_cache = None
        try:
            import redis.asyncio as aioredis

            # Create temporary Redis client for health check (don't use cached singleton)
            redis_cache = aioredis.from_url(
                str(settings.cache.redis_url),
                encoding="utf-8",
                decode_responses=True,
            )
            await redis_cache.ping()
            checks["cache"] = {"status": "healthy"}
        except Exception as e:
            overall_status = "unhealthy"
            checks["cache"] = {
                "status": "unhealthy",
                "error": str(e),
            }
        finally:
            if redis_cache:
                await redis_cache.close()

    # Check Redis rate limiter connectivity (if enabled)
    if settings.limiter.enabled:
        redis_limiter = None
        try:
            import redis.asyncio as aioredis

            # Create temporary Redis client for health check (don't use cached singleton)
            redis_limiter = aioredis.from_url(
                str(settings.limiter.redis_url),
                encoding="utf-8",
                decode_responses=True,
            )
            await redis_limiter.ping()
            checks["rate_limiter"] = {"status": "healthy"}
        except Exception as e:
            overall_status = "unhealthy"
            checks["rate_limiter"] = {
                "status": "unhealthy",
                "error": str(e),
            }
        finally:
            if redis_limiter:
                await redis_limiter.close()

    return {
        "status": overall_status,
        "app_name": settings.app_name,
        "version": settings.app_version,
        "checks": checks,
    }


# Get settings
settings = get_settings()

# Setup middleware (includes CORS, security headers, logging, etc.)
setup_middleware(app, settings)

# Setup exception handlers
setup_exception_handlers(app)

# Include API router
app.include_router(api_router, prefix=settings.api_v1_prefix)

# Add pagination support
add_pagination(app)
