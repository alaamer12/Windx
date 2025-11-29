# Requirements Document: Windx Hierarchical Data Management System

## Introduction

This document outlines the requirements for building a comprehensive hierarchical data management system for the Windx configurator. The system will enable administrators to:

1. **Insert complex hierarchical product data** (e.g., Material → uPVC → System → Aluplast → Profile → IDEAL 4000 → Color & Decor) JUST AN EXAMPLE
2. **Visualize the hierarchy** through an interactive dashboard with tree-like ASCII or diagram representations
3. **Manage the attribute tree** through a user-friendly interface

This system builds on top of the core Windx integration (windx-integration spec) and focuses specifically on the data entry and visualization aspects of the hierarchical attribute system.

## Requirements

### Requirement 1: Helper Functions for Programmatic Data Insertion

**User Story:** As a developer or data entry administrator, I want Python helper functions to easily insert hierarchical data, so that I can populate the attribute tree programmatically without writing complex SQL or ORM code.

#### Acceptance Criteria

1. WHEN I use a helper function to create a node THEN it SHALL automatically calculate and set the ltree_path
2. WHEN I use a helper function to create a node THEN it SHALL automatically calculate and set the depth
3. WHEN I create a child node THEN the helper function SHALL validate that the parent exists
4. WHEN I create a node with pricing THEN the helper function SHALL accept price_impact_value and price_impact_type
5. WHEN I create a node with weight THEN the helper function SHALL accept weight_impact
6. WHEN I create a node with technical properties THEN the helper function SHALL accept technical_property_type and formulas
7. WHEN I create multiple nodes in a hierarchy THEN the helper function SHALL support batch creation with parent references
8. WHEN insertion fails THEN the helper function SHALL rollback all changes and raise a descriptive exception
9. WHEN I use helper functions THEN they SHALL be available as a service method (e.g., `HierarchyBuilderService`)
10. WHEN I use helper functions THEN they SHALL support both synchronous and asynchronous operations
11. WHEN I retrieve hierarchy data THEN the service SHALL return Pydantic models that can be serialized to JSON
12. WHEN I serialize hierarchy to JSON THEN it SHALL include all node properties and maintain the tree structure
13. WHEN I serialize hierarchy to JSON THEN it SHALL be suitable for tree visualization libraries (D3.js, Mermaid, etc.) as it will be parsed by Json file

**Example Usage:**
```python
# Using helper service to create hierarchy
builder = HierarchyBuilderService(db_session)

# Create manufacturing type
window_type = await builder.create_manufacturing_type(
    name="Casement Window",
    description="Standard opening windows",
    base_category="window",
    base_price=150.00,
    base_weight=10.0
)

# Create category node
frame_material = await builder.create_node(
    manufacturing_type_id=window_type.id,
    name="Frame Material",
    node_type="category",
    parent=None  # Root node
)

# Create attribute node
material_type = await builder.create_node(
    manufacturing_type_id=window_type.id,
    name="Material Type",
    node_type="attribute",
    data_type="selection",
    ui_component="dropdown",
    parent=frame_material
)

# Create option nodes with pricing
upvc = await builder.create_node(
    manufacturing_type_id=window_type.id,
    name="uPVC",
    node_type="option",
    data_type="string",
    price_impact_type="fixed",
    price_impact_value=0,
    weight_impact=2.5,
    technical_property_type="u_value",
    technical_impact_formula="base_u_value + 0.1",
    parent=material_type
)

aluminum = await builder.create_node(
    manufacturing_type_id=window_type.id,
    name="Aluminum",
    node_type="option",
    data_type="string",
    price_impact_type="fixed",
    price_impact_value=50,
    weight_impact=1.8,
    technical_property_type="u_value",
    technical_impact_formula="base_u_value - 0.2",
    parent=material_type
)

# Batch creation from dictionary
hierarchy_data = {
    "name": "Glass Type",
    "node_type": "category",
    "children": [
        {
            "name": "Glass Configuration",
            "node_type": "attribute",
            "data_type": "selection",
            "children": [
                {
                    "name": "Single Pane",
                    "node_type": "option",
                    "price_impact_value": 0
                },
                {
                    "name": "Double Pane",
                    "node_type": "option",
                    "price_impact_value": 80
                }
            ]
        }
    ]
}

await builder.create_hierarchy_from_dict(
    manufacturing_type_id=window_type.id,
    hierarchy_data=hierarchy_data,
    parent=None
)

# Get hierarchy as Pydantic models (serializable to JSON)
tree = await builder.get_tree_as_pydantic(
    manufacturing_type_id=window_type.id
)

# Serialize to JSON for visualization
tree_json = tree.model_dump_json(indent=2)
# Output:
# {
#   "id": 1,
#   "name": "Frame Material",
#   "node_type": "category",
#   "ltree_path": "frame_material",
#   "depth": 0,
#   "price_impact_value": null,
#   "children": [
#     {
#       "id": 2,
#       "name": "Material Type",
#       "node_type": "attribute",
#       "ltree_path": "frame_material.material_type",
#       "depth": 1,
#       "children": [
#         {
#           "id": 3,
#           "name": "uPVC",
#           "node_type": "option",
#           "price_impact_value": 0,
#           "children": []
#         }
#       ]
#     }
#   ]
# }

# Use for tree visualization
import json
tree_data = json.loads(tree_json)
# Pass to frontend for D3.js, Mermaid, or ASCII tree rendering
```

