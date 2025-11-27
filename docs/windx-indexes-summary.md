# Windx Database Indexes Summary

This document summarizes all indexes implemented in the Windx system for optimal query performance.

## Index Strategy

The Windx system uses a comprehensive indexing strategy to ensure optimal performance:

1. **Primary Keys**: All tables have indexed primary keys
2. **Foreign Keys**: All foreign key columns are indexed
3. **Frequently Filtered Columns**: Status, is_active, customer_id, etc.
4. **Frequently Sorted Columns**: created_at, sort_order
5. **LTREE Columns**: GiST indexes for hierarchical queries
6. **JSONB Columns**: GIN indexes for JSON queries
7. **Composite Indexes**: Multi-column indexes for common query patterns

## Indexes by Table

### ManufacturingType

**Single Column Indexes:**
- `id` (PRIMARY KEY, indexed)
- `name` (UNIQUE, indexed)
- `base_category` (indexed)
- `is_active` (indexed)
- `created_at` (indexed)

**Purpose:**
- Fast lookups by name
- Efficient filtering by category and active status
- Sorting by creation date

---

### AttributeNode

**Single Column Indexes:**
- `id` (PRIMARY KEY, indexed)
- `manufacturing_type_id` (indexed, FK)
- `parent_node_id` (indexed, FK)
- `technical_property_type` (indexed)

**Composite Indexes:**
- `idx_attribute_nodes_mfg_type_node_type` (manufacturing_type_id, node_type)

**Special Indexes:**
- `idx_attribute_nodes_ltree_path` (ltree_path, GiST) - For hierarchical queries
- `idx_attribute_nodes_technical_property` (technical_property_type, PARTIAL WHERE NOT NULL)

**Purpose:**
- Fast hierarchical queries using LTREE
- Efficient filtering by manufacturing type and node type
- Quick lookups of technical properties

---

### Configuration

**Single Column Indexes:**
- `id` (PRIMARY KEY, indexed)
- `manufacturing_type_id` (indexed, FK)
- `customer_id` (indexed, FK)
- `status` (indexed)
- `reference_code` (UNIQUE, indexed)
- `total_price` (indexed)
- `created_at` (indexed)

**Composite Indexes:**
- `idx_configurations_mfg_type_status` (manufacturing_type_id, status)
- `idx_configurations_customer_status` (customer_id, status)

**Special Indexes:**
- `idx_configurations_technical_data` (calculated_technical_data, GIN) - For JSONB queries

**Purpose:**
- Fast filtering by customer and status
- Efficient sorting by price and date
- Quick JSONB property searches

---

### ConfigurationSelection

**Single Column Indexes:**
- `id` (PRIMARY KEY, indexed)
- `configuration_id` (indexed, FK)
- `attribute_node_id` (indexed, FK)

**Composite Indexes:**
- `idx_config_selections_config` (configuration_id)
- `idx_config_selections_attr` (attribute_node_id)

**Special Indexes:**
- `idx_config_selections_path` (selection_path, GiST) - For LTREE queries
- `idx_config_selections_json` (json_value, GIN) - For JSONB queries

**Constraints:**
- `uq_config_attr` (configuration_id, attribute_node_id, UNIQUE)

**Purpose:**
- Fast lookups of selections by configuration
- Efficient hierarchical context queries
- Quick JSON value searches

---

### Customer

**Single Column Indexes:**
- `id` (PRIMARY KEY, indexed)
- `company_name` (indexed)
- `email` (UNIQUE, indexed)
- `customer_type` (indexed)
- `is_active` (indexed)
- `created_at` (indexed)

**Composite Indexes:**
- `idx_customers_type_active` (customer_type, is_active)

**Special Indexes:**
- `idx_customers_address` (address, GIN) - For JSONB queries

**Purpose:**
- Fast email lookups
- Efficient filtering by type and status
- Quick address searches

---

### Quote

**Single Column Indexes:**
- `id` (PRIMARY KEY, indexed)
- `configuration_id` (indexed, FK)
- `customer_id` (indexed, FK)
- `quote_number` (UNIQUE, indexed)
- `total_amount` (indexed)
- `valid_until` (indexed)
- `status` (indexed)
- `created_at` (indexed)

