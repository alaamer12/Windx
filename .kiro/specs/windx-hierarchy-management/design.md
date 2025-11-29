# Design Document: Windx Hierarchical Data Management System

## Overview

This document describes the technical design for the Windx Hierarchical Data Management System, which provides tools for inserting, managing, and visualizing hierarchical attribute data through:

1. **HierarchyBuilderService** - Python service with helper functions for programmatic data insertion
2. **Backend Admin Dashboard** - Jinja2-based web interface for data entry
3. **Tree Visualization** - ASCII and diagram representations of hierarchies

This system builds on the core Windx integration and focuses on making it easy for administrators to populate and manage the attribute tree.

## Architecture

### Component Overview

```
┌─────────────────────────────────────────────────────────────┐
│                  Admin Dashboard (Jinja2)                    │
│  /admin/hierarchy - Server-rendered HTML forms              │
└──────────────────────┬──────────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────────┐
│              HierarchyBuilderService                         │
│  - create_node()                                             │
│  - create_hierarchy_from_dict()                              │
│  - get_tree_as_pydantic()                                    │
│  - generate_ascii_tree()                                     │
└──────────────────────┬──────────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────────┐
│              AttributeNodeRepository                         │
│  - LTREE path calculation                                    │
│  - Depth calculation                                         │
│  - Hierarchical queries                                      │
└──────────────────────┬──────────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────────┐
│              Database (PostgreSQL + LTREE)                   │
│  - attribute_nodes table                                     │
│  - manufacturing_types table                                 │
└─────────────────────────────────────────────────────────────┘
```

### Design Principles

1. **Ease of Use**: Simple Python functions for data insertion
2. **Server-Side Rendering**: Jinja2 templates, no separate frontend
3. **Automatic Path Management**: LTREE paths calculated automatically
4. **Pydantic Serialization**: Easy JSON export for visualization
5. **Validation**: Prevent invalid hierarchies and circular references

## Component Design

### 1. HierarchyBuilderService

**Purpose**: Provide high-level helper functions for creating and managing hierarchical data.

**Location**: `app/services/hierarchy_builder_service.py`

**Key Methods**:

```python
class HierarchyBuilderService(BaseService):
    """Service for building and managing attribute hierarchies."""
    
    def __init__(self, db: AsyncSession):
        super().__init__(db)
        self.mfg_type_repo = ManufacturingTypeRepository(db)
        self.attr_node_repo = AttributeNodeRepository(db)
    
    async def create_manufacturing_type(
        self,
        name: str,
        description: str | None = None,
        base_category: str | None = None,
        base_price: Decimal = Decimal("0"),
        base_weight: Decimal = Decimal("0")
    ) -> ManufacturingType:
        """Create a new manufacturing type."""
        pass
    
    async def create_node(
        self,
        manufacturing_type_id: int,
        name: str,
        node_type: str,
        parent: AttributeNode | None = None,
        data_type: str | None = None,
        price_impact_type: str = "fixed",
        price_impact_value: Decimal | None = None,
        weight_impact: Decimal = Decimal("0"),
        **kwargs
    ) -> AttributeNode:
        """Create a single attribute node with automatic path calculation."""
        pass
    
    async def create_hierarchy_from_dict(
        self,
        manufacturing_type_id: int,
        hierarchy_data: dict,
        parent: AttributeNode | None = None
    ) -> AttributeNode:
        """Create a hierarchy from nested dictionary."""
        pass
    
    async def get_tree_as_pydantic(
        self,
        manufacturing_type_id: int,
        root_node_id: int | None = None
    ) -> AttributeNodeTree:
        """Get hierarchy as Pydantic model (serializable to JSON)."""
        pass
    
    async def generate_ascii_tree(
        self,
        manufacturing_type_id: int,
        root_node_id: int | None = None
    ) -> str:
        """Generate ASCII tree representation."""
        pass
```



### 2. LTREE Path Calculation

**Algorithm**: Automatic path generation based on parent-child relationships.

**Implementation**:

