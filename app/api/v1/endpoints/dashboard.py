"""Admin dashboard endpoints.

This module provides endpoints for the admin dashboard including
statistics, data entry forms, and real-time updates.

Public Variables:
    router: FastAPI router for dashboard endpoints

Features:
    - Dashboard statistics
    - Real-time data updates
    - Admin-only access
    - Data entry forms
"""

from datetime import datetime, timedelta

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from app.api.types import CurrentSuperuser, DBSession
from app.schemas.responses import get_common_responses
from app.services.user import UserService

__all__ = ["router"]

router = APIRouter(
    tags=["Dashboard"],
    responses=get_common_responses(401, 403, 500),
)

# Templates directory
templates = Jinja2Templates(directory="app/templates")


@router.get(
    "/",
    response_class=HTMLResponse,
    summary="Admin Dashboard",
    description="Main admin dashboard with statistics and data entry forms.",
    operation_id="getDashboard",
)
async def get_dashboard(
    request: Request,
    current_superuser: CurrentSuperuser,
    db: DBSession,
) -> HTMLResponse:
    """Render admin dashboard.

    Args:
        request (Request): FastAPI request object
        current_superuser (User): Current superuser
        db (AsyncSession): Database session

    Returns:
        HTMLResponse: Rendered dashboard HTML
    """
    user_service = UserService(db)
    
    # Get statistics
    all_users = await user_service.list_users()
    active_users = [u for u in all_users if u.is_active]
    
    # Calculate statistics
    stats = {
        "total_users": len(all_users),
        "active_users": len(active_users),
        "inactive_users": len(all_users) - len(active_users),
        "superusers": len([u for u in all_users if u.is_superuser]),
        "new_users_today": len([
            u for u in all_users 
            if u.created_at.date() == datetime.utcnow().date()
        ]),
        "new_users_week": len([
            u for u in all_users 
            if u.created_at >= datetime.utcnow() - timedelta(days=7)
        ]),
    }
    
    return templates.TemplateResponse(
        "dashboard/index.jinja",
        {
            "request": request,
            "user": current_superuser,
            "stats": stats,
            "users": all_users[:10],  # Latest 10 users
        },
    )


@router.get(
    "/data-entry",
    response_class=HTMLResponse,
    summary="Data Entry Form",
    description="Form for entering new data into the system.",
    operation_id="getDataEntryForm",
)
async def get_data_entry_form(
    request: Request,
    current_superuser: CurrentSuperuser,
) -> HTMLResponse:
    """Render data entry form.

    Args:
        request (Request): FastAPI request object
        current_superuser (User): Current superuser

    Returns:
        HTMLResponse: Rendered data entry form HTML
    """
    return templates.TemplateResponse(
        "dashboard/data_entry.jinja",
        {
            "request": request,
            "user": current_superuser,
        },
    )


@router.get(
    "/stats",
    summary="Dashboard Statistics",
    description="Get real-time dashboard statistics (JSON).",
    operation_id="getDashboardStats",
    responses={
        200: {
            "description": "Dashboard statistics",
            "content": {
                "application/json": {
                    "example": {
                        "total_users": 100,
                        "active_users": 95,
                        "inactive_users": 5,
                        "superusers": 2,
                        "new_users_today": 3,
                        "new_users_week": 15,
                    }
                }
            },
        },
        **get_common_responses(401, 403, 500),
    },
)
async def get_dashboard_stats(
    current_superuser: CurrentSuperuser,
    db: DBSession,
) -> dict:
    """Get dashboard statistics.

    Args:
        current_superuser (User): Current superuser
        db (AsyncSession): Database session

    Returns:
        dict: Dashboard statistics
    """
    user_service = UserService(db)
    all_users = await user_service.list_users()
    active_users = [u for u in all_users if u.is_active]
    
    return {
        "total_users": len(all_users),
        "active_users": len(active_users),
        "inactive_users": len(all_users) - len(active_users),
        "superusers": len([u for u in all_users if u.is_superuser]),
        "new_users_today": len([
            u for u in all_users 
            if u.created_at.date() == datetime.utcnow().date()
        ]),
        "new_users_week": len([
            u for u in all_users 
            if u.created_at >= datetime.utcnow() - timedelta(days=7)
        ]),
        "timestamp": datetime.utcnow().isoformat(),
    }