**Test Example:**
```python
# Test file: tests/integration/test_hierarchy_builder.py
async def test_create_window_hierarchy(db_session):
    """Test creating a complete window hierarchy."""
    builder = HierarchyBuilderService(db_session)
    
    # Create manufacturing type
    window_type = await builder.create_manufacturing_type(
        name="Casement Window",
        base_price=150.00,
        base_weight=10.0
    )
    
    # Create hierarchy
    frame_material = await builder.create_node(
        manufacturing_type_id=window_type.id,
        name="Frame Material",
        node_type="category"
    )
    
    material_type = await builder.create_node(
        manufacturing_type_id=window_type.id,
        name="Material Type",
        node_type="attribute",
        parent=frame_material
    )
    
    upvc = await builder.create_node(
        manufacturing_type_id=window_type.id,
        name="uPVC",
        node_type="option",
        price_impact_value=0,
        weight_impact=2.5,
        parent=material_type
    )
    
    # Verify ltree_path was set correctly
    assert upvc.ltree_path == "frame_material.material_type.upvc"
    assert upvc.depth == 2
    
    # Verify parent-child relationships
    children = await builder.get_children(material_type.id)
    assert len(children) == 1
    assert children[0].id == upvc.id
```

---

### Requirement 2: Backend Admin Dashboard (Jinja Templates)

**User Story:** As a data entry administrator, I want a backend admin dashboard using Jinja templates to manage the attribute hierarchy, so that I can create, edit, and organize nodes through server-rendered HTML forms.

#### Acceptance Criteria

1. WHEN I access `/admin/hierarchy` THEN I SHALL see the hierarchy management dashboard
2. WHEN I access the dashboard THEN it SHALL be rendered using Jinja2 templates
3. WHEN I access the dashboard THEN it SHALL use FastAPI's template rendering (not a separate frontend)
4. WHEN I select a manufacturing type THEN the page SHALL reload/update to show its attribute tree
5. WHEN viewing the tree THEN it SHALL be rendered as HTML with expand/collapse functionality (using simple JavaScript)
6. WHEN I click on a node THEN I SHALL see its full details in a form
7. WHEN I create a new node THEN I SHALL submit an HTML form that posts to the backend
8. WHEN I edit a node THEN I SHALL submit an HTML form with updated values
9. WHEN I delete a node THEN I SHALL see a confirmation page before deletion
10. WHEN forms are submitted THEN the page SHALL redirect back to the dashboard with success/error messages

**Technology Stack:**
- **Backend**: FastAPI with Jinja2 templates
- **Templates**: Server-side rendered HTML (no React/Vue/Angular)
- **Styling**: Bootstrap or Tailwind CSS for forms and layout
- **JavaScript**: Minimal JS for tree expand/collapse and form validation
- **Forms**: Standard HTML forms with POST requests

**Dashboard Sections:**
- **Manufacturing Type Selector**: HTML `<select>` dropdown
- **Tree View Panel**: Server-rendered HTML tree with `<ul>/<li>` elements
- **Node Form Panel**: HTML form with input fields
- **Tree Visualization Panel**: ASCII tree rendered in `<pre>` tag or SVG diagram

