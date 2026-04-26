# YAML-Driven Runtime Migration — Implementation Plan

> Signatures, skeletons, and YAML shapes — not full implementations.
> Background: CONTEXT.md | Progress tracking: CHECKLIST.md

---

## Phase 1 — Delete Hardcoded Runtime Rules
**Effort:** 2h | **Risk:** Low | **No new files**

### `backend/app/services/entry.py` — MODIFIED

**DELETE entirely** (no replacement):
```python
@staticmethod
def evaluate_business_rules(form_data: dict[str, Any]) -> dict[str, bool]: ...

async def validate_business_rules(self, form_data: dict[str, Any]) -> dict[str, str]: ...
```

**MODIFY** `evaluate_display_conditions()` — remove last 2 lines:
```python
# REMOVE these two lines at the bottom of the method:
business_rules_visibility = self.evaluate_business_rules(form_data)
visibility.update(business_rules_visibility)
```

**MODIFY** `validate_profile_data()` — remove 2 lines:
```python
# REMOVE these two lines:
business_rule_errors = await self.validate_business_rules(form_data)
errors.update(business_rule_errors)
```

**MODIFY** `get_field_display_value()` — replace body:
```python
# OLD: calls evaluate_business_rules() to decide N/A
# NEW: simple null check only — frontend handles conditional visibility
def get_field_display_value(self, field_name: str, value: Any, form_data: dict[str, Any]) -> str:
    if value is None or value == "":
        return "N/A"
    return self.format_preview_value(value)
```

---

## Phase 2 — Runtime Config Loader + Cross-Field Validation in YAML
**Effort:** 1 day | **Risk:** Medium

---

### NEW FILE: `backend/app/core/config_loader.py`

```python
"""Runtime YAML configuration loader with file-mtime hot-reload caching."""

_BACKEND_DIR = Path(__file__).resolve().parent.parent.parent  # → backend/

class RuntimeConfigLoader:
    _cache: dict[str, tuple[dict, float, float]] = {}   # key → (data, load_time, mtime)
    _last_mtime_check: dict[str, float] = {}
    _mtime_check_interval: float = 5.0                  # seconds between mtime checks

    # --- private helpers ---
    @classmethod
    def _resolve_path(cls, relative_path: str) -> Path: ...
    # returns: _BACKEND_DIR / "config" / relative_path

    @classmethod
    def _load_yaml_file(cls, path: Path) -> dict: ...
    # returns: yaml.safe_load(f) or {}
    # raises: yaml.YAMLError on bad syntax (logged + re-raised)
    # returns: {} if file not found (logged as warning)

    @classmethod
    def _get_mtime(cls, path: Path) -> float: ...
    # returns: path.stat().st_mtime or 0.0 on OSError

    @classmethod
    def _should_reload(cls, cache_key: str, path: Path) -> bool: ...
    # returns True if: not in cache, OR mtime changed since last check

    @classmethod
    def _load_with_cache(cls, cache_key: str, path: Path) -> dict: ...
    # calls _should_reload → if stale, calls _load_yaml_file and updates cache

    # --- public API ---
    @classmethod
    def load_page_config(cls, page_type: str) -> dict: ...
    # reads: config/pages/{page_type}.yaml

    @classmethod
    def load_product_definition_config(cls, scope: str) -> dict: ...
    # reads: config/product_definition/{scope}.yaml

    @classmethod
    def load_config(cls, config_name: str) -> dict: ...
    # reads: config/{config_name}.yaml  (for ui_components, glazing_defaults, etc.)

    @classmethod
    def get_attribute_config(cls, page_type: str, field_name: str) -> dict | None: ...
    # finds attribute by name in load_page_config(page_type)["attributes"]

    @classmethod
    def get_entity_types(cls, scope: str) -> list[str]: ...
    # reads load_product_definition_config(scope)["entity_types"]
    # fallback: keys of ["entities"] dict if "entity_types" key missing

    @classmethod
    def get_glazing_types(cls) -> list[str]: ...
    # reads load_product_definition_config("glazing")["glazing_types"]

    @classmethod
    def get_page_types(cls) -> list[str]: ...
    # scans config/pages/*.yaml → returns [stem, ...]
    # fallback: ["profile", "accessories", "glazing"]

    @classmethod
    def get_ui_component_aliases(cls) -> dict[str, str]: ...
    # reads load_config("ui_components")["aliases"]

    @classmethod
    def get_ui_component_fallbacks(cls) -> dict[str, str]: ...
    # reads load_config("ui_components")["fallbacks_by_data_type"]

    @classmethod
    def get_relations_fields(cls, page_type: str) -> list[str]: ...
    # reads load_config("ui_components")["relations_fields"][page_type]

    @classmethod
    def clear_cache(cls) -> None: ...
    # clears _cache and _last_mtime_check — use in tests

    @classmethod
    def disable_mtime_check(cls) -> None: ...
    # sets _mtime_check_interval = 0.0 — always reload, use in tests

    @classmethod
    def enable_mtime_check(cls) -> None: ...
    # restores _mtime_check_interval = 5.0
```

