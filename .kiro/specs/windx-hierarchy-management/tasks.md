# Implementation Tasks: Windx Hierarchical Data Management System

## Overview

This task list implements the Windx Hierarchical Data Management System, providing tools for inserting, managing, and visualizing hierarchical attribute data.

**Current Status**: 
- ✅ Core models, repositories, and schemas are implemented
- ✅ AttributeNodeRepository has LTREE support and tree building methods
- ✅ AttributeNodeTree Pydantic model exists for JSON serialization
- ⏳ HierarchyBuilderService needs to be created
- ⏳ Admin dashboard templates and routes need to be created
- ⏳ ASCII tree visualization needs to be implemented

## Task List

- [x] 1. Core HierarchyBuilderService Implementation





  - Create service for programmatic hierarchy management
  - _Requirements: 1.1-1.13_
- [x] 1.1 Create HierarchyBuilderService class in `app/services/hierarchy_builder.py`


  - Inherit from BaseService
  - Initialize with AttributeNodeRepository and ManufacturingTypeRepository
  - Note before you continue you can create a dataclass or pydnatic class to handle all these paramters `     manufacturing_type_id: int,

        name: str,

        node_type: str,

        parent_node_id: int | None = None,

        data_type: str | None = None,

        display_condition: dict | None = None,

        validation_rules: dict | None = None,

        required: bool = False,

        price_impact_type: str = "fixed",

        price_impact_value: Decimal | None = None,

        price_formula: str | None = None,

        weight_impact: Decimal = Decimal("0"),

        weight_formula: str | None = None,

        technical_property_type: str | None = None,

        technical_impact_formula: str | None = None,

        sort_order: int = 0,

        ui_component: str | None = None,

        description: str | None = None,

        help_text: str | None = None,`

you name it like Node and handle common paramters between other functions to reduce duplication and ensure consistency, do you understand what i mean 
not only for this function but common global like AttributeNodeCreate had almost same params, so you can like make a base dataclass NodeParamas
  - _Requirements: 1.9_
- [x] 1.2 Implement `_calculate_ltree_path()` helper method


  - Sanitize node name (lowercase, replace spaces with underscores, replace & with and)
  - Handle root nodes (no parent) vs child nodes (append to parent path)
  - _Requirements: 1.1_


- [ ] 1.3 Implement `_calculate_depth()` helper method
  - Return 0 for root nodes


  - Return parent.depth + 1 for child nodes
  - _Requirements: 1.2_
- [x] 1.4 Implement `create_manufacturing_type()` method


  - Accept name, description, base_category, base_price, base_weight
  - Use ManufacturingTypeRepository to create
  - Return created instance
  - _Requirements: 1.1_
- [x] 1.5 Implement `create_node()` method with automatic path/depth




  - Accept manufacturing_type_id, name, node_type, parent_node_id, and all attribute fields
  - If parent_node_id provided, fetch parent node
  - Calculate ltree_path using _calculate_ltree_path()
  - Calculate depth using _calculate_depth()
  - Create AttributeNodeCreate schema with calculated fields
  - Use AttributeNodeRepository.create() to persist
  - Return created node
  - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 1.6_



- [x] 2. Node Validation and Error Handling



  - Add validation to prevent invalid hierarchies
  - _Requirements: 5.1-5.10_
- [x] 2.1 Add validation for parent node existence in `create_node()`


  - Check parent exists if parent_id provided
  - Raise NotFoundException if parent not found
  - _Requirements: 1.3, 5.1_
- [x] 2.2 Add validation for manufacturing type existence


  - Check manufacturing_type exists
  - Raise NotFoundException if not found
  - _Requirements: 5.2_
- [x] 2.3 Add circular reference detection


  - Use AttributeNodeRepository.would_create_cycle() when moving nodes
  - Raise ValidationException if cycle detected
  - _Requirements: 5.9_
- [x] 2.4 Add duplicate name detection at same level


  - Query for siblings with same name
  - Raise ConflictException if duplicate found
  - _Requirements: 5.4_

- [x] 2.5 Add node_type enum validation

  - Validate against allowed values (already in schema)
  - Raise ValidationException for invalid types
  - _Requirements: 5.4_

- [x] 3. Batch Hierarchy Creation





  - Enable creating entire hierarchies from nested dictionaries
  - _Requirements: 1.7, 1.8_
- [x] 3.1 Implement `create_hierarchy_from_dict()` method


  - Accept manufacturing_type_id, hierarchy_data dict, optional parent
  - Extract node data from dict
  - Create node using create_node()
  - Return root node
  - _Requirements: 1.7_
