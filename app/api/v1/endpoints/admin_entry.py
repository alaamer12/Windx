"""Admin Entry Page management endpoints.

This module provides admin-only endpoints for the Entry Page system including
profile data entry, schema generation, and preview functionality within the admin interface.

Public Variables:
    router: FastAPI router for admin entry page endpoints

Features:
    - Profile form schema generation (admin interface)
    - Profile data saving and loading (admin interface)
    - Real-time preview generation (admin interface)
    - Conditional field visibility evaluation (admin interface)
    - HTML page rendering for admin entry pages
    - Superuser authentication and authorization
    - Comprehensive error handling
"""

from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Query, Request, status
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import PositiveInt

from app.api.deps import get_admin_context
from app.api.types import CurrentSuperuser, DBSession
from app.schemas.configuration import Configuration
from app.schemas.entry import ProfileEntryData, ProfilePreviewData, ProfileSchema
from app.schemas.responses import get_common_responses

__all__ = ["router"]

router = APIRouter(
    tags=["Admin Entry"],
    responses=get_common_responses(401, 403, 500),
)

templates = Jinja2Templates(directory="app/templates")


@router.get(
    "/profile/schema/{manufacturing_type_id}",
    response_model=ProfileSchema,
    summary="Get Profile Form Schema (Admin)",
    description="Get dynamic form schema for profile data entry based on manufacturing type (admin interface)",
    response_description="Profile form schema with sections and fields",
    operation_id="getAdminProfileSchema",
    responses={
        200: {
            "description": "Successfully retrieved profile schema",
        },
        404: {
            "description": "Manufacturing type not found",
        },
        **get_common_responses(401, 403, 500),
    },
)
async def get_profile_schema(
    manufacturing_type_id: PositiveInt,
    current_superuser: CurrentSuperuser,
    db: DBSession,
) -> ProfileSchema:
    """Get profile form schema for a manufacturing type (admin interface).

    Generates dynamic form schema based on the attribute hierarchy
    defined for the specified manufacturing type.

    Args:
        manufacturing_type_id (PositiveInt): Manufacturing type ID
        current_superuser (User): Current authenticated superuser
        db (AsyncSession): Database session

    Returns:
        ProfileSchema: Generated form schema with sections and conditional logic

    Raises:
        NotFoundException: If manufacturing type not found

    Example:
        GET /api/v1/admin/entry/profile/schema/1
    """
    from app.services.entry import EntryService

    entry_service = EntryService(db)
    return await entry_service.get_profile_schema(manufacturing_type_id)


@router.post(
    "/profile/save",
    response_model=Configuration,
    status_code=status.HTTP_201_CREATED,
    summary="Save Profile Data (Admin)",
    description="Save profile configuration data and create configuration record (admin interface)",
    response_description="Created configuration",
    operation_id="saveAdminProfileData",
    responses={
        201: {
            "description": "Profile data successfully saved",
        },
        404: {
            "description": "Manufacturing type not found",
        },
        **get_common_responses(401, 403, 422, 500),
    },
)
async def save_profile_data(
    profile_data: ProfileEntryData,
    current_superuser: CurrentSuperuser,
    db: DBSession,
) -> Configuration:
    """Save profile configuration data (admin interface).

    Validates the profile data against schema rules and creates
    a new configuration with associated selections.

    Args:
        profile_data (ProfileEntryData): Profile data to save
        current_superuser (User): Current authenticated superuser
        db (AsyncSession): Database session

    Returns:
        Configuration: Created configuration

    Raises:
        ValidationException: If validation fails
        NotFoundException: If manufacturing type not found

    Example:
        POST /api/v1/admin/entry/profile/save
        {
            "manufacturing_type_id": 1,
            "name": "Living Room Window",
            "type": "Frame",
            "material": "Aluminum",
            "opening_system": "Casement",
            "system_series": "Kom800",
            "width": 48.5
        }
    """
    from app.services.entry import EntryService

    entry_service = EntryService(db)
    return await entry_service.save_profile_configuration(profile_data, current_superuser)


