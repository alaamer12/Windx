---
trigger: always_on
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