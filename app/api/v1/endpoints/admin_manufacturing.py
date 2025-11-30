"""Admin Manufacturing Types Management Endpoints.

This module provides endpoints for managing manufacturing types through
server-rendered templates.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, Form, Request, Response, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from app.api.types import (
    CurrentSuperuser,
    ManufacturingTypeRepo,
    OptionalStrForm,
    RequiredStrForm,
    RequiredIntForm,
)
from app.schemas.manufacturing_type import ManufacturingTypeCreate, ManufacturingTypeUpdate

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("", response_class=HTMLResponse)
async def list_manufacturing_types(
    request: Request,
    mfg_repo: ManufacturingTypeRepo,
    current_superuser: CurrentSuperuser,
):
    """List all manufacturing types."""
    manufacturing_types = await mfg_repo.get_multi(limit=1000)
    
    return templates.TemplateResponse(
        "admin/manufacturing_list.html.jinja",
        {
            "request": request,
            "current_user": current_superuser,
            "manufacturing_types": manufacturing_types,
            "active_page": "manufacturing",
        }
    )


@router.get("/create", response_class=HTMLResponse)
async def create_manufacturing_type_form(
    request: Request,
    current_superuser: CurrentSuperuser,
):
    """Render create manufacturing type form."""
    return templates.TemplateResponse(
        "admin/manufacturing_form.html.jinja",
        {
            "request": request,
            "current_user": current_superuser,
            "active_page": "manufacturing",
            "action": "Create",
        }
    )


@router.post("/create", response_class=HTMLResponse)
async def create_manufacturing_type(
    request: Request,
    mfg_repo: ManufacturingTypeRepo,
    current_superuser: CurrentSuperuser,
    name: Annotated[str, Form()],
    base_category: Annotated[str | None, Form()] = None,
    base_price: Annotated[float, Form()] = 0.0,
    base_weight: Annotated[float, Form()] = 0.0,
    description: Annotated[str | None, Form()] = None,
    image_url: Annotated[str | None, Form()] = None,
    is_active: Annotated[bool, Form()] = True,
):
    """Handle create manufacturing type submission."""
    try:
        from decimal import Decimal
        
        mfg_in = ManufacturingTypeCreate(
            name=name,
            base_category=base_category,
            base_price=Decimal(str(base_price)),
            base_weight=Decimal(str(base_weight)),
            description=description,
            image_url=image_url,
        )
        new_mfg = await mfg_repo.create(mfg_in)
        
        # Update is_active separately since it's not in the create schema
        if not is_active:
            new_mfg.is_active = False
            mfg_repo.db.add(new_mfg)
            await mfg_repo.db.commit()
        
        return RedirectResponse(
            url="/api/v1/admin/manufacturing-types?success=Manufacturing type created successfully",
            status_code=status.HTTP_302_FOUND
        )
    except Exception as e:
        return templates.TemplateResponse(
            "admin/manufacturing_form.html.jinja",
            {
                "request": request,
                "current_user": current_superuser,
                "active_page": "manufacturing",
                "action": "Create",
                "error": str(e),
                "form_data": {
                    "name": name,
                    "category": category,
                    "base_price": base_price,
                    "base_weight": base_weight,
                    "description": description,
                    "is_active": is_active,
                }
            },
            status_code=status.HTTP_400_BAD_REQUEST,
        )


@router.get("/{id}/edit", response_class=HTMLResponse)
async def edit_manufacturing_type_form(
    request: Request,
    id: int,
    mfg_repo: ManufacturingTypeRepo,
    current_superuser: CurrentSuperuser,
):
    """Render edit manufacturing type form."""
    mfg_type = await mfg_repo.get(id)
    if not mfg_type:
        return RedirectResponse(
            url="/api/v1/admin/manufacturing-types?error=Manufacturing type not found",
            status_code=status.HTTP_302_FOUND
        )
        
    return templates.TemplateResponse(
        "admin/manufacturing_form.html.jinja",
        {
            "request": request,
            "current_user": current_superuser,
            "active_page": "manufacturing",
            "action": "Edit",
            "mfg_type": mfg_type,
        }
    )


@router.post("/{id}/edit", response_class=HTMLResponse)
async def edit_manufacturing_type(
    request: Request,
    id: int,
    mfg_repo: ManufacturingTypeRepo,
    current_superuser: CurrentSuperuser,
    name: Annotated[str, Form()],
    base_category: Annotated[str, Form()],
    base_price: Annotated[float, Form()],
    base_weight: Annotated[float, Form()],
    description: Annotated[str | None, Form()] = None,
    is_active: Annotated[bool, Form()] = False,
):
    """Handle edit manufacturing type submission."""
    mfg_type = await mfg_repo.get(id)
    if not mfg_type:
        return RedirectResponse(
            url="/api/v1/admin/manufacturing-types?error=Manufacturing type not found",
            status_code=status.HTTP_302_FOUND
        )
        
    try:
        mfg_update = ManufacturingTypeUpdate(
            name=name,
            base_category=base_category,
            base_price=base_price,
            base_weight=base_weight,
            description=description,
            is_active=is_active,
        )
        await mfg_repo.update(mfg_type, mfg_update)
        
        return RedirectResponse(
            url="/api/v1/admin/manufacturing-types?success=Manufacturing type updated successfully",
            status_code=status.HTTP_302_FOUND
        )
    except Exception as e:
        return templates.TemplateResponse(
            "admin/manufacturing_form.html.jinja",
            {
                "request": request,
                "current_user": current_superuser,
                "active_page": "manufacturing",
                "action": "Edit",
                "error": str(e),
                "mfg_type": mfg_type, # Keep original object but maybe update fields?
                # Ideally we pass form_data back to pre-fill
            },
            status_code=status.HTTP_400_BAD_REQUEST,
        )


@router.post("/{id}/delete", response_class=HTMLResponse)
async def delete_manufacturing_type(
    request: Request,
    id: int,
    mfg_repo: ManufacturingTypeRepo,
    current_superuser: CurrentSuperuser,
):
    """Handle delete manufacturing type."""
    try:
        await mfg_repo.delete(id)
        return RedirectResponse(
            url="/api/v1/admin/manufacturing-types?success=Manufacturing type deleted successfully",
            status_code=status.HTTP_302_FOUND
        )
    except Exception as e:
        return RedirectResponse(
            url=f"/api/v1/admin/manufacturing-types?error={str(e)}",
            status_code=status.HTTP_302_FOUND
        )