```python
def _calculate_ltree_path(
    parent: AttributeNode | None,
    node_name: str
) -> str:
    """Calculate LTREE path for a new node."""
    # Sanitize node name for LTREE (lowercase, replace spaces with underscores)
    sanitized_name = node_name.lower().replace(" ", "_").replace("&", "and")
    
    if parent is None:
        # Root node
        return sanitized_name
    else:
        # Child node: append to parent's path
        return f"{parent.ltree_path}.{sanitized_name}"

def _calculate_depth(parent: AttributeNode | None) -> int:
    """Calculate depth level for a new node."""
    if parent is None:
        return 0
    else:
        return parent.depth + 1
```

**Example**:
- Parent: `frame_material.material_type` (depth=1)
- New node: "Aluminum"
- Result: `frame_material.material_type.aluminum` (depth=2)

### 3. Pydantic Models for Serialization

**Purpose**: Enable JSON serialization of hierarchies for visualization.

**Location**: `app/schemas/attribute_node.py`

**Models**:

```python
from pydantic import BaseModel, Field, ConfigDict
from typing import Annotated

class AttributeNodeTree(BaseModel):
    """Hierarchical attribute node with children (for tree visualization)."""
    
    id: Annotated[int, Field(description="Node ID")]
    name: Annotated[str, Field(description="Node name")]
    node_type: Annotated[str, Field(description="Node type")]
    data_type: Annotated[str | None, Field(default=None)]
    ltree_path: Annotated[str, Field(description="LTREE path")]
    depth: Annotated[int, Field(description="Depth level")]
    
    # Pricing information
    price_impact_type: Annotated[str, Field(default="fixed")]
    price_impact_value: Annotated[Decimal | None, Field(default=None)]
    weight_impact: Annotated[Decimal, Field(default=Decimal("0"))]
    
    # Nested children
    children: Annotated[list["AttributeNodeTree"], Field(default_factory=list)]
    
    model_config = ConfigDict(from_attributes=True)

# Enable forward references
AttributeNodeTree.model_rebuild()
```

**Usage**:
```python
tree = await builder.get_tree_as_pydantic(manufacturing_type_id=1)
json_str = tree.model_dump_json(indent=2)
```



### 4. Backend Admin Dashboard

**Technology Stack**:
- FastAPI for routing
- Fastapi-admin plugins [Add it using uv if not installed]
- Jinja2 for template rendering
- Bootstrap 5 for styling
- Minimal JavaScript for tree interactions

**Routes**:

```python
# app/api/v1/endpoints/admin_hierarchy.py

@router.get("/admin/hierarchy", response_class=HTMLResponse)
async def hierarchy_dashboard(
    request: Request,
    manufacturing_type_id: int | None = None,
    current_user: User = Depends(get_current_superuser)
):
    """Render hierarchy management dashboard."""
    pass

@router.get("/admin/hierarchy/node/create", response_class=HTMLResponse)
async def create_node_form(
    request: Request,
    manufacturing_type_id: int,
    parent_id: int | None = None,
    current_user: User = Depends(get_current_superuser)
):
    """Render node creation form."""
    pass

@router.post("/admin/hierarchy/node/save")
async def save_node(
    request: Request,
    node_data: NodeFormData = Depends(),
    current_user: User = Depends(get_current_superuser)
):
    """Save node (create or update)."""
    pass

@router.get("/admin/hierarchy/node/{node_id}/edit", response_class=HTMLResponse)
async def edit_node_form(
    request: Request,
    node_id: int,
    current_user: User = Depends(get_current_superuser)
):
    """Render node edit form."""
    pass

@router.post("/admin/hierarchy/node/{node_id}/delete")
async def delete_node(
    node_id: int,
    cascade: bool = False,
    current_user: User = Depends(get_current_superuser)
):
    """Delete node."""
    pass
```

**Template Structure**:

```
templates/
├── admin/
│   ├── base.html                    # Base layout
│   ├── hierarchy_dashboard.html     # Main dashboard
│   ├── node_form.html               # Create/edit form
│   ├── node_delete_confirm.html     # Delete confirmation
│   └── components/
│       ├── tree_view.html           # Tree rendering
│       └── ascii_tree.html          # ASCII visualization
```



