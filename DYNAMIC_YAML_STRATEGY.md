# Dynamic YAML Configuration Strategy

## The Problem

**Current State:**
- YAML files are **static** configuration files
- Setup script reads YAML → populates database (one-time)
- Users want to add new nodes dynamically via UI
- But YAML is the "source of truth" for configuration

**The Conflict:**
```
User adds node via UI → Stored in database
                      ↓
                   YAML file unchanged
                      ↓
                   Next deployment: YAML overwrites database
                      ↓
                   User's changes LOST! ❌
```

**The Question:**
How do we allow dynamic node creation while keeping YAML as source of truth?

---

## Solution Options Analysis

### Option 1: Watch YAML Files + Auto-Reload ⚡

**Concept:** Monitor YAML files for changes and reload configuration automatically.

```python
# backend/app/core/config_watcher.py
import asyncio
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

class YAMLConfigWatcher(FileSystemEventHandler):
    """Watch YAML files and reload on changes."""
    
    def __init__(self, config_dir: str):
        self.config_dir = config_dir
        self.observer = Observer()
    
    def on_modified(self, event):
        if event.src_path.endswith('.yaml'):
            page_type = Path(event.src_path).stem
            logger.info(f"YAML file changed: {page_type}.yaml")
            
            # Reload configuration
            RuntimeConfigLoader.clear_cache()
            
            # Re-run setup script to update database
            asyncio.create_task(self.reload_hierarchy(page_type))
    
    async def reload_hierarchy(self, page_type: str):
        """Reload hierarchy from YAML into database."""
        from backend.scripts.setup_hierarchy import setup_page_hierarchy
        await setup_page_hierarchy(page_type)
        logger.info(f"Reloaded hierarchy for {page_type}")
    
    def start(self):
        self.observer.schedule(self, self.config_dir, recursive=False)
        self.observer.start()
```

**Pros:**
- ✅ YAML remains single source of truth
- ✅ Changes to YAML automatically reflected
- ✅ Good for development/testing
- ✅ Simple to implement

