"""API v1 router configuration.

This module configures the main API v1 router by including all endpoint
routers with their respective prefixes and tags.

Public Variables:
    api_router: Main API v1 router

Features:
    - Centralized router configuration
    - Endpoint organization by feature
    - Tag-based API documentation
"""

from fastapi import APIRouter

from app.api.v1.endpoints import auth, dashboard, export, metrics, users

__all__ = ["api_router"]

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth")
api_router.include_router(users.router, prefix="/users")
api_router.include_router(export.router, prefix="/export")
api_router.include_router(dashboard.router, prefix="/dashboard")
api_router.include_router(metrics.router, prefix="/metrics")
