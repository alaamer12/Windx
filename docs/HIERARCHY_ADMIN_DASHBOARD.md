# Hierarchy Admin Dashboard Documentation

## Overview

The Hierarchy Admin Dashboard is a server-rendered web interface for managing attribute hierarchies in the Windx product configuration system. It provides a user-friendly way to create, edit, and visualize hierarchical product attributes without writing code.

**Key Features:**
- Visual tree representation of attribute hierarchies
- Create and edit nodes with comprehensive forms
- Delete nodes with safety checks
- ASCII tree visualization
- Graphical tree diagram visualization
- Real-time validation and error handling
- Superuser-only access for security

**Access URL:** `/admin/hierarchy`

---

## Authentication Requirements

### Superuser Access Only

The Hierarchy Admin Dashboard requires **superuser** authentication. Regular users cannot access this interface.

**Why superuser only?**
- Attribute hierarchies define the structure of product configurations
- Changes affect all customers and configurations
- Incorrect modifications can break the system
- Only administrators should manage product structure

### How to Access

1. **Log in as superuser:**
   - Navigate to `/auth/login`
   - Enter superuser credentials
   - You will receive a JWT token

2. **Access the dashboard:**
   - Navigate to `/admin/hierarchy`
   - If not authenticated, you'll be redirected to login
   - If authenticated but not superuser, you'll see a 403 Forbidden error

### Creating a Superuser

If you don't have a superuser account, create one using the management script:

```bash
# Using the create_superuser script
python scripts/create_superuser.py

# Or using the management CLI
python manage.py create-superuser --email admin@example.com --username admin
```

---

## Dashboard Features

### 1. Manufacturing Type Selector

**Location:** Top of the dashboard

**Purpose:** Select which product type's hierarchy to view and manage

**How to use:**
1. Click the dropdown menu labeled "Select Manufacturing Type"
2. Choose a manufacturing type (e.g., "Casement Window", "Sliding Door")
3. The page will reload and display the attribute tree for that type

**What happens:**
- The attribute tree panel updates to show nodes for the selected type
- The ASCII visualization updates
- The diagram visualization updates
- The "Create Node" button becomes active

**Note:** You must select a manufacturing type before you can create or edit nodes.

---

### 2. Viewing the Attribute Tree

**Location:** Left panel of the dashboard

**Purpose:** Visual representation of the hierarchical attribute structure

**Features:**
- **Hierarchical Display:** Nodes are displayed in a nested tree structure
- **Node Information:** Each node shows:
  - Name
  - Type badge (category, attribute, option, etc.)
  - Price impact (if applicable)
  - Edit and Delete buttons
- **Collapsible Branches:** Click on parent nodes to expand/collapse children
- **Color Coding:** Different node types have different badge colors

**Node Type Badges:**
- **Category** (Blue): Organizational grouping
- **Attribute** (Green): Configurable property
- **Option** (Orange): Selectable choice
- **Component** (Purple): Physical component
- **Technical Spec** (Gray): Technical property

**Example Tree:**
```
Frame Material [category]
├── Material Type [attribute]
│   ├── Aluminum [option] [+$50.00]
│   ├── Vinyl [option] [+$30.00]
│   └── Wood [option] [+$100.00]
└── Frame Color [attribute]
    ├── White [option]
    └── Brown [option] [+$15.00]
```

---

### 3. Creating New Nodes

**Location:** "Create Node" button at the top of the tree panel

**Purpose:** Add new nodes to the attribute hierarchy

**Steps:**

1. **Click "Create Node" button**
   - You'll be taken to the node creation form
   - The form will be pre-populated with the selected manufacturing type

2. **Fill in required fields:**
   - **Node Name:** Display name for the node (e.g., "Aluminum", "Frame Material")
   - **Node Type:** Select from dropdown (category, attribute, option, component, technical_spec)
   - **Parent Node:** Select parent from dropdown (or leave empty for root node)

3. **Fill in optional fields:**
   - **Data Type:** Type of value this node stores (string, number, boolean, etc.)
   - **Price Impact Type:** How this node affects price (fixed, percentage, formula)
   - **Price Impact Value:** Dollar amount to add/subtract
   - **Weight Impact:** Kilograms to add to total weight
   - **Description:** Help text for users
   - **Help Text:** Additional guidance
   - **Sort Order:** Display order among siblings
   - **UI Component:** Type of UI control (dropdown, radio, checkbox, etc.)
   - **Required:** Whether this attribute must be selected
   - **Display Condition:** JSON rules for conditional display
   - **Validation Rules:** JSON rules for input validation

4. **Click "Save Node"**
   - The node will be created with automatic LTREE path calculation
   - You'll be redirected back to the dashboard
   - The new node will appear in the tree

