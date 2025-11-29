# Tree Visualization

This document describes the tree visualization features of the Windx Hierarchy Management System.

## Overview

The HierarchyBuilderService provides multiple ways to visualize hierarchical attribute data:

1. **ASCII Tree** - Text-based tree using box-drawing characters
2. **Graphical Plot** - Visual tree diagram using Matplotlib
3. **JSON Export** - Pydantic-based serialization for custom visualizations

## ASCII Tree Visualization

Generate a text-based tree representation with box-drawing characters.

### Usage

```python
from app.services.hierarchy_builder import HierarchyBuilderService

service = HierarchyBuilderService(db_session)

# Generate ASCII tree for entire manufacturing type
ascii_tree = await service.asciify(manufacturing_type_id=1)
print(ascii_tree)

# Generate ASCII tree for subtree only
ascii_subtree = await service.asciify(
    manufacturing_type_id=1,
    root_node_id=42  # Start from specific node
)
print(ascii_subtree)
```

### Example Output

```
Frame Options [category]
├── Material Type [attribute]
│   ├── Aluminum [option] [+$50.00]
│   ├── Vinyl [option] [+$30.00]
│   └── Wood [option] [+$100.00]
└── Color [attribute]
    ├── White [option] [+$0.00]
    ├── Black [option] [+$25.00]
    └── Custom Color [option] [+$50.00]
```

### Features

- Box-drawing characters (├──, └──, │) for clear hierarchy
- Node type indicators in brackets `[category]`, `[option]`
- Price impacts displayed as `[+$50.00]`
- Depth-based indentation
- Supports subtree visualization

## Graphical Tree Plot

Generate a visual tree diagram using Matplotlib with automatic layout.

### Requirements

```bash
pip install matplotlib networkx
```

### Usage

```python
from app.services.hierarchy_builder import HierarchyBuilderService

service = HierarchyBuilderService(db_session)

# Generate tree plot
fig = await service.plot_tree(manufacturing_type_id=1)

# Save to file
fig.savefig('hierarchy_tree.png', dpi=300, bbox_inches='tight')

# Display in Jupyter notebook
import matplotlib.pyplot as plt
plt.show()

# Clean up
plt.close(fig)
```

### Subtree Plotting

```python
# Plot only a specific subtree
fig = await service.plot_tree(
    manufacturing_type_id=1,
    root_node_id=42  # Start from specific node
)
```

### Features

- **Automatic Layout**: Uses NetworkX for optimal node positioning
- **Color-Coded Nodes**: Different colors for each node type
  - Category: Peach (#FFE5B4)
  - Attribute: Light Blue (#B4D7FF)
  - Option: Light Green (#B4FFB4)
  - Component: Light Pink (#FFB4E5)
  - Technical Spec: Light Purple (#E5B4FF)
- **Node Labels**: Display name, type, and price impact
- **Hierarchical Edges**: Arrows show parent-child relationships
- **Legend**: Shows node type color mapping
- **High Resolution**: Supports DPI settings for print quality

### Layout Algorithms

The plotting system uses two layout strategies:

1. **NetworkX Layout** (preferred): Uses graphviz or spring layout for better positioning
2. **Manual Layout** (fallback): Recursive algorithm when NetworkX is unavailable

## JSON Export (Pydantic Serialization)

Export the tree structure as JSON for custom visualizations or API responses.

### Usage

```python
from app.services.hierarchy_builder import HierarchyBuilderService

service = HierarchyBuilderService(db_session)

# Get tree as Pydantic models
tree = await service.pydantify(manufacturing_type_id=1)

# Serialize to JSON
import json
tree_json = json.dumps([node.model_dump() for node in tree], indent=2)

# Use with visualization libraries (D3.js, Mermaid, etc.)
with open('tree_data.json', 'w') as f:
    f.write(tree_json)
```

### JSON Structure

```json
[
  {
    "id": 1,
    "name": "Frame Options",
    "node_type": "category",
    "ltree_path": "frame_options",
    "depth": 0,
    "price_impact_value": null,
    "children": [
      {
        "id": 2,
        "name": "Material Type",
        "node_type": "attribute",
        "ltree_path": "frame_options.material_type",
        "depth": 1,
        "children": [
          {
            "id": 3,
            "name": "Aluminum",
            "node_type": "option",
            "price_impact_value": "50.00",
            "ltree_path": "frame_options.material_type.aluminum",
            "depth": 2,
            "children": []
          }
        ]
      }
    ]
  }
]
```

### Features

- Complete node data including all attributes
- Nested structure preserves hierarchy
- Compatible with frontend visualization libraries
- Suitable for API responses

## Error Handling

All visualization methods handle errors gracefully:

```python
from app.core.exceptions import NotFoundException

try:
    fig = await service.plot_tree(manufacturing_type_id=999)
except NotFoundException as e:
    print(f"Error: {e}")
    # Output: Manufacturing type with id 999 not found

try:
    import matplotlib
except ImportError:
    print("matplotlib is required for tree plotting")
    print("Install it with: pip install matplotlib networkx")
```

## Performance Considerations

- **ASCII Trees**: Fast, suitable for large hierarchies
- **Graphical Plots**: Slower for very large trees (100+ nodes)
- **JSON Export**: Fast, efficient for API responses

### Recommendations

- Use ASCII for quick debugging and console output
- Use graphical plots for documentation and presentations
- Use JSON export for web applications and custom visualizations
- For large hierarchies (>100 nodes), consider plotting subtrees

## Examples

See `examples/tree_visualization_example.py` for a complete working example.

## API Integration

The visualization methods can be exposed via API endpoints:

```python
from fastapi import APIRouter, Depends
from app.services.hierarchy_builder import HierarchyBuilderService

router = APIRouter()

@router.get("/hierarchy/{type_id}/ascii")
async def get_ascii_tree(
    type_id: int,
    service: HierarchyBuilderService = Depends()
):
    """Get ASCII tree representation."""
    return {"tree": await service.asciify(manufacturing_type_id=type_id)}

@router.get("/hierarchy/{type_id}/json")
async def get_json_tree(
    type_id: int,
    service: HierarchyBuilderService = Depends()
):
    """Get JSON tree structure."""
    tree = await service.pydantify(manufacturing_type_id=type_id)
    return [node.model_dump() for node in tree]
```

## Troubleshooting

### Matplotlib Not Found

```bash
pip install matplotlib networkx
```

### Plot Layout Issues

If the automatic layout doesn't look good:

1. Try adjusting figure size in the code
2. Use subtree plotting for complex hierarchies
3. Consider manual layout adjustments

### Empty Tree

If visualization shows "No nodes found":

1. Verify manufacturing type ID is correct
2. Check that nodes exist for that type
3. Ensure database connection is working

## Future Enhancements

Potential improvements for tree visualization:

- Interactive plots with zoom/pan
- Export to SVG format
- Mermaid diagram generation
- D3.js integration for web
- Custom color schemes
- Node filtering options
- Search highlighting
