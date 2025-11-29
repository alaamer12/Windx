"""Admin Hierarchy Management Endpoints.

This module provides FastAPI endpoints for the admin dashboard to manage
hierarchical attribute data through server-rendered Jinja2 templates.

Endpoints:
    GET /admin/hierarchy - Dashboard view with tree visualization
    GET /admin/hierarchy/node/create - Node creation form
    POST /admin/hierarchy/node/save - Save node (create or update)
    GET /admin/hierarchy/node/{node_id}/edit - Node edit form
    POST /admin/hierarchy/node/{node_id}/delete - Delete node
"""

from decimal import Decimal

from fastapi import APIRouter, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from app.api.types import (
    AttributeNodeRepo,
    CurrentSuperuser,
    DBSession,
    ManufacturingTypeRepo,
    OptionalBoolForm,
    OptionalIntForm,
    OptionalIntQuery,
    OptionalStrForm,
    OptionalStrQuery,
    RequiredIntForm,
    RequiredIntQuery,
    RequiredStrForm,
)
from app.services.hierarchy_builder import HierarchyBuilderService

# Configure Jinja2 templates
templates = Jinja2Templates(directory="app/templates")

# Create router (prefix will be added in router.py)
router = APIRouter()


@router.get("/", response_class=HTMLResponse)
async def hierarchy_dashboard(
    request: Request,
    current_superuser: CurrentSuperuser,
    db: DBSession,
    mfg_repo: ManufacturingTypeRepo,
    attr_repo: AttributeNodeRepo,
    manufacturing_type_id: OptionalIntQuery = None,
    success: OptionalStrQuery = None,
    error: OptionalStrQuery = None,
    warning: OptionalStrQuery = None,
    info: OptionalStrQuery = None,
):
    """Render hierarchy management dashboard.
    
    Args:
        request: FastAPI request object
        current_superuser: Current authenticated superuser
        db: Database session
        mfg_repo: Manufacturing type repository
        attr_repo: Attribute node repository
        manufacturing_type_id: Optional manufacturing type ID to display
        success: Optional success message from query params
        error: Optional error message from query params
        warning: Optional warning message from query params
        info: Optional info message from query params
        
    Returns:
        HTMLResponse: Rendered dashboard template
    """
    # Get all manufacturing types for selector
    manufacturing_types = await mfg_repo.get_active()
    
    # Initialize context
    context = {
        "request": request,
        "manufacturing_types": manufacturing_types,
        "selected_type_id": manufacturing_type_id,
        "selected_manufacturing_type": None,
        "tree_nodes": None,
        "ascii_tree": None,
        "diagram_tree": None,
        # Flash messages
        "success": success,
        "error": error,
        "warning": warning,
        "info": info,
    }
    
    # If manufacturing type selected, get tree data
    if manufacturing_type_id:
        # Get the selected manufacturing type
        selected_mfg_type = await mfg_repo.get(manufacturing_type_id)
        if selected_mfg_type:
            context["selected_manufacturing_type"] = selected_mfg_type
            
            hierarchy_service = HierarchyBuilderService(db)
            
            # Get tree as Pydantic models
            tree = await hierarchy_service.pydantify(manufacturing_type_id)
            
            # Convert to dict for template
            if tree:
                context["tree_nodes"] = [node.model_dump() for node in tree]
            
            # Get ASCII tree visualization
            context["ascii_tree"] = await hierarchy_service.asciify(manufacturing_type_id)
            
            # Get diagram tree visualization (base64 encoded image)
            try:
                context["diagram_tree"] = await hierarchy_service.plot_tree(manufacturing_type_id)
            except Exception:
                # If diagram generation fails, just skip it
                context["diagram_tree"] = None
    
    return templates.TemplateResponse(request=request, name="admin/hierarchy_dashboard.html.jinja", context=context)