- [x] 3.2 Add recursive processing for nested children

  - Check for 'children' key in hierarchy_data
  - Recursively call create_hierarchy_from_dict() for each child
  - Pass created node as parent
  - _Requirements: 1.7_
- [x] 3.3 Add transaction handling (all-or-nothing)

  - Wrap entire operation in try/except
  - Rollback on any error
  - Commit only if all nodes created successfully
  - _Requirements: 1.8_
- [x] 3.4 Add error handling for batch operations

  - Catch and re-raise exceptions with context
  - Include which node failed in error message
  - _Requirements: 1.8_

- [x] 4. Pydantic Serialization for Tree Visualization
  - Enable JSON export of hierarchies
  - _Requirements: 1.11, 1.12, 1.13, 3.10-3.13_
- [x] 4.1 AttributeNodeTree Pydantic model already exists
  - Located in `app/schemas/attribute_node.py`
  - Has children field for nested structure
  - _Requirements: 1.11_

- [x] 4.2 Implement `get_tree_as_pydantic()` or "pydantify" <for simplicity> method in HierarchyBuilderService




  - Accept manufacturing_type_id and optional root_node_id
  - Use AttributeNodeRepository.get_by_manufacturing_type() to get all nodes
  - Use AttributeNodeRepository.build_tree() to create hierarchy
  - Return list of AttributeNodeTree
  - _Requirements: 1.11, 1.12_
- [x] 4.3 Recursive children loading already implemented
  - AttributeNodeRepository.build_tree() handles this
  - _Requirements: 1.12_

- [x] 5. ASCII Tree Visualization




  - Generate human-readable tree representations
  - Task 4.2 has been finished and with working function pydantify, which mean it could be easy to use this function to generate the visualization
  - _Requirements: 3.1-3.13_
- [x] 5.1 Implement `generate_ascii_tree()` or `asciify` <simple better name> method in HierarchyBuilderService


  - Accept manufacturing_type_id and optional root_node_id
  - Get all nodes for manufacturing type
  - Build tree structure
  - Call _generate_ascii_tree_recursive()
  - Return formatted string
  - _Requirements: 3.1, 3.2_
- [x] 5.2 Implement `_generate_ascii_tree_recursive()` helper

  - Accept node, children_map, prefix, is_last
  - Use box-drawing characters (├──, └──, │)
  - Format current node with connector
  - Recursively process children
  - Return formatted string
  - _Requirements: 3.2, 3.3_
- [x] 5.3 Add price display formatting

  - Show price_impact_value as [+$50.00] if present
  - Format with 2 decimal places
  - _Requirements: 3.4_
- [x] 5.4 Add node type and depth indicators

  - Show node_type in brackets [category], [option]
  - Include depth information if helpful
  - _Requirements: 3.3_

- [x] 6. Backend Admin Dashboard - Jinja2 Templates





  - Create server-rendered HTML interface
  - _Requirements: 2.1-2.10, 4.1-4.10_
- [x] 6.1 Create `app/templates/admin/base.html.jinja` template


  - Base layout with navigation
  - Include Bootstrap 5 CSS CDN
  - Define blocks for title, content, scripts
  - Add navigation menu with links to hierarchy dashboard
  - _Requirements: 2.2, 2.3_
- [x] 6.2 Create `app/templates/admin/hierarchy_dashboard.html.jinja` template


  - Extend base.html.jinja
  - Manufacturing type selector dropdown (form with GET method)
  - Two-column layout: left for tree view, right for ASCII visualization
  - Display selected manufacturing type name
  - Show "Create Node" button
  - _Requirements: 2.1, 2.4, 2.5, 4.1-4.10_

- [x] 6.3 Create `app/templates/admin/node_form.html.jinja` template

  - Extend base.html.jinja
  - Form for creating/editing nodes (POST method)
  - Fields: name, node_type (dropdown), parent_node_id (dropdown), data_type (dropdown)
  - Price fields: price_impact_type (dropdown), price_impact_value (number)
  - Weight field: weight_impact (number)
  - Technical fields: technical_property_type (text), technical_impact_formula (textarea)
  - UI fields: ui_component (dropdown), description (textarea), help_text (textarea)
  - Sort order field (number)
  - Submit and cancel buttons
  - Pre-fill form if editing existing node
  - _Requirements: 4.2-4.9_
