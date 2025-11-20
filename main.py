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

from app.api.v1.router import api_router
from app.core.cache import close_cache, init_cache
from app.core.config import Settings, get_settings
from app.core.exceptions import setup_exception_handlers
from app.core.limiter import close_limiter, init_limiter
from app.core.middleware import setup_middleware
from app.database import close_db, init_db

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
    print("🚀 Starting application...")
    await init_db()
    await init_cache()
    await init_limiter()
    print("✓ Application started successfully")

    yield

    # Shutdown
    print("🛑 Shutting down application...")
    await close_db()
    await close_cache()
    await close_limiter()
    print("✓ Application shutdown complete")


app = FastAPI(
    title="Backend API",
    description="Professional backend API with PostgreSQL/Supabase",
    version="1.0.0",
    lifespan=lifespan,
)


@app.get("/")
async def root() -> dict[str, str]:
    """Root endpoint.

    Returns:
        dict[str, str]: Welcome message
    """
    return {"message": "Welcome to the API"}


@app.get("/health")
async def health_check(
    settings: Annotated[Settings, Depends(get_settings)],
) -> dict[str, str]:
    """Health check endpoint.

    Args:
        settings (Settings): Application settings

    Returns:
        dict[str, str]: Health status with app name, version, and database info
    """
    return {
        "status": "healthy",
        "app_name": settings.app_name,
        "version": settings.app_version,
        "database": {
            "provider": settings.database.provider,
            "host": settings.database.host,
            "connected": True,
        },
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
