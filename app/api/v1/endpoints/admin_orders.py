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
    return templates.TemplateResponse(
        "admin/orders_list.html.jinja",
        {
            "request": request,
            "current_user": current_superuser,
            "orders": [],
            "active_page": "orders",
        }
    )
