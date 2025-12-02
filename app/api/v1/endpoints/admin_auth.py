"""Admin Authentication Endpoints.

This module provides endpoints for admin authentication using cookies
and server-rendered templates.
"""

from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Request, Response, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from app.api.deps import get_admin_context
from app.api.types import CurrentSuperuser, DBSession, RequiredStrForm, UserRepo
from app.core.config import get_settings
from app.core.security import create_access_token
from app.repositories.session import SessionRepository
from app.schemas.responses import get_common_responses
from app.schemas.session import SessionCreate

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")
settings = get_settings()


@router.get(
    "/login",
    response_class=HTMLResponse,
    summary="Admin Login Page",
    description="Render the admin login page with authentication form",
    response_description="HTML page with login form",
    operation_id="adminLoginPage",
    responses={
        200: {
            "description": "Successfully rendered login page",
            "content": {"text/html": {"example": "<html>...</html>"}},
        },
    },
)
async def login_page(request: Request):
    """Render admin login page.

    Displays the login form for admin users to authenticate.
    No authentication required to access this page.

    Args:
        request: FastAPI request object

    Returns:
        HTMLResponse: Rendered login page template
    """
    return templates.TemplateResponse("admin/login.html.jinja", {"request": request})


@router.post(
    "/login",
    response_class=HTMLResponse,
    summary="Admin Login",
    description="Authenticate admin user and create session with cookie",
    response_description="Redirect to dashboard on success or re-render form with errors",
    operation_id="adminLogin",
    responses={
        302: {
            "description": "Redirect to dashboard on successful authentication",
        },
        400: {
            "description": "Bad request - inactive user account",
            "content": {"text/html": {"example": "<html>...</html>"}},
        },
        **get_common_responses(401, 403),
    },
)
async def login(
    request: Request,
    db: DBSession,
    user_repo: UserRepo,
    username: RequiredStrForm = ...,
    password: RequiredStrForm = ...,
):
    """Handle admin login form submission.

    Authenticates the user credentials, validates superuser status,
    creates a session, and sets an authentication cookie.

    Args:
        request: FastAPI request object
        db: Database session
        user_repo: User repository for authentication
        username: Username from form submission
        password: Password from form submission

    Returns:
        RedirectResponse: Redirect to dashboard on success
        HTMLResponse: Re-rendered login form with error message on failure

    Raises:
        Returns 401 for invalid credentials
        Returns 400 for inactive accounts
        Returns 403 for non-superuser accounts
    """
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
        url=f"{settings.api_v1_prefix}/admin/dashboard",
        status_code=status.HTTP_302_FOUND,
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


@router.get(
    "/logout",
    summary="Admin Logout",
    description="Log out admin user by clearing authentication cookie",
    response_description="Redirect to login page",
    operation_id="adminLogout",
    responses={
        302: {
            "description": "Redirect to login page after logout",
        },
    },
)
async def logout(response: Response):
    """Handle admin logout.

    Clears the authentication cookie and redirects to the login page.
    No authentication required to access this endpoint.

    Args:
        response: FastAPI response object

    Returns:
        RedirectResponse: Redirect to login page with cleared cookie
    """
    response = RedirectResponse(
        url=f"{settings.api_v1_prefix}/admin/login",
        status_code=status.HTTP_302_FOUND,
    )
    response.delete_cookie("access_token")
    return response


@router.get(
    "/dashboard",
    response_class=HTMLResponse,
    summary="Admin Dashboard",
    description="Render the main admin dashboard with navigation and overview",
    response_description="HTML page with admin dashboard",
    operation_id="adminDashboard",
    responses={
        200: {
            "description": "Successfully rendered dashboard",
            "content": {"text/html": {"example": "<html>...</html>"}},
        },
        **get_common_responses(401, 403, 500),
    },
)
async def dashboard(
    request: Request,
    current_user: CurrentSuperuser,
):
    """Render main admin dashboard.

    Displays the admin dashboard with navigation menu and overview.
    Requires superuser authentication.

    Args:
        request: FastAPI request object
        current_user: Current authenticated superuser

    Returns:
        HTMLResponse: Rendered dashboard template with admin context
    """
    return templates.TemplateResponse(
        "admin/index.html.jinja",
        get_admin_context(
            request,
            current_user,
            active_page="dashboard",
        ),
    )