- [x] 6.4 Create `app/templates/admin/components/tree_view.html.jinja` component


  - Recursive tree rendering with <ul>/<li> structure
  - Show node name, type badge, price impact
  - Edit link: /admin/hierarchy/node/{id}/edit
  - Delete button with confirmation (POST to /admin/hierarchy/node/{id}/delete)
  - Use Jinja2 recursive macro for nested children
  - Add CSS classes for styling (collapsible tree)
  - _Requirements: 2.5, 2.6_
- [x] 6.5 Create `app/templates/admin/components/ascii_tree.html.jinja` component


  - Display ASCII tree in <pre> tag with monospace font
  - Preserve formatting and box-drawing characters
  - Add CSS for proper spacing and readability
  - _Requirements: 3.1-3.9_

- [x] 6.6 Create `app/templates/admin/components/diagram_tree.html.jinja` component


  - Display ASCII tree in <pre> tag with monospace font
  - Preserve formatting and box-drawing characters
  - Add CSS for proper spacing and readability
  - _Requirements: 11.1-11.9_


- [x] 7. Backend Admin Dashboard - FastAPI Routes




  - Create API endpoints for dashboard
  - _Requirements: 2.1-2.10, 4.1-4.10_
- [x] 7.1 Create `app/api/v1/endpoints/admin_hierarchy.py` router file


  - Import FastAPI (APIRouter, Request, Form, status)
  - Import HTMLResponse, RedirectResponse
  - Import Jinja2Templates (configure with app/templates directory)
  - Import dependencies (CurrentSuperuser from app.api.types)
  - Import HierarchyBuilderService
  - Import ManufacturingTypeRepository, AttributeNodeRepository
  - Create router with prefix="" (will be added in router.py)
  - _Requirements: 2.1_
- [x] 7.2 Implement GET `/admin/hierarchy` (dashboard view)

  - Dependency: current_superuser: CurrentSuperuser
  - Accept optional manufacturing_type_id query param (int | None)
  - Get all manufacturing types using ManufacturingTypeRepository
  - If manufacturing_type_id provided:
    - Get attribute tree using HierarchyBuilderService.get_tree_as_pydantic()
    - Get ASCII tree using HierarchyBuilderService.generate_ascii_tree()
    - Convert tree to dict for template
  - Render hierarchy_dashboard.html.jinja template with context
  - _Requirements: 2.1, 2.4, 2.5_


- [ ] 7.3 Implement GET `/admin/hierarchy/node/create` (create form)
  - Dependency: current_superuser: CurrentSuperuser
  - Accept manufacturing_type_id (required) and optional parent_id query params
  - Get manufacturing type by ID
  - If parent_id provided, get parent node
  - Get all nodes for manufacturing type (for parent selector)


  - Render node_form.html.jinja template with context
  - _Requirements: 4.1, 4.2_
- [ ] 7.4 Implement POST `/admin/hierarchy/node/save` (create/update)
  - Dependency: current_superuser: CurrentSuperuser
  - Accept form data using Form(...) for each field
  - If node_id present (hidden field), update existing node


  - Otherwise, create new node using HierarchyBuilderService.create_node()
  - Handle validation errors and display in form
  - Redirect to /admin/hierarchy?manufacturing_type_id={id} with success message
  - _Requirements: 4.3, 4.4, 2.7, 2.8_
- [x] 7.5 Implement GET `/admin/hierarchy/node/{node_id}/edit` (edit form)


  - Dependency: current_superuser: CurrentSuperuser
  - Get node by ID using AttributeNodeRepository
  - Get all nodes for same manufacturing type (for parent selector, excluding node and descendants)
  - Pre-fill form with current values
  - Render node_form.html.jinja template with node data
  - _Requirements: 2.6, 4.5_


- [ ] 7.6 Implement POST `/admin/hierarchy/node/{node_id}/delete` (delete)
  - Dependency: current_superuser: CurrentSuperuser


  - Get node by ID
  - Check for children using AttributeNodeRepository.get_children()
  - If has children, return error (cannot delete node with children)
  - Otherwise, delete node using AttributeNodeRepository.delete()
  - Redirect to /admin/hierarchy?manufacturing_type_id={id} with success message
  - _Requirements: 2.9_
- [ ] 7.7 Add flash message support
  - Use query parameters for success/error messages
  - Display messages in templates using Bootstrap alerts
  - _Requirements: 2.10_
- [ ] 7.8 Register admin_hierarchy router in `app/api/v1/router.py`
  - Import admin_hierarchy from endpoints
  - Include router with prefix="/admin/hierarchy" and tags=["Admin Hierarchy"]

