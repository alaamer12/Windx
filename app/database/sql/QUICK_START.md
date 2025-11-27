# Quick Start Guide - Database Triggers

## TL;DR

```bash
# Install all triggers
.venv\scripts\python -m app.database.sql.install_triggers install

# Verify installation
.venv\scripts\python -m app.database.sql.install_triggers verify
```

## What These Triggers Do

### 1. LTREE Path Maintenance
**Automatically generates hierarchical paths for attribute nodes**

```sql
-- You write:
INSERT INTO attribute_nodes (name, parent_node_id, manufacturing_type_id, node_type)
VALUES ('Aluminum', 5, 1, 'option');

-- Trigger automatically sets:
-- ltree_path = 'frame_material.aluminum'
-- depth = 1
```

### 2. Depth Calculation
**Automatically calculates nesting level**

```sql
-- Root node: depth = 0
-- Child: depth = 1
-- Grandchild: depth = 2
-- etc.
```

### 3. Price History
**Logs all price changes for audit trail**

```sql
-- You write:
UPDATE configurations SET total_price = 999.99 WHERE id = 1;

-- Trigger automatically logs:
-- old_total_price, new_total_price, timestamp, user
```

## Installation Methods

### Method 1: Python Script (Recommended)
```bash
.venv\scripts\python -m app.database.sql.install_triggers install
```

### Method 2: Manual SQL
```bash
psql -U user -d database -f app/database/sql/01_ltree_path_maintenance.sql
psql -U user -d database -f app/database/sql/02_depth_calculation.sql
psql -U user -d database -f app/database/sql/03_price_history.sql
```

### Method 3: Alembic Migration
Add to your migration:
```python
from pathlib import Path

def upgrade():
    sql_dir = Path("app/database/sql")
    for script in ["01_ltree_path_maintenance.sql", "02_depth_calculation.sql", "03_price_history.sql"]:
        with open(sql_dir / script) as f:
            op.execute(f.read())
```

## Testing

```bash
# Run test script
psql -U user -d database -f app/database/sql/test_triggers.sql
```

## Troubleshooting

### LTREE not available?
```sql
CREATE EXTENSION IF NOT EXISTS ltree;
```

### Trigger not firing?
```bash
.venv\scripts\python -m app.database.sql.install_triggers verify
```

### Need to reinstall?
```bash
.venv\scripts\python -m app.database.sql.install_triggers uninstall
.venv\scripts\python -m app.database.sql.install_triggers install
```

## More Information

- **Full Documentation**: See `README.md`
- **Implementation Details**: See `IMPLEMENTATION_SUMMARY.md`
- **Test Script**: See `test_triggers.sql`