### 5. ASCII Tree Generation

**Purpose**: Generate human-readable tree visualization.

**Algorithm**:

```python
def _generate_ascii_tree_recursive(
    node: AttributeNode,
    children_map: dict[int, list[AttributeNode]],
    prefix: str = "",
    is_last: bool = True
) -> str:
    """Recursively generate ASCII tree."""
    result = []
    
    # Current node
    connector = "└── " if is_last else "├── "
    price_str = f" [+${node.price_impact_value}]" if node.price_impact_value else ""
    result.append(f"{prefix}{connector}{node.name}{price_str}")
    
    # Children
    children = children_map.get(node.id, [])
    for i, child in enumerate(children):
        is_last_child = (i == len(children) - 1)
        extension = "    " if is_last else "│   "
        child_tree = _generate_ascii_tree_recursive(
            child,
            children_map,
            prefix + extension,
            is_last_child
        )
        result.append(child_tree)
    
    return "\n".join(result)
```

**Example Output**:
```
Material
├── uPVC
│   ├── System
│   │   ├── Aluplast
│   │   │   ├── Profile
│   │   │   │   ├── IDEAL 4000 [+$50.00]
│   │   │   │   │   └── Color & Decor
│   │   │   │   │       ├── Standard colors [+$0.00]
│   │   │   │   │       ├── Special colors [+$25.00]
│   │   │   │   │       └── Woodec collection [+$40.00]
│   │   │   │   └── IDEAL 5000 [+$75.00]
│   │   │   └── Type of Window
│   │   │       ├── Single sash [+$100.00]
│   │   │       └── Double sash [+$180.00]
│   │   └── Kommerling
│   └── Size
│       ├── Width (385-3010 mm)
│       └── Height (385-3010 mm)
└── Aluminium
```



## Data Flow

### Flow 1: Creating Nodes Programmatically

```
Developer → HierarchyBuilderService.create_node()
    ↓
Calculate ltree_path from parent
    ↓
Calculate depth from parent
    ↓
AttributeNodeRepository.create()
    ↓
Database INSERT with auto-calculated fields
    ↓
Return AttributeNode model
```

### Flow 2: Creating Nodes via Dashboard

```
Admin → Fill HTML form → POST /admin/hierarchy/node/save
    ↓
FastAPI endpoint receives form data
    ↓
HierarchyBuilderService.create_node()
    ↓
Calculate ltree_path and depth
    ↓
Save to database
    ↓
Redirect to dashboard with success message
    ↓
Jinja2 renders updated tree
```

### Flow 3: Visualizing Tree as JSON

```
Request → HierarchyBuilderService.get_tree_as_pydantic()
    ↓
AttributeNodeRepository.get_tree()
    ↓
Build nested Pydantic models
    ↓
tree.model_dump_json()
    ↓
JSON output for visualization
```

### Flow 4: Batch Import from Dictionary

```
Developer → Prepare nested dict → create_hierarchy_from_dict()
    ↓
Recursively process each node
    ↓
For each node: calculate path, create in DB
    ↓
Return root node
```



## Database Considerations

### LTREE Path Uniqueness

**Challenge**: Ensure LTREE paths are unique within a manufacturing type.

**Solution**: 
- Sanitize node names (lowercase, replace spaces)
- Add numeric suffix if duplicate exists
- Example: `aluminum`, `aluminum_2`, `aluminum_3`

### Cascade Deletion

**Challenge**: What happens when a parent node is deleted?

**Options**:
1. **Prevent deletion** if node has children (safest)
2. **Cascade delete** all descendants (requires confirmation)
3. **Orphan children** by setting parent_node_id to NULL (not recommended)

**Chosen Approach**: Option 1 by default, Option 2 with explicit confirmation.

### Performance

**Indexes**:
- GiST index on `ltree_path` (already in schema)
- Index on `parent_node_id` (already in schema)
- Index on `manufacturing_type_id` (already in schema)