---

### NEW FILE: `backend/app/core/validation_engine.py`

```python
"""Dynamic cross-field validation engine — reads rules from YAML, no hardcoded values."""

# module-level helpers (private)
def _eval_formula(formula: str, form_data: dict) -> float | None: ...
# Safely evaluates "field_a OP field_b" using form_data values.
# Supports: +  -  *  /  (one operator, two field names only)
# Returns None if either operand is missing or non-numeric.
# NO eval() — whitelist approach only.

def _render_message(template: str, context: dict) -> str: ...
# Formats template string with context dict.
# e.g. "Max diff is {max_difference}{unit}" → "Max diff is 50mm"
# Returns template unchanged if a key is missing.


class DynamicValidationEngine:

    def __init__(self) -> None: ...
    # instantiates ConditionEvaluator (imported from entry.py)

    def validate_field(
        self,
        field_name: str,
        field_value: Any,
        form_data: dict,
        field_config: dict,      # one attribute dict from YAML
    ) -> str | None: ...
    # Checks three rule types in order:
    #   1. required_when  → uses ConditionEvaluator on the condition, checks value present
    #   2. tolerance_check → abs(field_value - compare_value) > max_difference
    #   3. formula_check  → abs(actual - expected) > expected * tolerance
    # Returns error message string or None if valid.
    # Reads error_message template from field_config["validation_rules"]["error_message"].

    def validate_form(
        self,
        form_data: dict,
        page_type: str,
    ) -> dict[str, str]: ...
    # Loads page config via RuntimeConfigLoader.load_page_config(page_type).
    # Iterates attributes, skips those without cross-field rules.
    # Calls validate_field() for each relevant attribute.
    # Returns {field_name: error_message} for all failures.
```

---

### MODIFIED: `backend/config/pages/profile.yaml`

Add these keys inside `validation_rules:` for the listed attributes.
Existing keys (`min:`, `max:`, etc.) are kept — only additions shown:

```yaml
# attribute: total_width
validation_rules:
  min: 0
  max: 5000
  required_when:            # NEW
    operator: equals
    field: builtin_flyscreen_track
    value: true
  error_message: "..."      # NEW

# attribute: flyscreen_track_height
validation_rules:
  min: 0
  max: 200
  required_when:            # NEW
    operator: equals
    field: builtin_flyscreen_track
    value: true
  error_message: "..."      # NEW

# attribute: flying_mullion_horizontal_clearance
validation_rules:
  min: 0
  max: 100
  required_when:            # NEW
    operator: equals
    field: type
    value: Flying mullion
  error_message: "..."      # NEW

# attribute: flying_mullion_vertical_clearance  (same shape as above)

# attribute: rear_height
validation_rules:
  min: 0
  max: 5000
  tolerance_check:          # NEW
    compare_field: front_height
    max_difference: 50
    unit: mm
    error_message: "Rear height should not differ from front height by more than {max_difference}{unit}"

# attribute: price_per_beam
validation_rules:
  min: 0
  max: 50000
  formula_check:            # NEW
    formula: "price_per_meter * length_of_beam"
    tolerance: 0.1
    error_message: "Price per beam should be approximately price per meter × length of beam"
```

---

### MODIFIED: `backend/app/services/entry.py`

**MODIFY** `validate_cross_field_rules()` — replace body, keep signature shape:
```python
def validate_cross_field_rules(
    self,
    form_data: dict[str, Any],
    schema: ProfileSchema,
    page_type: str = "profile",   # ADD this param
) -> dict[str, str]:
    # OLD body: ~60 lines of hardcoded if/else
    # NEW body: 2 lines
    from app.core.validation_engine import DynamicValidationEngine
    return DynamicValidationEngine().validate_form(form_data, page_type)
```

