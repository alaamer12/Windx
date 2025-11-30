---
trigger: always_on
---

# Windx Configurator System Overview

## Executive Summary

Windx is an automated window and door configurator system that empowers customers to design, customize, and order manufactured products through a dynamic, hierarchical attribute system. The system provides real-time pricing, automated quote generation, and a flexible template system—all without requiring database schema changes when adding new product types or attributes.

**Key Capabilities:**
- Self-service product configuration with full transparency
- Dynamic hierarchical attributes (unlimited depth)
- Real-time automated pricing calculations
- Pre-defined configuration templates
- Quote generation with price snapshots
- Complete order lifecycle management

**Target Users:**
- **Customers**: Configure products independently with instant pricing
- **Sales Teams**: Assist customers and generate quotes quickly
- **Data Entry Staff**: Create and manage product templates
- **Administrators**: Manage product types and attribute hierarchies

---

## Business Context

### Business Drivers

**Customer Empowerment**
- Customers want to design their own products without waiting for sales calls
- Transparency in pricing builds trust and reduces friction
- Self-service reduces sales cycle time and operational costs

**Operational Efficiency**
- Manual quote generation is time-consuming and error-prone
- Product configuration knowledge is often siloed in individual salespeople
- Scaling requires automation, not more staff

**Market Expansion**
- New product lines should be easy to add without IT involvement
- Different markets may require different attribute combinations
- System must adapt to changing business needs

### Business Objectives

1. **Enhance Customer Satisfaction**: Provide clarity, control, and personalization
2. **Reduce Manual Overhead**: Automate pricing, quotes, and order processing
3. **Improve Profit Margins**: Accurate pricing prevents undercharging
4. **Enable Strategic Growth**: Scale to new products and markets easily

### Success Metrics

- Reduction in quote generation time (target: 80% faster)
- Increase in customer self-service rate (target: 60% of orders)
- Reduction in pricing errors (target: 95% accuracy)
- Time to add new product type (target: < 1 day)

---

## System Architecture Overview

### High-Level Flow

```
Customer → Product Type Selection → Attribute Configuration → 
Real-time Pricing → Template (Optional) → Quote Generation → 
Order Placement → Production
```

### Core Components

1. **Manufacturing Types**: Product categories (Window, Door, Table, etc.)
2. **Attribute Hierarchy**: Dynamic tree of configurable options
3. **Configuration Engine**: Manages customer selections and calculations
4. **Pricing Engine**: Real-time price computation with formulas
5. **Template System**: Pre-defined common configurations
6. **Quote System**: Price snapshots with validity periods
7. **Order Management**: Full order lifecycle tracking

---

## The Hierarchical Attribute System

### Conceptual Model

The Windx system uses a **hierarchical attribute tree** where each product type has its own tree of configurable options. This tree can be arbitrarily deep and supports conditional display logic.

### How It Works: Type → Options → Sub-options → Sub-sub-options

**Example: Window Configuration**

```
Window (Manufacturing Type)
├── Frame Material (Category)
│   ├── Material Type (Attribute)
│   │   ├── Aluminum (Option) [+$50]
│   │   ├── Wood (Option) [+$120]
│   │   └── Vinyl (Option) [+$30]
│   └── Frame Color (Attribute) - shown only if Wood selected
│       ├── Natural Oak (Option) [+$25]
│       ├── Walnut Stain (Option) [+$35]
│       └── White Paint (Option) [+$15]
├── Glass Type (Category)
│   ├── Pane Count (Attribute)
│   │   ├── Single Pane (Option) [+$0]
│   │   ├── Double Pane (Option) [+$80]
│   │   └── Triple Pane (Option) [+$150]
│   └── Glass Coating (Attribute) - shown only if Double/Triple Pane
│       ├── Low-E Coating (Option) [+$40]
│       ├── Tinted (Option) [+$30]
│       └── UV Protection (Option) [+$50]
└── Dimensions (Category)
    ├── Width (Attribute) [formula: width * $5/inch]
    ├── Height (Attribute) [formula: height * $5/inch]
    └── Opening Style (Attribute)
        ├── Casement (Option) [+$60]
        ├── Double-Hung (Option) [+$45]
        └── Sliding (Option) [+$35]
```

### Node Types

**Category**: Organizational grouping (e.g., "Frame Material", "Glass Type")
- No direct value
- Contains attributes or sub-categories
- Used for UI organization

**Attribute**: A configurable property (e.g., "Material Type", "Width")
- Has a data type (string, number, boolean, formula)
- Can be required or optional
- May have validation rules

**Option**: A specific choice for an attribute (e.g., "Aluminum", "Wood")
- Has a price impact (fixed amount, percentage, or formula)
- May have weight impact for shipping calculations
- Can trigger conditional display of other attributes

### Conditional Display Logic

Attributes can be shown or hidden based on previous selections:

**Example**: "Frame Color" only appears if "Wood" is selected for "Material Type"

```json
{
  "display_condition": {
    "operator": "equals",
    "field": "parent.material_type",
    "value": "Wood"
  }
}
```

**Supported Conditions**:
- `equals`: Field must equal specific value
- `contains`: Field must contain value
- `gt` / `lt`: Greater than / less than (for numbers)
- `exists`: Field must have any value
- `and` / `or`: Combine multiple conditions

### Validation Rules

Each attribute can have validation rules:

```json
{
  "validation_rules": {
    "rule_type": "range",
    "min": 24,
    "max": 96,
    "message": "Width must be between 24 and 96 inches"
  }
}
```

---

## Hybrid Database Approach

The Windx system uses a **hybrid database architecture** combining three powerful PostgreSQL features:

### 1. Relational Structure (Traditional Tables)