@router.get(
    "/profile/load/{configuration_id}",
    response_model=ProfileEntryData,
    summary="Load Profile Data (Admin)",
    description="Load profile configuration data and populate form fields (admin interface)",
    response_description="Profile data for form population",
    operation_id="loadAdminProfileData",
    responses={
        200: {
            "description": "Profile data successfully loaded",
        },
        404: {
            "description": "Configuration not found",
        },
        **get_common_responses(401, 403, 500),
    },
)
async def load_profile_data(
    configuration_id: PositiveInt,
    current_superuser: CurrentSuperuser,
    db: DBSession,
) -> ProfileEntryData:
    """Load profile configuration data for form population (admin interface).

    Retrieves the configuration and its selections, then populates
    the form data structure for editing.

    Args:
        configuration_id (PositiveInt): Configuration ID to load
        current_superuser (User): Current authenticated superuser
        db (AsyncSession): Database session

    Returns:
        ProfileEntryData: Populated form data

    Raises:
        NotFoundException: If configuration not found

    Example:
        GET /api/v1/admin/entry/profile/load/123
    """
    from app.services.entry import EntryService

    entry_service = EntryService(db)
    return await entry_service.load_profile_configuration(configuration_id, current_superuser)


@router.get(
    "/profile/preview/{configuration_id}",
    response_model=ProfilePreviewData,
    summary="Get Profile Preview (Admin)",
    description="Get preview table data for a configuration (admin interface)",
    response_description="Profile preview data with table structure",
    operation_id="getAdminProfilePreview",
    responses={
        200: {
            "description": "Successfully retrieved profile preview",
        },
        404: {
            "description": "Configuration not found",
        },
        **get_common_responses(401, 403, 500),
    },
)
async def get_profile_preview(
    configuration_id: PositiveInt,
    current_superuser: CurrentSuperuser,
    db: DBSession,
) -> ProfilePreviewData:
    """Get profile preview data for a configuration (admin interface).

    Generates preview table data matching CSV structure
    for the specified configuration.

    Args:
        configuration_id (PositiveInt): Configuration ID
        current_superuser (User): Current authenticated superuser
        db (AsyncSession): Database session

    Returns:
        ProfilePreviewData: Preview data with table structure

    Raises:
        NotFoundException: If configuration not found

    Example:
        GET /api/v1/admin/entry/profile/preview/123
    """
    from app.services.entry import EntryService

    entry_service = EntryService(db)
    return await entry_service.generate_preview_data(configuration_id, current_superuser)


@router.post(
    "/profile/evaluate-conditions",
    summary="Evaluate Display Conditions (Admin)",
    description="Evaluate conditional field visibility based on form data (admin interface)",
    response_description="Field visibility map",
    operation_id="evaluateAdminDisplayConditions",
    responses={
        200: {
            "description": "Successfully evaluated conditions",
        },
        **get_common_responses(401, 403, 422, 500),
    },
)
async def evaluate_display_conditions(
    manufacturing_type_id: PositiveInt,
    form_data: dict[str, Any],
    current_superuser: CurrentSuperuser,
    db: DBSession,
):
    """Evaluate display conditions for conditional field visibility (admin interface).

    Evaluates all conditional display rules against the current form data
    to determine which fields should be visible.

    Args:
        manufacturing_type_id (PositiveInt): Manufacturing type ID
        form_data (dict): Current form data
        current_superuser (User): Current authenticated superuser
        db (AsyncSession): Database session

    Returns:
        dict[str, bool]: Field visibility map

    Example:
        POST /api/v1/admin/entry/profile/evaluate-conditions
        {
            "manufacturing_type_id": 1,
            "form_data": {
                "type": "Frame",
                "opening_system": "sliding"
            }
        }
    """
    from app.services.entry import EntryService

    entry_service = EntryService(db)
    schema = await entry_service.get_profile_schema(manufacturing_type_id)
    return await entry_service.evaluate_display_conditions(form_data, schema)


# HTML Page Endpoints


