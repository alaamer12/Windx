"""Admin Authentication Endpoints.

This module provides endpoints for admin authentication using cookies
and server-rendered templates.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, Form, Request, Response, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_active_superuser, get_admin_context
from app.core.config import get_settings
from app.core.security import create_access_token
from app.database import get_db
from app.models.user import User
from app.repositories.user import UserRepository

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")
settings = get_settings()


@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    """Render login page."""
    return templates.TemplateResponse("admin/login.html.jinja", {"request": request})


@router.post("/login", response_class=HTMLResponse)
async def login(
    request: Request,
    username: Annotated[str, Form()],
    password: Annotated[str, Form()],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Handle login form submission."""
    user_repo = UserRepository(db)
    user = await user_repo.authenticate(username=username, password=password)

    if not user:
        return templates.TemplateResponse(
            "admin/login.html.jinja",
            {"request": request, "error": "Invalid username or password"},
            status_code=status.HTTP_401_UNAUTHORIZED,
        )

    if not user.is_active:
        return templates.TemplateResponse(
            "admin/login.html.jinja",
            {"request": request, "error": "User account is inactive"},
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    if not user.is_superuser:
        return templates.TemplateResponse(
            "admin/login.html.jinja",
            {"request": request, "error": "Not enough permissions"},
            status_code=status.HTTP_403_FORBIDDEN,
        )

    # Create access token
    access_token = create_access_token(subject=user.id)

    # Create session record in database
    from datetime import UTC, datetime, timedelta

    from app.repositories.session import SessionRepository
    from app.schemas.session import SessionCreate

    session_repo = SessionRepository(db)
    session_in = SessionCreate(
        user_id=user.id,
        token=access_token,
        expires_at=datetime.now(UTC)
        + timedelta(minutes=settings.security.access_token_expire_minutes),
        user_agent=request.headers.get("user-agent", "Unknown"),
        ip_address=request.client.host if request.client else "Unknown",
    )
    await session_repo.create(session_in)
    await db.commit()

    # Create redirect response
    redirect_response = RedirectResponse(
        url=f"{settings.api_v1_prefix}/admin/dashboard", status_code=status.HTTP_302_FOUND
    )

    # Set cookie
    redirect_response.set_cookie(
        key="access_token",
        value=f"Bearer {access_token}",
        httponly=True,
        max_age=settings.security.access_token_expire_minutes * 60,
        expires=settings.security.access_token_expire_minutes * 60,
        samesite="lax",
        secure=False,  # Set to True in production with HTTPS
    )

    return redirect_response


@router.get("/logout")
async def logout(response: Response):
    """Handle logout."""
    response = RedirectResponse(
        url=f"{settings.api_v1_prefix}/admin/login", status_code=status.HTTP_302_FOUND
    )
    response.delete_cookie("access_token")
    return response


@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard(
    request: Request,
    current_user: Annotated[User, Depends(get_current_active_superuser)],
):
    """Render main dashboard."""
    return templates.TemplateResponse(
        "admin/index.html.jinja",
        get_admin_context(
            request,
            current_user,
            active_page="dashboard",
        ),
    )