**Query Optimization**:
- Use LTREE operators for descendant/ancestor queries
- Eager load children when building tree
- Cache tree structure in memory for dashboard

## Security

### Authentication

- All admin routes require authentication
- Only users with `is_superuser=True` can access
- Use `Depends(get_current_superuser)` dependency

### Authorization

- Validate manufacturing_type_id exists
- Validate parent_node_id exists and belongs to same manufacturing type
- Prevent circular references (node cannot be its own ancestor)

### Input Validation

- Sanitize node names for LTREE compatibility
- Validate node_type enum values
- Validate price_impact_type enum values
- Validate numeric fields (price, weight) are non-negative
- Validate formulas for syntax errors (if applicable)



## Testing Strategy

### Unit Tests

**Location**: `tests/unit/services/test_hierarchy_builder_service.py`

**Coverage**:
- Test ltree_path calculation
- Test depth calculation
- Test node creation with various parameters
- Test validation logic
- Test ASCII tree generation

### Integration Tests

**Location**: `tests/integration/test_hierarchy_builder.py`

**Coverage**:
- Test creating manufacturing type
- Test creating root nodes
- Test creating child nodes
- Test creating hierarchy from dictionary
- Test querying descendants/ancestors
- Test complete uPVC hierarchy example
- Test Pydantic serialization

### Dashboard Tests

**Location**: `tests/integration/test_admin_hierarchy.py`

**Coverage**:
- Test dashboard renders correctly
- Test form submission creates node
- Test form validation
- Test node deletion
- Test authentication/authorization

## Error Handling

### Common Errors

1. **Parent Not Found**
   - Error: `NotFoundException("Parent node not found")`
   - HTTP: 404

2. **Invalid Manufacturing Type**
   - Error: `NotFoundException("Manufacturing type not found")`
   - HTTP: 404

3. **Circular Reference**
   - Error: `ValidationException("Cannot set node as its own ancestor")`
   - HTTP: 422

4. **Duplicate Name at Same Level**
   - Error: `ConflictException("Node with this name already exists at this level")`
   - HTTP: 409

5. **Invalid Node Type**
   - Error: `ValidationException("Invalid node_type. Must be: category, attribute, option, component, technical_spec")`
   - HTTP: 422

6. **Cannot Delete Node with Children**
   - Error: `ConflictException("Cannot delete node with children. Use cascade=True to delete all descendants.")`
   - HTTP: 409



## Implementation Notes

### Phase 1: Core Service

1. Implement `HierarchyBuilderService` with basic methods
2. Implement ltree_path and depth calculation
3. Add validation logic
4. Write unit tests

### Phase 2: Batch Import

1. Implement `create_hierarchy_from_dict()`
2. Add recursive processing
3. Add transaction handling (all-or-nothing)
4. Write integration tests

### Phase 3: Pydantic Serialization

1. Create `AttributeNodeTree` Pydantic model
2. Implement `get_tree_as_pydantic()`
3. Test JSON serialization
4. Verify nested structure

### Phase 4: ASCII Tree

1. Implement `generate_ascii_tree()`
2. Add box-drawing characters
3. Add price display
4. Test with various tree structures

### Phase 5: Dashboard

1. Create Jinja2 templates
2. Implement FastAPI routes
3. Add form handling
4. Add authentication/authorization
5. Test end-to-end

### Phase 6: Polish

1. Add search/filter functionality
2. Add export functionality
3. Improve error messages
4. Add audit logging
5. Performance optimization

## Future Enhancements

### Drag-and-Drop Reordering

- Use JavaScript library (SortableJS)
- Update sort_order on drop
- Recalculate ltree_path if parent changes

### Real-Time Collaboration

- WebSocket for live updates
- Show who is editing what
- Conflict resolution

### Version Control

- Track hierarchy versions
- Allow rollback to previous version
- Compare versions

### Import/Export

- Export to JSON, YAML, CSV
- Import from external sources
- Validate before import

### Advanced Visualization

- Interactive D3.js tree diagram
- Mermaid diagram generation
- Collapsible tree with search