@router.get(
    "/profile",
    response_class=HTMLResponse,
    summary="Admin Profile Entry Page",
    description="Render the admin profile data entry page",
    operation_id="adminProfileEntryPage",
    responses={
        200: {
            "description": "Admin profile entry page rendered successfully",
            "content": {"text/html": {"example": "<html>...</html>"}},
        },
        **get_common_responses(401, 403, 500),
    },
)
async def profile_page(
    request: Request,
    current_superuser: CurrentSuperuser,
    db: DBSession,
    manufacturing_type_id: Annotated[
        PositiveInt | None,
        Query(description="Manufacturing type ID for form generation"),
    ] = None,
) -> HTMLResponse:
    """Render the admin profile data entry page.

    Displays the profile entry page with dynamic form generation
    and real-time preview capabilities within the admin interface.

    Args:
        request (Request): FastAPI request object
        current_superuser (User): Current authenticated superuser
        db (AsyncSession): Database session
        manufacturing_type_id (PositiveInt | None): Optional manufacturing type ID

    Returns:
        HTMLResponse: Rendered HTML page

    Example:
        GET /api/v1/admin/entry/profile?manufacturing_type_id=1
    """
    from app.core.manufacturing_type_resolver import ManufacturingTypeResolver
    from app.services.entry import JAVASCRIPT_CONDITION_EVALUATOR

    # If no manufacturing_type_id provided, resolve the default profile entry type
    if manufacturing_type_id is None:
        default_type = await ManufacturingTypeResolver.get_default_profile_entry_type(db)
        if default_type:
            manufacturing_type_id = default_type.id
        else:
            # No manufacturing types exist - show error page or redirect to setup
            return templates.TemplateResponse(
                request,
                "admin/error.html.jinja",
                get_admin_context(
                    request,
                    current_superuser,
                    error_message="No manufacturing types found. Please run the setup script.",
                    page_title="Setup Required",
                ),
                status_code=503,
            )

    return templates.TemplateResponse(
        request,
        "admin/entry/profile.html.jinja",
        get_admin_context(
            request,
            current_superuser,
            active_page="entry_profile",
            manufacturing_type_id=manufacturing_type_id,
            page_title="Profile Entry",
            JAVASCRIPT_CONDITION_EVALUATOR=JAVASCRIPT_CONDITION_EVALUATOR,
        ),
    )


@router.get(
    "/accessories",
    response_class=HTMLResponse,
    summary="Admin Accessories Entry Page",
    description="Render the admin accessories data entry page (scaffold)",
    operation_id="adminAccessoriesEntryPage",
    responses={
        200: {
            "description": "Admin accessories entry page rendered successfully",
            "content": {"text/html": {"example": "<html>...</html>"}},
        },
        **get_common_responses(401, 403, 500),
    },
)
async def accessories_page(
    request: Request,
    current_superuser: CurrentSuperuser,
) -> HTMLResponse:
    """Render the admin accessories data entry page (scaffold).

    Displays a scaffold page for future accessories data entry implementation
    within the admin interface.

    Args:
        request (Request): FastAPI request object
        current_superuser (User): Current authenticated superuser

    Returns:
        HTMLResponse: Rendered HTML page

    Example:
        GET /api/v1/admin/entry/accessories
    """
    return templates.TemplateResponse(
        request,
        "admin/entry/accessories.html.jinja",
        get_admin_context(
            request,
            current_superuser,
            active_page="entry_accessories",
            page_title="Accessories Entry",
        ),
    )


@router.get(
    "/glazing",
    response_class=HTMLResponse,
    summary="Admin Glazing Entry Page",
    description="Render the admin glazing data entry page (scaffold)",
    operation_id="adminGlazingEntryPage",
    responses={
        200: {
            "description": "Admin glazing entry page rendered successfully",
            "content": {"text/html": {"example": "<html>...</html>"}},
        },
        **get_common_responses(401, 403, 500),
    },
)
async def glazing_page(
    request: Request,
    current_superuser: CurrentSuperuser,
) -> HTMLResponse:
    """Render the admin glazing data entry page (scaffold).

    Displays a scaffold page for future glazing data entry implementation
    within the admin interface.

    Args:
        request (Request): FastAPI request object
        current_superuser (User): Current authenticated superuser

    Returns:
        HTMLResponse: Rendered HTML page

    Example:
        GET /api/v1/admin/entry/glazing
    """
    return templates.TemplateResponse(
        request,
        "admin/entry/glazing.html.jinja",
        get_admin_context(
            request,
            current_superuser,
            active_page="entry_glazing",
            page_title="Glazing Entry",
        ),
    )