**Validation:**
- Node name cannot be empty
- Node type must be valid
- Parent node must exist (if specified)
- Duplicate names at the same level are not allowed
- Price and weight values must be non-negative

**Example: Creating an Option Node**

```
Node Name: Aluminum
Node Type: option
Parent Node: Material Type
Data Type: string
Price Impact Type: fixed
Price Impact Value: 50.00
Weight Impact: 2.00
Description: Durable aluminum frame
Help Text: Best for coastal areas
UI Component: radio
Required: No
```

**Result:**
- LTREE Path: `frame_material.material_type.aluminum` (calculated automatically)
- Depth: 2 (calculated automatically)
- Price Impact: +$50.00
- Weight Impact: +2.00 kg

---

### 4. Editing Existing Nodes

**Location:** "Edit" button next to each node in the tree

**Purpose:** Modify existing node properties

**Steps:**

1. **Click "Edit" button** next to the node you want to modify
   - You'll be taken to the edit form
   - The form will be pre-filled with current values

2. **Modify fields** as needed
   - All fields can be changed except:
     - Manufacturing Type ID (fixed)
     - LTREE Path (recalculated automatically)
     - Depth (recalculated automatically)

3. **Click "Save Node"**
   - Changes will be saved
   - If you changed the parent, the LTREE path and depth will be recalculated
   - All descendants will have their paths updated automatically
   - You'll be redirected back to the dashboard

**Important Notes:**
- **Changing Parent:** If you change the parent node, the entire subtree will be moved
- **Path Recalculation:** LTREE paths are automatically recalculated when parent changes
- **Circular References:** The system prevents you from creating circular references (e.g., making a node its own ancestor)

**Example: Editing Price Impact**

Original:
```
Aluminum [option] [+$50.00]
```

Edit:
```
Price Impact Value: 55.00
```

Result:
```
Aluminum [option] [+$55.00]
```

---

### 5. Deleting Nodes

**Location:** "Delete" button next to each node in the tree

**Purpose:** Remove nodes from the hierarchy

**Steps:**

1. **Click "Delete" button** next to the node you want to remove
   - A confirmation dialog will appear
   - The dialog shows the node name and warns about consequences

2. **Confirm deletion**
   - Click "Confirm" to proceed
   - Click "Cancel" to abort

3. **Deletion occurs**
   - The node and all its descendants are permanently deleted
   - You'll be redirected back to the dashboard
   - The tree will update to reflect the deletion

**Safety Checks:**
- **Confirmation Required:** You must confirm before deletion
- **Cascade Delete:** All descendants are deleted with the parent
- **Warning Message:** The system warns you if the node has children
- **No Undo:** Deletion is permanent and cannot be undone

**Example: Deleting a Node with Children**

Before deletion:
```
Material Type [attribute]
├── Aluminum [option]
├── Vinyl [option]
└── Wood [option]
```

Delete "Material Type":
- Warning: "This node has 3 children. All descendants will be deleted."
- Confirm: All 4 nodes (Material Type + 3 options) are deleted

After deletion:
```
(Material Type and all children removed)
```

**Best Practice:**
- Delete leaf nodes (nodes with no children) first
- Only delete parent nodes when you're sure you want to remove the entire subtree
- Consider moving children to a different parent before deleting

---

### 6. ASCII Tree Visualization

**Location:** Bottom panel of the dashboard

**Purpose:** Human-readable text representation of the hierarchy

**Features:**
- **Box-Drawing Characters:** Uses ├──, └──, │ for visual structure
- **Node Information:** Shows name, type, and price impact
- **Hierarchical Indentation:** Clearly shows parent-child relationships
- **Copy-Paste Friendly:** Can be copied and pasted into documentation

**Example Output:**
```
Frame Material [category]
├── Material Type [attribute]
│   ├── Aluminum [option] [+$50.00]
│   ├── Vinyl [option] [+$30.00]
│   └── Wood [option] [+$100.00]
└── Frame Color [attribute]
    ├── White [option]
    └── Brown [option] [+$15.00]
```

**Use Cases:**
- **Documentation:** Copy into technical documentation
- **Communication:** Share hierarchy structure with team
- **Debugging:** Quickly verify hierarchy structure
- **Export:** Save to text file for records

---

### 7. Diagram Tree Visualization

**Location:** Bottom panel of the dashboard (separate tab from ASCII)

**Purpose:** Graphical representation of the hierarchy

**Features:**
- **Visual Nodes:** Nodes displayed as colored boxes
- **Connecting Lines:** Lines show parent-child relationships
- **Color Coding:** Different colors for different node types
- **Interactive:** Can zoom and pan (if using interactive backend)
- **High Quality:** Suitable for presentations and reports

