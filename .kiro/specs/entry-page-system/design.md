# Design Document

## Overview

The Entry Page system is a comprehensive data entry interface for the Windx product configurator that enables users to input product configuration data through dynamic, schema-driven forms with real-time preview capabilities. The system leverages the existing Windx hierarchical attribute architecture to generate forms dynamically, eliminating the need for hardcoded form fields while providing intelligent conditional field visibility and comprehensive validation.

The system consists of three main sub-pages: Profile (fully implemented), Accessories (scaffold), and Glazing (scaffold). Each sub-page implements a dual-view architecture with an Input View for data entry and a Preview View for real-time tabular representation of entered data.

## Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    Entry Page System                            │
├─────────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐             │
│  │   Profile   │  │ Accessories │  │   Glazing   │             │
│  │    Page     │  │    Page     │  │    Page     │             │
│  │ (Full Impl) │  │ (Scaffold)  │  │ (Scaffold)  │             │
│  └─────────────┘  └─────────────┘  └─────────────┘             │
├─────────────────────────────────────────────────────────────────┤
│                    Dual-View Architecture                       │
│  ┌─────────────────────────┐  ┌─────────────────────────┐       │
│  │      Input View         │  │     Preview View        │       │
│  │  - Dynamic Forms        │  │  - Live Table Preview  │       │
│  │  - Conditional Fields   │  │  - CSV Structure Match │       │
│  │  - Real-time Validation │  │  - Real-time Updates   │       │
│  └─────────────────────────┘  └─────────────────────────┘       │
├─────────────────────────────────────────────────────────────────┤
│                    Existing Windx Foundation                    │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │  Attribute Hierarchy • Configuration System • Pricing      │ │
│  │  Authentication • Database • Repository/Service Patterns   │ │
│  └─────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

### System Integration

The Entry Page system integrates seamlessly with existing Windx components:

- **Attribute Hierarchy**: Uses `AttributeNode` models with LTREE paths for dynamic form generation
- **Configuration System**: Creates `Configuration` and `ConfigurationSelection` records
- **Authentication**: Leverages existing user authentication and authorization
- **Database**: Uses existing PostgreSQL database with JSONB for flexible metadata
- **API Layer**: Follows established FastAPI patterns with repository/service architecture

## Components and Interfaces

### 1. Entry Page Controller

**Location**: `app/api/v1/endpoints/entry.py`

**Responsibilities**:
- Route handling for all entry page endpoints
- Authentication and authorization enforcement
- Request/response transformation
- Error handling and validation

**Key Endpoints**:
```python
@router.get("/entry/profile/schema/{manufacturing_type_id}")
async def get_profile_schema(manufacturing_type_id: int) -> ProfileSchema

@router.post("/entry/profile/save")
async def save_profile_data(profile_data: ProfileEntryData) -> Configuration

@router.get("/entry/profile/preview/{configuration_id}")
async def get_profile_preview(configuration_id: int) -> ProfilePreviewData

@router.get("/entry/profile")
async def profile_page(manufacturing_type_id: int = None) -> HTMLResponse

@router.get("/entry/accessories")
async def accessories_page() -> HTMLResponse

@router.get("/entry/glazing")
async def glazing_page() -> HTMLResponse
```

### 2. Entry Service Layer

**Location**: `app/services/entry.py`

**Responsibilities**:
- Business logic for entry page operations
- Schema-driven form generation
- Conditional field visibility evaluation
- Data validation and transformation
- Configuration creation and management

**Key Methods**:
```python
class EntryService(BaseService):
    async def get_profile_schema(self, manufacturing_type_id: int) -> ProfileSchema
    async def evaluate_display_conditions(self, form_data: dict, schema: ProfileSchema) -> dict
    async def validate_profile_data(self, data: ProfileEntryData) -> ValidationResult
    async def save_profile_configuration(self, data: ProfileEntryData, user: User) -> Configuration
    async def generate_preview_data(self, configuration_id: int) -> ProfilePreviewData
```

### 3. Schema Generation Engine

**Responsibilities**:
- Convert attribute hierarchy to form schema
- Generate field definitions with validation rules
- Build conditional display logic
- Create UI component specifications