---

### Requirement 3: Tree Visualization (ASCII/Diagram)

**User Story:** As a data entry administrator, I want to see a tree-like visual representation of the hierarchy, so that I can quickly understand the structure and relationships.

#### Acceptance Criteria

1. WHEN I request a tree visualization THEN the system SHALL generate an ASCII tree representation
2. WHEN viewing the ASCII tree THEN it SHALL use box-drawing characters (├──, └──, │)
3. WHEN viewing the tree THEN node names SHALL be displayed with their types
4. WHEN viewing the tree THEN pricing information SHALL be shown inline [+$50.00]
5. WHEN the tree is large THEN I SHALL be able to collapse/expand branches
6. WHEN I export the tree THEN I SHALL be able to download it as text or image
7. WHEN viewing in diagram mode THEN the system SHALL generate a visual diagram (Mermaid, D3.js, or similar)
8. WHEN viewing the diagram THEN nodes SHALL be color-coded by type (category, attribute, option)
9. WHEN I click a node in the diagram THEN it SHALL navigate to the node details
10. WHEN generating visualizations THEN the service SHALL provide JSON-serialized tree data via Pydantic models
11. WHEN the tree is serialized THEN it SHALL maintain parent-child relationships in nested structure
12. WHEN the tree is serialized THEN it SHALL include all properties needed for visualization (name, type, price, depth, path)

**Example ASCII Output:**
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
│   │   │   │   │       ├── Aludec collection [+$35.00]
│   │   │   │   │       └── Woodec collection [+$40.00]
│   │   │   │   ├── IDEAL 5000 [+$75.00]
│   │   │   │   │   └── Color & Decor
│   │   │   │   │       ├── Standard colors
│   │   │   │   │       └── Special colors
│   │   │   └── Type of Window
│   │   │       ├── Single sash [+$100.00]
│   │   │       ├── Double sash [+$180.00]
│   │   │       └── Triple sash [+$250.00]
│   │   └── Kommerling
│   │       └── Profile
│   └── Size
│       ├── Width (385-3010 mm)
│       └── Height (385-3010 mm)
├── uPVC-Aluminium
├── Wood
├── Wood-Aluminium
└── Aluminium
```

---

### Requirement 4: Dashboard with Input Forms for Node Creation

**User Story:** As a data entry administrator, I want a web dashboard with input forms to create nodes, so that I can build the hierarchy through a user-friendly interface without writing code.

#### Acceptance Criteria

1. WHEN I access the dashboard THEN I SHALL see a "Create Node" form
2. WHEN I fill the form THEN I SHALL provide the following fields:
   - Manufacturing Type (dropdown)
   - Parent Node (tree selector or dropdown)
   - Node Name (text input)
   - Node Type (dropdown: category, attribute, option, component, technical_spec)
   - Data Type (dropdown: string, number, boolean, formula, dimension, selection)
   - Price Impact Type (dropdown: fixed, percentage, formula)
   - Price Impact Value (number input)
   - Weight Impact (number input)
   - Technical Property Type (text input)
   - Technical Impact Formula (text input)
   - UI Component (dropdown: dropdown, radio, checkbox, slider, input)
   - Description (textarea)
   - Help Text (textarea)
   - Sort Order (number input)
3. WHEN I submit the form THEN the node SHALL be created with automatic ltree_path and depth calculation
4. WHEN I submit the form THEN I SHALL see a success message with the created node details
5. WHEN I submit the form with invalid data THEN I SHALL see validation errors
6. WHEN I click "Edit" on a node THEN the form SHALL be pre-filled with current values
7. WHEN I update a node THEN the changes SHALL be saved and reflected in the tree
8. WHEN I click "Delete" on a node THEN I SHALL see a confirmation dialog
9. WHEN I delete a node with children THEN I SHALL be warned and choose to cascade delete
10. WHEN I create a node THEN the tree view SHALL automatically refresh to show the new node

**Dashboard Layout (Server-Rendered HTML):**
```html
<!-- Jinja2 Template: templates/admin/hierarchy_dashboard.html -->
<!DOCTYPE html>
<html>
<head>
    <title>Windx Hierarchy Management</title>
    <link rel="stylesheet" href="/static/css/bootstrap.min.css">
