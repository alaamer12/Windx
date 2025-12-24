# Entry Page Architecture Redesign - REQ-EPA-001

## Problem Statement

### Current Situation
The current entry system has a **fundamental architectural flaw** in how it organizes and resolves attribute schemas:

1. **Single Manufacturing Type Approach**: All attributes are tied only to `manufacturing_type_id`, which doesn't reflect the real business structure
2. **Missing Page Type Abstraction**: No concept of "Profile page", "Accessories page", "Glazing page" as distinct entities
3. **Hardcoded Assumptions**: The system assumes one manufacturing type = one page, but business reality shows we need multiple pages per manufacturing type
4. **Schema Inflexibility**: Cannot handle the fact that Window Profiles have different attributes than Door Profiles, even though both are "Profile" pages

### Business Reality (From Reference Documents)
From analyzing `upvc_cost_report.md` and `Villa Mountain View Hyde Park Order.md`, the real structure is:

```
Manufacturing Type (Window/Door) 
├── Profile Page (Frame profiles, dimensions, materials, codes)
├── Accessories Page (Hinges, handles, locks, hardware)  
└── Glazing Page (Glass specs, thickness, treatments)
```

**Each combination has unique attributes:**
- **Window Profile**: `sash_overlap`, `flyscreen_track_height`, `casement_opening_angle`
- **Door Profile**: `threshold_height`, `security_rating`, `weather_stripping_type`
- **Window Accessories**: Window hinges (7.5"), casement locks, window handles
- **Door Accessories**: Heavy hinges (10cm), door locks, panic bars

### Current Technical Issues

1. **Exception Handling**: Missing `admin/error.html.jinja` template causes 500 errors when no manufacturing types exist
2. **Manufacturing Type Resolution**: `ManufacturingTypeResolver.get_default_profile_entry_type()` only works for profile pages, not accessories/glazing
3. **URL Structure**: Routes like `/admin/entry/profile` don't indicate which manufacturing type they're for
4. **Schema Coupling**: Attribute nodes are only tied to `manufacturing_type_id`, missing the page type dimension

## Proposed Solution

### New Architecture: Dual-Key Schema System

**Core Concept**: Attributes are tied to **BOTH** `manufacturing_type_id` AND `page_type`

```sql
-- New composite key approach
AttributeNode {
    manufacturing_type_id: FK (Window, Door, etc.)
    page_type: ENUM('profile', 'accessories', 'glazing')  
    name: VARCHAR
    // ... existing fields
}

-- Composite unique constraint
UNIQUE(manufacturing_type_id, page_type, name)
```

### URL Structure Redesign

**Current (Broken):**
```
/admin/entry/profile                    # Which manufacturing type?
/admin/entry/accessories               # Which manufacturing type?
/admin/entry/glazing                   # Which manufacturing type?
```

**Proposed (Clear):**
```
/admin/entry/profile?type=window       # Window Profile page
/admin/entry/profile?type=door         # Door Profile page  
/admin/entry/accessories?type=window   # Window Accessories page
/admin/entry/accessories?type=door     # Door Accessories page
/admin/entry/glazing?type=window       # Window Glazing page
/admin/entry/glazing?type=door         # Door Glazing page
```

### Manufacturing Type Resolution Enhancement

**Current `ManufacturingTypeResolver`:**
- Only resolves default for profile entry
- Hardcoded to "Window Profile Entry"
- No page type awareness

**Enhanced Resolver:**
```python
class ManufacturingTypeResolver:
    @classmethod
    async def get_default_for_page_type(
        cls,
        db: AsyncSession,
        page_type: str,  # 'profile', 'accessories', 'glazing'
        manufacturing_category: str = "window"  # 'window', 'door'
    ) -> Optional[ManufacturingType]:
        # Resolve based on page type + category
```

## Implementation Plan

### Phase 1: Database Schema Update
1. **Add `page_type` field** to `AttributeNode` model
2. **Create migration** to add the field with default 'profile'
3. **Update unique constraints** to include page_type
4. **Migrate existing data** to set page_type='profile' for all current nodes

### Phase 2: Service Layer Updates
1. **Update `EntryService`** to handle page_type parameter
2. **Enhance schema generation** to filter by (manufacturing_type_id, page_type)
3. **Update `ManufacturingTypeResolver`** with page type awareness
4. **Add validation** for page_type values

### Phase 3: API Endpoint Updates
1. **Update admin entry routes** to accept page_type parameter
2. **Add error template** (`admin/error.html.jinja`)
3. **Update route handlers** to use enhanced resolver
4. **Add proper error handling** for missing manufacturing types

### Phase 4: Frontend Updates
1. **Update JavaScript** to handle page_type in API calls
2. **Update navigation** to show page type context
3. **Update form generation** to use (manufacturing_type_id, page_type) key
4. **Add page type selector** if multiple types exist

### Phase 5: Setup Script Updates
1. **Update `setup_profile_hierarchy.py`** to set page_type='profile'
2. **Create setup scripts** for accessories and glazing pages
3. **Update seed data** to include page_type information

## Files Requiring Updates

### Database & Models
- `app/models/attribute_node.py` - Add page_type field
- `alembic/versions/new_migration.py` - Database migration
- `app/schemas/entry.py` - Update Pydantic schemas

### Core Services  
- `app/core/manufacturing_type_resolver.py` - Add page type support
- `app/services/entry.py` - Update to handle page_type parameter
- `app/repositories/attribute_node.py` - Update queries for composite key

### API Endpoints
- `app/api/v1/endpoints/admin_entry.py` - Add page_type parameter handling
- `app/templates/admin/error.html.jinja` - Create missing error template

### Frontend
- `app/static/js/profile-entry.js` - Update API calls with page_type
- `app/templates/admin/entry/profile.html.jinja` - Add page type context
- Navigation templates - Update to show page type

### Setup & Configuration
- `scripts/setup_profile_hierarchy.py` - Set page_type='profile'
- New: `scripts/setup_accessories_hierarchy.py`
- New: `scripts/setup_glazing_hierarchy.py`

## Benefits of This Approach

### 1. **Business Alignment**
- Matches real-world structure: Manufacturing Type + Page Type
- Supports different schemas per combination
- Enables future expansion (new page types, new manufacturing types)

### 2. **Technical Flexibility**
- Schema-driven: Add new attributes without code changes
- Composite key: Proper data modeling
- Backward compatible: Existing profile data migrates cleanly

### 3. **User Experience**
- Clear URL structure shows context
- Proper error handling when data missing
- Consistent navigation across page types

### 4. **Maintainability**
- Single source of truth for attribute schemas
- Centralized manufacturing type resolution
- Clear separation of concerns

## Risk Mitigation

### 1. **Data Migration Risk**
- **Risk**: Existing attribute nodes lose context
- **Mitigation**: Migration sets page_type='profile' for all existing nodes
- **Validation**: Verify all existing configurations still work

### 2. **API Breaking Changes**
- **Risk**: Frontend breaks due to API changes
- **Mitigation**: Add page_type parameter with default value
- **Backward Compatibility**: Support old API calls during transition

### 3. **Performance Impact**
- **Risk**: Composite key queries slower
- **Mitigation**: Add proper indexes on (manufacturing_type_id, page_type)
- **Monitoring**: Track query performance before/after

## Success Criteria

1. **Functional**: All three page types (Profile, Accessories, Glazing) work independently
2. **Data Integrity**: No data loss during migration
3. **Performance**: No significant query performance degradation
4. **User Experience**: Clear error messages when manufacturing types missing
5. **Extensibility**: Easy to add new page types or manufacturing types

## Timeline Estimate

- **Phase 1 (Database)**: 2 days
- **Phase 2 (Services)**: 3 days  
- **Phase 3 (API)**: 2 days
- **Phase 4 (Frontend)**: 3 days
- **Phase 5 (Setup)**: 1 day
- **Testing & Validation**: 2 days

**Total**: ~2 weeks

---

**Status**: Draft  
**Priority**: High  
**Complexity**: Medium-High  
**Dependencies**: None  
**Stakeholders**: Development Team, Business Users