**Core Logic**:
```python
def generate_form_schema(attribute_nodes: List[AttributeNode]) -> FormSchema:
    """Convert attribute hierarchy to form schema"""
    sections = {}
    for node in attribute_nodes:
        section = get_or_create_section(node.ltree_path)
        field = create_field_definition(node)
        section.fields.append(field)
    return FormSchema(sections=sections)

def create_field_definition(node: AttributeNode) -> FieldDefinition:
    """Create field definition from attribute node"""
    return FieldDefinition(
        name=node.name,
        data_type=node.data_type,
        required=node.required,
        validation_rules=node.validation_rules,
        display_condition=node.display_condition,
        ui_component=node.ui_component,
        description=node.description,
        help_text=node.help_text
    )
```

### 4. Smart Conditional Logic Engine

**Responsibilities**:
- Evaluate display conditions in real-time
- Support complex logical expressions with multiple operators
- Handle nested conditional dependencies and cross-field references
- Provide consistent evaluation in both Python and JavaScript
- Optimize evaluation performance with caching and short-circuiting

**Enhanced Condition Evaluation**:

The system uses a smart expression evaluator that supports a rich set of operators and can handle complex nested conditions:

```python
class ConditionEvaluator:
    """Smart condition evaluator with support for complex expressions"""
    
    OPERATORS = {
        # Comparison operators
        'equals': lambda a, b: a == b,
        'not_equals': lambda a, b: a != b,
        'greater_than': lambda a, b: (a or 0) > (b or 0),
        'less_than': lambda a, b: (a or 0) < (b or 0),
        'greater_equal': lambda a, b: (a or 0) >= (b or 0),
        'less_equal': lambda a, b: (a or 0) <= (b or 0),
        
        # String operators
        'contains': lambda a, b: str(b).lower() in str(a or '').lower(),
        'starts_with': lambda a, b: str(a or '').lower().startswith(str(b).lower()),
        'ends_with': lambda a, b: str(a or '').lower().endswith(str(b).lower()),
        'matches_pattern': lambda a, b: bool(re.match(b, str(a or ''))),
        
        # Collection operators
        'in': lambda a, b: a in (b if isinstance(b, list) else [b]),
        'not_in': lambda a, b: a not in (b if isinstance(b, list) else [b]),
        'any_of': lambda a, b: any(item in (a if isinstance(a, list) else [a]) for item in b),
        'all_of': lambda a, b: all(item in (a if isinstance(a, list) else [a]) for item in b),
        
        # Existence operators
        'exists': lambda a, b: a is not None and a != '',
        'not_exists': lambda a, b: a is None or a == '',
        'is_empty': lambda a, b: not bool(a),
        'is_not_empty': lambda a, b: bool(a),
        
        # Logical operators
        'and': lambda conditions, data: all(evaluate_condition(c, data) for c in conditions),
        'or': lambda conditions, data: any(evaluate_condition(c, data) for c in conditions),
        'not': lambda condition, data: not evaluate_condition(condition, data)
    }
    
    def evaluate_condition(self, condition: dict, form_data: dict) -> bool:
        """Evaluate a condition against form data"""
        if not condition:
            return True
            
        operator = condition.get('operator')
        if not operator:
            return True
            
        # Handle logical operators (and, or, not)
        if operator in ['and', 'or']:
            conditions = condition.get('conditions', [])
            return self.OPERATORS[operator](conditions, form_data)
        elif operator == 'not':
            inner_condition = condition.get('condition', {})
            return self.OPERATORS[operator](inner_condition, form_data)
        
        # Handle field-based operators
        field = condition.get('field')
        if not field:
            return True
            
        field_value = self.get_field_value(field, form_data)
        expected_value = condition.get('value')
        
        if operator not in self.OPERATORS:
            raise ValueError(f"Unknown operator: {operator}")
            
        return self.OPERATORS[operator](field_value, expected_value)
    
    def get_field_value(self, field_path: str, form_data: dict):
        """Get field value supporting dot notation for nested fields"""
        if '.' not in field_path:
            return form_data.get(field_path)
        
        # Support nested field access: "parent.child.grandchild"
        value = form_data
        for part in field_path.split('.'):
            if isinstance(value, dict):
                value = value.get(part)
            else:
                return None
        return value

# JavaScript equivalent for client-side evaluation
JAVASCRIPT_EVALUATOR = """
class ConditionEvaluator {
    static OPERATORS = {
        // Comparison operators
        equals: (a, b) => a == b,
        not_equals: (a, b) => a != b,
        greater_than: (a, b) => (a || 0) > (b || 0),
        less_than: (a, b) => (a || 0) < (b || 0),
        greater_equal: (a, b) => (a || 0) >= (b || 0),
        less_equal: (a, b) => (a || 0) <= (b || 0),
        
        // String operators
        contains: (a, b) => String(b).toLowerCase().includes(String(a || '').toLowerCase()),
        starts_with: (a, b) => String(a || '').toLowerCase().startsWith(String(b).toLowerCase()),
        ends_with: (a, b) => String(a || '').toLowerCase().endsWith(String(b).toLowerCase()),
        matches_pattern: (a, b) => new RegExp(b).test(String(a || '')),
        
        // Collection operators
        in: (a, b) => (Array.isArray(b) ? b : [b]).includes(a),
        not_in: (a, b) => !(Array.isArray(b) ? b : [b]).includes(a),
        any_of: (a, b) => b.some(item => (Array.isArray(a) ? a : [a]).includes(item)),
        all_of: (a, b) => b.every(item => (Array.isArray(a) ? a : [a]).includes(item)),
        
        // Existence operators
        exists: (a, b) => a !== null && a !== undefined && a !== '',
        not_exists: (a, b) => a === null || a === undefined || a === '',
        is_empty: (a, b) => !Boolean(a),
        is_not_empty: (a, b) => Boolean(a),
        
        // Logical operators handled separately
    };
    
    static evaluateCondition(condition, formData) {
        if (!condition) return true;
        
        const operator = condition.operator;
        if (!operator) return true;
        
        // Handle logical operators
        if (operator === 'and') {
            return (condition.conditions || []).every(c => 
                ConditionEvaluator.evaluateCondition(c, formData)
            );
        } else if (operator === 'or') {
            return (condition.conditions || []).some(c => 
                ConditionEvaluator.evaluateCondition(c, formData)
            );
        } else if (operator === 'not') {
            return !ConditionEvaluator.evaluateCondition(condition.condition, formData);
        }
        
        // Handle field-based operators
        const field = condition.field;
        if (!field) return true;
        
        const fieldValue = ConditionEvaluator.getFieldValue(field, formData);
        const expectedValue = condition.value;
        
        const operatorFn = ConditionEvaluator.OPERATORS[operator];
        if (!operatorFn) {
            throw new Error(`Unknown operator: ${operator}`);
        }
        
        return operatorFn(fieldValue, expectedValue);
    }
    
    static getFieldValue(fieldPath, formData) {
        if (!fieldPath.includes('.')) {
            return formData[fieldPath];
        }
        
        // Support nested field access
        let value = formData;
        for (const part of fieldPath.split('.')) {
            if (value && typeof value === 'object') {
                value = value[part];
            } else {
                return undefined;
            }
        }
        return value;
    }
}
"""
```