- [ ] 8. Dashboard Form Handling and Validation
  - Handle form submissions and validation
  - _Requirements: 4.2-4.9, 5.1-5.10_
- [ ] 8.1 Implement form data handling in POST routes
  - Use Form(...) dependencies for each form field
  - Create AttributeNodeCreate or AttributeNodeUpdate schema from form data
  - Handle Pydantic validation errors
  - Display validation errors in template
  - _Requirements: 4.2, 4.4_
- [ ] 8.2 Add parent node selector logic
  - Get all nodes for same manufacturing type
  - If editing, exclude current node and its descendants using AttributeNodeRepository.get_descendants()
  - Format dropdown options with hierarchical path (e.g., "Frame > Material > Aluminum")
  - _Requirements: 4.5, 5.9_
- [ ] 8.3 Add node type and data type dropdowns
  - Node types: category, attribute, option, component, technical_spec
  - Data types: string, number, boolean, formula, dimension, selection
  - Price impact types: fixed, percentage, formula
  - UI components: dropdown, radio, checkbox, slider, input
  - _Requirements: 5.4, 5.5_

- [ ] 9. Integration Testing - Complete uPVC Hierarchy
  - Test creating complex real-world hierarchy
  - _Requirements: 10.1-10.12_
- [ ] 9.1 Create test file `tests/integration/test_hierarchy_builder.py`
  - Import HierarchyBuilderService
  - Import ManufacturingTypeRepository, AttributeNodeRepository
  - Create fixtures for db_session
  - _Requirements: 10.1_
- [ ] 9.2 Implement `test_create_manufacturing_type()`
  - Create "Casement Window" manufacturing type using HierarchyBuilderService
  - Verify base_price and base_weight are set
  - _Requirements: 10.1_
- [ ] 9.3 Implement `test_create_root_node()`
  - Create root category node "Material"
  - Verify ltree_path is sanitized name
  - Verify depth is 0
  - Verify parent_node_id is None
  - _Requirements: 10.2, 10.9_
- [ ] 9.4 Implement `test_create_child_node()`
  - Create child node "uPVC" under "Material"
  - Verify ltree_path is "material.upvc"
  - Verify depth is 1
  - Verify parent_node_id is set correctly
  - _Requirements: 10.3, 10.9_
- [ ] 9.5 Implement `test_create_complete_upvc_hierarchy()`
  - Create full hierarchy: Material → uPVC → System → Aluplast → Profile → IDEAL 4000 → Color & Decor
  - Create color options with price impacts
  - Verify all ltree_paths are correct
  - Verify all depths are correct
  - _Requirements: 10.4, 10.5, 10.6, 10.9_
- [ ] 9.6 Implement `test_get_descendants()`
  - Create hierarchy with multiple levels
  - Use AttributeNodeRepository.get_descendants() on root node
  - Verify all descendants are returned
  - _Requirements: 10.10_
- [ ] 9.7 Implement `test_create_hierarchy_from_dict()`
  - Create nested dictionary structure
  - Use HierarchyBuilderService.create_hierarchy_from_dict()
  - Verify all nodes are created with correct relationships
  - _Requirements: 10.11_
- [ ] 9.8 Implement `test_batch_creation_rollback()`
  - Test that batch creation rolls back on error
  - Create hierarchy with invalid node in middle
  - Verify no nodes are created
  - _Requirements: 10.12_

- [ ] 10. Documentation and Examples
  - Document the hierarchy management system
  - _Requirements: 11.1-11.5_
- [ ] 10.1 Add comprehensive docstrings to HierarchyBuilderService
  - Document all public methods with parameters, return values, exceptions
  - Include usage examples in docstrings
  - Follow Google-style docstring format
  - _Requirements: 11.1, 11.4_
- [ ] 10.2 Create example script `examples/hierarchy_insertion.py`
  - Import HierarchyBuilderService and required dependencies
  - Show how to create manufacturing type
  - Show how to create nodes with automatic path calculation
  - Show how to create hierarchy from dictionary
  - Show how to get tree as JSON
  - Include detailed comments explaining each step
  - _Requirements: 11.2_
- [ ] 10.3 Create `docs/HIERARCHY_ADMIN_DASHBOARD.md`
  - Document how to access dashboard (/admin/hierarchy)
  - Explain authentication requirements (superuser only)
  - Document each feature:
    - Selecting manufacturing type
    - Viewing attribute tree
    - Creating new nodes
    - Editing existing nodes
    - Deleting nodes
    - Viewing ASCII tree visualization
  - Include example workflows
  - _Requirements: 11.3_