**Purpose**: Maintain data integrity and relationships

**Tables**:
- `manufacturing_types`: Product categories
- `attribute_nodes`: Hierarchical attribute definitions
- `configurations`: Customer product designs
- `configuration_selections`: Individual attribute choices
- `customers`, `quotes`, `orders`: Business entities

**Benefits**:
- Foreign key constraints ensure referential integrity
- Standard SQL queries for business logic
- Easy to understand and maintain
- ACID transactions guarantee consistency

### 2. LTREE (Hierarchical Paths)

**Purpose**: Fast hierarchical queries without recursion

**What is LTREE?**
LTREE is a PostgreSQL extension that stores hierarchical labels as dot-separated paths:
- `window.frame_material.material_type.wood`
- `window.glass_type.pane_count.double_pane`

**Why LTREE?**
- **Fast Descendant Queries**: "Get all options under Frame Material" is a single indexed query
- **Fast Ancestor Queries**: "Get all parents of this option" is instant
- **Pattern Matching**: "Find all nodes with 'coating' in path" uses regex
- **No Recursion Needed**: Traditional recursive queries become slow at depth

**Example Query**:
```sql
-- Get all descendants of "frame_material" (instant with GiST index)
SELECT * FROM attribute_nodes 
WHERE ltree_path <@ 'window.frame_material'::ltree;

-- Get all ancestors of "walnut_stain"
SELECT * FROM attribute_nodes 
WHERE 'window.frame_material.frame_color.walnut_stain'::ltree <@ ltree_path;
```

**Performance**: O(log n) with GiST index, regardless of tree depth

### 3. JSONB (Flexible Metadata)

**Purpose**: Store flexible, schema-less data

**Use Cases**:
- **Display Conditions**: Complex conditional logic without schema changes
- **Validation Rules**: Flexible validation without code deployment
- **Technical Specifications**: Product-specific data (U-value, load capacity)
- **Price Breakdowns**: Detailed cost component tracking
- **Customer Addresses**: Flexible address formats for different regions

**Example**:
```json
{
  "display_condition": {
    "operator": "and",
    "conditions": [
      {"field": "material_type", "operator": "equals", "value": "Wood"},
      {"field": "pane_count", "operator": "gt", "value": 1}
    ]
  },
  "validation_rules": {
    "rule_type": "pattern",
    "pattern": "^[A-Z]{2}\\d{5}$",
    "message": "Invalid format"
  }
}
```

### Why This Hybrid Approach?

| Requirement | Solution | Benefit |
|-------------|----------|---------|
| Data integrity | Relational tables with foreign keys | Prevents orphaned records |
| Fast tree queries | LTREE paths with GiST indexes | No slow recursive CTEs |
| Flexible metadata | JSONB columns | No schema changes for new logic |
| Type safety | Relational columns for core data | Database enforces types |
| Complex conditions | JSONB for rules | Add new condition types without code |
| Audit trail | Relational history tables | Track all changes |

### Synchronization Strategy

The system maintains consistency between adjacency list and LTREE using **database triggers**:

1. When a node is inserted/updated, a trigger automatically:
   - Computes the LTREE path from parent relationships
   - Updates the depth field
   - Cascades path updates to all descendants

2. Application code only manages `parent_node_id`
3. Database ensures LTREE and depth stay synchronized

**Result**: Best of both worlds—easy writes (adjacency list) and fast reads (LTREE)

---

## Pricing Calculation System

### Pricing Model

**Base Price**: Every manufacturing type has a base price (e.g., Window base = $200)

**Option Impacts**: Each selected option can affect price in three ways:

1. **Fixed Amount**: Add/subtract a fixed dollar amount
   - Example: "Aluminum Frame" adds $50

2. **Percentage**: Add/subtract a percentage of current price
   - Example: "Premium Finish" adds 15%

3. **Formula**: Calculate based on other selections
   - Example: "Width" uses formula: `width_inches * $5`

### Price Calculation Flow

```
1. Start with base price from manufacturing type
   Base: $200

2. Add fixed price impacts from selected options
   + Aluminum Frame: $50
   + Double Pane Glass: $80
   + Casement Opening: $60
   Subtotal: $390

3. Apply percentage impacts
   + Premium Finish (15%): $58.50
   Subtotal: $448.50

4. Apply formula-based impacts
   + Width (48 inches * $5): $240
   + Height (60 inches * $5): $300
   Final Total: $988.50
```

### Formula System

**Formula Storage**: Formulas are stored as text in the database:
```sql
price_formula: "width * height * 0.05"
weight_formula: "width * height * 0.002"
```

**Formula Evaluation**: Application code safely evaluates formulas:
- Parse formula string
- Substitute variables from configuration
- Validate for safety (no dangerous operations)
- Compute result

**Available Variables**:
- `width`, `height`, `depth`: Dimension values
- `base_price`: Current base price
- `quantity`: Order quantity
- Any other selected numeric attribute

**Example Formulas**:
```
Simple: "width * 5"
Complex: "(width * height * 0.05) + (depth * 2)"
Conditional: "pane_count > 1 ? base_price * 1.2 : base_price"
```

### Real-Time Calculation

As the customer makes selections:
1. Frontend sends selection to backend
2. Backend updates `configuration_selections` table
3. Database trigger recalculates total price
4. Updated price returned to frontend
5. UI updates instantly

**Performance**: Calculations complete in < 100ms for typical configurations

### Price History and Snapshots

**Problem**: Prices change over time, but quotes must remain valid

**Solution**: Configuration snapshots
- When a quote is generated, create a snapshot of:
  - All selections
  - All price impacts
  - Total calculated price
  - Technical specifications
- Quote references the snapshot, not live configuration
- Customer sees the same price even if base prices change later