**MODIFY** `validate_profile_data()` — pass `page_type` to the call:
```python
cross_field_errors = self.validate_cross_field_rules(form_data, schema, page_type)
```

---

## Phase 3 — Entity Types from YAML
**Effort:** 4h | **Risk:** Low

---

### MODIFIED: `backend/config/product_definition/profile.yaml`

```yaml
# ADD at top level (after scope: profile)
entity_types:
  - company
  - material
  - opening_system
  - system_series
  - color
```

### MODIFIED: `backend/config/product_definition/glazing.yaml`

```yaml
# ADD at top level
entity_types:
  - glass_type
  - spacer
  - gas

glazing_types:
  - single
  - double
  - triple
```

---

### MODIFIED: `backend/app/services/product_definition/profile.py`

```python
# ADD import
from app.core.config_loader import RuntimeConfigLoader

# MODIFY create_entity() — line ~121
# OLD: valid_types = ["company", "material", "opening_system", "system_series", "color"]
# NEW: valid_types = RuntimeConfigLoader.get_entity_types("profile")

# MODIFY _validate_entity_type() — line ~419
# OLD: valid_types = ["company", "material", "opening_system", "system_series", "color"]
# NEW: valid_types = RuntimeConfigLoader.get_entity_types("profile")

# MODIFY get_dependent_options() — line ~393
# OLD: entity_types = ["company", "material", "opening_system", "system_series", "color"]
# NEW: entity_types = RuntimeConfigLoader.get_entity_types("profile") or [fallback list]
```

---

### MODIFIED: `backend/app/services/product_definition/glazing.py`

```python
# ADD import
from app.core.config_loader import RuntimeConfigLoader

# MODIFY _validate_entity_type() — line ~596
# OLD: valid_types = ["glass_type", "spacer", "gas"]
# NEW: valid_types = RuntimeConfigLoader.get_entity_types("glazing")

# MODIFY get_scope_metadata() — lines ~547-548
# OLD: "entity_types": ["glass_type", "spacer", "gas"],
#      "glazing_types": ["single", "double", "triple"],
# NEW: "entity_types": RuntimeConfigLoader.get_entity_types("glazing") or [...fallback],
#      "glazing_types": RuntimeConfigLoader.get_glazing_types() or [...fallback],
# ALSO: remove the _scope_metadata_cache early-return (RuntimeConfigLoader has its own cache)
```

---

### MODIFIED: `backend/app/schemas/product_definition/profile.py`

```python
# ADD import
from app.core.config_loader import RuntimeConfigLoader

# MODIFY ProfileEntityCreate
# OLD: entity_type: str = Field(..., pattern="^(company|material|opening_system|system_series|color)$")
# NEW:
class ProfileEntityCreate(BaseEntityCreate):
    entity_type: str = Field(..., description="Type of profile entity")

    @field_validator("entity_type")
    @classmethod
    def validate_entity_type(cls, v: str) -> str: ...
    # loads RuntimeConfigLoader.get_entity_types("profile"), raises ValueError if not in list

# MODIFY ProfileScopeResponse.entity_types default_factory
# OLD: default_factory=lambda: ["company", "material", "opening_system", "system_series", "color"]
# NEW: default_factory=lambda: RuntimeConfigLoader.get_entity_types("profile") or [...]
```

---

### MODIFIED: `backend/app/schemas/product_definition/glazing.py`

```python
# ADD import
from app.core.config_loader import RuntimeConfigLoader

# MODIFY GlazingComponentCreate
# OLD: entity_type: Literal["glass_type", "spacer", "gas"]
# NEW: entity_type: str  +  @field_validator("entity_type") → RuntimeConfigLoader.get_entity_types("glazing")

# MODIFY GlazingUnitCreate
# OLD: glazing_type: Literal["single", "double", "triple"]
# NEW: glazing_type: str  +  @field_validator("glazing_type") → RuntimeConfigLoader.get_glazing_types()

# MODIFY GlazingCalculationRequest (in endpoint file)
# OLD: glazing_type: Literal["single", "double", "triple"]
# NEW: glazing_type: str  +  @field_validator("glazing_type") → RuntimeConfigLoader.get_glazing_types()

# MODIFY GlazingScopeResponse.glazing_types default_factory
# OLD: default_factory=lambda: ["single", "double", "triple"]
# NEW: default_factory=lambda: RuntimeConfigLoader.get_glazing_types() or [...]
```

