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

---

## Template System

### Purpose

Templates are **pre-defined configurations** for common use cases. They accelerate the configuration process and ensure consistency.

### Template Types

**Standard Templates**: Common configurations (e.g., "Standard Casement Window")
- Created by data entry staff
- Public (visible to all customers)
- Track usage metrics

**Premium Templates**: High-end configurations (e.g., "Luxury Triple-Pane Window")
- Higher estimated price
- May include premium options

**Custom Templates**: Customer-specific or project-specific
- Created by sales team
- Can be private (specific customer only)

### Template Workflow

```
1. Data Entry Staff Creates Template
   - Select manufacturing type (Window)
   - Make all attribute selections
   - Name template ("Standard Casement Window")
   - Set visibility (public/private)
   - Save template

2. Customer Starts from Template
   - Browse available templates
   - Select "Standard Casement Window"
   - System creates new configuration with all template selections
   - Customer can modify any selection
   - Price updates in real-time

3. System Tracks Usage
   - Increment template usage_count
   - Track conversion to quote
   - Track conversion to order
   - Calculate success_rate metric
```

### Template Metrics

**Usage Count**: How many times template was applied
**Success Rate**: Percentage of template uses that became orders
**Estimated Price**: Pre-calculated price for quick reference
**Estimated Weight**: Pre-calculated weight for shipping

### Template Benefits

**For Customers**:
- Faster configuration (start with 80% complete)
- Confidence in proven combinations
- See estimated price before customizing

**For Business**:
- Guide customers toward profitable configurations
- Reduce support calls (fewer configuration errors)
- Identify popular combinations
- Optimize inventory based on template usage

---

## Quote and Order Workflow

### Quote Generation Process

```
1. Customer Completes Configuration
   - All required attributes selected
   - Price calculated and displayed
   - Technical specifications computed

2. Customer Requests Quote
   - System validates configuration
   - Creates configuration snapshot (immutable)
   - Generates unique quote number (Q-20250125-001)
   - Calculates:
     * Subtotal (configuration price)
     * Tax (based on customer location)
     * Discounts (if applicable)
     * Total amount
   - Sets validity period (e.g., 30 days)
   - Status: "draft"

3. Quote Review and Approval
   - Sales team reviews quote
   - May adjust discounts or terms
   - Status changes to "sent"
   - Customer receives quote document

4. Customer Accepts Quote
   - Customer reviews and accepts
   - Status changes to "accepted"
   - Ready for order placement
```

### Quote Snapshot System

**Why Snapshots?**
- Prices change over time
- Quotes must honor original pricing
- Audit trail for compliance

**What's Captured**:
```json
{
  "base_price": 200.00,
  "total_price": 988.50,
  "calculated_weight": 45.2,
  "price_breakdown": {
    "base": 200.00,
    "frame_material": 50.00,
    "glass_type": 80.00,
    "opening_style": 60.00,
    "dimensions": 540.00,
    "premium_finish": 58.50
  },
  "weight_breakdown": {
    "base": 25.0,
    "glass": 15.2,
    "frame": 5.0
  },
  "technical_snapshot": {
    "u_value": 0.28,
    "shgc": 0.35,
    "vt": 0.65
  },
  "snapshot_type": "price_quote",
  "valid_until": "2025-02-24"
}
```

### Order Placement Process

```
1. Customer Accepts Quote
   - Quote status: "accepted"
   - Customer provides:
     * Installation address
     * Required delivery date
     * Special instructions
     * Payment information

2. Order Creation
   - System creates order from quote
   - Generates unique order number (ORD-20250125-001)
   - Links to quote (preserves pricing)
   - Status: "confirmed"
   - Order date recorded

3. Order Processing
   - Status: "production"
   - Manufacturing team receives specifications
   - Technical data from snapshot guides production
   - Progress tracked in system

4. Order Fulfillment
   - Status: "shipped"
   - Tracking information added
   - Customer notified

5. Order Completion
   - Status: "installed" or "delivered"
   - Customer feedback collected
   - Template success metrics updated
```

### Order Items

Orders can contain multiple configurations:
- Customer orders 5 identical windows → 1 order, 1 configuration, quantity = 5
- Customer orders 3 different window types → 1 order, 3 configurations

Each order item tracks:
- Configuration reference
- Quantity
- Unit price (from quote snapshot)
- Total price
- Production status

---

## Data Flow Through the System

### Configuration Creation Flow

```
User Action → API Endpoint → Service Layer → Repository Layer → Database

Example: Create Window Configuration

1. POST /api/v1/configurations
   Body: {
     "manufacturing_type_id": 1,
     "name": "Living Room Window",
     "customer_id": 42
   }

2. ConfigurationService.create_configuration()
   - Validates manufacturing type exists
   - Creates configuration record
   - Sets base_price from manufacturing type
   - Returns configuration

3. ConfigurationRepository.create()
   - Inserts into configurations table
   - Commits transaction

4. Database
   - configurations table: new row
   - Status: "draft"
   - total_price: base_price (no selections yet)
```

### Selection Update Flow

```
User Selects Option → Real-time Price Update

Example: Select "Aluminum Frame"

1. PATCH /api/v1/configurations/123/selections
   Body: {
     "selections": [
       {
         "attribute_node_id": 7,
         "string_value": "Aluminum"
       }
     ]
   }

2. ConfigurationService.update_selections()
   - Validates attribute belongs to manufacturing type
   - Checks display conditions
   - Validates against rules
   - Updates selections

3. Database Trigger Fires
   - Recalculates total_price
   - Updates calculated_weight
   - Updates calculated_technical_data
   - Updates updated_at timestamp

4. Response Returns Updated Configuration
   - New total_price: $250 (base $200 + aluminum $50)
   - Frontend updates display instantly
```