**Example Complex Conditions**:

```json
{
  "operator": "and",
  "conditions": [
    {
      "operator": "equals",
      "field": "type",
      "value": "Frame"
    },
    {
      "operator": "or",
      "conditions": [
        {
          "operator": "contains",
          "field": "opening_system",
          "value": "sliding"
        },
        {
          "operator": "equals",
          "field": "system_series",
          "value": "Kom800"
        }
      ]
    },
    {
      "operator": "greater_than",
      "field": "width",
      "value": 50
    }
  ]
}
```

**Performance Optimizations**:
- Condition result caching for repeated evaluations
- Short-circuit evaluation for logical operators
- Lazy evaluation of expensive operations
- Batch evaluation for multiple conditions

### 5. Preview Generation Engine

**Responsibilities**:
- Transform form data to tabular format
- Match CSV structure exactly
- Handle null/empty values gracefully
- Update in real-time

**Preview Logic**:
```python
def generate_preview_table(form_data: dict, schema: ProfileSchema) -> PreviewTable:
    """Generate preview table matching CSV structure"""
    headers = CSV_COLUMN_HEADERS  # All 29 columns
    row_data = {}
    
    for header in headers:
        field_name = header_to_field_mapping[header]
        value = form_data.get(field_name)
        row_data[header] = format_preview_value(value)
    
    return PreviewTable(headers=headers, rows=[row_data])
```

## Data Models

### 1. Profile Entry Schema