---

### MODIFIED: `backend/app/services/product_definition/types.py`

```python
# ADD import
from app.core.config_loader import RuntimeConfigLoader

# MODIFY GlazingComponentData
# OLD: component_type: str = Field(..., pattern="^(glass_type|spacer|gas)$")
# NEW: component_type: str = Field(...)  +  @field_validator → RuntimeConfigLoader.get_entity_types("glazing")

# MODIFY GlazingUnitData
# OLD: glazing_type: str = Field(..., pattern="^(single|double|triple)$")
# NEW: glazing_type: str = Field(...)  +  @field_validator → RuntimeConfigLoader.get_glazing_types()
```

---

### MODIFIED: `backend/app/core/manufacturing_type_resolver.py`

```python
# ADD import
from app.core.config_loader import RuntimeConfigLoader

# ADD new classmethod
@classmethod
def get_valid_page_types(cls) -> set[str]: ...
# returns set(RuntimeConfigLoader.get_page_types()) or fallback to the 3 constants

# MODIFY validate_page_type()
# OLD: return page_type in cls.VALID_PAGE_TYPES
# NEW: return page_type in cls.get_valid_page_types()

# KEEP VALID_PAGE_TYPES class attribute unchanged (backward compat)
```

---

### MODIFIED: `backend/app/services/product_definition/factory.py`

```python
# MODIFY _services dict — add missing accessories scope
_services: Dict[str, Type[BaseProductDefinitionService]] = {
    "profile": ProfileProductDefinitionService,
    "glazing": GlazingProductDefinitionService,
    "accessories": GlazingProductDefinitionService,   # ADD — placeholder until dedicated service exists
}
```

---

## Phase 4 — UI Component Mappings + Relations Fields from YAML
**Effort:** 3h | **Risk:** Low

---

### NEW FILE: `backend/config/ui_components.yaml`

```yaml
# Maps raw ui_component strings → canonical component names
aliases:
  input: text
  text: text
  string: text
  textinput: text
  multiselect: multi-select
  multi_select: multi-select
  file: picture-input
  image: picture-input
  picture: picture-input
  pic: picture-input

# Default component when ui_component is null/empty, keyed by data_type
fallbacks_by_data_type:
  boolean: checkbox
  number: number
  float: number
  selection: dropdown
  string: text

# Field names that load options from the relations system (not child nodes)
relations_fields:
  profile:
    - system_series
    - company
    - material
    - opening_system
    - colours
```

---

### MODIFIED: `backend/app/services/entry.py`

**MODIFY** `create_field_definition()`:

```python
async def create_field_definition(
    self,
    node: AttributeNode,
    page_type: str = "profile",   # ADD this param
) -> FieldDefinition:
    ...
    # REPLACE alias block:
    # OLD: if ui_component in ["input", "text", "string", "textinput"]: ui_component = "text"
    #      elif ui_component in ["multiselect", "multi_select"]: ui_component = "multi-select"
    #      elif ui_component in ["file", "image", "picture", "pic"]: ui_component = "picture-input"
    # NEW: aliases = RuntimeConfigLoader.get_ui_component_aliases()
    #      ui_component = aliases.get(ui_component, ui_component)

    # REPLACE fallback block:
    # OLD: if node.data_type == "boolean": ui_component = "checkbox"  (etc.)
    # NEW: fallbacks = RuntimeConfigLoader.get_ui_component_fallbacks()
    #      ui_component = fallbacks.get(node.data_type, "text")

    # REPLACE relations check:
    # OLD: if node.name in ["system_series", "company", "material", "opening_system", "colours"]:
    # NEW: relations_fields = RuntimeConfigLoader.get_relations_fields(page_type)
    #      if node.name in relations_fields:
```

**MODIFY** `generate_form_schema()` — pass `page_type` to `create_field_definition()`:
```python
# OLD: field = await self.create_field_definition(node)
# NEW: field = await self.create_field_definition(node, page_type)
```

---

## Phase 5 — Glazing Calculation Defaults from YAML
**Effort:** 2h | **Risk:** Low

---

### NEW FILE: `backend/config/glazing_defaults.yaml`