### Quote Generation Flow

```
Configuration Complete → Quote Request → Snapshot Creation

1. POST /api/v1/quotes
   Body: {
     "configuration_id": 123,
     "customer_id": 42,
     "valid_until": "2025-02-24"
   }

2. QuoteService.generate_quote()
   - Validates configuration is complete
   - Calculates tax based on customer location
   - Applies any discounts
   - Creates quote record
   - Calls create_configuration_snapshot()

3. Snapshot Creation
   - Captures current price breakdown
   - Captures weight breakdown
   - Captures technical specifications
   - Links to quote
   - Marks as immutable

4. Quote Number Generated
   - Format: Q-{timestamp}-{sequence}
   - Example: Q-20250125-001

5. Response
   - Quote with all details
   - Snapshot reference
   - Validity period
```

---

## Technical Specifications System

### Product-Specific Technical Data

Different product types have different technical requirements:

**Windows**:
- U-value (thermal insulation)
- SHGC (solar heat gain coefficient)
- VT (visible transmittance)
- Air infiltration rating
- Water resistance rating

**Doors**:
- Fire rating
- Security rating
- Sound transmission class
- Weather stripping type

**Tables**:
- Load capacity
- Surface hardness
- Moisture resistance

### Storage Approach

Technical specifications are stored in JSONB columns:

```sql
-- In configurations table
calculated_technical_data JSONB DEFAULT '{}'

-- Example data
{
  "u_value": 0.28,
  "shgc": 0.35,
  "vt": 0.65,
  "air_infiltration": "A3",
  "water_resistance": "B7"
}
```

### Calculation

Technical properties are calculated from selections:

1. Each attribute node can have `technical_impact_formula`
2. As selections are made, formulas are evaluated
3. Results are aggregated into `calculated_technical_data`
4. Snapshots preserve technical specs at quote time

**Example**:
```
Base Window U-value: 0.35
+ Double Pane Glass: -0.05 (better insulation)
+ Low-E Coating: -0.02 (even better)
= Final U-value: 0.28
```

---

## System Scalability and Performance

### Current Scale (Design Target)

- **Users**: 800 concurrent users
- **Manufacturing Types**: 100+ product categories
- **Attribute Nodes**: 10,000+ configurable options
- **Configurations**: 5,000+ customer designs
- **Hierarchy Depth**: Up to 10 levels

### Performance Characteristics

**Fast Operations** (< 100ms):
- Load attribute tree for product type
- Get configuration with selections
- Calculate price for configuration
- Apply template to new configuration

**Medium Operations** (100-500ms):
- Create new configuration
- Update multiple selections
- Generate quote with snapshot
- Search configurations

**Acceptable Operations** (500ms-2s):
- Complex hierarchical searches
- Bulk template operations
- Report generation

### Optimization Strategies

**Database Level**:
- GiST indexes on LTREE paths (O(log n) queries)
- B-tree indexes on foreign keys
- Partial indexes on active records
- Query result caching

**Application Level**:
- Eager loading of relationships (prevent N+1 queries)
- Pagination on list endpoints
- Rate limiting on public endpoints
- Response caching for read-only data

**Architecture Level**:
- Stateless API (horizontal scaling)
- Database connection pooling
- Async operations where possible
- Background jobs for heavy operations

---

## Security and Authorization

### User Roles

**Customer**:
- Create and manage own configurations
- Generate quotes for own configurations
- View own orders
- Apply public templates

**Sales Representative**:
- View all customer configurations
- Assist customers with configuration
- Generate quotes for any customer
- Create custom templates

**Data Entry Staff**:
- Create and manage templates
- Update attribute hierarchies
- Manage manufacturing types

**Administrator (Superuser)**:
- Full system access
- Manage users and roles
- Configure system settings
- Access audit logs

### Authorization Rules

**Configurations**:
- Customers see only their own
- Sales reps see all
- Admins see all

**Templates**:
- Public templates visible to all
- Private templates visible to creator and admins
- Only data entry staff and admins can create

**Quotes**:
- Customers see only their own
- Sales reps see all
- Admins see all

**Manufacturing Types & Attributes**:
- All users can read
- Only admins can modify

---

## Future Enhancements

### Planned Features

**Phase 2**:
- 3D visualization of configured products
- AR preview (view window in your room)
- Bulk ordering (multiple configurations in one order)
- Saved configuration sharing (send link to friend)

**Phase 3**:
- AI-powered configuration suggestions
- Automated compatibility checking
- Integration with ERP systems
- Mobile app for field sales

**Phase 4**:
- Multi-language support
- Multi-currency support
- Regional pricing variations
- Franchise/dealer management

### Extensibility

The system is designed for easy extension:

**New Product Types**: Add row to `manufacturing_types`, define attribute tree
**New Attributes**: Add nodes to attribute tree, no schema changes
**New Pricing Models**: Add formula types, update evaluation logic
**New Conditions**: Add condition operators to JSONB, update evaluation
**New Technical Specs**: Add fields to JSONB, no schema changes

---

## Conclusion

The Windx configurator system provides a powerful, flexible platform for product configuration that:

✅ **Empowers customers** with self-service configuration
✅ **Automates pricing** with real-time calculations
✅ **Scales easily** to new products and markets
✅ **Maintains data integrity** with hybrid database approach
✅ **Preserves pricing** with snapshot system
✅ **Accelerates sales** with template system
✅ **Tracks everything** with comprehensive audit trail

The hybrid database architecture (Relational + LTREE + JSONB) provides the optimal balance of flexibility, performance, and maintainability—enabling the business to adapt quickly while maintaining system reliability.