- [ ] 10.4 Update main `README.md`
  - Add "Hierarchy Management" section
  - Explain HierarchyBuilderService purpose
  - Link to HIERARCHY_ADMIN_DASHBOARD.md
  - Mention key features (automatic path calculation, tree visualization)
  - _Requirements: 11.5_


- [x] 11. Tree Visualization




  - Generate human-readable **graphical tree representations** 
  - Can leverage `pydantify` output from Task 4.2 for node information  
  - _Requirements: 3.1–3.13_
    
- [x] 11.1 Implement `generate_tree_plot()` or `plot_tree` method in `HierarchyBuilderService`    


    - Accept `manufacturing_type_id` and optional `root_node_id` 
    - Retrieve all nodes for the given manufacturing type  
    - Build hierarchical tree structure (parent → children map)
    - Call `_plot_tree_recursive()` or equivalent to draw the nodes   
    - Return **Matplotlib figure object**   
    -   _Requirements: 3.1, 3.2_
        
- [x] 11.2 Implement `_plot_tree_recursive()` helper (or plotting logic)

    - Use **Matplotlib** for plotting nodes and edges
    - Optionally, if **Graphviz** is available on the platform:
      - Use **NetworkX** + `pygraphviz` layout for nicer automatic tree positioning    
    - Draw node labels with `node_type` and `price_impact_value`  
    - Recursively plot children nodes according to hierarchy  
    - Return the Matplotlib figure object   
    -   _Requirements: 3.2, 3.3_
        
- [x] 11.3 Add node data formatting on plot

    
    -   Display `price_impact_value` as `[+$50.00]` if present
        
    -   Include `node_type` in brackets `[category]`, `[option]`
        
    -   Optional: show depth/level indicators for clarity
        
    -   _Requirements: 3.3, 3.4_
        



## Notes

- **Foundation Already Complete**: 
  - ✅ Models: AttributeNode, ManufacturingType exist in `app/models/`
  - ✅ Repositories: AttributeNodeRepository with LTREE support in `app/repositories/`
  - ✅ Schemas: AttributeNodeTree for JSON serialization in `app/schemas/`
  - ✅ Repository has `build_tree()`, `get_descendants()`, `would_create_cycle()` methods
- **Focus on Service Layer**: HierarchyBuilderService is the main new component
- **Admin Dashboard**: Server-rendered Jinja2 templates (`.jinja` extension), not a separate frontend
- **Template Location**: `app/templates/admin/` directory
- **Testing**: Integration tests more important than unit tests for this feature
- **Use `.venv\scripts\python`** for running tests on Windows
- **LTREE paths**: Automatically calculated by HierarchyBuilderService (sanitize name, append to parent)
- **Authentication**: All admin routes require superuser access (use CurrentSuperuser dependency)
- **Flash Messages**: Use query parameters for success/error messages (e.g., `?success=Node created`)
- **Form Handling**: Use FastAPI Form(...) dependencies, not Pydantic models for form data

## Success Criteria

- [ ] HierarchyBuilderService can create nodes with automatic path calculation
- [ ] Batch import from dictionary works for nested hierarchies
- [ ] Pydantic serialization produces valid JSON for visualization (using existing build_tree method)
- [ ] ASCII tree displays correctly with box-drawing characters
- [ ] Admin dashboard allows CRUD operations on nodes
- [ ] Complete uPVC hierarchy can be created and visualized
- [ ] All integration tests pass
- [ ] Documentation is complete and clear

## Implementation Priority

1. **Phase 1**: HierarchyBuilderService (Tasks 1-3) - Core functionality
2. **Phase 2**: ASCII Tree Visualization (Task 5) - Visualization feature
3. **Phase 3**: Admin Dashboard Templates (Task 6) - UI templates
4. **Phase 4**: Admin Dashboard Routes (Tasks 7-8) - API endpoints
5. **Phase 5**: Integration Testing (Task 9) - Validation
6. **Phase 6**: Documentation (Task 10) - User guides

- [ ]* 11.4 Optional enhancements
    
  - Customize node colors, shapes, or sizes based on type or price impact
        
  - Improve layout readability for large hierarchies    
  - Add interactive zoom/pan if using `matplotlib` with `mplcursors` or `plotly` backend
        
  - _Requirements: 3.5_