</head>
<body>
    <div class="container-fluid">
        <h1>Windx Hierarchy Management Dashboard</h1>
        
        <!-- Manufacturing Type Selector -->
        <form method="GET" action="/admin/hierarchy">
            <select name="manufacturing_type_id" onchange="this.form.submit()">
                <option value="">Select Manufacturing Type</option>
                {% for mfg_type in manufacturing_types %}
                <option value="{{ mfg_type.id }}" 
                        {% if mfg_type.id == selected_type_id %}selected{% endif %}>
                    {{ mfg_type.name }}
                </option>
                {% endfor %}
            </select>
        </form>
        
        <div class="row">
            <!-- Tree View (Left Panel) -->
            <div class="col-md-6">
                <h3>Attribute Tree</h3>
                <ul class="tree">
                    {% for node in tree_nodes %}
                    <li>
                        <span class="node-name">{{ node.name }}</span>
                        <span class="node-type">[{{ node.node_type }}]</span>
                        {% if node.price_impact_value %}
                        <span class="price">[+${{ node.price_impact_value }}]</span>
                        {% endif %}
                        <a href="/admin/hierarchy/node/{{ node.id }}/edit">Edit</a>
                        <a href="/admin/hierarchy/node/{{ node.id }}/delete" 
                           onclick="return confirm('Delete this node?')">Delete</a>
                        
                        {% if node.children %}
                        <ul>
                            {% for child in node.children recursive %}
                            <li>{{ child.name }} ...</li>
                            {% endfor %}
                        </ul>
                        {% endif %}
                    </li>
                    {% endfor %}
                </ul>
                
                <a href="/admin/hierarchy/node/create" class="btn btn-primary">+ Add Node</a>
            </div>
            
            <!-- Node Form (Right Panel) -->
            <div class="col-md-6">
                <h3>{% if node %}Edit Node{% else %}Create Node{% endif %}</h3>
                
                <form method="POST" action="/admin/hierarchy/node/save">
                    {% if node %}<input type="hidden" name="node_id" value="{{ node.id }}">{% endif %}
                    
                    <div class="form-group">
                        <label>Node Name</label>
                        <input type="text" name="name" class="form-control" 
                               value="{{ node.name if node else '' }}" required>
                    </div>
                    
                    <div class="form-group">
                        <label>Node Type</label>
                        <select name="node_type" class="form-control" required>
                            <option value="category">Category</option>
                            <option value="attribute">Attribute</option>
                            <option value="option">Option</option>
                        </select>
                    </div>
                    
                    <div class="form-group">
                        <label>Parent Node</label>
                        <select name="parent_node_id" class="form-control">
                            <option value="">None (Root)</option>
                            {% for parent in available_parents %}
                            <option value="{{ parent.id }}">{{ parent.name }}</option>
                            {% endfor %}
                        </select>
                    </div>
                    
                    <h4>Pricing</h4>
                    <div class="form-group">
                        <label>Price Impact Value</label>
                        <input type="number" name="price_impact_value" class="form-control" 
                               step="0.01" value="{{ node.price_impact_value if node else 0 }}">
                    </div>
                    
                    <button type="submit" class="btn btn-success">Save Node</button>
                    <a href="/admin/hierarchy" class="btn btn-secondary">Cancel</a>
                </form>
            </div>
        </div>
        
        <!-- ASCII Tree Visualization -->
        <div class="row mt-4">
            <div class="col-md-12">
                <h3>Tree Visualization</h3>
                <pre>{{ ascii_tree }}</pre>
            </div>
        </div>
    </div>
