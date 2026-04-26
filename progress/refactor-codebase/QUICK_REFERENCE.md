# YAML-Driven Configuration — Quick Reference Guide

**For:** Developers and business users who need to modify business rules  
**Last Updated:** April 26, 2026

---

## How to Change Business Rules (No Code Required)

### 1. Change Field Visibility Rules

**File:** `backend/config/pages/profile.yaml`

**Example:** Make `renovation` field visible only when `type = Frame`

```yaml
- name: renovation
  display_name: Renovation
  data_type: boolean
  ui_component: checkbox
  display_condition:
    operator: equals
    field: type
    value: Frame
```

**Operators available:** `equals`, `not_equals`, `contains`, `not_contains`, `in`, `not_in`, `greater_than`, `less_than`, `greater_than_or_equal`, `less_than_or_equal`, `is_empty`, `is_not_empty`, `starts_with`, `ends_with`, `matches_regex`, `any_of`, `all_of`, `none_of`, `between`, `and`, `or`, `not`

**Hot-reload:** Changes take effect within 5 seconds (no restart needed)

---

### 2. Change Validation Rules

**File:** `backend/config/pages/profile.yaml`

#### Required Field (Conditional)

```yaml
- name: total_width
  validation_rules:
    min: 0
    max: 5000
    required_when:
      operator: equals
      field: builtin_flyscreen_track
      value: true
    error_message: "Total width is required when builtin flyscreen track is enabled"
```

#### Tolerance Check (Compare Two Fields)

```yaml
- name: rear_height
  validation_rules:
    min: 0
    max: 5000
    tolerance_check:
      compare_field: front_height
      max_difference: 50
      unit: "mm"
      error_message: "Rear height should not differ from front height by more than {max_difference}{unit}"
```

#### Formula Check (Calculated Value)

```yaml
- name: price_per_beam
  validation_rules:
    min: 0
    max: 50000
    formula_check:
      formula: "price_per_meter * length_of_beam"
      tolerance: 0.1  # 10% tolerance
      error_message: "Price per beam should be approximately price per meter × length of beam"
```

**Hot-reload:** Changes take effect within 5 seconds

---

### 3. Add New Entity Types

**File:** `backend/config/product_definition/profile.yaml`

```yaml
entity_types:
  - company
  - material
  - opening_system
  - system_series
  - color
  - new_entity_type  # Add here
```

**File:** `backend/config/product_definition/glazing.yaml`

```yaml
entity_types:
  - glass_type
  - spacer
  - gas
  - new_component_type  # Add here

glazing_types:
  - single
  - double
  - triple
  - quadruple  # Add here
```

**Hot-reload:** Changes take effect within 5 seconds

---

### 4. Change UI Component Mappings

**File:** `backend/config/ui_components.yaml`

```yaml
aliases:
  input: text
  multiselect: multi-select
  file: picture-input
  new_alias: canonical_name  # Add here

fallbacks_by_data_type:
  boolean: checkbox
  number: number
  selection: dropdown
  new_type: component_name  # Add here

relations_fields:
  profile:
    - system_series
    - company
    - material
    - opening_system
    - colours
    - new_relations_field  # Add here
```

**Hot-reload:** Changes take effect within 5 seconds

---

### 5. Change Glazing Calculation Defaults

**File:** `backend/config/glazing_defaults.yaml`

```yaml
calculation_defaults:
  u_value_fallback: 5.8
  single_glass_thickness: 6.0
  inner_glass_thickness: 4.0
  outer_weight_per_sqm: 15.0
  inner_weight_per_sqm: 10.0
  spacer_thickness_double: 16.0
  spacer_thickness_triple: 12.0
  gas_u_value_improvement_factor: 0.9  # 10% improvement
  default_combined_u_value: 5.8
```

**Hot-reload:** Changes take effect within 5 seconds

---

### 6. Change Field Defaults

**File:** `backend/config/pages/profile.yaml`

```yaml
- name: upvc_profile_discount
  display_name: UPVC Profile Discount
  data_type: float
  ui_component: number
  default: 20.0  # Change this value
```

**Hot-reload:** Changes take effect within 5 seconds

---

## How to Add New Attributes

### Step 1: Add to YAML