**Node Colors:**
- **Category:** Peach (#FFE5B4)
- **Attribute:** Light Blue (#B4D7FF)
- **Option:** Light Green (#B4FFB4)
- **Component:** Light Pink (#FFB4E5)
- **Technical Spec:** Light Purple (#E5B4FF)

**Use Cases:**
- **Presentations:** Include in stakeholder presentations
- **Training:** Visual aid for training new team members
- **Analysis:** Identify complex or unbalanced hierarchies
- **Export:** Save as PNG for documentation

**How to Use:**
1. Click the "Diagram" tab in the visualization panel
2. The diagram will render automatically
3. Right-click to save the image
4. Use browser zoom to adjust view

---

## Example Workflows

### Workflow 1: Creating a Simple Hierarchy

**Goal:** Create a basic frame material hierarchy

**Steps:**

1. **Select Manufacturing Type**
   - Choose "Casement Window" from dropdown

2. **Create Root Category**
   - Click "Create Node"
   - Name: "Frame Material"
   - Type: category
   - Parent: (none - root level)
   - Save

3. **Create Attribute**
   - Click "Create Node"
   - Name: "Material Type"
   - Type: attribute
   - Parent: Frame Material
   - Data Type: selection
   - UI Component: dropdown
   - Required: Yes
   - Save

4. **Create Options**
   - Click "Create Node"
   - Name: "Aluminum"
   - Type: option
   - Parent: Material Type
   - Price Impact: $50.00
   - Weight Impact: 2.00 kg
   - Save

   - Repeat for "Vinyl" ($30, 1.5kg) and "Wood" ($100, 3kg)

5. **Verify**
   - View the tree structure
   - Check ASCII visualization
   - Verify prices are correct

**Result:**
```
Frame Material [category]
└── Material Type [attribute]
    ├── Aluminum [option] [+$50.00]
    ├── Vinyl [option] [+$30.00]
    └── Wood [option] [+$100.00]
```

---

### Workflow 2: Reorganizing a Hierarchy

**Goal:** Move a node to a different parent

**Steps:**

1. **Identify Node to Move**
   - Find "Frame Color" attribute in the tree
   - Currently under "Frame Material"

2. **Edit the Node**
   - Click "Edit" next to "Frame Color"
   - Change Parent to: "Material Type"
   - Save

3. **Verify**
   - Check that "Frame Color" now appears under "Material Type"
   - Verify LTREE path was updated automatically
   - Check that all descendants moved with it

**Before:**
```
Frame Material [category]
├── Material Type [attribute]
└── Frame Color [attribute]
```

**After:**
```
Frame Material [category]
└── Material Type [attribute]
    └── Frame Color [attribute]
```

---

### Workflow 3: Adding Conditional Display

**Goal:** Show "Custom Color" option only when "Wood" is selected

**Steps:**

1. **Create the Conditional Node**
   - Click "Create Node"
   - Name: "Custom Color"
   - Type: option
   - Parent: Frame Color

2. **Add Display Condition**
   - In the "Display Condition" field, enter:
   ```json
   {
     "operator": "equals",
     "field": "parent.material_type",
     "value": "Wood"
   }
   ```
   - Save

3. **Test**
   - The "Custom Color" option will only appear when "Wood" is selected
   - It will be hidden for "Aluminum" and "Vinyl"

---

### Workflow 4: Bulk Import from Script

**Goal:** Create a complex hierarchy programmatically

**Steps:**

1. **Use the Example Script**
   - Run: `python examples/hierarchy_insertion.py`
   - This creates a complete hierarchy from a dictionary

2. **Verify in Dashboard**
   - Navigate to `/admin/hierarchy`
   - Select the manufacturing type
   - View the created hierarchy

3. **Make Adjustments**
   - Use the dashboard to fine-tune nodes
   - Edit prices, descriptions, etc.
   - Add or remove nodes as needed

**Benefit:** Combine programmatic creation with manual refinement

---

## Troubleshooting

### Issue: Cannot Access Dashboard

**Symptoms:**
- 403 Forbidden error
- Redirected to login page

**Solutions:**
1. **Check Authentication:**
   - Ensure you're logged in
   - Check that your JWT token is valid
   - Try logging in again

2. **Check Superuser Status:**
   - Verify your account has `is_superuser=True`
   - Contact an administrator to grant superuser access
   - Use the create_superuser script if needed

3. **Check Session:**
   - Clear browser cookies
   - Try in incognito/private mode
   - Check for CORS issues in browser console

---

### Issue: Cannot Create Node

**Symptoms:**
- Validation errors
- "Duplicate name" error
- "Parent not found" error

**Solutions:**
1. **Check Required Fields:**
   - Ensure all required fields are filled
   - Node name cannot be empty
   - Node type must be selected

2. **Check Duplicate Names:**
   - Node names must be unique at the same level
   - Check if a sibling already has that name
   - Use a different name or delete the duplicate

3. **Check Parent Node:**
   - Ensure the parent node exists
   - Verify the parent belongs to the same manufacturing type
   - Try selecting a different parent

4. **Check Validation Rules:**
   - Price and weight must be non-negative
   - Sort order must be non-negative
   - JSON fields must be valid JSON

---

### Issue: Tree Not Displaying

**Symptoms:**
- Empty tree panel
- "No nodes found" message

**Solutions:**
1. **Check Manufacturing Type:**
   - Ensure a manufacturing type is selected
   - Try selecting a different type
   - Verify the type has nodes

2. **Check Database:**
   - Verify nodes exist in the database
   - Check for database connection issues
   - Try refreshing the page

3. **Check Browser Console:**
   - Open browser developer tools
   - Check for JavaScript errors
   - Check for failed API requests

---

### Issue: Circular Reference Error

**Symptoms:**
- "Cannot move node: would create circular reference"
- Error when changing parent

**Solutions:**
1. **Understand the Error:**
   - You're trying to make a node its own ancestor
   - Example: Making "Aluminum" the parent of "Material Type" when "Aluminum" is already a child of "Material Type"

2. **Fix the Hierarchy:**
   - Choose a different parent
   - Move the node to a different branch
   - Create a new parent node if needed

3. **Verify Structure:**
   - Use the ASCII visualization to understand the current structure
   - Plan the move carefully
   - Consider moving children first

---

## Best Practices

### 1. Plan Your Hierarchy

**Before creating nodes:**
- Sketch the hierarchy on paper or whiteboard
- Identify categories, attributes, and options
- Plan pricing and weight impacts
- Consider conditional display logic

**Benefits:**
- Fewer mistakes and rework
- Clearer structure
- Easier to maintain

---

### 2. Use Consistent Naming

**Naming conventions:**
- Use clear, descriptive names
- Be consistent with capitalization
- Avoid special characters
- Use singular nouns for options

**Examples:**
- ✅ Good: "Frame Material", "Aluminum", "Double Pane"
- ❌ Bad: "frame_material", "aluminum!", "double-pane-glass"

---

### 3. Set Appropriate Node Types

**Node type guidelines:**
- **Category:** Use for organizational grouping (no value)
- **Attribute:** Use for configurable properties (has value)
- **Option:** Use for specific choices (concrete value)
- **Component:** Use for physical parts
- **Technical Spec:** Use for calculated properties

**Example:**
```
Frame Material [category] ← Organizational
└── Material Type [attribute] ← Configurable
    ├── Aluminum [option] ← Specific choice
    ├── Vinyl [option] ← Specific choice
    └── Wood [option] ← Specific choice
```

---

### 4. Test Thoroughly

**After making changes:**
- View the tree structure
- Check ASCII visualization
- Verify prices are correct
- Test conditional display logic
- Create a test configuration

**Testing checklist:**
- [ ] All nodes appear in tree
- [ ] Prices are correct
- [ ] Weights are correct
- [ ] Conditional logic works
- [ ] Validation rules work
- [ ] No duplicate names
- [ ] No circular references

---

### 5. Document Your Changes

**Keep records:**
- Note why you made changes
- Document pricing decisions
- Explain conditional logic
- Record validation rules

**Benefits:**
- Easier to maintain
- Helps onboard new team members
- Provides audit trail
- Supports troubleshooting

---

## API Integration

The dashboard uses the following API endpoints:

### GET `/api/v1/manufacturing-types`
- List all manufacturing types
- Used by the type selector dropdown

### GET `/api/v1/attribute-nodes?manufacturing_type_id={id}`
- Get all nodes for a manufacturing type
- Used to build the tree view

### GET `/api/v1/attribute-nodes/{node_id}`
- Get a single node by ID
- Used when editing a node

### POST `/api/v1/attribute-nodes`
- Create a new node
- Used by the create form

### PATCH `/api/v1/attribute-nodes/{node_id}`
- Update an existing node
- Used by the edit form

### DELETE `/api/v1/attribute-nodes/{node_id}`
- Delete a node and its descendants
- Used by the delete button

**Note:** All endpoints require superuser authentication.

---

## Related Documentation

- **HierarchyBuilderService API:** See docstrings in `app/services/hierarchy_builder.py`
- **Example Scripts:** See `examples/hierarchy_insertion.py`
- **Database Schema:** See `docs/windx-sql-explanations.md`
- **API Documentation:** See OpenAPI docs at `/docs`
- **Main README:** See `README.md` for overview

---

## Support

For issues or questions:
1. Check this documentation first
2. Review the example scripts
3. Check the API documentation
4. Contact the development team
5. File an issue in the project repository

---

**Last Updated:** 2025-01-27
**Version:** 1.0.0