</body>
</html>
```

---

### Requirement 5: Hierarchy Validation

**User Story:** As a data entry administrator, I want the system to validate the hierarchy structure, so that I don't create invalid or inconsistent data.

#### Acceptance Criteria

1. WHEN I create a node THEN the system SHALL validate that the parent exists
2. WHEN I create a node THEN the system SHALL validate that the manufacturing_type_id is valid
3. WHEN I create a node THEN the system SHALL prevent duplicate names at the same level
4. WHEN I create a node THEN the system SHALL validate that node_type is valid
5. WHEN I set pricing THEN the system SHALL validate that price_impact_type matches price_impact_value or price_formula
6. WHEN I set formulas THEN the system SHALL validate formula syntax
7. WHEN I set display conditions THEN the system SHALL validate JSON structure
8. WHEN I set validation rules THEN the system SHALL validate JSON structure
9. WHEN I move a node THEN the system SHALL prevent circular references
10. WHEN I delete a node THEN the system SHALL check for references in configurations

---

### Requirement 6: Search and Filter

**User Story:** As a data entry administrator, I want to search and filter the attribute tree, so that I can quickly find specific nodes in large hierarchies.

#### Acceptance Criteria

1. WHEN I enter a search term THEN the tree SHALL filter to show only matching nodes and their ancestors
2. WHEN I search THEN matches SHALL be highlighted in the tree
3. WHEN I filter by node_type THEN only nodes of that type SHALL be shown
4. WHEN I filter by price range THEN only nodes with prices in that range SHALL be shown
5. WHEN I clear filters THEN the full tree SHALL be restored
6. WHEN I search THEN the search SHALL be case-insensitive
7. WHEN I search THEN partial matches SHALL be included
8. WHEN I search THEN the ltree_path SHALL be searchable

---

### Requirement 7: Export and Import

**User Story:** As a data entry administrator, I want to export and import attribute trees, so that I can backup data, share configurations, or migrate between environments.

#### Acceptance Criteria

1. WHEN I export a tree THEN I SHALL be able to choose format (JSON, YAML, CSV, ASCII)
2. WHEN I export THEN all node properties SHALL be included
3. WHEN I export THEN the hierarchical structure SHALL be preserved
4. WHEN I import THEN the system SHALL validate the format
5. WHEN I import THEN the system SHALL preview changes before applying
6. WHEN I import THEN I SHALL choose to merge or replace existing data
7. WHEN I import THEN the system SHALL handle conflicts (duplicate names, etc.)
8. WHEN I export THEN I SHALL be able to export a subtree (not just the full tree)

---

### Requirement 8: Audit Trail

**User Story:** As a system administrator, I want to see who made changes to the attribute hierarchy and when, so that I can track modifications and troubleshoot issues.

#### Acceptance Criteria

1. WHEN a node is created THEN the system SHALL log who created it and when
2. WHEN a node is updated THEN the system SHALL log who updated it, when, and what changed
3. WHEN a node is deleted THEN the system SHALL log who deleted it and when
4. WHEN I view audit logs THEN I SHALL see a chronological list of changes
5. WHEN I view audit logs THEN I SHALL be able to filter by user, date range, and node
6. WHEN I view audit logs THEN I SHALL see before/after values for updates
7. WHEN I view audit logs THEN I SHALL be able to export them

---

### Requirement 9: Batch Operations

**User Story:** As a data entry administrator, I want to perform batch operations on multiple nodes, so that I can make bulk changes efficiently.

#### Acceptance Criteria

1. WHEN I select multiple nodes THEN I SHALL be able to delete them all at once
2. WHEN I select multiple nodes THEN I SHALL be able to move them to a new parent
3. WHEN I select multiple nodes THEN I SHALL be able to update common properties (e.g., set all to inactive)
4. WHEN I select multiple nodes THEN I SHALL be able to apply a price adjustment (e.g., increase all by 10%)
5. WHEN I perform batch operations THEN the system SHALL show a preview of changes
6. WHEN I perform batch operations THEN I SHALL be able to confirm or cancel
7. WHEN batch operations fail THEN the system SHALL rollback all changes

---

### Requirement 10: Comprehensive Testing of Insertion Functions

**User Story:** As a developer, I want comprehensive tests for the hierarchy insertion functions, so that I can verify they work correctly and catch regressions.

#### Acceptance Criteria

1. WHEN I run tests THEN there SHALL be tests for creating a manufacturing type
2. WHEN I run tests THEN there SHALL be tests for creating root nodes (no parent)
3. WHEN I run tests THEN there SHALL be tests for creating child nodes with correct ltree_path
4. WHEN I run tests THEN there SHALL be tests for creating nodes with pricing information
5. WHEN I run tests THEN there SHALL be tests for creating nodes with weight impact
6. WHEN I run tests THEN there SHALL be tests for creating nodes with technical properties
7. WHEN I run tests THEN there SHALL be tests for batch creation from dictionary
8. WHEN I run tests THEN there SHALL be tests for validation (invalid parent, circular references)
9. WHEN I run tests THEN there SHALL be tests for ltree_path calculation at different depths
10. WHEN I run tests THEN there SHALL be tests for querying descendants and ancestors
11. WHEN I run tests THEN there SHALL be integration tests that create a complete hierarchy (like the uPVC example)
12. WHEN tests fail THEN they SHALL provide clear error messages

**Example Test Suite:**
```python
# tests/integration/test_hierarchy_builder.py