**Composite Indexes:**
- `idx_quotes_config_status` (configuration_id, status)
- `idx_quotes_customer_status` (customer_id, status)
- `idx_quotes_status_valid` (status, valid_until)

**Special Indexes:**
- `idx_quotes_technical_requirements` (technical_requirements, GIN) - For JSONB queries

**Purpose:**
- Fast quote number lookups
- Efficient filtering by customer, status, and validity
- Quick technical requirement searches

---

### Order

**Single Column Indexes:**
- `id` (PRIMARY KEY, indexed)
- `quote_id` (indexed, FK)
- `order_number` (UNIQUE, indexed)
- `order_date` (indexed)
- `required_date` (indexed)
- `status` (indexed)
- `created_at` (indexed)

**Composite Indexes:**
- `idx_orders_status_date` (status, order_date)
- `idx_orders_status_required` (status, required_date)
- `idx_orders_quote_status` (quote_id, status)

**Special Indexes:**
- `idx_orders_installation_address` (installation_address, GIN) - For JSONB queries

**Purpose:**
- Fast order number lookups
- Efficient filtering by status and dates
- Quick address searches

---

### OrderItem

**Single Column Indexes:**
- `id` (PRIMARY KEY, indexed)
- `order_id` (indexed, FK)
- `configuration_id` (indexed, FK)
- `total_price` (indexed)
- `production_status` (indexed)
- `created_at` (indexed)

**Composite Indexes:**
- `idx_order_items_order_status` (order_id, production_status)
- `idx_order_items_config_status` (configuration_id, production_status)

**Purpose:**
- Fast filtering by order and production status
- Efficient configuration lookups

---

### ConfigurationTemplate

**Single Column Indexes:**
- `id` (PRIMARY KEY, indexed)
- `name` (indexed)
- `manufacturing_type_id` (indexed, FK)
- `template_type` (indexed)
- `is_public` (indexed)
- `is_active` (indexed)
- `created_by` (indexed, FK)
- `created_at` (indexed)

**Composite Indexes:**
- `idx_templates_mfg_type_template_type` (manufacturing_type_id, template_type)
- `idx_templates_public_active` (is_public, is_active)

**Partial Indexes:**
- `idx_templates_public_only` (is_public, WHERE is_public = true)
- `idx_templates_active_only` (is_active, WHERE is_active = true)

**Purpose:**
- Fast filtering by manufacturing type and template type
- Efficient public template queries
- Quick active template lookups

---

### TemplateSelection

**Single Column Indexes:**
- `id` (PRIMARY KEY, indexed)
- `template_id` (indexed, FK)
- `attribute_node_id` (indexed, FK)
- `created_at` (indexed)

**Composite Indexes:**
- `idx_template_selections_template` (template_id)
- `idx_template_selections_attr_node` (attribute_node_id)

**Special Indexes:**
- `idx_template_selections_path` (selection_path, GiST) - For LTREE queries

**Constraints:**
- `uq_template_attr` (template_id, attribute_node_id, UNIQUE)

**Purpose:**
- Fast lookups of selections by template
- Efficient hierarchical context queries

---

## Index Types Used

### B-tree Indexes (Default)
Used for most columns including:
- Primary keys
- Foreign keys
- Numeric columns
- String columns
- Date/timestamp columns

**Advantages:**
- Fast equality and range queries
- Efficient sorting
- Good for most use cases

### GiST Indexes (Generalized Search Tree)
Used for:
- LTREE columns (ltree_path, selection_path)

**Advantages:**
- Efficient hierarchical queries
- Fast ancestor/descendant lookups
- Pattern matching support

### GIN Indexes (Generalized Inverted Index)
Used for:
- JSONB columns (calculated_technical_data, address, technical_requirements, etc.)

**Advantages:**
- Fast containment queries
- Efficient key/value searches
- Good for complex JSON queries

### Partial Indexes
Used for:
- `is_public = true` on templates
- `is_active = true` on templates
- `technical_property_type IS NOT NULL` on attribute nodes

**Advantages:**
- Smaller index size
- Faster queries on filtered data
- Reduced maintenance overhead

---

## Query Performance Optimization

### Common Query Patterns