@router.get("/node/create", response_class=HTMLResponse)
async def create_node_form(
    request: Request,
    current_superuser: CurrentSuperuser,
    db: DBSession,
    mfg_repo: ManufacturingTypeRepo,
    attr_repo: AttributeNodeRepo,
    manufacturing_type_id: RequiredIntQuery,
    parent_id: OptionalIntQuery = None,
):
    """Render node creation form.
    
    Args:
        request: FastAPI request object
        current_superuser: Current authenticated superuser
        db: Database session
        mfg_repo: Manufacturing type repository
        attr_repo: Attribute node repository
        manufacturing_type_id: Manufacturing type ID (required)
        parent_id: Optional parent node ID
        
    Returns:
        HTMLResponse: Rendered node form template
    """
    # Get manufacturing type
    manufacturing_type = await mfg_repo.get(manufacturing_type_id)
    if not manufacturing_type:
        # Redirect back with error
        return RedirectResponse(
            url=f"/admin/hierarchy?error=Manufacturing type not found",
            status_code=status.HTTP_303_SEE_OTHER,
        )
    
    # Get parent node if provided
    parent_node = None
    if parent_id:
        parent_node = await attr_repo.get(parent_id)
        if not parent_node:
            return RedirectResponse(
                url=f"/admin/hierarchy?manufacturing_type_id={manufacturing_type_id}&error=Parent node not found",
                status_code=status.HTTP_303_SEE_OTHER,
            )
    
    # Get all nodes for manufacturing type (for parent selector)
    all_nodes = await attr_repo.get_by_manufacturing_type(manufacturing_type_id)
    
    context = {
        "request": request,
        "manufacturing_type": manufacturing_type,
        "parent_node": parent_node,
        "all_nodes": all_nodes,
        "node": None,  # No existing node (create mode)
        "is_edit": False,
    }
    
    return templates.TemplateResponse(request=request, name="admin/node_form.html.jinja", context=context)


@router.post("/node/save")
async def save_node(
    request: Request,
    current_superuser: CurrentSuperuser,
    db: DBSession,
    attr_repo: AttributeNodeRepo,
    node_id: OptionalIntForm = None,
    manufacturing_type_id: RequiredIntForm = ...,
    name: RequiredStrForm = ...,
    node_type: RequiredStrForm = ...,
    parent_node_id: OptionalIntForm = None,
    data_type: OptionalStrForm = None,
    required: OptionalBoolForm = False,
    price_impact_type: RequiredStrForm = "fixed",
    price_impact_value: OptionalStrForm = None,
    price_formula: OptionalStrForm = None,
    weight_impact: RequiredStrForm = "0",
    weight_formula: OptionalStrForm = None,
    technical_property_type: OptionalStrForm = None,
    technical_impact_formula: OptionalStrForm = None,
    sort_order: OptionalIntForm = 0,
    ui_component: OptionalStrForm = None,
    description: OptionalStrForm = None,
    help_text: OptionalStrForm = None,
):
    """Save node (create or update).
    
    Args:
        request: FastAPI request object
        current_superuser: Current authenticated superuser
        db: Database session
        attr_repo: Attribute node repository
        node_id: Optional node ID for update
        manufacturing_type_id: Manufacturing type ID
        name: Node name
        node_type: Node type
        parent_node_id: Optional parent node ID
        data_type: Optional data type
        required: Whether node is required
        price_impact_type: Price impact type
        price_impact_value: Price impact value
        price_formula: Price formula
        weight_impact: Weight impact
        weight_formula: Weight formula
        technical_property_type: Technical property type
        technical_impact_formula: Technical impact formula
        sort_order: Sort order
        ui_component: UI component type
        description: Description
        help_text: Help text
        
    Returns:
        RedirectResponse: Redirect to dashboard with success message
    """
    try:
        hierarchy_service = HierarchyBuilderService(db)
        
        # Convert string values to Decimal
        price_value = Decimal(price_impact_value) if price_impact_value else None
        weight_value = Decimal(weight_impact) if weight_impact else Decimal("0")
        
        if node_id:
            # Update existing node
            node = await attr_repo.get(node_id)
            if not node:
                return RedirectResponse(
                    url=f"/admin/hierarchy?manufacturing_type_id={manufacturing_type_id}&error=Node not found",
                    status_code=status.HTTP_303_SEE_OTHER,
                )
            
            # Update node fields
            node.name = name
            node.node_type = node_type
            node.parent_node_id = parent_node_id
            node.data_type = data_type
            node.required = required
            node.price_impact_type = price_impact_type
            node.price_impact_value = price_value
            node.price_formula = price_formula
            node.weight_impact = weight_value
            node.weight_formula = weight_formula
            node.technical_property_type = technical_property_type
            node.technical_impact_formula = technical_impact_formula
            node.sort_order = sort_order
            node.ui_component = ui_component
            node.description = description
            node.help_text = help_text
            
            # Recalculate path and depth if parent changed
            if parent_node_id:
                parent = await attr_repo.get(parent_node_id)
                if parent:
                    node.ltree_path = hierarchy_service._calculate_ltree_path(parent, name)
                    node.depth = hierarchy_service._calculate_depth(parent)
            else:
                node.ltree_path = hierarchy_service._calculate_ltree_path(None, name)
                node.depth = 0
            
            await db.commit()
            await db.refresh(node)
            
            return RedirectResponse(
                url=f"/admin/hierarchy?manufacturing_type_id={manufacturing_type_id}&success=Node updated successfully",
                status_code=status.HTTP_303_SEE_OTHER,
            )
        else:
            # Create new node
            await hierarchy_service.create_node(
                manufacturing_type_id=manufacturing_type_id,
                name=name,
                node_type=node_type,
                parent_node_id=parent_node_id,
                data_type=data_type,
                required=required,
                price_impact_type=price_impact_type,
                price_impact_value=price_value,
                price_formula=price_formula,
                weight_impact=weight_value,
                weight_formula=weight_formula,
                technical_property_type=technical_property_type,
                technical_impact_formula=technical_impact_formula,
                sort_order=sort_order,
                ui_component=ui_component,
                description=description,
                help_text=help_text,
            )
            
            return RedirectResponse(
                url=f"/admin/hierarchy?manufacturing_type_id={manufacturing_type_id}&success=Node created successfully",
                status_code=status.HTTP_303_SEE_OTHER,
            )
    
    except Exception as e:
        # Handle validation errors
        return RedirectResponse(
            url=f"/admin/hierarchy?manufacturing_type_id={manufacturing_type_id}&error={str(e)}",
            status_code=status.HTTP_303_SEE_OTHER,
        )