**Cons:**
- ❌ Doesn't solve the core problem: Users can't edit YAML via UI
- ❌ Requires file system access (doesn't work in containerized/cloud environments)
- ❌ Race conditions if multiple instances
- ❌ Still requires manual YAML editing

**Verdict:** ⚠️ **Useful for development, but NOT a solution for production dynamic changes**

---

### Option 2: Generate/Update YAML on Node Creation 📝

**Concept:** When user creates node via UI, automatically update the YAML file.

```python
# backend/app/services/yaml_generator.py
import yaml
from pathlib import Path

class YAMLGenerator:
    """Generate and update YAML files from database state."""
    
    @staticmethod
    async def add_attribute_to_yaml(
        page_type: str,
        attribute_data: dict
    ) -> None:
        """Add new attribute to YAML file."""
        yaml_path = f"backend/config/pages/{page_type}.yaml"
        
        # Load existing YAML
        with open(yaml_path, 'r') as f:
            config = yaml.safe_load(f)
        
        # Add new attribute
        config['attributes'].append({
            'name': attribute_data['name'],
            'display_name': attribute_data['display_name'],
            'node_type': attribute_data['node_type'],
            'data_type': attribute_data['data_type'],
            'required': attribute_data.get('required', False),
            'ltree_path': attribute_data['ltree_path'],
            'depth': attribute_data['depth'],
            'sort_order': len(config['attributes']) + 1,
            'ui_component': attribute_data.get('ui_component'),
            'description': attribute_data.get('description'),
            'validation_rules': attribute_data.get('validation_rules'),
            'display_condition': attribute_data.get('display_condition'),
        })
        
        # Write back to YAML
        with open(yaml_path, 'w') as f:
            yaml.dump(config, f, default_flow_style=False, sort_keys=False)
        
        logger.info(f"Added attribute {attribute_data['name']} to {page_type}.yaml")
    
    @staticmethod
    async def sync_database_to_yaml(page_type: str) -> None:
        """Sync entire database state back to YAML."""
        from backend.app.repositories.attribute_node import AttributeNodeRepository
        
        # Query all nodes for this page type
        async with get_db_session() as db:
            repo = AttributeNodeRepository(db)
            nodes = await repo.get_by_page_type(page_type)
        
        # Build YAML structure
        config = {
            'page_type': page_type,
            'manufacturing_type': nodes[0].manufacturing_type.name,
            'attributes': []
        }
        
        for node in nodes:
            config['attributes'].append({
                'name': node.name,
                'display_name': node.display_name,
                'node_type': node.node_type,
                'data_type': node.data_type,
                'required': node.required,
                'ltree_path': str(node.ltree_path),
                'depth': node.depth,
                'sort_order': node.sort_order,
                'ui_component': node.ui_component,
                'description': node.description,
                'validation_rules': node.validation_rules,
                'display_condition': node.display_condition,
            })
        
        # Write to YAML
        yaml_path = f"backend/config/pages/{page_type}.yaml"
        with open(yaml_path, 'w') as f:
            yaml.dump(config, f, default_flow_style=False, sort_keys=False)
        
        logger.info(f"Synced database to {page_type}.yaml")
```

**Usage in API:**
```python
# backend/app/api/v1/endpoints/attribute_nodes.py
@router.post("/")
async def create_attribute_node(
    node_data: AttributeNodeCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create new attribute node and update YAML."""
    
    # Create in database
    service = AttributeNodeService(db)
    node = await service.create_node(node_data)
    
    # Update YAML file
    await YAMLGenerator.add_attribute_to_yaml(
        page_type=node_data.page_type,
        attribute_data=node_data.model_dump()
    )
    
    return node
```

**Pros:**
- ✅ YAML stays in sync with database
- ✅ YAML remains source of truth
- ✅ Works in any environment
- ✅ Version control tracks changes
- ✅ Can review changes via Git

**Cons:**
- ❌ Requires write access to YAML files (problematic in containers)
- ❌ Concurrent writes can corrupt YAML
- ❌ YAML formatting may change (comments lost)
- ❌ Merge conflicts in version control
- ❌ Complex to handle nested structures

**Verdict:** ⚠️ **Works but has significant operational challenges**

---

### Option 3: Hybrid Approach - Two-Tier Configuration 🎯 **RECOMMENDED**

**Concept:** Separate **static configuration** (YAML) from **dynamic extensions** (database).

```
┌─────────────────────────────────────────────────────────┐
│              STATIC CONFIGURATION (YAML)                 │
│  • Core attributes defined by developers                │
│  • Shipped with application                             │
│  • Version controlled                                   │
│  • Immutable at runtime                                 │
└─────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────┐
│            DYNAMIC EXTENSIONS (Database)                 │
│  • Custom attributes added by users                     │
│  • Stored in database only                              │
│  • Mutable at runtime                                   │
│  • Backed up with database                              │
└─────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────┐
│              MERGED CONFIGURATION (Runtime)              │
│  • YAML attributes + Database extensions                │
│  • Presented as single unified schema                   │
│  • Used by application                                  │
└─────────────────────────────────────────────────────────┘
```

**Implementation:**

```python
# backend/app/models/attribute_node.py
class AttributeNode(Base):
    __tablename__ = "attribute_nodes"
    
    # ... existing fields ...
    
    # NEW: Track source of attribute
    source: Mapped[str] = mapped_column(
        String(20), 
        default="yaml",  # "yaml" or "dynamic"
        nullable=False
    )
    
    # NEW: Track if this is a user-created extension
    is_custom: Mapped[bool] = mapped_column(
        Boolean, 
        default=False,
        nullable=False
    )
    
    # NEW: Reference to parent YAML attribute (for extensions)
    extends_attribute_id: Mapped[int | None] = mapped_column(
        ForeignKey("attribute_nodes.id"),
        nullable=True
    )
```

```python
# backend/app/core/config_merger.py
class ConfigurationMerger:
    """Merge YAML configuration with dynamic database extensions."""
    
    @staticmethod
    async def get_merged_configuration(
        page_type: str,
        db: AsyncSession
    ) -> dict:
        """Get merged configuration from YAML + database."""
        
        # 1. Load base configuration from YAML
        yaml_config = await RuntimeConfigLoader.load_page_config(page_type)
        
        # 2. Load dynamic extensions from database
        repo = AttributeNodeRepository(db)
        dynamic_nodes = await repo.get_dynamic_nodes(page_type)
        
        # 3. Merge configurations
        merged_attributes = yaml_config['attributes'].copy()
        
        for node in dynamic_nodes:
            merged_attributes.append({
                'name': node.name,
                'display_name': node.display_name,
                'node_type': node.node_type,
                'data_type': node.data_type,
                'required': node.required,
                'ltree_path': str(node.ltree_path),
                'depth': node.depth,
                'sort_order': node.sort_order,
                'ui_component': node.ui_component,
                'description': node.description,
                'validation_rules': node.validation_rules,
                'display_condition': node.display_condition,
                'source': 'dynamic',  # Mark as dynamic
                'is_custom': True,
            })
        
        # 4. Sort by sort_order
        merged_attributes.sort(key=lambda x: x.get('sort_order', 999))
        
        return {
            **yaml_config,
            'attributes': merged_attributes
        }
```

```python
# backend/app/repositories/attribute_node.py
class AttributeNodeRepository(BaseRepository[AttributeNode]):
    
    async def get_dynamic_nodes(
        self, 
        page_type: str
    ) -> list[AttributeNode]:
        """Get only dynamically created nodes."""
        stmt = (
            select(AttributeNode)
            .where(
                AttributeNode.page_type == page_type,
                AttributeNode.source == "dynamic",
                AttributeNode.is_custom == True
            )
            .order_by(AttributeNode.sort_order)
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())
    
    async def get_yaml_nodes(
        self, 
        page_type: str
    ) -> list[AttributeNode]:
        """Get only YAML-defined nodes."""
        stmt = (
            select(AttributeNode)
            .where(
                AttributeNode.page_type == page_type,
                AttributeNode.source == "yaml"
            )
            .order_by(AttributeNode.sort_order)
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())
```

```python
# backend/app/services/entry.py
class EntryService(BaseService):
    
    async def generate_form_schema(
        self,
        manufacturing_type_id: int,
        page_type: str = "profile"
    ) -> ProfileSchema:
        """Generate form schema from merged configuration."""
        
        # Get merged configuration (YAML + dynamic)
        config = await ConfigurationMerger.get_merged_configuration(
            page_type, 
            self.db
        )
        
        # Generate schema from merged config
        sections = await self._build_sections_from_config(config)
        
        return ProfileSchema(
            manufacturing_type_id=manufacturing_type_id,
            sections=sections,
            conditional_logic=self._extract_conditional_logic(config),
            dependencies=self._extract_dependencies(config)
        )
```

**Setup Script Behavior:**
```python
# backend/scripts/setup_hierarchy.py
async def setup_page_hierarchy(page_type: str):
    """Setup hierarchy from YAML, preserving dynamic nodes."""
    
    # Load YAML configuration
    config = load_yaml_config(page_type)
    
    # Get existing dynamic nodes
    dynamic_nodes = await repo.get_dynamic_nodes(page_type)
    
    # Delete only YAML-sourced nodes
    await repo.delete_yaml_nodes(page_type)
    
    # Recreate YAML nodes
    for attr in config['attributes']:
        node = AttributeNode(
            **attr,
            source="yaml",
            is_custom=False
        )
        await repo.create(node)
    
    # Dynamic nodes are preserved!
    logger.info(f"Setup complete. Preserved {len(dynamic_nodes)} dynamic nodes.")
```

**API for Creating Dynamic Nodes:**
```python
# backend/app/api/v1/endpoints/attribute_nodes.py
@router.post("/dynamic")
async def create_dynamic_attribute(
    node_data: DynamicAttributeCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Create a dynamic attribute node (not in YAML)."""
    
    service = AttributeNodeService(db)
    
    # Create node with dynamic source
    node = await service.create_node(
        node_data,
        source="dynamic",
        is_custom=True
    )
    
    # No YAML update needed!
    
    return {
        "message": "Dynamic attribute created",
        "node": node,
        "note": "This attribute exists only in database and will persist across deployments"
    }
```

**Pros:**
- ✅ **Best of both worlds**: Static + Dynamic
- ✅ YAML for core configuration (version controlled)
- ✅ Database for user customizations (runtime flexibility)
- ✅ No file system writes needed
- ✅ Works in any environment (containers, cloud)
- ✅ No merge conflicts
- ✅ Clear separation of concerns
- ✅ Dynamic nodes survive deployments
- ✅ Can export dynamic nodes to YAML if needed

**Cons:**
- ⚠️ Slightly more complex implementation
- ⚠️ Need to track node source
- ⚠️ Need migration to add source field

**Verdict:** ✅ **RECOMMENDED - Most flexible and production-ready**

---

## Recommended Architecture

### Implementation Plan

#### Phase 1: Add Source Tracking (Week 1)

**1. Database Migration:**
```python
# backend/alembic/versions/xxx_add_source_tracking.py
def upgrade():
    op.add_column('attribute_nodes', 
        sa.Column('source', sa.String(20), nullable=False, server_default='yaml'))
    op.add_column('attribute_nodes', 
        sa.Column('is_custom', sa.Boolean(), nullable=False, server_default='false'))
    op.add_column('attribute_nodes', 
        sa.Column('extends_attribute_id', sa.Integer(), nullable=True))
    
    op.create_foreign_key(
        'fk_attribute_nodes_extends',
        'attribute_nodes', 'attribute_nodes',
        ['extends_attribute_id'], ['id']
    )
    
    op.create_index('idx_attribute_nodes_source', 'attribute_nodes', ['source'])
    op.create_index('idx_attribute_nodes_is_custom', 'attribute_nodes', ['is_custom'])
```

**2. Update Model:**
```python
# backend/app/models/attribute_node.py
class AttributeNode(Base):
    # ... existing fields ...
    
    source: Mapped[str] = mapped_column(String(20), default="yaml")
    is_custom: Mapped[bool] = mapped_column(Boolean, default=False)
    extends_attribute_id: Mapped[int | None] = mapped_column(
        ForeignKey("attribute_nodes.id"), nullable=True
    )
    
    # Relationship
    extends_attribute: Mapped["AttributeNode | None"] = relationship(
        "AttributeNode",
        remote_side="AttributeNode.id",
        foreign_keys=[extends_attribute_id]
    )
```

#### Phase 2: Implement Configuration Merger (Week 2)

**1. Create ConfigurationMerger:**
```python
# backend/app/core/config_merger.py
# (Implementation shown above)
```

**2. Update EntryService:**
```python
# backend/app/services/entry.py
# Use ConfigurationMerger.get_merged_configuration()
```

**3. Update Setup Script:**
```python
# backend/scripts/setup_hierarchy.py
# Only delete/recreate YAML nodes, preserve dynamic nodes
```

#### Phase 3: Add Dynamic Node Management API (Week 3)

**1. Create Schemas:**
```python
# backend/app/schemas/attribute_node.py
class DynamicAttributeCreate(BaseModel):
    """Schema for creating dynamic attributes."""
    page_type: str
    name: str
    display_name: str
    node_type: str
    data_type: str
    parent_node_id: int | None = None
    extends_attribute_id: int | None = None
    # ... other fields ...

class DynamicAttributeResponse(BaseModel):
    """Response schema for dynamic attributes."""
    id: int
    name: str
    display_name: str
    source: str
    is_custom: bool
    created_at: datetime
    # ... other fields ...
```

**2. Create API Endpoints:**
```python
# backend/app/api/v1/endpoints/dynamic_attributes.py
@router.post("/")
async def create_dynamic_attribute(...):
    """Create a new dynamic attribute."""
    pass

@router.get("/")
async def list_dynamic_attributes(...):
    """List all dynamic attributes for a page type."""
    pass

@router.put("/{attribute_id}")
async def update_dynamic_attribute(...):
    """Update a dynamic attribute."""
    pass

@router.delete("/{attribute_id}")
async def delete_dynamic_attribute(...):
    """Delete a dynamic attribute."""
    pass

@router.post("/export")
async def export_dynamic_to_yaml(...):
    """Export dynamic attributes to YAML format."""
    pass
```

#### Phase 4: Add UI for Dynamic Attributes (Week 4)

**1. Admin UI Components:**
- Attribute tree viewer (show YAML vs Dynamic)
- "Add Custom Attribute" button
- Inline editing for dynamic attributes
- Visual indicator for custom attributes
- Export to YAML button

**2. Differentiation in UI:**
```typescript
// frontend/src/components/AttributeTree.tsx
interface AttributeNode {
  id: number;
  name: string;
  source: 'yaml' | 'dynamic';
  is_custom: boolean;
  // ... other fields
}

function AttributeTreeNode({ node }: { node: AttributeNode }) {
  return (
    <div className={`attribute-node ${node.source}`}>
      <span>{node.display_name}</span>
      
      {node.source === 'dynamic' && (
        <Badge color="blue">Custom</Badge>
      )}
      
      {node.source === 'yaml' && (
        <Badge color="gray">Core</Badge>
      )}
      
      {node.is_custom && (
        <Button onClick={() => editAttribute(node)}>Edit</Button>
      )}
    </div>
  );
}
```

---

## Comparison Matrix

| Feature | Option 1: Watch YAML | Option 2: Generate YAML | Option 3: Hybrid | Winner |
|---------|---------------------|------------------------|------------------|--------|
| **YAML as Source of Truth** | ✅ Yes | ✅ Yes | ✅ Yes | All |
| **Dynamic Node Creation** | ❌ No | ✅ Yes | ✅ Yes | 2, 3 |
| **Works in Containers** | ❌ No | ⚠️ Difficult | ✅ Yes | **3** |
| **No File System Writes** | ❌ No | ❌ No | ✅ Yes | **3** |
| **No Merge Conflicts** | ✅ Yes | ❌ No | ✅ Yes | 1, **3** |
| **Preserves YAML Formatting** | ✅ Yes | ❌ No | ✅ Yes | 1, **3** |
| **Version Control Friendly** | ✅ Yes | ⚠️ Noisy | ✅ Yes | 1, **3** |
| **Concurrent Safe** | ⚠️ Maybe | ❌ No | ✅ Yes | **3** |
| **Clear Separation** | ❌ No | ❌ No | ✅ Yes | **3** |
| **Export Capability** | N/A | ✅ Yes | ✅ Yes | 2, **3** |
| **Implementation Complexity** | Low | Medium | Medium | 1 |
| **Production Ready** | ❌ No | ⚠️ Maybe | ✅ Yes | **3** |

**Winner: Option 3 - Hybrid Approach** 🏆

---

## Migration Path

### Step 1: Prepare Database (Day 1)
```bash
# Create migration
.venv/scripts/python -m alembic revision -m "add_source_tracking_to_attribute_nodes"

# Edit migration file
# Add source, is_custom, extends_attribute_id columns

# Run migration
.venv/scripts/python -m alembic upgrade head
```

### Step 2: Mark Existing Nodes (Day 1)
```python
# One-time script to mark all existing nodes as YAML-sourced
async def mark_existing_nodes_as_yaml():
    async with get_db_session() as db:
        await db.execute(
            update(AttributeNode)
            .values(source="yaml", is_custom=False)
        )
        await db.commit()
```

### Step 3: Implement Merger (Day 2-3)
- Create ConfigurationMerger class
- Update EntryService to use merged config
- Test with existing YAML nodes

### Step 4: Update Setup Script (Day 4)
- Modify to preserve dynamic nodes
- Only delete/recreate YAML nodes
- Test deployment scenario

### Step 5: Add Dynamic API (Day 5-7)
- Create dynamic attribute endpoints
- Add validation
- Add tests

### Step 6: Add UI (Week 2)
- Attribute tree with source indicators
- Add/edit/delete dynamic attributes
- Export functionality

---

## Best Practices

### 1. Clear Naming Convention
```yaml
# YAML attributes (core)
- name: width
- name: height
- name: material

# Dynamic attributes (user-created)
- name: custom_field_1
- name: client_specific_attribute
- name: ext_special_requirement
```

### 2. Visual Differentiation
```
Core Attributes (YAML):
  ├─ Basic Information [CORE]
  │  ├─ Name [CORE]
  │  └─ Type [CORE]
  └─ Dimensions [CORE]
     ├─ Width [CORE]
     └─ Height [CORE]

Custom Attributes (Dynamic):
  └─ Custom Fields [CUSTOM]
     ├─ Client Code [CUSTOM] ✏️
     └─ Special Notes [CUSTOM] ✏️
```

### 3. Export Capability
```python
# Allow exporting dynamic attributes to YAML
@router.post("/export")
async def export_dynamic_to_yaml(page_type: str):
    """Export dynamic attributes to YAML format for version control."""
    dynamic_nodes = await repo.get_dynamic_nodes(page_type)
    
    yaml_content = {
        'attributes': [
            {
                'name': node.name,
                'display_name': node.display_name,
                # ... all fields
            }
            for node in dynamic_nodes
        ]
    }
    
    return {
        'yaml_content': yaml.dump(yaml_content),
        'instructions': 'Copy this content to your YAML file to make these attributes permanent'
    }
```

### 4. Backup Strategy
```python
# Backup dynamic attributes before deployment
async def backup_dynamic_attributes():
    """Backup all dynamic attributes to JSON."""
    for page_type in ['profile', 'accessories', 'glazing']:
        dynamic_nodes = await repo.get_dynamic_nodes(page_type)
        
        backup_data = [node.to_dict() for node in dynamic_nodes]
        
        with open(f'backups/dynamic_{page_type}_{datetime.now()}.json', 'w') as f:
            json.dump(backup_data, f, indent=2)
```

---

## Conclusion

**Recommended Solution: Hybrid Approach (Option 3)**

**Why:**
1. ✅ Maintains YAML as source of truth for core configuration
2. ✅ Allows dynamic user customizations without file system access
3. ✅ Works in any deployment environment
4. ✅ Clear separation between core and custom
5. ✅ Production-ready and scalable
6. ✅ Supports export to YAML when needed

**Implementation Timeline:**
- Week 1: Database migration + source tracking
- Week 2: Configuration merger + API
- Week 3: UI components
- Week 4: Testing + documentation

**Next Steps:**
1. Review and approve this approach
2. Create database migration
3. Implement ConfigurationMerger
4. Update setup script
5. Build dynamic attribute API
6. Create admin UI

This approach gives you the best of both worlds: **static YAML for core configuration** and **dynamic database for user customizations**.
