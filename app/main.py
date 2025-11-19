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

from typing import Annotated

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router
from app.core.config import Settings, get_settings

__all__ = ["app", "root", "health_check", "configure_cors"]

app = FastAPI(
    title="Backend API",
    description="Professional backend API with PostgreSQL/Supabase",
    version="1.0.0",
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
        dict[str, str]: Health status with app name and version
    """
    return {
        "status": "healthy",
        "app_name": settings.app_name,
        "version": settings.app_version,
    }


def configure_cors(application: FastAPI, settings: Settings) -> None:
    """Configure CORS middleware.

    Args:
        application (FastAPI): FastAPI application instance
        settings (Settings): Application settings
    """
    if settings.backend_cors_origins:
        application.add_middleware(
            CORSMiddleware,
            allow_origins=[str(origin) for origin in settings.backend_cors_origins],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )


# Configure CORS
settings = get_settings()
configure_cors(app, settings)

# Include API router
app.include_router(api_router, prefix=settings.api_v1_prefix)