@router.get("/node/{node_id}/edit", response_class=HTMLResponse)
async def edit_node_form(
    request: Request,
    node_id: int,
    current_superuser: CurrentSuperuser,
    db: DBSession,
    mfg_repo: ManufacturingTypeRepo,
    attr_repo: AttributeNodeRepo,
):
    """Render node edit form.
    
    Args:
        request: FastAPI request object
        node_id: Node ID to edit
        current_superuser: Current authenticated superuser
        db: Database session
        mfg_repo: Manufacturing type repository
        attr_repo: Attribute node repository
        
    Returns:
        HTMLResponse: Rendered node form template with pre-filled data
    """
    # Get node by ID
    node = await attr_repo.get(node_id)
    if not node:
        return RedirectResponse(
            url="/admin/hierarchy?error=Node not found",
            status_code=status.HTTP_303_SEE_OTHER,
        )
    
    # Get manufacturing type
    manufacturing_type = await mfg_repo.get(node.manufacturing_type_id)
    if not manufacturing_type:
        return RedirectResponse(
            url="/admin/hierarchy?error=Manufacturing type not found",
            status_code=status.HTTP_303_SEE_OTHER,
        )
    
    # Get all nodes for manufacturing type (for parent selector)
    # Exclude current node and its descendants to prevent circular references
    all_nodes = await attr_repo.get_by_manufacturing_type(node.manufacturing_type_id)
    
    # Get descendants to exclude them from parent selector
    descendants = await attr_repo.get_descendants(node_id)
    descendant_ids = {d.id for d in descendants}
    descendant_ids.add(node_id)  # Also exclude the node itself
    
    # Filter out node and descendants
    available_parents = [n for n in all_nodes if n.id not in descendant_ids]
    
    # Get parent node if exists
    parent_node = None
    if node.parent_node_id:
        parent_node = await attr_repo.get(node.parent_node_id)
    
    context = {
        "request": request,
        "manufacturing_type": manufacturing_type,
        "parent_node": parent_node,
        "all_nodes": available_parents,
        "node": node,
        "is_edit": True,
    }
    
    return templates.TemplateResponse(request=request, name="admin/node_form.html.jinja", context=context)


@router.post("/node/{node_id}/delete")
async def delete_node(
    node_id: int,
    current_superuser: CurrentSuperuser,
    db: DBSession,
    attr_repo: AttributeNodeRepo,
):
    """Delete node.
    
    Args:
        node_id: Node ID to delete
        current_superuser: Current authenticated superuser
        db: Database session
        attr_repo: Attribute node repository
        
    Returns:
        RedirectResponse: Redirect to dashboard with success/error message
    """
    # Get node by ID
    node = await attr_repo.get(node_id)
    if not node:
        return RedirectResponse(
            url="/admin/hierarchy?error=Node not found",
            status_code=status.HTTP_303_SEE_OTHER,
        )
    
    manufacturing_type_id = node.manufacturing_type_id
    
    # Check for children
    children = await attr_repo.get_children(node_id)
    if children:
        return RedirectResponse(
            url=f"/admin/hierarchy?manufacturing_type_id={manufacturing_type_id}&error=Cannot delete node with children. Delete children first.",
            status_code=status.HTTP_303_SEE_OTHER,
        )
    
    # Delete node
    try:
        await attr_repo.delete(node_id)
        await db.commit()
        
        return RedirectResponse(
            url=f"/admin/hierarchy?manufacturing_type_id={manufacturing_type_id}&success=Node deleted successfully",
            status_code=status.HTTP_303_SEE_OTHER,
        )
    except Exception as e:
        return RedirectResponse(
            url=f"/admin/hierarchy?manufacturing_type_id={manufacturing_type_id}&error=Failed to delete node: {str(e)}",
            status_code=status.HTTP_303_SEE_OTHER,
        )
