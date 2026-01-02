# WindX Database Schema Explanations

This document provides a comprehensive explanation of the WindX database schema, including the Entity-Relationship Diagram (ERD), table purposes, design decisions, and data flow patterns.

---

## Table of Contents

1. [High-Level ERD Overview](#high-level-erd-overview)
2. [Core Table Purposes](#core-table-purposes)
3. [Key Design Decisions](#key-design-decisions)
4. [Data Flow Through the System](#data-flow-through-the-system)
5. [Column Purpose Reference](#column-purpose-reference)

---

## High-Level ERD Overview

The WindX database implements a flexible product configuration system using a hybrid approach that combines:

- **Hierarchical attribute trees** (using LTREE for efficient traversal)
- **EAV-style flexibility** (attributes defined as data, not schema columns)
- **Template-based configuration** (reusable pre-configured products)
- **Snapshot-based pricing** (historical price tracking for quotes)

### Entity Relationship Structure

```
Manufacturing Types (Product Categories)
    ↓
Attribute Nodes (Hierarchical Configuration Options)
    ↓
Configurations (Customer Product Designs)
    ↓
Configuration Selections (Chosen Attributes)
    ↓
Quotes (Price Snapshots)
    ↓
Orders (Confirmed Purchases)
```

### Parallel Template System

```
Configuration Templates (Pre-defined Designs)
    ↓
Template Selections (Pre-selected Attributes)
    ↓
Template Usage (Tracking & Metrics)
```

---

## Core Table Purposes


### 1. Manufacturing Types Table

**Purpose**: Defines product categories (Windows, Doors, Tables, etc.)

**Why it exists**: 
- Provides the top-level classification for all products
- Each product type has its own attribute tree
- Stores base pricing and weight for each product category
- Allows the system to support multiple product lines without schema changes

**Key characteristics**:
- One manufacturing type = one complete attribute hierarchy
- Base price and weight serve as starting points for calculations
- Can be activated/deactivated without deleting data
- Supports categorization (window, furniture, door) for grouping

**Example**: A "Casement Window" manufacturing type would have base_price=$200, base_weight=15kg, and its own attribute tree for glass type, frame material, hardware options, etc.

---

### 2. Attribute Nodes Table

**Purpose**: Defines the hierarchical structure of product configuration options

**Why it exists**:
- Provides unlimited flexibility for product configuration without schema changes
- Supports nested attributes (e.g., Frame → Material → Color)
- Stores pricing impacts, formulas, and validation rules at each node
- Enables conditional display logic (show option X only if Y is selected)

**Node types**:
- `category`: Organizational grouping (e.g., "Frame Options")
- `attribute`: Configurable property (e.g., "Frame Material")
- `option`: Selectable choice (e.g., "Aluminum", "Vinyl")
- `component`: Physical component (e.g., "Handle", "Lock")
- `technical_spec`: Technical property (e.g., "U-Value", "Load Capacity")

**Key characteristics**:
- Self-referential hierarchy using `parent_node_id`
- LTREE path for efficient tree traversal
- Universal properties: price_impact, weight_impact (all products have these)
- Specialized properties: technical_property_type (product-specific)
- Dynamic behavior: display_condition, validation_rules (JSONB)

**Example**: 
```
Frame Options (category)
  └─ Frame Material (attribute)
      ├─ Aluminum (option, +$50, +2kg)
      ├─ Vinyl (option, +$30, +1.5kg)
      └─ Wood (option, +$100, +3kg)
```

---

### 3. Configurations Table

**Purpose**: Represents individual customer product designs

**Why it exists**:
- Each configuration is a unique product design created by a customer
- Stores calculated totals (price, weight, technical specs)
- Tracks configuration status (draft, saved, quoted, ordered)
- Links to customer and manufacturing type

**Key characteristics**:
- One configuration = one product instance
- Stores calculated results (total_price, calculated_weight)
- JSONB field for flexible technical specifications
- Reference code for easy identification
- Status tracking through the sales pipeline

**Example**: "Living Room Bay Window" configuration with total_price=$1,250, calculated_weight=45kg, status='quoted'

---

### 4. Configuration Selections Table

**Purpose**: Stores the specific attribute choices made for each configuration

**Why it exists**:
- Implements the EAV (Entity-Attribute-Value) pattern
- Links configurations to their selected attributes
- Stores flexible values (string, numeric, boolean, JSON)
- Tracks calculated impacts (price, weight, technical)

**Key characteristics**:
- One row per attribute selection
- Flexible value storage based on attribute data type
- Stores calculated impacts for performance
- LTREE selection_path for hierarchical context
- Unique constraint prevents duplicate selections

**Example**: Configuration #123 selects "Aluminum" frame (string_value='Aluminum', calculated_price_impact=50.00, calculated_weight_impact=2.00)

---


### 5. Configuration Templates Table

**Purpose**: Pre-defined product configurations that can be reused

**Why it exists**:
- Speeds up configuration process for common products
- Provides starting points for customers
- Tracks which templates convert to orders (success metrics)
- Reduces data entry errors with validated pre-sets

**Key characteristics**:
- Links to manufacturing type
- Stores estimated price/weight for quick reference
- Tracks usage count and success rate
- Can be public (customer-facing) or private (internal)
- Template types: standard, premium, economy, custom

**Example**: "Standard Double-Hung Window" template with pre-selected vinyl frame, double-pane glass, standard hardware

---

### 6. Template Selections Table

**Purpose**: Stores the pre-selected attribute choices for each template

**Why it exists**:
- Defines what makes a template a template (the pre-configured choices)
- When a customer uses a template, these selections are copied to configuration_selections
- Allows templates to be modified without affecting existing configurations

**Key characteristics**:
- Mirrors structure of configuration_selections
- One row per pre-selected attribute
- Cascade deletes when template is deleted
- LTREE path for hierarchical context

**Example**: "Standard Window" template has pre-selections for frame_material='Vinyl', glass_type='Double Pane', hardware='Standard'

---

### 7. Template Usage Table

**Purpose**: Tracks when and how templates are used

**Why it exists**:
- Analytics: which templates are most popular?
- Conversion tracking: which templates lead to orders?
- Customer insights: what do customers start with?
- Success metrics: calculate template effectiveness

**Key characteristics**:
- Links template to resulting configuration
- Tracks usage context (customer_start, sales_assist, quick_quote)
- Conversion flags (converted_to_quote, converted_to_order)
- Enables template success rate calculations

**Example**: Template #5 used 47 times, 23 converted to quotes, 12 converted to orders (25.5% success rate)

---

### 8. Template Categories Table

**Purpose**: Organizes templates into browsable categories

**Why it exists**:
- Helps customers find relevant templates quickly
- Supports nested categories (e.g., Windows → Casement → Energy Efficient)
- Enables filtering and search in UI
- Allows same template in multiple categories

**Key characteristics**:
- Self-referential for nested categories
- Sort order for display control
- Can be activated/deactivated
- Many-to-many relationship with templates via junction table

**Example**: Categories like "Energy Efficient", "Budget Friendly", "Premium", "Commercial Grade"

---

### 9. Customers Table

**Purpose**: Stores customer information and business relationships

**Why it exists**:
- Links configurations and quotes to customers
- Stores contact and billing information
- Tracks customer type (residential, commercial, contractor)
- Maintains payment terms and tax information

**Key characteristics**:
- JSONB address for flexible international formats
- Customer type affects pricing and terms
- Can be active/inactive without deletion
- Internal notes for sales team

**Example**: "ABC Construction" (commercial contractor, net-30 terms, tax_id=12-3456789)

---

### 10. Quotes Table

**Purpose**: Formal price proposals for configurations

**Why it exists**:
- Provides official pricing to customers
- Tracks quote validity period
- Stores pricing breakdown (subtotal, tax, discounts)
- Links to configuration snapshot for price protection

**Key characteristics**:
- Unique quote number for reference
- Validity period (quotes expire)
- Status tracking (draft, sent, accepted, expired)
- Links to configuration snapshot (immutable pricing)
- Tax and discount calculations

**Example**: Quote Q-2024-001 for $1,250 (valid until 2024-12-31, status='sent')

---


### 11. Orders Table

**Purpose**: Confirmed purchases that enter production

**Why it exists**:
- Converts accepted quotes into production orders
- Tracks delivery dates and special instructions
- Manages order status through fulfillment
- Links to installation/delivery address

**Key characteristics**:
- Unique order number
- Timeline tracking (order_date, required_date)
- Status progression (confirmed → production → shipped → installed)
- JSONB installation address (may differ from customer address)
- Special instructions for production/installation

**Example**: Order O-2024-001 (confirmed, required_date=2024-02-15, status='production')

---

### 12. Order Items Table

**Purpose**: Links orders to configurations (orders can have multiple items)

**Why it exists**:
- Supports multi-item orders (e.g., 5 windows + 2 doors)
- Tracks quantity per configuration
- Stores unit and total pricing
- Monitors production status per item

**Key characteristics**:
- Many-to-many between orders and configurations
- Quantity support (order 10 of the same window)
- Production status per item (some items may ship before others)
- Price snapshot at order time

**Example**: Order #123 contains 3x "Bay Window" config at $1,250 each = $3,750 total

---

### 13. Configuration Snapshots Table

**Purpose**: Historical records of configuration pricing and specifications

**Why it exists**:
- **Price protection**: Locks in quoted prices even if base prices change
- **Audit trail**: Shows what was quoted vs what was ordered
- **Historical analysis**: Compare pricing over time
- **Regulatory compliance**: Maintain records of what was sold

**Key characteristics**:
- Immutable records (never updated, only created)
- Stores complete breakdowns (price, weight, technical specs)
- Links to quote for price protection
- Snapshot types: price_quote, technical_calculation, order_confirmation
- Validity period for quotes

**Example**: Snapshot created when quote is generated, preserving $1,250 price even if aluminum frame price increases next week

---

### 14. Price History Tables

**Purpose**: Track changes to base prices and attribute pricing over time

**Why it exists**:
- Audit trail for price changes
- Understand pricing trends
- Regulatory compliance
- Analyze impact of price changes on sales

**Tables**:
- `manufacturing_type_price_history`: Base price changes
- `attribute_node_history`: Attribute price/weight/formula changes

**Key characteristics**:
- Triggered automatically on updates
- Stores old and new values
- Includes change reason and who made the change
- Effective date tracking

**Example**: Aluminum frame price increased from $50 to $55 on 2024-01-15 due to "Raw material cost increase"

---

### 15. Users Table

**Purpose**: System access and authentication

**Why it exists**:
- Controls who can access the system
- Role-based permissions (admin, customer, sales)
- Tracks user activity (last_login)
- Links to created templates and configurations

**Key characteristics**:
- Email-based authentication
- Password hashing for security
- Role-based access control
- Activity tracking

**Example**: user@example.com (role='customer', last_login=2024-01-20)

---

## Key Design Decisions


### Why Manufacturing Types Table?

**Problem**: How do we support multiple product categories (windows, doors, furniture) without creating separate schemas for each?

**Solution**: Manufacturing types table provides:

1. **Product category abstraction**: One table defines all product types
2. **Isolated attribute trees**: Each type has its own attribute hierarchy
3. **Base pricing/weight**: Starting point for calculations
4. **Easy expansion**: Add new product types without schema changes

**Alternative approaches considered**:
- ❌ Separate tables per product type (rigid, requires migrations)
- ❌ Single monolithic product table (can't handle different attributes)
- ✅ Manufacturing types + flexible attributes (chosen approach)

**Benefits**:
- Add "Garage Doors" product type in 1 INSERT statement
- Each product type has completely different attributes
- No schema changes needed for new product lines
- Base price/weight provides consistent calculation foundation

---

### Why LTREE for Attribute Nodes?

**Problem**: How do we efficiently query hierarchical attribute trees without expensive recursive queries?

**Solution**: PostgreSQL LTREE extension provides:

1. **Materialized paths**: Store full hierarchy path as `metal.hardness.scale.brinell`
2. **Fast descendant queries**: `WHERE path <@ 'metal.hardness'` (all descendants)
3. **Fast ancestor queries**: `WHERE 'metal.hardness.scale' <@ path` (all ancestors)
4. **Pattern matching**: `WHERE path ~ '*.scale.*'` (find all scale attributes)
5. **GiST indexing**: O(log n) performance for hierarchical queries

**Alternative approaches considered**:
- ❌ Pure adjacency list: Requires recursive CTEs (slow for deep trees)
- ❌ Closure table: Storage overhead, complex updates
- ❌ Nested sets: Fast reads but expensive writes
- ✅ Adjacency + LTREE hybrid: Best of both worlds

**Benefits**:
- Single-query descendant/ancestor lookups (no recursion)
- Efficient at any depth (10+ levels)
- Pattern matching for complex queries
- Maintains simple parent_node_id for easy updates

**Tradeoff**: PostgreSQL-specific (vendor lock-in), but performance gains justify it

---

### Why Separate Configuration and Configuration_Selections?

**Problem**: How do we store flexible attribute selections without creating columns for every possible attribute?

**Solution**: Separate tables implement EAV (Entity-Attribute-Value) pattern:

**Configurations table**:
- Stores configuration metadata (name, status, customer)
- Stores calculated totals (total_price, calculated_weight)
- One row per product design

**Configuration_selections table**:
- Stores individual attribute choices
- Flexible value storage (string, numeric, boolean, JSON)
- Many rows per configuration (one per selected attribute)

**Why not combine them?**
- ❌ JSONB blob: Hard to query, no referential integrity
- ❌ Columns per attribute: Requires schema changes, sparse data
- ✅ Separate tables: Queryable, flexible, normalized

**Benefits**:
- Add new attributes without schema changes
- Query specific attribute selections efficiently
- Maintain referential integrity (foreign keys)
- Calculate impacts per selection
- Support any number of attributes per configuration

**Example**:
```
Configuration #123: "Living Room Window"
  Selection #1: frame_material = "Aluminum" (+$50)
  Selection #2: glass_type = "Triple Pane" (+$200)
  Selection #3: hardware = "Premium" (+$75)
  Total: $200 base + $325 options = $525
```

---

### Why Template System Tables?

**Problem**: How do we speed up configuration for common products without forcing customers to select every option?

**Solution**: Template system provides pre-configured starting points:

**Configuration_templates table**:
- Defines reusable product configurations
- Stores estimated pricing for quick reference
- Tracks usage metrics and success rates

**Template_selections table**:
- Stores pre-selected attribute choices
- Copied to configuration_selections when template is used

**Template_usage table**:
- Tracks which templates are popular
- Measures conversion rates (template → quote → order)
- Provides analytics for template effectiveness

**Why not just copy configurations?**
- ❌ Copying configurations: No metrics, no updates, no categorization
- ✅ Template system: Trackable, updatable, analyzable

**Benefits**:
- Faster configuration (start with 80% complete)
- Reduced errors (validated pre-sets)
- Analytics (which templates convert best?)
- Marketing insights (what do customers want?)
- Continuous improvement (update templates based on data)

**Example workflow**:
1. Customer selects "Standard Casement Window" template
2. System copies template_selections to configuration_selections
3. Customer modifies a few options (glass type, color)
4. Template_usage records this (template_id, configuration_id)
5. If customer orders, template success_rate increases

---


### Why Quote Snapshot Approach?

**Problem**: What happens when prices change after a quote is sent but before the customer accepts?

**Solution**: Configuration snapshots provide immutable price records:

**Without snapshots**:
```
Day 1: Quote sent for $1,250 (aluminum frame = $50)
Day 5: Aluminum price increases to $55
Day 7: Customer accepts quote
Result: Price is now $1,255 (customer sees different price!)
```

**With snapshots**:
```
Day 1: Quote sent for $1,250
        → Snapshot created with complete price breakdown
Day 5: Aluminum price increases to $55
Day 7: Customer accepts quote
Result: Price is still $1,250 (snapshot protects quoted price)
```

**Configuration_snapshots table stores**:
- Complete price breakdown (base + options)
- Complete weight breakdown
- Technical specifications at quote time
- Validity period (quote expiration)
- Snapshot type (price_quote, order_confirmation)

**Benefits**:
- **Price protection**: Quoted prices are honored
- **Audit trail**: See what was quoted vs current pricing
- **Customer trust**: No surprise price changes
- **Regulatory compliance**: Maintain records of transactions
- **Historical analysis**: Compare pricing over time

**Alternative approaches considered**:
- ❌ Recalculate on demand: Prices change, customer confusion
- ❌ Lock prices globally: Can't update pricing for new quotes
- ✅ Snapshot per quote: Isolated, immutable, auditable

---

## Data Flow Through the System

### Flow 1: Creating a Configuration from Scratch

```
1. Customer selects Manufacturing Type
   └─ "Casement Window" (base_price=$200, base_weight=15kg)

2. System loads Attribute Nodes for that type
   └─ Frame Options → Material → [Aluminum, Vinyl, Wood]
   └─ Glass Options → Type → [Single, Double, Triple]
   └─ Hardware Options → Quality → [Standard, Premium]

3. Customer makes selections
   └─ INSERT INTO configuration_selections
       - frame_material = "Aluminum" (+$50, +2kg)
       - glass_type = "Triple Pane" (+$200, +5kg)
       - hardware = "Premium" (+$75, +1kg)

4. System calculates totals (via trigger)
   └─ UPDATE configurations SET
       total_price = $200 + $50 + $200 + $75 = $525
       calculated_weight = 15 + 2 + 5 + 1 = 23kg

5. Configuration saved (status='draft')
```

---

### Flow 2: Creating a Configuration from Template

```
1. Customer browses Template Categories
   └─ "Energy Efficient" → "Standard Casement Window"

2. Customer selects template
   └─ Function: create_configuration_from_template(template_id)

3. System creates new configuration
   └─ INSERT INTO configurations (from template metadata)

4. System copies template selections
   └─ INSERT INTO configuration_selections
       SELECT * FROM template_selections WHERE template_id = X

5. System records usage
   └─ INSERT INTO template_usage (template_id, configuration_id)

6. Customer modifies selections (optional)
   └─ UPDATE configuration_selections (change glass type)

7. Configuration ready (status='draft')
```

---

### Flow 3: Quote Generation with Price Protection

```
1. Customer requests quote for configuration
   └─ Configuration #123 (total_price=$525)

2. System creates quote
   └─ Function: create_quote_with_snapshot(config_id, customer_id)
   └─ INSERT INTO quotes (quote_number, subtotal, tax, total)

3. System creates snapshot (CRITICAL STEP)
   └─ INSERT INTO configuration_snapshots
       - base_price = $200
       - total_price = $525
       - price_breakdown = {"base": 200, "options": 325}
       - weight_breakdown = {"base": 15, "options": 8}
       - technical_snapshot = {u_value: 0.28, ...}
       - valid_until = 30 days from now

4. Quote sent to customer (status='sent')

5. Prices change in system
   └─ Aluminum frame: $50 → $55 (trigger logs to history)

6. Customer accepts quote
   └─ Quote references snapshot (price still $525)
   └─ UPDATE quotes SET status='accepted'

7. Order created from quote
   └─ INSERT INTO orders (quote_id, order_number)
   └─ Order uses snapshot pricing (customer pays $525, not $530)
```

---

### Flow 4: Order Fulfillment

```
1. Order created from accepted quote
   └─ INSERT INTO orders (quote_id, order_number, status='confirmed')

2. Order items created
   └─ INSERT INTO order_items
       - configuration_id = 123
       - quantity = 3
       - unit_price = $525 (from snapshot)
       - total_price = $1,575

3. Production begins
   └─ UPDATE order_items SET production_status='in_production'

4. Items ship
   └─ UPDATE order_items SET production_status='shipped'
   └─ UPDATE orders SET status='shipped'

5. Installation complete
   └─ UPDATE orders SET status='installed'
```

---

### Flow 5: Template Analytics

```
1. Template used
   └─ INSERT INTO template_usage (template_id, configuration_id)

2. Configuration becomes quote
   └─ UPDATE template_usage SET converted_to_quote=true

3. Quote becomes order
   └─ UPDATE template_usage SET converted_to_order=true
   └─ Trigger: update_template_success_metrics()

4. Template metrics updated
   └─ UPDATE configuration_templates SET
       usage_count = (count of template_usage)
       success_rate = (converted_to_order / total_usage * 100)

5. Business insights
   └─ Query: Which templates have highest success rate?
   └─ Query: Which templates are most popular?
   └─ Query: Which templates need improvement?
```

---


## Column Purpose Reference

### Manufacturing Types Table

| Column | Purpose | Example |
|--------|---------|---------|
| `id` | Primary key | 1 |
| `name` | Product category name | "Casement Window" |
| `description` | Detailed description | "Energy-efficient casement windows..." |
| `base_category` | High-level grouping | "window" |
| `image_url` | Product image | "/images/casement.jpg" |
| `base_price` | Starting price | 200.00 |
| `base_weight` | Base weight in kg | 15.00 |
| `is_active` | Available for sale | true |
| `created_at` | Creation timestamp | 2024-01-01 10:00:00 |
| `updated_at` | Last modification | 2024-01-15 14:30:00 |

---

### Attribute Nodes Table

| Column | Purpose | Example |
|--------|---------|---------|
| `id` | Primary key | 42 |
| `manufacturing_type_id` | Which product type | 1 (Casement Window) |
| `parent_node_id` | Parent in hierarchy | 10 (Frame Options) |
| `name` | Display name | "Frame Material" |
| `node_type` | Type of node | "attribute" |
| `data_type` | Value type | "string" |
| `display_condition` | When to show | {"parent.selected": "custom"} |
| `validation_rules` | Input validation | {"min": 10, "max": 100} |
| `required` | Must be selected | true |
| `price_impact_type` | How it affects price | "fixed" |
| `price_impact_value` | Price change | 50.00 |
| `price_formula` | Dynamic pricing | "base_price * 1.15" |
| `weight_impact` | Weight change in kg | 2.00 |
| `weight_formula` | Dynamic weight | "area * density" |
| `technical_property_type` | Technical spec type | "u_value" |
| `technical_impact_formula` | Technical calculation | "1/(r_value + 0.5)" |
| `ltree_path` | Hierarchy path | "window.frame.material" |
| `depth` | Nesting level | 3 |
| `sort_order` | Display order | 1 |
| `ui_component` | UI control type | "dropdown" |
| `description` | Help text | "Select frame material" |
| `help_text` | Additional guidance | "Aluminum is most durable" |

**Key columns explained**:

- **node_type**: Determines behavior
  - `category`: Organizational grouping (no value)
  - `attribute`: Configurable property (has value)
  - `option`: Selectable choice (specific value)
  - `component`: Physical part (has properties)
  - `technical_spec`: Calculated property (formula-based)

- **data_type**: Determines value storage
  - `string`: Text values (colors, materials)
  - `number`: Numeric values (dimensions, quantities)
  - `boolean`: Yes/no choices (features)
  - `formula`: Calculated values (area, volume)
  - `dimension`: Size measurements (width, height)
  - `selection`: Choice from options

- **price_impact_type**: How pricing works
  - `fixed`: Add/subtract fixed amount (+$50)
  - `percentage`: Multiply by percentage (+15%)
  - `formula`: Calculate dynamically (area * price_per_sqft)

- **ltree_path**: Enables fast queries
  - Stores full path: `window.frame.material.aluminum`
  - Find descendants: `WHERE path <@ 'window.frame'`
  - Find ancestors: `WHERE 'window.frame.material' <@ path`
  - Pattern match: `WHERE path ~ '*.material.*'`

---

### Configurations Table

| Column | Purpose | Example |
|--------|---------|---------|
| `id` | Primary key | 123 |
| `manufacturing_type_id` | Product type | 1 (Casement Window) |
| `customer_id` | Who created it | 456 |
| `name` | Configuration name | "Living Room Window" |
| `description` | Customer notes | "Bay window facing south" |
| `status` | Current state | "quoted" |
| `reference_code` | Unique identifier | "WIN-2024-001" |
| `base_price` | Starting price | 200.00 |
| `total_price` | Final calculated price | 525.00 |
| `calculated_weight` | Total weight | 23.00 |
| `calculated_technical_data` | Technical specs | {"u_value": 0.28, "shgc": 0.35} |
| `created_at` | Creation time | 2024-01-10 09:00:00 |
| `updated_at` | Last modification | 2024-01-15 11:30:00 |

**Status values**:
- `draft`: Being configured
- `saved`: Saved for later
- `quoted`: Quote generated
- `ordered`: Converted to order

---

### Configuration Selections Table

| Column | Purpose | Example |
|--------|---------|---------|
| `id` | Primary key | 789 |
| `configuration_id` | Which configuration | 123 |
| `attribute_node_id` | Which attribute | 42 (Frame Material) |
| `string_value` | Text value | "Aluminum" |
| `numeric_value` | Number value | 48.5 |
| `boolean_value` | True/false value | true |
| `json_value` | Complex value | {"color": "white", "finish": "matte"} |
| `calculated_price_impact` | Price effect | 50.00 |
| `calculated_weight_impact` | Weight effect | 2.00 |
| `calculated_technical_impact` | Technical effect | {"u_value_impact": -0.05} |
| `selection_path` | Hierarchy context | "window.frame.material.aluminum" |
| `created_at` | Selection time | 2024-01-10 09:15:00 |

**Value storage logic**:
- Only one value column is populated per row
- `string_value`: For text selections (materials, colors)
- `numeric_value`: For numbers (dimensions, quantities)
- `boolean_value`: For yes/no (features enabled/disabled)
- `json_value`: For complex data (multiple properties)

---

### Configuration Templates Table

| Column | Purpose | Example |
|--------|---------|---------|
| `id` | Primary key | 10 |
| `name` | Template name | "Standard Casement Window" |
| `description` | Template description | "Most popular configuration" |
| `manufacturing_type_id` | Product type | 1 |
| `template_type` | Template category | "standard" |
| `is_public` | Customer visible | true |
| `usage_count` | Times used | 47 |
| `success_rate` | Conversion rate | 25.50 |
| `estimated_price` | Quick reference price | 450.00 |
| `estimated_weight` | Quick reference weight | 20.00 |
| `created_by` | Creator user | 5 |
| `is_active` | Available for use | true |

**Template types**:
- `standard`: Common configurations
- `premium`: High-end options
- `economy`: Budget-friendly
- `custom`: Specialized designs

---


### Quotes Table

| Column | Purpose | Example |
|--------|---------|---------|
| `id` | Primary key | 501 |
| `configuration_id` | Which configuration | 123 |
| `customer_id` | Who receives quote | 456 |
| `quote_number` | Unique identifier | "Q-2024-001" |
| `subtotal` | Price before tax | 525.00 |
| `tax_rate` | Tax percentage | 8.50 |
| `tax_amount` | Calculated tax | 44.63 |
| `discount_amount` | Applied discounts | 25.00 |
| `total_amount` | Final amount | 544.63 |
| `technical_requirements` | Special needs | {"installation": "professional"} |
| `valid_until` | Expiration date | 2024-02-15 |
| `status` | Quote state | "sent" |

**Status values**:
- `draft`: Being prepared
- `sent`: Delivered to customer
- `accepted`: Customer approved
- `expired`: Past valid_until date

---

### Orders Table

| Column | Purpose | Example |
|--------|---------|---------|
| `id` | Primary key | 301 |
| `quote_id` | Source quote | 501 |
| `order_number` | Unique identifier | "O-2024-001" |
| `order_date` | When placed | 2024-01-20 |
| `required_date` | Requested delivery | 2024-02-15 |
| `status` | Order state | "production" |
| `special_instructions` | Custom requests | "Call before delivery" |
| `installation_address` | Delivery location | {"street": "123 Main St", ...} |

**Status progression**:
1. `confirmed`: Order accepted
2. `production`: Being manufactured
3. `shipped`: In transit
4. `installed`: Complete

---

### Configuration Snapshots Table

| Column | Purpose | Example |
|--------|---------|---------|
| `id` | Primary key | 1001 |
| `configuration_id` | Which configuration | 123 |
| `quote_id` | Related quote | 501 |
| `base_price` | Base at snapshot time | 200.00 |
| `total_price` | Total at snapshot time | 525.00 |
| `calculated_weight` | Weight at snapshot time | 23.00 |
| `price_breakdown` | Cost components | {"base": 200, "options": 325} |
| `weight_breakdown` | Weight components | {"base": 15, "options": 8} |
| `technical_snapshot` | Technical specs | {"u_value": 0.28, "shgc": 0.35} |
| `snapshot_type` | Purpose | "price_quote" |
| `snapshot_reason` | Why created | "Quote generation" |
| `valid_until` | Expiration | 2024-02-15 |

**Snapshot types**:
- `price_quote`: For quote generation (price protection)
- `technical_calculation`: For engineering review
- `order_confirmation`: For order records

**Why immutable?**
- Never updated, only created
- Preserves historical accuracy
- Protects quoted prices
- Audit trail for compliance

---

### Price History Tables

**manufacturing_type_price_history**:

| Column | Purpose | Example |
|--------|---------|---------|
| `id` | Primary key | 50 |
| `manufacturing_type_id` | Which product type | 1 |
| `old_base_price` | Previous price | 200.00 |
| `new_base_price` | New price | 210.00 |
| `old_base_weight` | Previous weight | 15.00 |
| `new_base_weight` | New weight | 15.50 |
| `change_reason` | Why changed | "Material cost increase" |
| `effective_date` | When effective | 2024-01-15 |
| `changed_by` | Who changed it | "admin@company.com" |

**attribute_node_history**:

| Column | Purpose | Example |
|--------|---------|---------|
| `id` | Primary key | 75 |
| `attribute_node_id` | Which attribute | 42 |
| `old_price_impact` | Previous price | 50.00 |
| `new_price_impact` | New price | 55.00 |
| `old_weight_impact` | Previous weight | 2.00 |
| `new_weight_impact` | New weight | 2.10 |
| `old_price_formula` | Previous formula | "base * 1.1" |
| `new_price_formula` | New formula | "base * 1.15" |
| `change_reason` | Why changed | "Supplier price increase" |
| `effective_date` | When effective | 2024-01-15 |

**Triggered automatically**: Database triggers detect changes and log them

---

## System Behavior Examples

### Example 1: Conditional Display Logic

**Scenario**: Show "Custom Color" option only if "Premium Frame" is selected

**Attribute node setup**:
```json
{
  "name": "Custom Color",
  "display_condition": {
    "operator": "equals",
    "field": "parent.frame_quality",
    "value": "premium"
  }
}
```

**Application logic**:
1. User selects frame_quality = "premium"
2. System evaluates display_condition for all attributes
3. "Custom Color" option becomes visible
4. User can now select custom color

---

### Example 2: Dynamic Pricing Formula

**Scenario**: Window price based on area (width × height)

**Attribute node setup**:
```sql
-- Width attribute
name: "Width"
data_type: "number"
price_impact_type: "formula"
price_formula: NULL  -- No direct price impact

-- Height attribute
name: "Height"
data_type: "number"
price_impact_type: "formula"
price_formula: NULL  -- No direct price impact

-- Area calculation (technical_spec)
name: "Area"
data_type: "formula"
value_formula: "width * height"
price_formula: "area * 15.50"  -- $15.50 per sq ft
```

**Calculation flow**:
1. User enters width = 48 inches
2. User enters height = 60 inches
3. System calculates area = 48 × 60 = 2,880 sq inches = 20 sq ft
4. System calculates price = 20 × $15.50 = $310
5. Total price = base_price + $310 + other options

---

### Example 3: Technical Specifications

**Scenario**: Calculate U-value (thermal efficiency) based on glass and frame choices

**Attribute nodes**:
```sql
-- Glass type options with technical impacts
"Double Pane": technical_impact = {"u_value_contribution": 0.30}
"Triple Pane": technical_impact = {"u_value_contribution": 0.20}

-- Frame material options with technical impacts
"Aluminum": technical_impact = {"u_value_contribution": 0.15}
"Vinyl": technical_impact = {"u_value_contribution": 0.10}

-- U-value calculation (technical_spec)
name: "U-Value"
technical_property_type: "thermal_efficiency"
technical_impact_formula: "glass.u_value + frame.u_value"
```

**Calculation flow**:
1. User selects "Triple Pane" glass (u_value = 0.20)
2. User selects "Vinyl" frame (u_value = 0.10)
3. System calculates total U-value = 0.20 + 0.10 = 0.30
4. Stored in configurations.calculated_technical_data = {"u_value": 0.30}
5. Lower U-value = better insulation (marketing point!)

---


## Database Functions and Triggers

### Function: calculate_universal_properties()

**Purpose**: Calculate total price and weight for a configuration

**How it works**:
1. Gets base price/weight from manufacturing type
2. Sums price_impact_value from all selected options
3. Sums weight_impact from all selected options
4. Returns total_price and total_weight

**Usage**:
```sql
SELECT * FROM calculate_universal_properties(123);
-- Returns: (total_price: 525.00, total_weight: 23.00)
```

---

### Function: create_quote_with_snapshot()

**Purpose**: Create quote and snapshot in one atomic operation

**How it works**:
1. Calculates current pricing using calculate_universal_properties()
2. Creates quote record with calculated totals
3. Creates configuration_snapshot with complete breakdown
4. Links snapshot to quote for price protection
5. Returns quote_id

**Why atomic?**: Ensures quote and snapshot are always in sync

**Usage**:
```sql
SELECT create_quote_with_snapshot(
  p_configuration_id := 123,
  p_customer_id := 456,
  p_valid_until := '2024-02-15'
);
-- Returns: quote_id (501)
```

---

### Function: create_configuration_from_template()

**Purpose**: Instantiate a configuration from a template

**How it works**:
1. Validates template exists and is active
2. Creates new configuration with template metadata
3. Copies all template_selections to configuration_selections
4. Records usage in template_usage table
5. Updates template usage_count
6. Returns new configuration_id

**Usage**:
```sql
SELECT create_configuration_from_template(
  p_template_id := 10,
  p_customer_id := 456,
  p_config_name := 'My Custom Window'
);
-- Returns: configuration_id (124)
```

---

### Trigger: log_manufacturing_price_change()

**Purpose**: Automatically track price changes

**When**: BEFORE UPDATE on manufacturing_types

**What it does**:
- Detects if base_price or base_weight changed
- Inserts record into manufacturing_type_price_history
- Logs old and new values
- Records who made the change

**Example**:
```sql
UPDATE manufacturing_types 
SET base_price = 210.00 
WHERE id = 1;

-- Trigger automatically creates:
INSERT INTO manufacturing_type_price_history
(manufacturing_type_id, old_base_price, new_base_price, changed_by)
VALUES (1, 200.00, 210.00, 'admin@company.com');
```

---

### Trigger: update_configuration_calculations()

**Purpose**: Keep configuration totals up-to-date

**When**: AFTER INSERT OR UPDATE on configuration_selections

**What it does**:
- Recalculates total_price using calculate_universal_properties()
- Recalculates calculated_weight
- Updates calculated_technical_data
- Sets updated_at timestamp

**Why important**: Ensures configuration totals are always accurate

**Example**:
```sql
-- User adds new selection
INSERT INTO configuration_selections
(configuration_id, attribute_node_id, string_value)
VALUES (123, 42, 'Aluminum');

-- Trigger automatically updates:
UPDATE configurations
SET 
  total_price = 525.00,  -- Recalculated
  calculated_weight = 23.00,  -- Recalculated
  updated_at = NOW()
WHERE id = 123;
```

---

### Trigger: update_template_success_metrics()

**Purpose**: Track template conversion rates

**When**: AFTER UPDATE on template_usage

**What it does**:
- Detects when converted_to_order changes to true
- Calculates success_rate for the template
- Updates configuration_templates.success_rate

**Formula**: `success_rate = (orders / total_usage) * 100`

**Example**:
```sql
-- Order is placed from template-based configuration
UPDATE template_usage
SET converted_to_order = true
WHERE id = 50;

-- Trigger calculates:
-- Template #10: 47 uses, 12 orders = 25.5% success rate
UPDATE configuration_templates
SET success_rate = 25.50
WHERE id = 10;
```

---

### Trigger: update_template_estimates()

**Purpose**: Keep template pricing estimates current

**When**: AFTER INSERT OR UPDATE OR DELETE on template_selections

**What it does**:
- Recalculates estimated_price based on template selections
- Recalculates estimated_weight
- Updates configuration_templates

**Why important**: Template estimates shown to customers must be accurate

**Example**:
```sql
-- Admin adds premium option to template
INSERT INTO template_selections
(template_id, attribute_node_id, string_value)
VALUES (10, 55, 'Premium Hardware');

-- Trigger recalculates:
UPDATE configuration_templates
SET 
  estimated_price = 475.00,  -- Was 450.00
  estimated_weight = 21.00,  -- Was 20.00
  updated_at = NOW()
WHERE id = 10;
```

---

## Performance Indexes

### Why These Indexes?

**GIST indexes on LTREE columns**:
```sql
CREATE INDEX idx_attribute_nodes_ltree 
ON attribute_nodes USING GIST (ltree_path);
```
- Enables fast hierarchical queries
- O(log n) performance for descendant/ancestor lookups
- Required for LTREE operators (<@, @>, ~)

**B-tree indexes on foreign keys**:
```sql
CREATE INDEX idx_config_selections_config 
ON configuration_selections(configuration_id);
```
- Fast JOIN operations
- Efficient filtering by configuration
- Supports CASCADE deletes

**Composite indexes**:
```sql
CREATE INDEX idx_template_usage_converted 
ON template_usage(converted_to_order) 
WHERE converted_to_order = true;
```
- Partial index (only successful conversions)
- Faster analytics queries
- Smaller index size

**GIN indexes on JSONB**:
```sql
CREATE INDEX idx_configurations_tech_data 
ON configurations USING GIN (calculated_technical_data);
```
- Fast queries on JSON properties
- Supports containment operators (@>, ?)
- Enables filtering by technical specs

---

## Query Performance Examples

### Fast: Get all descendants using LTREE
```sql
-- O(log n) with GIST index
SELECT * FROM attribute_nodes
WHERE ltree_path <@ 'window.frame'::ltree;
```

### Slow: Get all descendants using recursion
```sql
-- O(n) recursive scan
WITH RECURSIVE descendants AS (
  SELECT * FROM attribute_nodes WHERE id = 10
  UNION ALL
  SELECT an.* FROM attribute_nodes an
  JOIN descendants d ON an.parent_node_id = d.id
)
SELECT * FROM descendants;
```

**Recommendation**: Always use LTREE for hierarchical queries

---

### Fast: Get configuration with selections (indexed JOIN)
```sql
-- Uses foreign key indexes
SELECT c.*, cs.*, an.name
FROM configurations c
JOIN configuration_selections cs ON c.id = cs.configuration_id
JOIN attribute_nodes an ON cs.attribute_node_id = an.id
WHERE c.id = 123;
```

### Slow: Get configuration with selections (no indexes)
```sql
-- Full table scans without indexes
SELECT c.*, cs.*, an.name
FROM configurations c, configuration_selections cs, attribute_nodes an
WHERE c.id = cs.configuration_id
AND cs.attribute_node_id = an.id
AND c.id = 123;
```

**Recommendation**: Always define foreign key indexes

---

## Summary

The WindX database schema provides:

1. **Flexibility**: Add new product types and attributes without schema changes
2. **Performance**: LTREE and proper indexing enable fast queries at scale
3. **Price Protection**: Snapshots preserve quoted prices
4. **Analytics**: Template usage tracking and conversion metrics
5. **Audit Trail**: Complete history of price changes
6. **Scalability**: Handles millions of configurations efficiently

**Key architectural decisions**:
- Manufacturing types for product abstraction
- LTREE for efficient hierarchical queries
- Separate configuration/selections for EAV flexibility
- Template system for faster configuration
- Snapshot approach for price protection
- Automatic triggers for data consistency

**Trade-offs accepted**:
- PostgreSQL-specific (LTREE, JSONB, triggers)
- More complex than simple relational schema
- Requires understanding of hierarchical patterns

**Benefits gained**:
- No schema changes for new products
- Fast queries regardless of hierarchy depth
- Complete flexibility in product configuration
- Strong data consistency guarantees
- Comprehensive audit trail