**File:** `backend/config/pages/profile.yaml`

```yaml
- name: new_field_name
  display_name: New Field Display Name
  data_type: string  # string, number, float, boolean, selection
  ui_component: text  # text, number, checkbox, dropdown, multi-select, etc.
  section: Basic Information  # or Dimensions, Technical Specifications, Pricing
  order: 100
  required: false
  validation_rules:
    min_length: 0
    max_length: 255
  help_text: "Help text for the user"
  display_condition:  # Optional
    operator: equals
    field: some_other_field
    value: some_value
```

### Step 2: Run Setup Script

```bash
cd backend
python scripts/setup_hierarchy.py --page profile
```

This populates the `attribute_nodes` table in the database.

### Step 3: Verify

The new field will appear in the form schema immediately. No code changes needed.

---

## How to Add New Page Types

### Step 1: Create YAML File

**File:** `backend/config/pages/new_page_type.yaml`

```yaml
page_type: new_page_type
display_name: New Page Type
description: Description of this page type

sections:
  - name: Section 1
    display_name: Section 1 Display Name
    order: 1

attributes:
  - name: field1
    display_name: Field 1
    data_type: string
    ui_component: text
    section: Section 1
    order: 1
```

### Step 2: Run Setup Script

```bash
cd backend
python scripts/setup_hierarchy.py --page new_page_type
```

### Step 3: Verify

The new page type will be recognized by `ManufacturingTypeResolver.get_valid_page_types()` immediately.

---

## Troubleshooting

### Changes Not Taking Effect?

1. **Check hot-reload interval:** Config cache refreshes every 5 seconds. Wait 5 seconds and try again.
2. **Check YAML syntax:** Run `python -c "import yaml; yaml.safe_load(open('path/to/file.yaml'))"`
3. **Check logs:** Look for warnings like `Config file not found: ...`
4. **Clear cache manually:** In Python shell: `from app.core.config_loader import RuntimeConfigLoader; RuntimeConfigLoader.clear_cache()`

### YAML Syntax Errors?

- Use 2 spaces for indentation (not tabs)
- Quote strings with special characters: `"value: with: colons"`
- Use `true`/`false` for booleans (not `True`/`False`)
- Use `null` for null values (not `None`)

### Validation Not Working?

1. **Check field names:** Field names in `display_condition` and `validation_rules` must match exactly
2. **Check operators:** Use lowercase operators (`equals`, not `Equals`)
3. **Check data types:** Ensure field values match expected types (string vs number)

---

## File Locations

| Config Type | File Path |
|-------------|-----------|
| Profile page attributes | `backend/config/pages/profile.yaml` |
| Accessories page attributes | `backend/config/pages/accessories.yaml` |
| Glazing page attributes | `backend/config/pages/glazing.yaml` |
| Profile entity types | `backend/config/product_definition/profile.yaml` |
| Glazing entity types | `backend/config/product_definition/glazing.yaml` |
| UI component mappings | `backend/config/ui_components.yaml` |
| Glazing calculation defaults | `backend/config/glazing_defaults.yaml` |

---

## Code Locations (For Developers)

| Component | File Path |
|-----------|-----------|
| Config loader | `backend/app/core/config_loader.py` |
| Validation engine | `backend/app/core/validation_engine.py` |
| Condition evaluator | `backend/app/services/entry.py` (ConditionEvaluator class) |
| Entry service | `backend/app/services/entry.py` (EntryService class) |
| Setup script | `backend/scripts/setup_hierarchy.py` |

---

## API Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/v1/entry/profile/schema/{manufacturing_type_id}` | GET | Get form schema (includes all YAML-driven metadata) |
| `/api/v1/entry/profile/save` | POST | Save profile data (validates against YAML rules) |
| `/api/v1/entry/profile/evaluate-conditions` | POST | Evaluate display conditions (uses YAML conditions) |

---

## Support

For questions or issues:
1. Check this guide first
2. Check `CONTEXT.md` for codebase background
3. Check `IMPLEMENTATION_PLAN.md` for technical details
4. Check `COMPLETION_SUMMARY.md` for what was implemented

---

**Remember:** All business rule changes are now YAML-driven. No code changes or deployments needed. Hot-reload happens automatically within 5 seconds.