class TestHierarchyBuilder:
    """Test suite for hierarchy builder service."""
    
    async def test_create_manufacturing_type(self, db_session):
        """Test creating a manufacturing type."""
        builder = HierarchyBuilderService(db_session)
        
        mfg_type = await builder.create_manufacturing_type(
            name="Test Window",
            base_price=100.00,
            base_weight=5.0
        )
        
        assert mfg_type.id is not None
        assert mfg_type.name == "Test Window"
        assert mfg_type.base_price == 100.00
    
    async def test_create_root_node(self, db_session, sample_manufacturing_type):
        """Test creating a root node."""
        builder = HierarchyBuilderService(db_session)
        
        root = await builder.create_node(
            manufacturing_type_id=sample_manufacturing_type.id,
            name="Frame Material",
            node_type="category"
        )
        
        assert root.ltree_path == "frame_material"
        assert root.depth == 0
        assert root.parent_node_id is None
    
    async def test_create_child_node(self, db_session, sample_root_node):
        """Test creating a child node with correct ltree_path."""
        builder = HierarchyBuilderService(db_session)
        
        child = await builder.create_node(
            manufacturing_type_id=sample_root_node.manufacturing_type_id,
            name="Material Type",
            node_type="attribute",
            parent=sample_root_node
        )
        
        assert child.ltree_path == "frame_material.material_type"
        assert child.depth == 1
        assert child.parent_node_id == sample_root_node.id
    
    async def test_create_node_with_pricing(self, db_session, sample_parent_node):
        """Test creating a node with pricing information."""
        builder = HierarchyBuilderService(db_session)
        
        node = await builder.create_node(
            manufacturing_type_id=sample_parent_node.manufacturing_type_id,
            name="Aluminum",
            node_type="option",
            price_impact_type="fixed",
            price_impact_value=50.00,
            weight_impact=1.8,
            parent=sample_parent_node
        )
        
        assert node.price_impact_type == "fixed"
        assert node.price_impact_value == 50.00
        assert node.weight_impact == 1.8
    
    async def test_create_hierarchy_from_dict(self, db_session, sample_manufacturing_type):
        """Test batch creation from dictionary."""
        builder = HierarchyBuilderService(db_session)
        
        hierarchy = {
            "name": "Glass Type",
            "node_type": "category",
            "children": [
                {
                    "name": "Configuration",
                    "node_type": "attribute",
                    "children": [
                        {"name": "Single Pane", "node_type": "option", "price_impact_value": 0},
                        {"name": "Double Pane", "node_type": "option", "price_impact_value": 80}
                    ]
                }
            ]
        }
        
        root = await builder.create_hierarchy_from_dict(
            manufacturing_type_id=sample_manufacturing_type.id,
            hierarchy_data=hierarchy
        )
        
        # Verify structure
        assert root.name == "Glass Type"
        children = await builder.get_children(root.id)
        assert len(children) == 1
        assert children[0].name == "Configuration"
        
        grandchildren = await builder.get_children(children[0].id)
        assert len(grandchildren) == 2
        assert grandchildren[0].name == "Single Pane"
        assert grandchildren[1].name == "Double Pane"
    
    async def test_complete_upvc_hierarchy(self, db_session):
        """Test creating the complete uPVC hierarchy from the example."""
        builder = HierarchyBuilderService(db_session)
        
        # Create manufacturing type
        window = await builder.create_manufacturing_type(
            name="Casement Window",
            base_price=150.00,
            base_weight=10.0
        )
        
        # Create Material category
        material = await builder.create_node(
            manufacturing_type_id=window.id,
            name="Material",
            node_type="category"
        )
        
        # Create uPVC branch
        upvc = await builder.create_node(
            manufacturing_type_id=window.id,
            name="uPVC",
            node_type="category",
            parent=material
        )
        
        system = await builder.create_node(
            manufacturing_type_id=window.id,
            name="System",
            node_type="category",
            parent=upvc
        )
        
        aluplast = await builder.create_node(
            manufacturing_type_id=window.id,
            name="Aluplast",
            node_type="option",
            parent=system
        )
        
        profile = await builder.create_node(
            manufacturing_type_id=window.id,
            name="Profile",
            node_type="attribute",
            parent=aluplast
        )
        
        ideal_4000 = await builder.create_node(
            manufacturing_type_id=window.id,
            name="IDEAL 4000",
            node_type="option",
            price_impact_type="fixed",
            price_impact_value=50.00,
            parent=profile
        )
        
        color_decor = await builder.create_node(
            manufacturing_type_id=window.id,
            name="Color & Decor",
            node_type="attribute",
            parent=ideal_4000
        )
        
        # Create color options
        colors = [
            ("Standard colors", 0),
            ("Special colors", 25.00),
            ("Aludec collection", 35.00),
            ("Woodec collection", 40.00)
        ]
        
        for color_name, price in colors:
            await builder.create_node(
                manufacturing_type_id=window.id,
                name=color_name,
                node_type="option",
                price_impact_type="fixed",
                price_impact_value=price,
                parent=color_decor
            )
        
        # Verify the hierarchy
        descendants = await builder.get_descendants(material.id)
        assert len(descendants) > 10  # Should have many nodes
        
        # Verify ltree paths
        assert ideal_4000.ltree_path == "material.upvc.system.aluplast.profile.ideal_4000"
        assert ideal_4000.depth == 5