```yaml
calculation_defaults:
  u_value_fallback: 5.8           # used when component has no u_value metadata
  single_glass_thickness: 6.0     # mm — fallback for single pane outer glass
  inner_glass_thickness: 4.0      # mm — fallback for double/triple inner glass
  outer_weight_per_sqm: 15.0      # kg/m² — fallback for outer glass weight
  inner_weight_per_sqm: 10.0      # kg/m² — fallback for inner glass weight
  spacer_thickness_double: 16.0   # mm — fallback spacer for double glazing
  spacer_thickness_triple: 12.0   # mm — fallback spacer for triple glazing
  gas_u_value_improvement_factor: 0.9   # multiplier applied when gas filling present
  default_combined_u_value: 5.8   # used when no u_values collected at all
```

---

### MODIFIED: `backend/app/services/product_definition/glazing.py`

**MODIFY** `_calculate_glazing_properties()`:

```python
async def _calculate_glazing_properties(
    self, data: GlazingUnitData, components: dict[int, Any]
) -> CalculationResult:
    # ADD at top of method:
    defaults = RuntimeConfigLoader.load_config("glazing_defaults")["calculation_defaults"]

    # REPLACE all hardcoded fallbacks:
    # OLD: thickness_value if thickness_value is not None else 6.0
    # NEW: thickness_value if thickness_value is not None else defaults["single_glass_thickness"]

    # OLD: u_values.append(u_value if u_value is not None else 5.8)
    # NEW: u_values.append(u_value if u_value is not None else defaults["u_value_fallback"])

    # OLD: combined_u_value *= 0.9
    # NEW: combined_u_value *= defaults["gas_u_value_improvement_factor"]

    # OLD: combined_u_value = 5.8  # Default
    # NEW: combined_u_value = defaults["default_combined_u_value"]

    # (apply same pattern for all 8 hardcoded fallback values)
```

---

## Phase 6 — ProfileEntryData Schema Flexibility
**Effort:** 4h | **Risk:** Medium

---

### MODIFIED: `backend/config/pages/profile.yaml`

```yaml
# In the upvc_profile_discount attribute, ADD to metadata section:
  - name: upvc_profile_discount
    ...
    metadata:
      placeholder: "e.g. 20"
      default: 20.0             # ADD — loaded by schema instead of hardcoding
```

---

### MODIFIED: `backend/app/schemas/entry.py`

**MODIFY** `ProfileEntryData`:

```python
class ProfileEntryData(BaseModel):
    model_config = ConfigDict(extra="allow")   # ADD — accepts new YAML fields without code change

    # ... all existing fields unchanged ...

    upvc_profile_discount: float | None = Field(
        # OLD: default=20.0  (hardcoded)
        # NEW: load from YAML at class definition time:
        default=_load_upvc_default(),   # module-level helper that calls RuntimeConfigLoader
        ge=0,
        le=100,
        ...
    )
```

Add module-level helper before the class:
```python
def _load_upvc_default() -> float:
    # reads RuntimeConfigLoader.get_attribute_config("profile", "upvc_profile_discount")
    # returns metadata["default"] or 20.0 as fallback
    ...
```

---

## Phase 7 — Tests Cleanup
**Effort:** 4h | **Risk:** Low

---

### MODIFIED: `backend/tests/unit/services/test_entry_schema_generation.py`

```python
# OLD:
VALID_UI_COMPONENTS = ["input", "dropdown", "radio", "checkbox", "slider", "multiselect"]

# NEW:
from app.core.config_loader import RuntimeConfigLoader
_aliases = RuntimeConfigLoader.get_ui_component_aliases()
_fallbacks = RuntimeConfigLoader.get_ui_component_fallbacks()
VALID_UI_COMPONENTS = list(set(_aliases.values()) | set(_fallbacks.values()))
```

---

### MODIFIED: `backend/tests/unit/test_entry_validation.py`

```python
# OLD: "rear_height": 200.0  (hardcoded value > 50mm tolerance)
# NEW:
from app.core.config_loader import RuntimeConfigLoader
_rear_height_config = RuntimeConfigLoader.get_attribute_config("profile", "rear_height")
_max_diff = _rear_height_config["validation_rules"]["tolerance_check"]["max_difference"]
# use _max_diff + 1 as the test value that should trigger the error
```

---

### MODIFIED: `backend/tests/unit/test_entry_csv_structure.py`

```python
# OLD: hardcoded dict of 29 field names and headers
# NEW:
from app.core.config_loader import RuntimeConfigLoader

def _get_expected_fields() -> list[str]:
    config = RuntimeConfigLoader.load_page_config("profile")
    return [attr["name"] for attr in config["attributes"]]

def _get_expected_headers() -> list[str]:
    config = RuntimeConfigLoader.load_page_config("profile")
    return [attr.get("display_name") or attr["name"] for attr in config["attributes"]]
```

