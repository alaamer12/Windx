# WindX System Architecture - Complete Context Document

## Executive Summary

WindX is a **dynamic product configurator system** built on an **Entity-Attribute-Value (EAV) pattern** with **hierarchical attributes** using PostgreSQL's LTREE extension. The system enables **zero-code configuration** of complex products through YAML-driven attribute definitions that generate dynamic forms, validation rules, and pricing calculations at runtime.

**Core Innovation:** Instead of hardcoding product attributes in database columns, WindX uses a flexible EAV schema where attributes are defined in YAML, stored in a hierarchical tree structure, and dynamically rendered as forms with real-time validation and pricing.

---

## Table of Contents

1. [System Architecture Overview](#system-architecture-overview)
2. [The EAV Pattern in WindX](#the-eav-pattern-in-windx)
3. [Hierarchical Attribute System](#hierarchical-attribute-system)
4. [YAML-Driven Configuration](#yaml-driven-configuration)
5. [Dynamic Form Generation](#dynamic-form-generation)
6. [Data Flow Architecture](#data-flow-architecture)
7. [Database Schema Deep Dive](#database-schema-deep-dive)
8. [Runtime Behavior](#runtime-behavior)
9. [Key Components](#key-components)
10. [The Gap: Setup vs Runtime](#the-gap-setup-vs-runtime)

---

## System Architecture Overview

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    YAML Configuration Layer                  │
│  (Data Definition - What attributes exist)                   │
│                                                              │
│  backend/config/pages/                                       │
│  ├── profile.yaml      (29 attributes)                      │
│  ├── accessories.yaml  (15 attributes)                      │
│  └── glazing.yaml      (20 attributes)                      │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                    Setup Scripts Layer                       │
│  (One-Time Database Population)                             │
│                                                              │
│  backend/scripts/setup_hierarchy.py                         │
│  • Reads YAML configurations                                │
│  • Creates manufacturing_types records                      │
│  • Creates attribute_nodes tree structure                   │
│  • Populates database with attribute definitions            │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                    Database Layer (EAV Schema)               │
│  (Persistent Storage)                                        │
│                                                              │
│  Tables:                                                     │
│  • manufacturing_types  (Product categories)                │
│  • attribute_nodes      (Attribute definitions - LTREE)     │
│  • configurations       (Customer product instances)        │
│  • configuration_selections (Attribute values - EAV)        │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                    Application Layer                         │
│  (Runtime Behavior - How attributes work)                   │
│                                                              │
│  backend/app/services/entry.py                              │
│  • Queries attribute_nodes from database                    │
│  • Generates dynamic forms (ProfileSchema)                  │
│  • Evaluates display conditions (HARDCODED)                 │
│  • Validates user input (HARDCODED)                         │
│  • Saves configuration_selections                           │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                    Frontend Layer                            │
│  (User Interface)                                            │
│                                                              │
│  • Receives ProfileSchema from backend                      │
│  • Renders dynamic forms based on schema                    │
│  • Handles user input and validation                        │
│  • Submits configuration_selections to backend              │
└─────────────────────────────────────────────────────────────┘
```

### Key Architectural Principles

1. **Schema-Driven**: Forms are generated from database schema, not hardcoded
2. **Hierarchical**: Attributes organized in tree structure using LTREE
3. **Flexible**: EAV pattern allows any attribute without schema changes
4. **Dynamic**: Add new attributes by editing YAML and running setup script
5. **Typed**: Each attribute has a data_type (string, number, boolean, formula)

---

## The EAV Pattern in WindX

### What is EAV?

**Entity-Attribute-Value (EAV)** is a data model where instead of having fixed columns for each attribute, you have:
- **Entity**: The thing being described (Configuration)
- **Attribute**: The property being stored (AttributeNode)
- **Value**: The actual data (ConfigurationSelection)

### Traditional vs EAV Approach

**Traditional Approach (Fixed Schema):**
```sql
CREATE TABLE products (
    id INT PRIMARY KEY,
    name VARCHAR(200),
    width DECIMAL(10,2),
    height DECIMAL(10,2),
    material VARCHAR(100),
    color VARCHAR(100),
    -- Adding new attribute requires ALTER TABLE
);
```

**WindX EAV Approach (Flexible Schema):**
```sql
-- Entity table
CREATE TABLE configurations (
    id INT PRIMARY KEY,
    manufacturing_type_id INT,
    total_price DECIMAL(12,2),
    -- No product-specific columns!
);

-- Attribute definition table
CREATE TABLE attribute_nodes (
    id INT PRIMARY KEY,
    name VARCHAR(200),
    data_type VARCHAR(20),
    -- Defines what attributes exist
);

-- Value table (EAV)
CREATE TABLE configuration_selections (
    id INT PRIMARY KEY,
    configuration_id INT,  -- Entity
    attribute_node_id INT, -- Attribute
    string_value TEXT,     -- Value (polymorphic)
    numeric_value DECIMAL,
    boolean_value BOOLEAN,
    json_value JSONB
);
```

### Why EAV for WindX?

**Problem:** Different product types need different attributes:
- Windows need: width, height, frame_material, glass_type, opening_system
- Doors need: width, height, material, lock_type, fire_rating
- Tables need: length, width, material, load_capacity, finish

**Solution:** EAV allows each product type to have its own set of attributes without changing the database schema.


---

## Hierarchical Attribute System

### The LTREE Extension

WindX uses PostgreSQL's **LTREE extension** to store hierarchical paths for efficient tree queries.

**What is LTREE?**
- Stores hierarchical labels as dot-separated paths
- Enables fast ancestor/descendant queries without recursion
- Uses GiST indexes for O(log n) performance

**Example LTREE Paths:**
```
profile.basic_information.name
profile.basic_information.type
profile.dimensions.width
profile.dimensions.height
profile.frame_options.material
profile.frame_options.material.aluminum
profile.frame_options.material.wood
```

### Attribute Node Types

WindX supports multiple node types in the hierarchy:

```yaml
node_types:
  category:
    description: "Organizational grouping (e.g., 'Frame Options')"
    has_value: false
    can_have_children: true
    example: "Basic Information"
  
  attribute:
    description: "Configurable property (e.g., 'Frame Material')"
    has_value: true
    can_have_children: true  # Can have option children
    example: "Width"
  
  option:
    description: "Selectable choice (e.g., 'Aluminum', 'Wood')"
    has_value: true
    can_have_children: false
    example: "Aluminum"
    parent_type: attribute
```

### Hierarchical Structure Example

```
Window Profile Entry (Manufacturing Type)
│
├── Basic Information (Category)
│   ├── Name (Attribute: string)
│   ├── Type (Attribute: string)
│   │   ├── Frame (Option)
│   │   ├── Sash (Option)
│   │   └── Mullion (Option)
│   └── System Series (Attribute: string)
│       ├── Kom700 (Option)
│       ├── Kom800 (Option)
│       └── Kom900 (Option)
│
├── Dimensions (Category)
│   ├── Width (Attribute: number)
│   ├── Height (Attribute: number)
│   └── Depth (Attribute: number)
│
└── Frame Options (Category)
    ├── Material (Attribute: string)
    │   ├── Aluminum (Option) [+$50]
    │   ├── Wood (Option) [+$120]
    │   └── Vinyl (Option) [+$30]
    └── Color (Attribute: string)
        ├── White (Option)
        ├── Black (Option)
        └── Custom (Option) [+$25]
```

### LTREE Query Examples

**Get all descendants of a node:**
```sql
SELECT * FROM attribute_nodes 
WHERE ltree_path <@ 'profile.frame_options'::ltree;
-- Returns: material, color, and all their options
```

**Get all ancestors of a node:**
```sql
SELECT * FROM attribute_nodes 
WHERE 'profile.frame_options.material.aluminum'::ltree <@ ltree_path;
-- Returns: profile, frame_options, material
```

**Pattern matching:**
```sql
SELECT * FROM attribute_nodes 
WHERE ltree_path ~ '*.material.*'::lquery;
-- Returns: All nodes with 'material' in their path
```

### Benefits of Hierarchical Structure

1. **Logical Organization**: Attributes grouped by category
2. **Conditional Display**: Show/hide based on parent selections
3. **Efficient Queries**: LTREE indexes enable fast tree traversal
4. **Flexible Depth**: Unlimited nesting levels
5. **Path-Based Access**: Easy to find related attributes

---

## YAML-Driven Configuration

### Configuration File Structure

WindX uses YAML files to define attribute hierarchies. These files are the **single source of truth** for attribute definitions.

**File Location:**
```
backend/config/pages/
├── profile.yaml      # Window profile attributes (29 fields)
├── accessories.yaml  # Accessory attributes (15 fields)
└── glazing.yaml      # Glazing attributes (20 fields)
```

### YAML Schema Structure

```yaml
# Page identification
page_type: profile
manufacturing_type: Window Profile Entry

# Manufacturing type configuration
manufacturing_type_config:
  description: "Window profile data entry system"
  base_category: window
  base_price: 200.00
  base_weight: 15.00

# Attribute definitions
attributes:
  - name: field_name              # Database identifier
    display_name: Field Label     # UI label
    description: |                # Rich HTML description
      Multi-line description with **markdown**
      • Bullet points
      • Examples
    node_type: attribute          # category | attribute | option
    data_type: string             # string | number | boolean | formula
    required: true                # Validation
    ltree_path: section.field     # Hierarchical path
    depth: 1                      # Tree depth
    sort_order: 1                 # Display order
    ui_component: input           # UI control type
    help_text: "Tooltip text"    # Help tooltip
    
    # Conditional display
    display_condition:
      operator: equals
      field: type
      value: Frame
    
    # Validation rules
    validation_rules:
      min_length: 1
      max_length: 200
      pattern: "^[A-Z]"
    
    # Pricing impact
    price_impact_type: fixed      # fixed | percentage | formula
    price_impact_value: 50.00     # Dollar amount
    price_formula: "width * height * 0.05"
    
    # Weight impact
    weight_impact: 5.00           # Kg
    weight_formula: "width * height * 0.002"
    
    # Technical properties
    technical_property_type: u_value
    technical_impact_formula: "base_u_value - 0.05"
    
    # Calculated fields
    calculated_field:
      type: multiply
      operands: [price_per_meter, length_of_beam]
      trigger_on: [price_per_meter, length_of_beam]
      precision: 2
    
    # UI metadata
    metadata:
      placeholder: "e.g. Standard Window"
      icon: "window-icon"
    
    # Options for dropdown/select
    options:
      - Frame
      - Sash
      - Mullion
```

### YAML to Database Flow

```
1. YAML File (profile.yaml)
   ↓
2. Setup Script (setup_hierarchy.py)
   • Reads YAML with yaml.safe_load()
   • Validates structure
   • Normalizes option values
   ↓
3. Database Population
   • Creates ManufacturingType record
   • Creates AttributeNode records
   • Creates option nodes as children
   • Sets LTREE paths automatically
   ↓
4. Database (attribute_nodes table)
   • Stores attribute definitions
   • Ready for runtime queries
```

### Key YAML Features

**1. Multi-line Descriptions:**
```yaml
description: |
  This is a multi-line description.
  
  **Features:**
  • Feature 1
  • Feature 2
```

**2. Nested Conditions:**
```yaml
display_condition:
  operator: and
  conditions:
    - operator: equals
      field: type
      value: Frame
    - operator: contains
      field: opening_system
      value: sliding
```

**3. Option Normalization:**
```yaml
options:
  - "Full Screen"      # Stored as: full_screen
  - "Half Screen"      # Stored as: half_screen
  - "No Screen"        # Stored as: no_screen
```

The setup script automatically normalizes option values to lowercase with underscores for database storage while preserving display names.

---

## Dynamic Form Generation

### How Forms are Generated

WindX generates forms dynamically at runtime by querying the `attribute_nodes` table and converting the results into a `ProfileSchema`.

**Flow:**

```
1. Frontend requests form schema
   GET /api/v1/admin/entry/profile/schema/123?page_type=profile
   ↓
2. Backend queries attribute_nodes
   SELECT * FROM attribute_nodes 
   WHERE manufacturing_type_id = 123 
   AND page_type = 'profile'
   ORDER BY ltree_path, sort_order
   ↓
3. EntryService.generate_form_schema()
   • Groups attributes by section (from ltree_path)
   • Creates FieldDefinition for each attribute
   • Extracts display_condition, validation_rules
   • Builds FormSection objects
   • Returns ProfileSchema
   ↓
4. Frontend receives ProfileSchema
   {
     "manufacturing_type_id": 123,
     "sections": [
       {
         "title": "Basic Information",
         "fields": [
           {
             "name": "name",
             "label": "Product Name",
             "data_type": "string",
             "required": true,
             "ui_component": "input",
             "validation_rules": {"min_length": 1}
           }
         ]
       }
     ],
     "conditional_logic": {
       "renovation": {"operator": "equals", "field": "type", "value": "Frame"}
     }
   }
   ↓
5. Frontend renders dynamic form
   • Creates input fields based on ui_component
   • Applies validation rules
   • Evaluates display conditions
   • Shows/hides fields dynamically
```

### ProfileSchema Structure

```python
class ProfileSchema(BaseModel):
    """Complete profile form schema."""
    
    manufacturing_type_id: int
    sections: List[FormSection]
    conditional_logic: Dict[str, Any]
    dependencies: List[Dict[str, Any]] | None

class FormSection(BaseModel):
    """Logical grouping of form fields."""
    
    title: str
    description: str | None
    fields: List[FieldDefinition]
    sort_order: int

class FieldDefinition(BaseModel):
    """Individual form field definition."""
    
    name: str
    label: str
    data_type: str
    required: bool
    validation_rules: Dict[str, Any] | None
    display_condition: Dict[str, Any] | None
    ui_component: str | None
    description: str | None
    help_text: str | None
    options: List[str] | None
    sort_order: int
```

### Field Definition Creation

```python
async def create_field_definition(self, node: AttributeNode) -> FieldDefinition:
    """Create field definition from attribute node."""
    
    # Get options if this is a dropdown/select field
    options = None
    if node.validation_rules and 'options' in node.validation_rules:
        options = node.validation_rules['options']
    
    # Map UI component
    ui_component = node.ui_component or self.get_default_ui_component(node.data_type)
    
    return FieldDefinition(
        name=node.name,
        label=node.get_display_name(),
        data_type=node.data_type,
        required=node.required,
        validation_rules=node.validation_rules,
        display_condition=node.display_condition,
        ui_component=ui_component,
        description=node.description,
        help_text=node.help_text,
        options=options,
        sort_order=node.sort_order,
    )
```


---

## Data Flow Architecture

### Complete User Journey

```
┌─────────────────────────────────────────────────────────────┐
│ 1. USER OPENS CONFIGURATION PAGE                            │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ 2. FRONTEND REQUESTS FORM SCHEMA                            │
│    GET /api/v1/admin/entry/profile/schema/123               │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ 3. BACKEND QUERIES ATTRIBUTE_NODES                          │
│    SELECT * FROM attribute_nodes                            │
│    WHERE manufacturing_type_id = 123                        │
│    AND page_type = 'profile'                                │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ 4. BACKEND GENERATES PROFILESCHEMA                          │
│    • Groups attributes by section                           │
│    • Creates FieldDefinition objects                        │
│    • Extracts conditional logic                             │
│    • Returns JSON schema                                    │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ 5. FRONTEND RENDERS DYNAMIC FORM                            │
│    • Creates input fields                                   │
│    • Applies validation rules                               │
│    • Sets up conditional display                            │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ 6. USER FILLS OUT FORM                                      │
│    • Enters values                                          │
│    • Selects options                                        │
│    • Triggers conditional fields                            │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ 7. USER SUBMITS FORM                                        │
│    POST /api/v1/admin/entry/profile                         │
│    Body: {                                                  │
│      "manufacturing_type_id": 123,                          │
│      "name": "Standard Window",                             │
│      "type": "Frame",                                       │
│      "width": 1200,                                         │
│      "height": 1500,                                        │
│      ...                                                    │
│    }                                                        │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ 8. BACKEND VALIDATES DATA                                   │
│    • Checks required fields                                 │
│    • Validates data types                                   │
│    • Evaluates validation rules (HARDCODED)                 │
│    • Checks cross-field dependencies (HARDCODED)            │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ 9. BACKEND CREATES CONFIGURATION                            │
│    INSERT INTO configurations (                             │
│      manufacturing_type_id,                                 │
│      name,                                                  │
│      base_price,                                            │
│      total_price                                            │
│    ) VALUES (123, 'Standard Window', 200.00, 200.00)       │
│    RETURNING id; -- Returns: 456                            │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ 10. BACKEND CREATES CONFIGURATION_SELECTIONS (EAV)          │
│     For each form field:                                    │
│     INSERT INTO configuration_selections (                  │
│       configuration_id,                                     │
│       attribute_node_id,                                    │
│       string_value / numeric_value / boolean_value,         │
│       selection_path                                        │
│     ) VALUES (456, <attr_id>, <value>, <path>)              │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ 11. BACKEND CALCULATES TOTALS                               │
│     • Sums price impacts from selections                    │
│     • Evaluates price formulas                              │
│     • Calculates weight                                     │
│     • Updates configuration.total_price                     │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ 12. BACKEND RETURNS CONFIGURATION                           │
│     Response: {                                             │
│       "id": 456,                                            │
│       "name": "Standard Window",                            │
│       "total_price": 988.50,                                │
│       "selections": [...]                                   │
│     }                                                       │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ 13. FRONTEND DISPLAYS CONFIRMATION                          │
│     • Shows saved configuration                             │
│     • Displays calculated price                             │
│     • Allows editing or quote generation                    │
└─────────────────────────────────────────────────────────────┘
```

### EAV Data Storage Example

**User Input:**
```json
{
  "manufacturing_type_id": 123,
  "name": "Standard Window",
  "type": "Frame",
  "width": 1200,
  "height": 1500,
  "material": "Aluminum",
  "color": "White"
}
```

**Database Storage:**

**configurations table:**
```sql
id  | manufacturing_type_id | name             | total_price | created_at
456 | 123                   | Standard Window  | 988.50      | 2025-01-15
```

**configuration_selections table (EAV):**
```sql
id  | config_id | attr_node_id | string_value | numeric_value | selection_path
1   | 456       | 10           | Standard...  | NULL          | profile.name
2   | 456       | 11           | Frame        | NULL          | profile.type
3   | 456       | 12           | NULL         | 1200          | profile.width
4   | 456       | 13           | NULL         | 1500          | profile.height
5   | 456       | 14           | Aluminum     | NULL          | profile.material
6   | 456       | 15           | White        | NULL          | profile.color
```

**Key Points:**
- Each form field becomes a row in `configuration_selections`
- Values stored in appropriate column (string_value, numeric_value, etc.)
- `attribute_node_id` links to attribute definition
- `selection_path` preserves hierarchical context

---

## Database Schema Deep Dive

### Core Tables

#### 1. manufacturing_types
**Purpose:** Product categories (Window, Door, Table, etc.)

```sql
CREATE TABLE manufacturing_types (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL,
    description TEXT,
    base_category VARCHAR(50),
    base_price NUMERIC(10,2) DEFAULT 0.00,
    base_weight NUMERIC(10,2) DEFAULT 0.00,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

**Example Data:**
```
id | name                  | base_price | base_weight
1  | Window Profile Entry  | 200.00     | 15.00
2  | Accessories Entry     | 50.00      | 2.00
3  | Glazing Entry         | 150.00     | 10.00
```

#### 2. attribute_nodes (The Heart of EAV)
**Purpose:** Defines what attributes exist and their behavior

```sql
CREATE TABLE attribute_nodes (
    id SERIAL PRIMARY KEY,
    manufacturing_type_id INT REFERENCES manufacturing_types(id),
    parent_node_id INT REFERENCES attribute_nodes(id),
    page_type VARCHAR(20) DEFAULT 'profile',
    
    -- Basic info
    name VARCHAR(200) NOT NULL,
    display_name VARCHAR(300),
    node_type VARCHAR(20) NOT NULL,  -- category, attribute, option
    data_type VARCHAR(20),            -- string, number, boolean, formula
    
    -- Behavior
    display_condition JSONB,
    validation_rules JSONB,
    required BOOLEAN DEFAULT FALSE,
    
    -- Pricing
    price_impact_type VARCHAR(20) DEFAULT 'fixed',
    price_impact_value NUMERIC(10,2),
    price_formula TEXT,
    
    -- Weight
    weight_impact NUMERIC(10,2) DEFAULT 0,
    weight_formula TEXT,
    
    -- Technical
    technical_property_type VARCHAR(50),
    technical_impact_formula TEXT,
    
    -- Calculated fields
    calculated_field JSONB,
    
    -- Hierarchy (LTREE)
    ltree_path LTREE NOT NULL,
    depth INT DEFAULT 0,
    
    -- UI
    sort_order INT DEFAULT 0,
    ui_component VARCHAR(50),
    description TEXT,
    help_text TEXT,
    metadata_ JSONB,
    image_url VARCHAR(500),
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Critical index for fast tree queries
CREATE INDEX idx_attribute_nodes_ltree_path 
ON attribute_nodes USING GIST (ltree_path);
```

**Example Data:**
```
id | name   | node_type | data_type | ltree_path           | price_impact_value
10 | name   | attribute | string    | profile.name         | NULL
11 | type   | attribute | string    | profile.type         | NULL
12 | Frame  | option    | string    | profile.type.frame   | 0.00
13 | Sash   | option    | string    | profile.type.sash    | 25.00
14 | width  | attribute | number    | profile.width        | NULL
```

#### 3. configurations (Entity in EAV)
**Purpose:** Customer product instances

```sql
CREATE TABLE configurations (
    id SERIAL PRIMARY KEY,
    manufacturing_type_id INT REFERENCES manufacturing_types(id),
    customer_id INT REFERENCES customers(id),
    
    name VARCHAR(200) NOT NULL,
    description TEXT,
    status VARCHAR(20) DEFAULT 'draft',
    reference_code VARCHAR(100) UNIQUE,
    
    -- Calculated totals
    base_price NUMERIC(12,2) DEFAULT 0.00,
    total_price NUMERIC(12,2) DEFAULT 0.00,
    calculated_weight NUMERIC(10,2) DEFAULT 0.00,
    calculated_technical_data JSONB DEFAULT '{}',
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

#### 4. configuration_selections (Value in EAV)
**Purpose:** Stores actual attribute values

```sql
CREATE TABLE configuration_selections (
    id SERIAL PRIMARY KEY,
    configuration_id INT REFERENCES configurations(id) ON DELETE CASCADE,
    attribute_node_id INT REFERENCES attribute_nodes(id),
    
    -- Polymorphic value storage
    string_value TEXT,
    numeric_value NUMERIC(15,6),
    boolean_value BOOLEAN,
    json_value JSONB,
    
    -- Calculated impacts
    calculated_price_impact NUMERIC(10,2),
    calculated_weight_impact NUMERIC(10,2),
    calculated_technical_impact JSONB,
    
    -- Hierarchy context
    selection_path LTREE NOT NULL,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- One selection per attribute per configuration
    UNIQUE(configuration_id, attribute_node_id)
);

CREATE INDEX idx_config_selections_path 
ON configuration_selections USING GIST (selection_path);
```

### EAV Relationships

```
manufacturing_types (1) ──────┐
                              │
                              ├──> attribute_nodes (Many)
                              │    • Defines attributes
                              │    • Hierarchical (LTREE)
                              │    • Reusable across configs
                              │
                              └──> configurations (Many)
                                   • Customer instances
                                   │
                                   └──> configuration_selections (Many)
                                        • Actual values (EAV)
                                        • References attribute_nodes
```

### Why This Schema Works

1. **Flexibility**: Add attributes without ALTER TABLE
2. **Reusability**: Attribute definitions shared across configurations
3. **Hierarchy**: LTREE enables fast tree queries
4. **Type Safety**: Polymorphic value columns (string, numeric, boolean, json)
5. **Performance**: Indexed LTREE paths and GIN indexes on JSONB
6. **Auditability**: Timestamps on all tables


---

## Runtime Behavior

### How Dynamic Attributes Control Everything

The power of WindX comes from how attribute definitions in the database control runtime behavior:

#### 1. Form Rendering

**Attribute Definition:**
```yaml
- name: width
  data_type: number
  ui_component: input
  validation_rules:
    min: 100
    max: 5000
```

**Runtime Behavior:**
```javascript
// Frontend receives this from ProfileSchema
{
  "name": "width",
  "data_type": "number",
  "ui_component": "input",
  "validation_rules": {"min": 100, "max": 5000}
}

// Frontend renders:
<input 
  type="number" 
  name="width" 
  min="100" 
  max="5000"
  v-model="formData.width"
/>
```

#### 2. Conditional Display

**Attribute Definition:**
```yaml
- name: renovation
  display_condition:
    operator: equals
    field: type
    value: Frame
```

**Runtime Behavior:**
```python
# Backend evaluates condition
def evaluate_display_conditions(form_data, schema):
    visibility = {}
    for field_name, condition in schema.conditional_logic.items():
        visibility[field_name] = ConditionEvaluator.evaluate_condition(
            condition, 
            form_data
        )
    return visibility

# Result:
# If form_data['type'] == 'Frame': visibility['renovation'] = True
# Else: visibility['renovation'] = False
```

#### 3. Validation

**Attribute Definition:**
```yaml
- name: name
  required: true
  validation_rules:
    min_length: 1
    max_length: 200
```

**Runtime Behavior:**
```python
# Backend validates
def validate_field(field_name, field_value, field_config):
    if field_config['required'] and not field_value:
        return f"{field_name} is required"
    
    rules = field_config.get('validation_rules', {})
    if 'min_length' in rules:
        if len(field_value) < rules['min_length']:
            return f"{field_name} must be at least {rules['min_length']} characters"
    
    return None  # Valid
```

#### 4. Pricing Calculation

**Attribute Definition:**
```yaml
- name: aluminum_frame
  node_type: option
  price_impact_type: fixed
  price_impact_value: 50.00
```

**Runtime Behavior:**
```python
# Backend calculates price
def calculate_total_price(configuration):
    total = configuration.base_price
    
    for selection in configuration.selections:
        attr_node = selection.attribute_node
        
        if attr_node.price_impact_type == 'fixed':
            total += attr_node.price_impact_value
        elif attr_node.price_impact_type == 'percentage':
            total *= (1 + attr_node.price_impact_value / 100)
        elif attr_node.price_impact_type == 'formula':
            total += evaluate_formula(attr_node.price_formula, form_data)
    
    return total
```

#### 5. Dynamic Options

**Attribute Definition:**
```yaml
- name: type
  options:
    - Frame
    - Sash
    - Mullion
```

**Runtime Behavior:**
```python
# Setup script creates option nodes
for option_value in attribute_config['options']:
    option_node = AttributeNode(
        parent_node_id=parent_attribute.id,
        name=normalize(option_value),
        display_name=option_value,
        node_type="option",
        ltree_path=f"{parent_attribute.ltree_path}.{normalize(option_value)}"
    )
    session.add(option_node)

# Frontend receives options
{
  "name": "type",
  "options": ["Frame", "Sash", "Mullion"]
}

# Frontend renders dropdown
<select name="type">
  <option value="Frame">Frame</option>
  <option value="Sash">Sash</option>
  <option value="Mullion">Mullion</option>
</select>
```

### The Power of JSONB

WindX uses JSONB columns extensively for flexible, schema-less data:

#### display_condition (JSONB)
```json
{
  "operator": "and",
  "conditions": [
    {"operator": "equals", "field": "type", "value": "Frame"},
    {"operator": "contains", "field": "opening_system", "value": "sliding"}
  ]
}
```

#### validation_rules (JSONB)
```json
{
  "min_length": 1,
  "max_length": 200,
  "pattern": "^[A-Z]",
  "options": ["Frame", "Sash", "Mullion"]
}
```

#### calculated_field (JSONB)
```json
{
  "type": "multiply",
  "operands": ["price_per_meter", "length_of_beam"],
  "trigger_on": ["price_per_meter", "length_of_beam"],
  "precision": 2
}
```

#### metadata_ (JSONB)
```json
{
  "placeholder": "e.g. Standard Window",
  "icon": "window-icon",
  "help_text": "Enter a descriptive name"
}
```

**Benefits of JSONB:**
- No schema changes needed for new rule types
- Complex nested structures
- Queryable with GIN indexes
- Type-safe with Pydantic validation

---

## Key Components

### 1. Setup Scripts

**Location:** `backend/scripts/setup_hierarchy.py`

**Purpose:** One-time database population from YAML

**Key Classes:**
```python
class HierarchySetup:
    async def setup_from_yaml_file(yaml_file: Path)
    async def get_or_create_manufacturing_type(name, config)
    async def create_attributes_from_config(mfg_type, page_type, attributes)
    async def create_attribute_node(mfg_type_id, page_type, config)
    async def create_option_nodes(parent_node, options)
    def normalize_option_value(option_value)
    def normalize_display_condition(condition)
```

**What It Does:**
1. Reads YAML configuration files
2. Creates/updates manufacturing_types
3. Deletes existing attribute_nodes for page_type
4. Creates new attribute_nodes from YAML
5. Creates option nodes for dropdown fields
6. Normalizes values for consistency

**Usage:**
```bash
# Setup all pages
python backend/scripts/setup_hierarchy.py

# Setup specific page
python backend/scripts/setup_hierarchy.py profile
python backend/scripts/setup_hierarchy.py accessories
python backend/scripts/setup_hierarchy.py glazing
```

### 2. EntryService

**Location:** `backend/app/services/entry.py`

**Purpose:** Runtime form generation and data handling

**Key Methods:**
```python
class EntryService:
    async def get_profile_schema(manufacturing_type_id, page_type)
    async def generate_form_schema(mfg_type_id, attribute_nodes)
    async def create_field_definition(node: AttributeNode)
    async def evaluate_display_conditions(form_data, schema)
    async def validate_profile_data(data, page_type)
    async def save_profile_configuration(data, user, page_type)
    def evaluate_business_rules(form_data)  # ❌ HARDCODED
    def validate_cross_field_rules(form_data, schema)  # ❌ HARDCODED
```

**What It Does:**
1. Queries attribute_nodes from database
2. Generates ProfileSchema dynamically
3. Creates FieldDefinition objects
4. Groups fields into FormSections
5. Extracts conditional logic
6. Validates user input (partially hardcoded)
7. Saves configurations and selections

### 3. AttributeNode Model

**Location:** `backend/app/models/attribute_node.py`

**Purpose:** ORM model for attribute definitions

**Key Fields:**
```python
class AttributeNode(Base):
    # Identity
    id: int
    manufacturing_type_id: int
    parent_node_id: int | None
    page_type: str
    
    # Definition
    name: str
    display_name: str | None
    node_type: str  # category, attribute, option
    data_type: str  # string, number, boolean, formula
    
    # Behavior
    display_condition: dict | None  # JSONB
    validation_rules: dict | None   # JSONB
    required: bool
    
    # Pricing
    price_impact_type: str
    price_impact_value: Decimal | None
    price_formula: str | None
    
    # Hierarchy
    ltree_path: str  # LTREE
    depth: int
    
    # UI
    sort_order: int
    ui_component: str | None
    description: str | None
    help_text: str | None
    metadata_: dict | None  # JSONB
```

### 4. Configuration & ConfigurationSelection Models

**Location:** 
- `backend/app/models/configuration.py`
- `backend/app/models/configuration_selection.py`

**Purpose:** Store customer product instances (EAV)

**Configuration (Entity):**
```python
class Configuration(Base):
    id: int
    manufacturing_type_id: int
    customer_id: int | None
    name: str
    status: str  # draft, saved, quoted, ordered
    
    # Calculated totals
    base_price: Decimal
    total_price: Decimal
    calculated_weight: Decimal
    calculated_technical_data: dict  # JSONB
    
    # Relationships
    selections: list[ConfigurationSelection]
```

**ConfigurationSelection (Value):**
```python
class ConfigurationSelection(Base):
    id: int
    configuration_id: int  # Entity
    attribute_node_id: int  # Attribute
    
    # Polymorphic value storage
    string_value: str | None
    numeric_value: Decimal | None
    boolean_value: bool | None
    json_value: dict | None
    
    # Calculated impacts
    calculated_price_impact: Decimal | None
    calculated_weight_impact: Decimal | None
    
    # Hierarchy context
    selection_path: str  # LTREE
```

### 5. ConditionEvaluator

**Location:** `backend/app/services/entry.py`

**Purpose:** Evaluate display conditions dynamically

**Supported Operators:**
```python
OPERATORS = {
    # Comparison
    "equals": lambda a, b: a == b,
    "not_equals": lambda a, b: a != b,
    "greater_than": lambda a, b: a > b,
    "less_than": lambda a, b: a < b,
    
    # String
    "contains": lambda a, b: b.lower() in a.lower(),
    "starts_with": lambda a, b: a.lower().startswith(b.lower()),
    "ends_with": lambda a, b: a.lower().endswith(b.lower()),
    
    # Collection
    "in": lambda a, b: a in b,
    "not_in": lambda a, b: a not in b,
    
    # Existence
    "exists": lambda a, b: a is not None and a != "",
    "not_exists": lambda a, b: a is None or a == "",
}
```

**Usage:**
```python
evaluator = ConditionEvaluator()

condition = {
    "operator": "and",
    "conditions": [
        {"operator": "equals", "field": "type", "value": "Frame"},
        {"operator": "contains", "field": "opening_system", "value": "sliding"}
    ]
}

form_data = {
    "type": "Frame",
    "opening_system": "Sliding Window"
}

result = evaluator.evaluate_condition(condition, form_data)
# Returns: True
```


---

## The Gap: Setup vs Runtime

### The Current State

WindX has **successfully implemented** the EAV pattern with YAML-driven setup, but there's a critical gap between setup and runtime:

```
┌─────────────────────────────────────────────────────────────┐
│                    SETUP LAYER (Complete ✅)                 │
│                                                              │
│  YAML → setup_hierarchy.py → attribute_nodes table          │
│                                                              │
│  • Reads YAML configurations                                │
│  • Creates attribute definitions                            │
│  • Stores display_condition in JSONB                        │
│  • Stores validation_rules in JSONB                         │
│  • Creates option nodes                                     │
│                                                              │
│  Result: Database contains all attribute metadata           │
└─────────────────────────────────────────────────────────────┘
                            ↓
                      ❌ GAP HERE ❌
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                  RUNTIME LAYER (Incomplete ❌)               │
│                                                              │
│  attribute_nodes → EntryService → ProfileSchema             │
│                                                              │
│  ✅ Reads attribute definitions from database               │
│  ✅ Generates dynamic forms                                 │
│  ✅ Passes display_condition to frontend                    │
│  ✅ Passes validation_rules to frontend                     │
│                                                              │
│  ❌ Business rules hardcoded in Python                      │
│  ❌ Validation logic hardcoded in Python                    │
│  ❌ YAML display_condition ignored at runtime               │
│  ❌ YAML validation_rules not evaluated                     │
│                                                              │
│  Result: Configuration changes don't affect behavior        │
└─────────────────────────────────────────────────────────────┘
```

### What Works ✅

1. **YAML to Database**
   - YAML files define attributes
   - Setup script populates database
   - attribute_nodes table contains all metadata

2. **Database to Schema**
   - EntryService queries attribute_nodes
   - Generates ProfileSchema dynamically
   - Frontend receives schema

3. **Dynamic Form Rendering**
   - Frontend renders forms from schema
   - UI components based on ui_component field
   - Options loaded from database

4. **EAV Data Storage**
   - User input saved to configuration_selections
   - Polymorphic value storage works
   - LTREE paths maintained

### What Doesn't Work ❌

1. **Business Rules Evaluation**
   ```python
   # ❌ HARDCODED in entry.py
   def evaluate_business_rules(form_data):
       visibility = {}
       product_type = form_data.get("type", "").lower()
       
       # Rule 1: Hardcoded
       visibility["renovation"] = product_type == "frame"
       
       # Rule 2: Hardcoded
       visibility["builtin_flyscreen_track"] = (
           product_type == "frame" and "sliding" in opening_system
       )
       # ... 7 more hardcoded rules
   ```
   
   **Should Be:**
   ```python
   # ✅ YAML-DRIVEN
   async def evaluate_business_rules_from_config(form_data, page_type):
       config = await load_page_config(page_type)
       visibility = {}
       
       for attr in config['attributes']:
           if 'display_condition' in attr:
               visibility[attr['name']] = evaluate_condition(
                   attr['display_condition'],
                   form_data
               )
       
       return visibility
   ```

2. **Cross-Field Validation**
   ```python
   # ❌ HARDCODED in entry.py
   def validate_cross_field_rules(form_data, schema):
       errors = {}
       
       # Hardcoded: flyscreen track dependencies
       if form_data.get("builtin_flyscreen_track") is True:
           if not form_data.get("total_width"):
               errors["total_width"] = "Total width is required..."
       
       # Hardcoded: height difference tolerance
       if abs(front_height - rear_height) > 50:  # 50mm hardcoded
           errors["rear_height"] = "Rear height should not differ..."
       
       # Hardcoded: price calculation tolerance
       if abs(expected - actual) > expected * 0.1:  # 10% hardcoded
           errors["price_per_beam"] = "Price per beam should be..."
   ```
   
   **Should Be:**
   ```yaml
   # ✅ YAML-DRIVEN
   - name: total_width
     validation_rules:
       required_when:
         field: builtin_flyscreen_track
         operator: equals
         value: true
       error_message: "Total width is required when builtin flyscreen track is enabled"
   
   - name: rear_height
     validation_rules:
       tolerance_check:
         compare_field: front_height
         max_difference: 50
         unit: mm
   ```

3. **Entity Type Lists**
   ```python
   # ❌ HARDCODED in profile.py
   valid_types = ["company", "material", "opening_system", "system_series", "color"]
   
   # ❌ HARDCODED in glazing.py
   valid_types = ["glass_type", "spacer", "gas"]
   ```
   
   **Should Be:**
   ```yaml
   # ✅ YAML-DRIVEN
   # profile.yaml
   entity_types:
     - company
     - material
     - opening_system
     - system_series
     - color
   
   # glazing.yaml
   entity_types:
     - glass_type
     - spacer
     - gas
   ```

### The Root Cause

**The system has two sources of truth:**

1. **YAML files** (for setup)
   - Define attribute structure
   - Define display conditions
   - Define validation rules

2. **Python code** (for runtime)
   - Hardcoded business rules
   - Hardcoded validation logic
   - Hardcoded entity types

**Result:** Changing YAML doesn't change runtime behavior.

### Example of the Problem

**Scenario:** Business wants to change when "renovation" field is visible.

**Current Process (Broken):**
1. Edit `profile.yaml`:
   ```yaml
   - name: renovation
     display_condition:
       operator: equals
       field: type
       value: Sash  # Changed from Frame to Sash
   ```

2. Run setup script:
   ```bash
   python backend/scripts/setup_hierarchy.py profile
   ```

3. Database updated ✅
   ```sql
   UPDATE attribute_nodes 
   SET display_condition = '{"operator": "equals", "field": "type", "value": "Sash"}'
   WHERE name = 'renovation';
   ```

4. **But runtime behavior unchanged! ❌**
   ```python
   # entry.py still has:
   visibility["renovation"] = product_type == "frame"  # Still checking for "frame"!
   ```

5. **Must also edit Python code:**
   ```python
   # entry.py
   visibility["renovation"] = product_type == "sash"  # Manual code change required
   ```

6. **Must redeploy application** ❌

**Correct Process (What Should Happen):**
1. Edit `profile.yaml` only
2. Run setup script
3. Database updated
4. **Runtime automatically uses new condition** ✅
5. **No code changes needed** ✅
6. **No deployment needed** ✅

---

## Summary: How WindX Works

### The Good Parts ✅

1. **EAV Pattern Implementation**
   - Flexible attribute storage
   - No schema changes for new attributes
   - Polymorphic value columns

2. **Hierarchical Structure**
   - LTREE for efficient tree queries
   - Logical organization
   - Fast ancestor/descendant lookups

3. **YAML-Driven Setup**
   - Single source of truth for attribute definitions
   - Easy to add new attributes
   - Version controlled configuration

4. **Dynamic Form Generation**
   - Forms generated from database
   - No hardcoded form fields
   - Automatic UI rendering

5. **Comprehensive Metadata**
   - Display conditions stored in JSONB
   - Validation rules stored in JSONB
   - Pricing formulas stored in database

### The Missing Parts ❌

1. **Runtime Configuration Loader**
   - No mechanism to load YAML at runtime
   - Configuration only used during setup
   - Changes require database queries, not YAML reads

2. **Dynamic Condition Evaluation**
   - ConditionEvaluator exists but not used for business rules
   - Business rules hardcoded in Python
   - display_condition from database ignored

3. **Dynamic Validation Engine**
   - Validation rules stored but not evaluated
   - Cross-field validation hardcoded
   - Tolerance values hardcoded

4. **Entity Type Management**
   - Entity types hardcoded in multiple files
   - Not loaded from configuration
   - Duplicated across services and schemas

### The Path Forward

To complete the YAML-driven architecture:

1. **Create RuntimeConfigLoader**
   - Load YAML configurations at runtime
   - Cache for performance
   - Hot-reload support

2. **Implement Dynamic Evaluation**
   - Use ConditionEvaluator for business rules
   - Evaluate display_condition from database
   - Remove hardcoded rules

3. **Build Validation Engine**
   - Evaluate validation_rules from database
   - Support cross-field validation
   - Dynamic tolerance values

4. **Centralize Entity Types**
   - Load from YAML configuration
   - Remove hardcoded lists
   - Dynamic schema generation

**Result:** True zero-code configuration where YAML changes immediately affect runtime behavior.

---

## Conclusion

WindX has built a **solid foundation** with:
- ✅ EAV pattern for flexible attributes
- ✅ LTREE for hierarchical organization
- ✅ YAML-driven setup scripts
- ✅ Dynamic form generation
- ✅ Comprehensive metadata storage

But it's **incomplete** because:
- ❌ Runtime behavior is hardcoded
- ❌ YAML changes don't affect application
- ❌ Business rules duplicated in code
- ❌ Validation logic not dynamic

**The system is 70% YAML-driven, 30% hardcoded.**

To reach 100%, implement the runtime configuration layer that bridges the gap between database metadata and application behavior.