```python
class ProfileEntryData(BaseModel):
    """Profile page form data"""
    manufacturing_type_id: int
    name: str
    type: str
    company: Optional[str] = None
    material: str
    opening_system: str
    system_series: str
    code: Optional[str] = None
    length_of_beam: Optional[float] = None
    renovation: Optional[bool] = None
    width: Optional[float] = None
    builtin_flyscreen_track: Optional[bool] = None
    total_width: Optional[float] = None
    flyscreen_track_height: Optional[float] = None
    front_height: Optional[float] = None
    rear_height: Optional[float] = None
    glazing_height: Optional[float] = None
    renovation_height: Optional[float] = None
    glazing_undercut_height: Optional[float] = None
    pic: Optional[str] = None
    sash_overlap: Optional[float] = None
    flying_mullion_horizontal_clearance: Optional[float] = None
    flying_mullion_vertical_clearance: Optional[float] = None
    steel_material_thickness: Optional[float] = None
    weight_per_meter: Optional[float] = None
    reinforcement_steel: Optional[List[str]] = None
    colours: Optional[List[str]] = None
    price_per_meter: Optional[Decimal] = None
    price_per_beam: Optional[Decimal] = None
    upvc_profile_discount: Optional[float] = 20.0
```

### 2. Form Schema Models

```python
class FieldDefinition(BaseModel):
    """Individual form field definition"""
    name: str
    label: str
    data_type: str
    required: bool = False
    validation_rules: Optional[dict] = None
    display_condition: Optional[dict] = None
    ui_component: Optional[str] = None
    description: Optional[str] = None
    help_text: Optional[str] = None
    options: Optional[List[str]] = None

class FormSection(BaseModel):
    """Logical grouping of form fields"""
    title: str
    description: Optional[str] = None
    fields: List[FieldDefinition]
    sort_order: int = 0

class ProfileSchema(BaseModel):
    """Complete profile form schema"""
    manufacturing_type_id: int
    sections: List[FormSection]
    conditional_logic: dict
```

### 3. Preview Data Models

```python
class PreviewTable(BaseModel):
    """Preview table structure"""
    headers: List[str]
    rows: List[dict]
    
class ProfilePreviewData(BaseModel):
    """Profile preview response"""
    configuration_id: int
    table: PreviewTable
    last_updated: datetime
```

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system-essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property Reflection

After analyzing the prework, several properties can be consolidated:

- Properties 1.1, 1.2, 5.1, and 5.2 all relate to schema-driven form generation and can be combined into a comprehensive form generation property
- Properties 2.1, 2.4, and 6.4 all test real-time updates and can be combined into a single real-time update property
- Properties 3.1-3.5 are all specific examples of conditional display and can be covered by a general conditional display property
- Properties 4.1, 4.2, and 4.4 are specific examples of scaffold page content
- Properties 7.1 and 7.2 are specific examples of CSV structure matching

### Core Properties

**Property 1: Schema-driven form generation**
*For any* manufacturing type with attribute nodes, the system should generate forms containing exactly the fields defined in the attribute hierarchy with correct data types, validation rules, and display conditions
**Validates: Requirements 1.1, 1.2, 5.1, 5.2**

**Property 2: Real-time conditional field visibility**
*For any* form with conditional fields, when trigger field values change, dependent fields should immediately show or hide according to their display conditions
**Validates: Requirements 1.3, 3.1-3.5**

**Property 3: Real-time preview synchronization**
*For any* form data changes, the preview table should update immediately to reflect the current form state without requiring manual refresh
**Validates: Requirements 2.1, 2.4, 6.4**

**Property 4: CSV structure preservation**
*For any* profile configuration, the preview table should contain exactly 29 columns with headers matching the profile table example CSV structure
**Validates: Requirements 2.2, 7.1, 7.2**

**Property 5: Graceful null value handling**
*For any* form fields with null, empty, or N/A values, the system should display them appropriately without errors and preserve them through save/load cycles
**Validates: Requirements 2.3, 7.3, 7.4, 7.5**

**Property 6: Schema-based validation enforcement**
*For any* form submission, validation should be applied according to the attribute schema rules, preventing invalid data submission and displaying clear error messages
**Validates: Requirements 1.4, 5.3, 6.1, 6.2, 6.3**

**Property 7: Configuration data persistence**
*For any* valid profile data submission, the system should create proper Configuration and ConfigurationSelection records that can be accurately retrieved and restored to the form
**Validates: Requirements 1.5, 5.4, 5.5**

**Property 8: Navigation state preservation**
*For any* navigation between entry pages, the system should maintain the current page state and provide consistent navigation experience
**Validates: Requirements 4.5**

**Property 9: Authentication integration**
*For any* entry page access, the system should enforce authentication requirements consistent with existing Windx authentication patterns
**Validates: Requirements 8.3**