---

### MODIFIED: `backend/tests/unit/test_entry_preview_sync.py`

```python
# OLD: hardcoded field list
# NEW: same pattern as test_entry_csv_structure.py above
from app.core.config_loader import RuntimeConfigLoader
PROFILE_FIELDS = [a["name"] for a in RuntimeConfigLoader.load_page_config("profile")["attributes"]]
```

---

### MODIFIED: `backend/tests/unit/test_entry_error_recovery_properties.py`

```python
# OLD: hardcoded FieldDefinition instances with hardcoded validation_rules dicts
# NEW: build FieldDefinition from YAML config
from app.core.config_loader import RuntimeConfigLoader

def _field_from_yaml(field_name: str) -> FieldDefinition:
    attr = RuntimeConfigLoader.get_attribute_config("profile", field_name)
    return FieldDefinition(
        name=attr["name"],
        label=attr.get("display_name", attr["name"]),
        data_type=attr["data_type"],
        required=attr.get("required", False),
        validation_rules=attr.get("validation_rules"),
    )
```

---

### MODIFIED: `backend/tests/unit/services/test_entry_unit.py`

```python
# OLD: hardcoded validation_rules={"min_length": 1, "max_length": 200} etc.
# NEW: load from YAML
from app.core.config_loader import RuntimeConfigLoader

def _get_validation_rules(field_name: str) -> dict:
    attr = RuntimeConfigLoader.get_attribute_config("profile", field_name)
    return attr.get("validation_rules") or {}
```

---

## File Change Summary

| File | Action | Phase |
|------|--------|-------|
| `backend/app/core/config_loader.py` | **NEW** | 2 |
| `backend/app/core/validation_engine.py` | **NEW** | 2 |
| `backend/config/ui_components.yaml` | **NEW** | 4 |
| `backend/config/glazing_defaults.yaml` | **NEW** | 5 |
| `backend/app/services/entry.py` | MODIFIED | 1, 2, 4 |
| `backend/config/pages/profile.yaml` | MODIFIED | 2, 6 |
| `backend/config/product_definition/profile.yaml` | MODIFIED | 3 |
| `backend/config/product_definition/glazing.yaml` | MODIFIED | 3 |
| `backend/app/services/product_definition/profile.py` | MODIFIED | 3 |
| `backend/app/services/product_definition/glazing.py` | MODIFIED | 3, 5 |
| `backend/app/schemas/product_definition/profile.py` | MODIFIED | 3 |
| `backend/app/schemas/product_definition/glazing.py` | MODIFIED | 3 |
| `backend/app/services/product_definition/types.py` | MODIFIED | 3 |
| `backend/app/core/manufacturing_type_resolver.py` | MODIFIED | 3 |
| `backend/app/services/product_definition/factory.py` | MODIFIED | 3 |
| `backend/app/schemas/entry.py` | MODIFIED | 6 |
| `backend/tests/unit/services/test_entry_schema_generation.py` | MODIFIED | 7 |
| `backend/tests/unit/test_entry_validation.py` | MODIFIED | 7 |
| `backend/tests/unit/test_entry_csv_structure.py` | MODIFIED | 7 |
| `backend/tests/unit/test_entry_preview_sync.py` | MODIFIED | 7 |
| `backend/tests/unit/test_entry_error_recovery_properties.py` | MODIFIED | 7 |
| `backend/tests/unit/services/test_entry_unit.py` | MODIFIED | 7 |

**Deleted code (no file deletions — lines removed from existing files):**

| Method | File | Lines removed |
|--------|------|---------------|
| `EntryService.evaluate_business_rules()` | entry.py | ~58 |
| `EntryService.validate_business_rules()` | entry.py | ~70 |
| `EntryService.validate_cross_field_rules()` body | entry.py | ~60 replaced with 3 |
| Alias/fallback/relations hardcoded blocks in `create_field_definition()` | entry.py | ~20 |
| Hardcoded `valid_types` in `profile.py` service | product_definition/profile.py | 3 × 1 line |
| Hardcoded `valid_types` in `glazing.py` service | product_definition/glazing.py | 2 × 1 line |
| Hardcoded fallbacks in `_calculate_glazing_properties()` | product_definition/glazing.py | ~8 lines |