```

### Requirement 11: Performance for Large Hierarchies

**User Story:** As a data entry administrator, I want the dashboard to remain responsive even with large attribute trees (1000+ nodes), so that I can work efficiently.

#### Acceptance Criteria

1. WHEN loading a tree with 1000+ nodes THEN the initial load SHALL complete in < 2 seconds
2. WHEN expanding a node THEN children SHALL load in < 500ms
3. WHEN searching THEN results SHALL appear in < 1 second
4. WHEN the tree is large THEN the system SHALL use lazy loading (load children on demand)
5. WHEN the tree is large THEN the system SHALL use virtual scrolling for the tree view
6. WHEN the tree is large THEN the system SHALL cache loaded nodes
7. WHEN the tree is large THEN the system SHALL provide pagination for search results

---

## Non-Functional Requirements

### Usability
- Dashboard SHALL be intuitive for backend administrators
- Dashboard SHALL work on desktop browsers (Chrome, Firefox, Safari, Edge)
- Dashboard SHALL be server-rendered using Jinja2 templates (no separate frontend build)
- Dashboard SHALL provide helpful error messages via flash messages or form validation
- Dashboard SHALL be accessible only to authenticated users with admin/superuser roles

### Performance
- Tree visualization SHALL render in < 2 seconds for trees with 1000 nodes
- Bulk import SHALL process 500 nodes in < 10 seconds
- Search SHALL return results in < 1 second

### Security
- Only authenticated users with "superuser" or "data_entry" roles SHALL access the dashboard
- All operations SHALL be logged for audit purposes
- Bulk import SHALL validate data to prevent SQL injection or XSS attacks

### Reliability
- Bulk import SHALL be transactional (all-or-nothing)
- System SHALL handle concurrent edits gracefully
- System SHALL prevent data corruption from invalid operations

## Success Criteria

1. Administrator can import a complex hierarchy (100+ nodes) in < 5 minutes
2. Administrator can visualize the hierarchy as an ASCII tree
3. Administrator can create, edit, and delete nodes through the dashboard
4. Administrator can search and filter the tree efficiently
5. System validates all operations and prevents invalid data
6. Dashboard remains responsive with 1000+ node trees
7. All operations are logged for audit purposes

## Out of Scope (Future Enhancements)

- Drag-and-drop reordering in the tree view (manual move only)
- Real-time collaboration (multiple users editing simultaneously)
- Version control for the hierarchy (rollback to previous versions)
- AI-powered suggestions for node creation
- Mobile app for hierarchy management
- Integration with external product catalogs
