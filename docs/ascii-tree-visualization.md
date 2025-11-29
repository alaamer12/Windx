# ASCII Tree Visualization

## Overview

The ASCII Tree Visualization feature provides a human-readable text representation of hierarchical attribute trees using box-drawing characters. This makes it easy to visualize and understand complex product configuration hierarchies.

## Implementation

### Methods Added to HierarchyBuilderService

#### `asciify(manufacturing_type_id, root_node_id=None)`

Generates an ASCII tree representation of the hierarchy.

**Parameters:**
- `manufacturing_type_id` (int): The manufacturing type ID to visualize
- `root_node_id` (int, optional): Optional root node ID to visualize a subtree only

**Returns:**
- `str`: Formatted ASCII tree string

**Raises:**
- `NotFoundException`: If manufacturing type or root node not found

**Example Usage:**

```python
from app.services.hierarchy_builder import HierarchyBuilderService

service = HierarchyBuilderService(db_session)

# Generate full tree
tree_str = await service.asciify(manufacturing_type_id=1)
print(tree_str)

# Generate subtree starting from specific node
subtree_str = await service.asciify(
    manufacturing_type_id=1,
    root_node_id=42
)
print(subtree_str)
```

#### `_generate_ascii_tree_recursive(node, prefix="", is_last=True)`

Internal helper method that recursively builds the ASCII tree string.

**Parameters:**
- `node` (AttributeNodeTree): Current node to render
- `prefix` (str): Prefix string for indentation (accumulated from parents)
- `is_last` (bool): Whether this is the last child of its parent

**Returns:**
- `str`: Formatted ASCII tree string for this node and its descendants

## Features

### Box-Drawing Characters

The visualization uses Unicode box-drawing characters for a clean, professional appearance:

- `├──` - Branch connector (not last child)
- `└──` - Branch connector (last child)
- `│` - Vertical line (continuation)
- `    ` - Spaces (for completed branches)

### Node Type Indicators

Each node displays its type in brackets:

- `[category]` - Organizational grouping
- `[attribute]` - Configurable property
- `[option]` - Selectable choice
- `[component]` - Physical component
- `[technical_spec]` - Technical property

### Price Display

Nodes with price impacts show the amount formatted with 2 decimal places:

- `[+$50.00]` - Positive price impact
- Nodes with zero or null price don't show the indicator

### Example Output

```
Material [category]
├── uPVC [category]
│   ├── System [category]
│   │   ├── Aluplast [option]
│   │   │   └── Profile [attribute]
│   │   │       ├── IDEAL 4000 [option] [+$50.00]
│   │   │       │   └── Color & Decor [attribute]
│   │   │       │       ├── Standard colors [option]
│   │   │       │       └── Special colors [option] [+$25.00]
│   │   │       └── IDEAL 5000 [option] [+$75.00]
│   │   └── Kommerling [option]
│   └── Size [category]
└── Aluminium [category]
```

## Integration with Pydantic Serialization

The `asciify()` method leverages the existing `pydantify()` method to get the tree structure, ensuring consistency between JSON serialization and ASCII visualization.

**Workflow:**
1. `asciify()` calls `pydantify()` to get the tree as Pydantic models
2. Recursively processes each node with `_generate_ascii_tree_recursive()`
3. Builds the ASCII string with proper indentation and connectors
4. Returns the complete formatted tree

## Use Cases

### 1. Development and Debugging

Quickly visualize hierarchy structure during development:

```python
tree = await service.asciify(manufacturing_type_id=1)
print(tree)
```

### 2. Documentation

Include ASCII trees in documentation to show example hierarchies:

```python
# Generate tree for documentation
tree = await service.asciify(manufacturing_type_id=1)
with open("hierarchy-example.txt", "w") as f:
    f.write(tree)
```

### 3. Admin Dashboard

Display tree structure in admin interfaces (see Task 6 for dashboard implementation).

### 4. API Responses

Return ASCII representation in API responses for debugging:

```python
@router.get("/attribute-nodes/tree/ascii/{type_id}")
async def get_ascii_tree(type_id: int, db: AsyncSession = Depends(get_db)):
    service = HierarchyBuilderService(db)
    tree_str = await service.asciify(manufacturing_type_id=type_id)
    return {"tree": tree_str}
```

### 5. Testing and Validation

Verify hierarchy structure in tests:

```python
async def test_hierarchy_structure(db_session):
    service = HierarchyBuilderService(db_session)
    tree = await service.asciify(manufacturing_type_id=1)
    
    # Verify expected nodes are present
    assert "Frame Material [category]" in tree
    assert "Aluminum [option] [+$50.00]" in tree
```

## Performance Considerations

- **Efficient**: Uses existing `pydantify()` method which leverages repository's `build_tree()`
- **Memory**: Builds string in memory, suitable for trees up to ~1000 nodes
- **Caching**: Consider caching ASCII output for frequently accessed trees
- **Large Trees**: For very large trees (>1000 nodes), consider pagination or subtree visualization

## Testing

Comprehensive test coverage in `tests/integration/test_hierarchy_ascii_tree.py`:

- ✅ Simple hierarchy visualization
- ✅ Nested hierarchy with multiple levels
- ✅ Multiple branches at same level
- ✅ Price formatting (2 decimal places)
- ✅ Zero and null price handling
- ✅ Node type indicators
- ✅ Empty tree handling
- ✅ Subtree visualization
- ✅ Error handling (invalid IDs)
- ✅ Complex real-world hierarchy (uPVC example)

Run tests:

```bash
.venv\scripts\python -m pytest tests/integration/test_hierarchy_ascii_tree.py -v
```

## Future Enhancements

Potential improvements for future versions:

1. **Color Support**: Add ANSI color codes for terminal output
2. **Compact Mode**: Option to hide certain fields for more compact display
3. **Filtering**: Show only specific node types or price ranges
4. **Export Formats**: Support for Markdown, HTML, or other formats
5. **Interactive Mode**: Collapsible sections for large trees
6. **Depth Indicators**: Optional display of depth levels
7. **Path Display**: Show LTREE paths alongside node names

## Requirements Satisfied

This implementation satisfies the following requirements from the spec:

- ✅ **3.1**: Generate ASCII tree representation
- ✅ **3.2**: Use box-drawing characters (├──, └──, │)
- ✅ **3.3**: Display node names with their types
- ✅ **3.4**: Show pricing information inline [+$50.00]
- ✅ **3.13**: Maintain parent-child relationships in visualization

## Related Documentation

- [Hierarchy Builder Service](hierarchy-builder-service.md)
- [Pydantic Serialization](pydantic-serialization.md)
- [Admin Dashboard](HIERARCHY_ADMIN_DASHBOARD.md) (Task 6)