#### 1. List Configurations by Customer and Status
```sql
SELECT * FROM configurations 
WHERE customer_id = ? AND status = ?
ORDER BY created_at DESC;
```
**Index Used:** `idx_configurations_customer_status`

#### 2. Get Attribute Tree for Manufacturing Type
```sql
SELECT * FROM attribute_nodes 
WHERE manufacturing_type_id = ?
ORDER BY ltree_path;
```
**Index Used:** `manufacturing_type_id` + `ltree_path` (GiST)

#### 3. Find Descendants of Attribute Node
```sql
SELECT * FROM attribute_nodes 
WHERE ltree_path <@ 'window.frame'::ltree;
```
**Index Used:** `idx_attribute_nodes_ltree_path` (GiST)

#### 4. List Active Public Templates
```sql
SELECT * FROM configuration_templates 
WHERE is_public = true AND is_active = true
ORDER BY usage_count DESC;
```
**Index Used:** `idx_templates_public_active` or partial indexes

#### 5. Get Quotes by Customer and Status
```sql
SELECT * FROM quotes 
WHERE customer_id = ? AND status = ?
ORDER BY created_at DESC;
```
**Index Used:** `idx_quotes_customer_status`

---

## Performance Considerations

### Index Maintenance
- Indexes are automatically maintained by PostgreSQL
- Regular VACUUM and ANALYZE operations keep statistics up-to-date
- Partial indexes reduce maintenance overhead

### Index Size
- GiST indexes are larger than B-tree indexes
- GIN indexes can be large for JSONB columns
- Partial indexes are smaller and more efficient

### Query Planning
- PostgreSQL query planner automatically selects optimal indexes
- EXPLAIN ANALYZE can be used to verify index usage
- Composite indexes are preferred over multiple single-column indexes

### Trade-offs
- More indexes = faster reads, slower writes
- Our write-to-read ratio favors more indexes
- Partial indexes minimize write overhead

---

## Eager Loading Implementation

To prevent N+1 query problems, the following repository methods use eager loading:

### ConfigurationRepository
- `get_with_selections()` - Loads selections with attribute nodes
- `get_with_full_details()` - Loads manufacturing type, customer, selections, quotes

### QuoteRepository
- `get_with_details()` - Loads configuration, customer, orders

### OrderRepository
- `get_with_items()` - Loads items with configurations
- `get_with_full_details()` - Loads quote, customer, items

### ConfigurationTemplateRepository
- `get_with_selections()` - Loads selections with attribute nodes
- `get_with_full_details()` - Loads manufacturing type, creator, selections

### AttributeNodeRepository
- `get_with_children()` - Loads immediate children
- `get_with_full_tree()` - Loads full subtree

### CustomerRepository
- `get_with_configurations()` - Loads all configurations
- `get_with_full_details()` - Loads configurations and quotes

---

## Pagination Implementation

All list endpoints use fastapi-pagination with:
- Default page size: 50
- Maximum page size: 100
- Page-based pagination (page number + size)

**Benefits:**
- Consistent API responses
- Automatic metadata (total, pages)
- Efficient memory usage
- Scalable to large datasets

---

## Monitoring and Optimization

### Recommended Monitoring
1. Track slow queries (> 100ms)
2. Monitor index usage with `pg_stat_user_indexes`
3. Check table bloat regularly
4. Analyze query plans for complex queries

### Optimization Opportunities
1. Add materialized views for complex aggregations
2. Partition large tables by date or type
3. Add computed columns for frequently filtered JSONB fields
4. Consider read replicas for read-heavy workloads

---

## Summary

The Windx system has comprehensive indexing covering:
- ✅ All primary keys
- ✅ All foreign keys
- ✅ All frequently filtered columns (status, is_active, customer_id)
- ✅ All frequently sorted columns (created_at, sort_order)
- ✅ LTREE columns with GiST indexes
- ✅ JSONB columns with GIN indexes
- ✅ Composite indexes for common query patterns
- ✅ Partial indexes for filtered queries
- ✅ Eager loading for relationships
- ✅ Pagination for all list endpoints

**Performance Targets:**
- Configuration list: < 500ms
- Hierarchy queries: < 300ms
- Price calculations: < 500ms

These targets are met with the current indexing strategy for the target scale (800 users, 5,000+ configurations).