**Property 10: Error recovery and user experience**
*For any* system errors or validation failures, the system should provide user-friendly error messages and maintain user-entered data to allow corrections
**Validates: Requirements 6.5**

## Error Handling

### Client-Side Error Handling

**Validation Errors**:
- Real-time field validation using schema rules
- Immediate error display next to invalid fields
- Error clearing when fields are corrected
- Form submission prevention when errors exist

**Network Errors**:
- Retry mechanisms for transient failures
- Offline state detection and messaging
- Graceful degradation when JavaScript fails
- Progress indicators for long operations

**User Experience Errors**:
- Clear error messages in user-friendly language
- Contextual help and recovery suggestions
- Data preservation during error states
- Undo/redo capabilities where appropriate

### Server-Side Error Handling

**Validation Errors**:
```python
class ValidationException(Exception):
    def __init__(self, message: str, field_errors: dict = None):
        self.message = message
        self.field_errors = field_errors or {}

@router.post("/entry/profile/save")
async def save_profile_data(profile_data: ProfileEntryData):
    try:
        result = await entry_service.save_profile_configuration(profile_data)
        return result
    except ValidationException as e:
        raise HTTPException(
            status_code=422,
            detail={
                "message": e.message,
                "field_errors": e.field_errors
            }
        )
```

**Database Errors**:
- Transaction rollback on failures
- Constraint violation handling
- Connection timeout recovery
- Data integrity preservation

**Authentication Errors**:
- Consistent with existing Windx patterns
- Proper HTTP status codes
- Secure error messages (no information leakage)
- Session management integration

## Testing Strategy

### Dual Testing Approach

The Entry Page system requires both unit testing and property-based testing to ensure comprehensive coverage:

**Unit Tests**:
- Specific examples of conditional field visibility
- CSV structure validation with known data
- Error handling scenarios
- Integration points between components

**Property-Based Tests**:
- Schema-driven form generation across all manufacturing types
- Conditional logic evaluation with random form data
- Real-time updates with various data combinations
- Data persistence round-trip testing

### Property-Based Testing Framework

**Framework**: Hypothesis (Python property-based testing library)
**Configuration**: Minimum 100 iterations per property test
**Tagging**: Each property-based test tagged with format: `**Feature: entry-page-system, Property {number}: {property_text}**`

### Testing Implementation Requirements

**Property Test Examples**:
```python
from hypothesis import given, strategies as st
import pytest

@given(st.lists(st.builds(AttributeNode, ...)))
def test_schema_driven_form_generation(attribute_nodes):
    """**Feature: entry-page-system, Property 1: Schema-driven form generation**"""
    schema = generate_form_schema(attribute_nodes)
    assert len(schema.sections) > 0
    for section in schema.sections:
        for field in section.fields:
            assert field.name is not None
            assert field.data_type in VALID_DATA_TYPES

@given(st.dictionaries(st.text(), st.one_of(st.text(), st.integers(), st.booleans())))
def test_real_time_preview_synchronization(form_data):
    """**Feature: entry-page-system, Property 3: Real-time preview synchronization**"""
    preview = generate_preview_table(form_data, test_schema)
    assert len(preview.headers) == 29
    assert len(preview.rows) == 1
    # Verify all form data appears in preview
```

**Unit Test Examples**:
```python
def test_frame_type_shows_renovation_fields():
    """Test specific conditional display rule"""
    form_data = {"type": "Frame"}
    visible_fields = evaluate_field_visibility(form_data, profile_schema)
    assert "renovation" in visible_fields
    assert "renovation_height" in visible_fields

def test_csv_structure_matches_exactly():
    """Test preview table structure"""
    preview = generate_preview_table({}, profile_schema)
    expected_headers = load_csv_headers("reference/profile table example data.csv")
    assert preview.headers == expected_headers
```

### Integration Testing

**End-to-End Scenarios**:
- Complete profile entry workflow
- Navigation between pages
- Data persistence and retrieval
- Error handling and recovery

**Performance Testing**:
- Form generation time with large attribute hierarchies
- Real-time update responsiveness
- Database query optimization
- Memory usage with complex forms

### Test Data Management

**Fixtures**:
- Manufacturing types with complete attribute hierarchies
- Sample profile data covering all 29 CSV columns
- Various conditional display scenarios
- Error condition test cases

**Test Database**:
- Isolated test database with sample data
- Automated setup and teardown
- Consistent test data across test runs
- Performance benchmarking data