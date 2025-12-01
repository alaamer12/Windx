"""Admin orders endpoints."""

from typing import Annotated

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from app.api.deps import get_current_active_superuser
from app.models.user import User

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

CurrentSuperuser = Annotated[User, Depends(get_current_active_superuser)]


@router.get("", response_class=HTMLResponse)
async def list_orders(
    request: Request,
    current_superuser: CurrentSuperuser,
):
    """List all orders (placeholder)."""
    from fastapi import status
    from fastapi.responses import RedirectResponse

    return RedirectResponse(
        url="/api/v1/admin/dashboard?error=Orders module is currently under development",
        status_code=status.HTTP_302_FOUND,
    )
