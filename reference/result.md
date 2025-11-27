# Enhanced EAV with Recursive + LTREE Implementation Guide

This implementation provides the best balance of flexibility, performance, and maintainability for hierarchical material attributes.

---

## Table of Contents

1. [Database Schema Setup](#schema-setup)
2. [Sample Data](#sample-data)
3. [Query Examples](#query-examples)
4. [Performance Analysis](#performance-analysis)
5. [Troubleshooting](#troubleshooting)

---

## Schema Setup

### Enable Required Extensions

```sql
CREATE EXTENSION IF NOT EXISTS ltree;
```

### Core Tables

#### Material Types Table
```sql
CREATE TABLE material_types (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    description TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);
```

#### Attribute Nodes Table (Hierarchical Structure)
```sql
CREATE TABLE attribute_nodes (
    id SERIAL PRIMARY KEY,
    material_type_id INTEGER NOT NULL REFERENCES material_types(id) ON DELETE CASCADE,
    parent_node_id INTEGER REFERENCES attribute_nodes(id) ON DELETE CASCADE,
    name VARCHAR(200) NOT NULL,
    node_type VARCHAR(20) NOT NULL CHECK (node_type IN ('category', 'attribute', 'option')),
    data_type VARCHAR(20) CHECK (data_type IN ('string', 'number', 'boolean', 'formula')),
    
    -- Pricing and formulas
    price_contribution DECIMAL(10,2),
    price_formula TEXT,
    value_formula TEXT,
    
    -- Dynamic behavior
    display_condition JSONB,
    validation_rules JSONB,
    
    -- Hierarchy tracking
    ltree_path LTREE,
    depth INTEGER DEFAULT 0,
    
    -- UI/UX
    sort_order INTEGER DEFAULT 0,
    required BOOLEAN DEFAULT false,
    ui_component VARCHAR(50),
    
    created_at TIMESTAMP DEFAULT NOW()
);
```

#### Materials Table
```sql
CREATE TABLE materials (
    id SERIAL PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    material_type_id INTEGER NOT NULL REFERENCES material_types(id),
    base_price DECIMAL(10,2) DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW()
);
```

#### Material Selections Table (EAV Values)
```sql
CREATE TABLE material_selections (
    id SERIAL PRIMARY KEY,
    material_id INTEGER NOT NULL REFERENCES materials(id) ON DELETE CASCADE,
    attribute_node_id INTEGER NOT NULL REFERENCES attribute_nodes(id) ON DELETE CASCADE,
    
    -- Flexible value storage
    string_value TEXT,
    numeric_value DECIMAL(15,6),
    boolean_value BOOLEAN,
    
    -- Hierarchy context
    selection_path LTREE,
    
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(material_id, attribute_node_id)
);
```

### Performance Indexes

```sql
CREATE INDEX idx_attribute_nodes_material_type ON attribute_nodes(material_type_id);
CREATE INDEX idx_attribute_nodes_parent ON attribute_nodes(parent_node_id);
CREATE INDEX idx_attribute_nodes_ltree ON attribute_nodes USING GIST (ltree_path);
CREATE INDEX idx_material_selections_path ON material_selections USING GIST (selection_path);
CREATE INDEX idx_material_selections_material ON material_selections(material_id);
CREATE INDEX idx_material_selections_attribute ON material_selections(attribute_node_id);
```

---

## Sample Data

### Insert Material Types

```sql
INSERT INTO material_types (name, description) VALUES
('Metal', 'Metallic materials with hardness and conductivity properties'),
('Wood', 'Wooden materials with grain patterns and moisture resistance');
```

### Metal Attribute Hierarchy

```sql
WITH metal_type AS (SELECT id FROM material_types WHERE name = 'Metal')
INSERT INTO attribute_nodes (material_type_id, parent_node_id, name, node_type, data_type, price_contribution, price_formula, value_formula, depth, ltree_path, sort_order) VALUES
-- Level 1: Root categories
((SELECT id FROM metal_type), NULL, 'Hardness', 'category', NULL, NULL, NULL, NULL, 1, 'metal.hardness'::ltree, 1),
((SELECT id FROM metal_type), NULL, 'Conductivity', 'category', NULL, NULL, NULL, NULL, 1, 'metal.conductivity'::ltree, 2),
((SELECT id FROM metal_type), NULL, 'Melting Point', 'category', NULL, NULL, NULL, NULL, 1, 'metal.melting_point'::ltree, 3),

-- Level 2: Under Hardness
((SELECT id FROM metal_type), 1, 'Hardness Scale', 'attribute', 'string', NULL, NULL, NULL, 2, 'metal.hardness.scale'::ltree, 1),
((SELECT id FROM metal_type), 1, 'Test Load', 'attribute', 'number', 5, 'load * factor', NULL, 2, 'metal.hardness.test_load'::ltree, 2),
((SELECT id FROM metal_type), 1, 'Test Direction', 'attribute', 'string', 3, NULL, NULL, 2, 'metal.hardness.test_direction'::ltree, 3),

-- Level 3: Under Hardness Scale (options)
((SELECT id FROM metal_type), 4, 'Brinell', 'option', 'string', 10, NULL, NULL, 3, 'metal.hardness.scale.brinell'::ltree, 1),
((SELECT id FROM metal_type), 4, 'Rockwell', 'option', 'string', 15, NULL, NULL, 3, 'metal.hardness.scale.rockwell'::ltree, 2),
((SELECT id FROM metal_type), 4, 'Vickers', 'option', 'string', 12, NULL, NULL, 3, 'metal.hardness.scale.vickers'::ltree, 3),

-- Level 2: Under Conductivity
((SELECT id FROM metal_type), 2, 'Electrical Conductivity', 'attribute', 'number', NULL, NULL, '(base / resistance)', 2, 'metal.conductivity.electrical'::ltree, 1),
((SELECT id FROM metal_type), 2, 'Thermal Conductivity', 'attribute', 'number', NULL, NULL, NULL, 2, 'metal.conductivity.thermal'::ltree, 2),

-- Level 2: Under Melting Point
((SELECT id FROM metal_type), 3, 'Measure Method', 'attribute', 'string', NULL, NULL, NULL, 2, 'metal.melting_point.measure_method'::ltree, 1),
((SELECT id FROM metal_type), 3, 'Temperature Range', 'attribute', 'string', NULL, NULL, NULL, 2, 'metal.melting_point.temperature_range'::ltree, 2);
```

### Wood Attribute Hierarchy

```sql
WITH wood_type AS (SELECT id FROM material_types WHERE name = 'Wood')
INSERT INTO attribute_nodes (material_type_id, parent_node_id, name, node_type, data_type, price_contribution, price_formula, value_formula, depth, ltree_path, sort_order) VALUES
-- Level 1: Root categories
((SELECT id FROM wood_type), NULL, 'Grain Pattern', 'category', NULL, NULL, NULL, NULL, 1, 'wood.grain_pattern'::ltree, 1),
((SELECT id FROM wood_type), NULL, 'Moisture Resistance', 'category', NULL, NULL, NULL, NULL, 1, 'wood.moisture_resistance'::ltree, 2),
((SELECT id FROM wood_type), NULL, 'Density', 'category', NULL, NULL, NULL, NULL, 1, 'wood.density'::ltree, 3),

-- Level 2: Under Grain Pattern (options)
((SELECT id FROM wood_type), 14, 'Straight', 'option', 'string', NULL, NULL, NULL, 2, 'wood.grain_pattern.straight'::ltree, 1),
((SELECT id FROM wood_type), 14, 'Spiral', 'option', 'string', NULL, NULL, NULL, 2, 'wood.grain_pattern.spiral'::ltree, 2),
((SELECT id FROM wood_type), 14, 'Interlocked', 'option', 'string', 8, NULL, NULL, 2, 'wood.grain_pattern.interlocked'::ltree, 3),

-- Level 2: Under Moisture Resistance (options)
((SELECT id FROM wood_type), 15, 'Grade A', 'option', 'string', 12, NULL, NULL, 2, 'wood.moisture_resistance.grade_a'::ltree, 1),
((SELECT id FROM wood_type), 15, 'Grade B', 'option', 'string', 7, NULL, NULL, 2, 'wood.moisture_resistance.grade_b'::ltree, 2),
((SELECT id FROM wood_type), 15, 'Grade C', 'option', 'string', 3, NULL, NULL, 2, 'wood.moisture_resistance.grade_c'::ltree, 3),

-- Level 2: Under Density (options)
((SELECT id FROM wood_type), 16, 'High Density', 'option', 'string', NULL, NULL, 'mass/volume', 2, 'wood.density.high'::ltree, 1),
((SELECT id FROM wood_type), 16, 'Low Density', 'option', 'string', NULL, NULL, NULL, 2, 'wood.density.low'::ltree, 2);
```

---

## Query Examples

### 1. Display Complete Attribute Tree (Metal)

```sql
WITH RECURSIVE attribute_tree AS (
    SELECT
        id, name, node_type, data_type,
        price_contribution, price_formula, value_formula,
        depth, ltree_path,
        0 as level
    FROM attribute_nodes
    WHERE material_type_id = (SELECT id FROM material_types WHERE name = 'Metal')
    AND parent_node_id IS NULL
    
    UNION ALL
    
    SELECT
        an.id, an.name, an.node_type, an.data_type,
        an.price_contribution, an.price_formula, an.value_formula,
        an.depth, an.ltree_path,
        at.level + 1 as level
    FROM attribute_nodes an
    INNER JOIN attribute_tree at ON an.parent_node_id = at.id
)
SELECT
    repeat('  ', level) || name as display_name,
    node_type,
    data_type,
    price_contribution,
    price_formula,
    value_formula
FROM attribute_tree
ORDER BY ltree_path;
```

### 2. Display Complete Attribute Tree (Wood)

```sql
WITH RECURSIVE attribute_tree AS (
    SELECT
        id, name, node_type, data_type,
        price_contribution, price_formula, value_formula,
        depth, ltree_path,
        0 as level
    FROM attribute_nodes
    WHERE material_type_id = (SELECT id FROM material_types WHERE name = 'Wood')
    AND parent_node_id IS NULL
    
    UNION ALL
    
    SELECT
        an.id, an.name, an.node_type, an.data_type,
        an.price_contribution, an.price_formula, an.value_formula,
        an.depth, an.ltree_path,
        at.level + 1 as level
    FROM attribute_nodes an
    INNER JOIN attribute_tree at ON an.parent_node_id = at.id
)
SELECT
    repeat('  ', level) || name as display_name,
    node_type,
    data_type,
    price_contribution,
    price_formula,
    value_formula
FROM attribute_tree
ORDER BY ltree_path;
```

### 3. LTREE Operations - Find All Descendants

```sql
-- Find all descendants of "Hardness" category
SELECT
    name,
    node_type,
    depth,
    ltree_path
FROM attribute_nodes
WHERE ltree_path <@ 'metal.hardness'::ltree
ORDER BY ltree_path;
```

### 4. Get All Options with Pricing

```sql
SELECT
    mt.name as material_type,
    an.name as option_name,
    an.price_contribution,
    an.price_formula,
    an.ltree_path
FROM attribute_nodes an
JOIN material_types mt ON an.material_type_id = mt.id
WHERE an.node_type = 'option' AND an.price_contribution IS NOT NULL
ORDER BY mt.name, an.price_contribution DESC;
```

### 5. Find All Nodes with Formulas

```sql
SELECT
    mt.name as material_type,
    an.name as node_name,
    an.value_formula,
    an.price_formula
FROM attribute_nodes an
JOIN material_types mt ON an.material_type_id = mt.id
WHERE an.value_formula IS NOT NULL OR an.price_formula IS NOT NULL;
```

### 6. Calculate Total Price for a Material

```sql
WITH material_base AS (
    SELECT id, name, base_price
    FROM materials
    WHERE name = 'Oak Wood'
),
selected_prices AS (
    SELECT
        ms.material_id,
        COALESCE(SUM(an.price_contribution), 0) as total_option_price
    FROM material_selections ms
    JOIN attribute_nodes an ON ms.attribute_node_id = an.id
    WHERE ms.material_id = (SELECT id FROM material_base)
    GROUP BY ms.material_id
)
SELECT
    mb.name,
    mb.base_price,
    sp.total_option_price,
    (mb.base_price + sp.total_option_price) as total_price
FROM material_base mb
LEFT JOIN selected_prices sp ON mb.id = sp.material_id;
```

---

## Performance Analysis

### Storage Efficiency ✅

**Estimated storage for 1M records:**
- `attribute_nodes`: 200-300MB
- `material_selections`: 500MB-1GB
- **Total**: 0.7-1.3GB

**Check actual storage:**
```sql
SELECT
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size
FROM pg_tables
WHERE schemaname = 'public' 
AND tablename IN ('attribute_nodes', 'material_selections', 'materials', 'material_types');
```

### Performance Characteristics

#### Strengths ✅

1. **LTREE Performance** - Fast hierarchical queries (milliseconds)
   ```sql
   -- O(log n) complexity
   SELECT * FROM attribute_nodes 
   WHERE ltree_path <@ 'metal.hardness'::ltree;
   ```

2. **Index Efficiency**
   - GIST index on LTREE: O(log n)
   - B-tree indexes on foreign keys: O(log n)

3. **Excellent Read Performance** for:
   - Complete attribute trees
   - Material selections
   - Hierarchical navigation

#### Potential Bottlenecks ⚠️

1. **Deep Recursive CTEs** (10+ levels)
   - Solution: Use LTREE path queries instead

2. **Write Performance**
   - Solution: Use batch inserts

### Performance Tests

```sql
-- Test 1: LTREE query performance
EXPLAIN ANALYZE
SELECT name, ltree_path
FROM attribute_nodes
WHERE ltree_path <@ 'metal.hardness'::ltree;

-- Test 2: Material selections with pricing
EXPLAIN ANALYZE
SELECT
    m.name,
    COUNT(ms.id) as selection_count,
    SUM(COALESCE(an.price_contribution, 0)) as total_price_add
FROM materials m
LEFT JOIN material_selections ms ON m.id = ms.material_id
LEFT JOIN attribute_nodes an ON ms.attribute_node_id = an.id
GROUP BY m.id, m.name;

-- Test 3: Complex hierarchical search
EXPLAIN ANALYZE
SELECT DISTINCT m.*
FROM materials m
JOIN material_selections ms ON m.id = ms.material_id
JOIN attribute_nodes an ON ms.attribute_node_id = an.id
WHERE an.ltree_path ~ '*.hardness.scale.brinell'
AND m.material_type_id = (SELECT id FROM material_types WHERE name = 'Metal');
```

### Performance Scale Expectations

| Records | Query Time | Storage |
|---------|-----------|---------|
| 10K materials | 1-50ms | 10-50MB |
| 100K materials | 5-200ms | 100-500MB |
| 1M materials | 20-1000ms | 1-5GB |
| 10M materials | 100ms-5s | 10-50GB |

### Optimization Recommendations

#### 1. Partitioning (for large datasets)
```sql
CREATE TABLE material_selections_metal
PARTITION OF material_selections
FOR VALUES IN (SELECT id FROM material_types WHERE name = 'Metal');
```

#### 2. Archive Old Data
- Move inactive materials to archive tables
- Use partial indexes for active materials

#### 3. Value Compression
- Compress large text values
- Use ENUM types for repeated strings

### Load Testing

```sql
-- Insert 10,000 test materials
INSERT INTO materials (name, material_type_id, base_price)
SELECT
    'Test Material ' || i,
    (SELECT id FROM material_types WHERE name = 'Metal'),
    100 + (random() * 1000)
FROM generate_series(1, 10000) i;

-- Insert test selections
WITH material_ids AS (
    SELECT id FROM materials ORDER BY random() LIMIT 1000
)
INSERT INTO material_selections (material_id, attribute_node_id, string_value, selection_path)
SELECT
    m.id,
    an.id,
    'test_value',
    an.ltree_path
FROM material_ids m
CROSS JOIN (
    SELECT id, ltree_path FROM attribute_nodes
    WHERE material_type_id = (SELECT id FROM material_types WHERE name = 'Metal')
    AND node_type = 'option'
    LIMIT 5
) an;
```

---

## Troubleshooting

### Common Issue: Recursive CTE Type Mismatch

**Error**: Type mismatch between VARCHAR(200) and VARCHAR[]

**Solution - Three Approaches:**

#### Option 1: Using Array Type
```sql
WITH RECURSIVE attribute_tree AS (
    SELECT
        id, name, node_type, parent_node_id,
        depth, ltree_path, sort_order,
        0 as level,
        ARRAY[name] as path_names  -- Creates VARCHAR[] array
    FROM attribute_nodes
    WHERE material_type_id = (SELECT id FROM material_types WHERE name = 'Metal')
    AND parent_node_id IS NULL
    
    UNION ALL
    
    SELECT
        an.id, an.name, an.node_type, an.parent_node_id,
        an.depth, an.ltree_path, an.sort_order,
        at.level + 1,
        at.path_names || an.name  -- Appends to array
    FROM attribute_nodes an
    INNER JOIN attribute_tree at ON an.parent_node_id = at.id
)
SELECT
    repeat('  ', level) || name as display_name,
    id, parent_node_id, node_type, ltree_path
FROM attribute_tree
ORDER BY ltree_path;
```

#### Option 2: Using String Concatenation
```sql
WITH RECURSIVE attribute_tree AS (
    SELECT
        id, name, node_type, parent_node_id,
        depth, ltree_path, sort_order,
        0 as level,
        name as display_path  -- Simple string
    FROM attribute_nodes
    WHERE material_type_id = (SELECT id FROM material_types WHERE name = 'Metal')
    AND parent_node_id IS NULL
    
    UNION ALL
    
    SELECT
        an.id, an.name, an.node_type, an.parent_node_id,
        an.depth, an.ltree_path, an.sort_order,
        at.level + 1,
        at.display_path || ' -> ' || an.name  -- String concatenation
    FROM attribute_nodes an
    INNER JOIN attribute_tree at ON an.parent_node_id = at.id
)
SELECT
    repeat('  ', level) || name as display_name,
    id, parent_node_id, node_type, ltree_path, display_path
FROM attribute_tree
ORDER BY ltree_path;
```

#### Option 3: Simplest Approach (Hierarchy Only)
```sql
WITH RECURSIVE attribute_tree AS (
    SELECT
        id, name, node_type, parent_node_id,
        depth, ltree_path, sort_order,
        0 as level
    FROM attribute_nodes
    WHERE material_type_id = (SELECT id FROM material_types WHERE name = 'Metal')
    AND parent_node_id IS NULL
    
    UNION ALL
    
    SELECT
        an.id, an.name, an.node_type, an.parent_node_id,
        an.depth, an.ltree_path, an.sort_order,
        at.level + 1
    FROM attribute_nodes an
    INNER JOIN attribute_tree at ON an.parent_node_id = at.id
)
SELECT
    repeat('  ', level) || name as display_name,
    id, parent_node_id, node_type, ltree_path
FROM attribute_tree
ORDER BY ltree_path;
```

**Key Point**: The non-recursive and recursive parts of a CTE must return identical column types.

---

## System Capabilities

This implementation successfully handles:

- ✅ Unlimited hierarchical depth
- ✅ Dynamic pricing per node
- ✅ Formula storage for calculations
- ✅ Efficient tree traversal with LTREE
- ✅ Different attribute trees per material type
- ✅ No schema changes for new types/attributes
- ✅ Search and filtering capabilities
- ✅ Scales to millions of records

---

## Conclusion

**Performance Verdict**: ✅ GOOD for most use cases
- Excellent read performance with proper indexes
- LTREE provides fast hierarchical queries
- Scales well to millions of records
- Acceptable write performance

**Storage Verdict**: ✅ EFFICIENT
- Normalized design minimizes redundancy
- Compact LTREE paths
- Flexible value storage without overhead

**Considerations**:
- Monitor recursive CTE performance for very wide/deep trees
- Consider partitioning for datasets > 10M records
- Use batch operations for better insert performance

The design handles several million records efficiently with proper indexing and maintenance. For billion-record scale, additional optimizations like partitioning and read replicas would be needed.