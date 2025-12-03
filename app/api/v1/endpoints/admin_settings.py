"""Admin Settings Endpoints.

This module provides endpoints for admin user settings management
including username and password updates.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, Form, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_admin_context, get_current_active_superuser

# Shared admin utilities for consistent context (feature flags, etc.)
from app.core.config import get_settings
from app.core.exceptions import ConflictException
from app.database import get_db
from app.models.user import User
from app.schemas.user import UserUpdate
from app.services.user import UserService

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")
settings = get_settings()


@router.get("/settings", response_class=HTMLResponse)
async def settings_page(
    request: Request,
    current_user: Annotated[User, Depends(get_current_active_superuser)],
):
    """Render settings page with shared admin context."""
    return templates.TemplateResponse(
        request,
        "admin/settings.html.jinja",
        get_admin_context(request, current_user, active_page="settings"),
    )


@router.post("/settings/update-username", response_class=HTMLResponse)
async def update_username(
    request: Request,
    new_username: Annotated[str, Form()],
    current_user: Annotated[User, Depends(get_current_active_superuser)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Handle username update form submission."""
    try:
        # Validate that new username is different
        if new_username == current_user.username:
            return RedirectResponse(
                url=f"{settings.api_v1_prefix}/admin/settings?error=New username must be different from current username",
                status_code=status.HTTP_302_FOUND,
            )

        # Update username using service
        user_service = UserService(db)
        user_update = UserUpdate(username=new_username)
        await user_service.update_user(
            user_id=current_user.id,
            user_update=user_update,
            current_user=current_user,
        )

        return RedirectResponse(
            url=f"{settings.api_v1_prefix}/admin/settings?success=Username updated successfully",
            status_code=status.HTTP_302_FOUND,
        )
    except ConflictException as e:
        return RedirectResponse(
            url=f"{settings.api_v1_prefix}/admin/settings?error={e.message}",
            status_code=status.HTTP_302_FOUND,
        )
    except Exception as e:
        return RedirectResponse(
            url=f"{settings.api_v1_prefix}/admin/settings?error=Failed to update username: {str(e)}",
            status_code=status.HTTP_302_FOUND,
        )


@router.post("/settings/update-password", response_class=HTMLResponse)
async def update_password(
    request: Request,
    new_password: Annotated[str, Form()],
    confirm_password: Annotated[str, Form()],
    current_user: Annotated[User, Depends(get_current_active_superuser)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Handle password update form submission."""
    try:
        # Validate passwords match
        if new_password != confirm_password:
            return RedirectResponse(
                url=f"{settings.api_v1_prefix}/admin/settings?error=Passwords do not match",
                status_code=status.HTTP_302_FOUND,
            )

        # Validate password length
        if len(new_password) < 8:
            return RedirectResponse(
                url=f"{settings.api_v1_prefix}/admin/settings?error=Password must be at least 8 characters",
                status_code=status.HTTP_302_FOUND,
            )

        if len(new_password) > 100:
            return RedirectResponse(
                url=f"{settings.api_v1_prefix}/admin/settings?error=Password must be at most 100 characters",
                status_code=status.HTTP_302_FOUND,
            )

        # Update password using service
        user_service = UserService(db)
        user_update = UserUpdate(password=new_password)
        await user_service.update_user(
            user_id=current_user.id,
            user_update=user_update,
            current_user=current_user,
        )

        return RedirectResponse(
            url=f"{settings.api_v1_prefix}/admin/settings?success=Password updated successfully",
            status_code=status.HTTP_302_FOUND,
        )
    except Exception as e:
        return RedirectResponse(
            url=f"{settings.api_v1_prefix}/admin/settings?error=Failed to update password: {str(e)}",
            status_code=status.HTTP_302_FOUND,
        )
