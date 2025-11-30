"""Admin customers endpoints."""
from typing import Annotated

from fastapi import APIRouter, Depends, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from app.api.deps import get_current_active_superuser
from app.models.user import User

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

CurrentSuperuser = Annotated[User, Depends(get_current_active_superuser)]


@router.get("", response_class=HTMLResponse)
async def list_customers(
    request: Request,
    current_superuser: CurrentSuperuser,
):
    """List all customers (placeholder)."""
    return RedirectResponse(
        url="/api/v1/admin/dashboard?error=Customers module is currently under development",
        status_code=status.HTTP_302_FOUND
    )
