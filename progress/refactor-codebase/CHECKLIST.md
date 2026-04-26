# YAML-Driven Runtime Migration — Master Checklist

> **Goal:** Every piece of business logic, validation rule, entity type, UI mapping, and configuration
> value that currently lives as hardcoded Python must be driven from YAML at runtime.
>
> **Status legend:** `[ ]` not started · `[~]` in progress · `[x]` done · `[!]` blocked

---

## Phase 1 — Delete Hardcoded Runtime Rules
> Estimated effort: 2 hours | Risk: LOW | Impact: 🔴 CRITICAL
> No new infrastructure needed. The ConditionEvaluator + DB already handle this correctly.

### 1.1 — `backend/app/services/entry.py`
- [x] Delete `evaluate_business_rules()` static method (~lines 594–651, ~58 lines)
- [x] Delete `validate_business_rules()` async method (~lines 860–930, ~70 lines)
- [x] Delete `_has_meaningful_value()` static method (only used by deleted methods)
- [x] Fix `evaluate_display_conditions()` — removed the two lines that called `evaluate_business_rules()` and overwrote YAML-driven results
- [x] Fix `validate_profile_data()` — removed `business_rule_errors` call and merge
- [x] Fix `get_field_display_value()` — now returns N/A on empty value only; frontend handles conditional visibility via schema.conditional_logic
- [x] `validate_cross_field_rules()` — hardcoded body removed, returns `{}` as Phase 2 stub

### 1.2 — Verification
- [ ] Run existing test suite — all tests that tested `evaluate_business_rules` should now test `evaluate_display_conditions` instead
- [ ] Manually verify: submit a form with `type=Frame` and confirm `renovation` field is visible
- [ ] Manually verify: submit a form with `type=Sash` and confirm `renovation` field is hidden (N/A)
- [ ] Manually verify: `builtin_flyscreen_track` only visible when `type=frame AND opening_system contains sliding`
- [ ] Manually verify: `total_width` only visible when `builtin_flyscreen_track=true`

---

## Phase 2 — Runtime Config Loader + Cross-Field Validation in YAML
> Estimated effort: 1 day | Risk: MEDIUM | Impact: 🔴 CRITICAL

### 2.1 — Create `backend/app/core/config_loader.py`
- [x] Create `RuntimeConfigLoader` class
- [x] Implement `load_page_config(page_type: str) -> dict` with file-mtime-based cache
- [x] Implement `load_config(config_name: str) -> dict` for non-page configs
- [x] Implement `get_attribute_config(page_type: str, field_name: str) -> dict | None`
- [x] Implement `get_entity_types(scope: str) -> list[str]`
- [x] Implement `get_page_types() -> list[str]` — scans `config/pages/*.yaml` directory
- [x] Implement `clear_cache()` for hot-reload support
- [x] Add file path resolution using `__file__`-relative paths
- [x] Add graceful fallback if YAML file not found (log warning, return empty dict)

### 2.2 — Create `backend/app/core/validation_engine.py`
- [x] Create `DynamicValidationEngine` class
- [x] Implement `validate_field(field_name, field_value, form_data, field_config) -> str | None`
- [x] Support `required_when` rule type
- [x] Support `tolerance_check` rule type
- [x] Support `formula_check` rule type
- [x] Support template variables in `error_message` strings
- [x] Implement `validate_form(form_data, page_type) -> dict[str, str]`
- [x] Add safe formula evaluator (whitelist only, no eval())

### 2.3 — Extend `backend/config/pages/profile.yaml`
- [x] Add `required_when` to `total_width` attribute validation_rules
- [x] Add `required_when` to `flyscreen_track_height` attribute validation_rules
- [x] Add `required_when` to `flying_mullion_horizontal_clearance` attribute validation_rules
- [x] Add `required_when` to `flying_mullion_vertical_clearance` attribute validation_rules
- [x] Add `tolerance_check` to `rear_height` attribute validation_rules (max_difference: 50, unit: mm)
- [x] Add `formula_check` to `price_per_beam` attribute validation_rules
- [x] Add `error_message` templates to all new validation rules

### 2.4 — Update `backend/app/services/entry.py`
- [x] Replace `validate_cross_field_rules()` body with `DynamicValidationEngine().validate_form()`
- [x] Pass `page_type` through to `validate_cross_field_rules()`

### 2.5 — Verification
- [ ] Test: `builtin_flyscreen_track=true` without `total_width` → validation error
- [ ] Test: `front_height=100, rear_height=200` → validation error (diff > 50mm)
- [ ] Test: `price_per_meter=10, length_of_beam=6, price_per_beam=100` → error
- [ ] Test: change tolerance in YAML from 50 to 30, verify validation changes without code deploy

---

## Phase 3 — Entity Types from YAML
> Estimated effort: 4 hours | Risk: LOW | Impact: 🟠 HIGH

### 3.1 — Update `backend/app/services/product_definition/profile.py`
- [x] Replace hardcoded `valid_types` in `create_entity()` with `RuntimeConfigLoader.get_entity_types("profile")`
- [x] Replace hardcoded `valid_types` in `_validate_entity_type()` with loader call
- [x] Replace hardcoded `entity_types` in `get_dependent_options()` with loader call

### 3.2 — Update `backend/app/services/product_definition/glazing.py`
- [x] Replace `valid_types` in `_validate_entity_type()` with `RuntimeConfigLoader.get_entity_types("glazing")`
- [x] Replace hardcoded lists in `get_scope_metadata()` with loader calls
- [x] Remove `_scope_metadata_cache` early-return from `get_scope_metadata()`

### 3.3 — Update `backend/config/product_definition/glazing.yaml`
- [x] Add `glazing_types: [single, double, triple]` top-level key
- [x] Add `entity_types: [glass_type, spacer, gas]` top-level key

### 3.4 — Update `backend/config/product_definition/profile.yaml`
- [x] Add `entity_types: [company, material, opening_system, system_series, color]` top-level key

### 3.5 — Update `backend/app/schemas/product_definition/profile.py`
- [x] Change `ProfileEntityCreate.entity_type` pattern to `@field_validator` using `RuntimeConfigLoader`
- [x] Change `ProfileScopeResponse.entity_types` default_factory to load from config

### 3.6 — Update `backend/app/schemas/product_definition/glazing.py`
- [x] Change `GlazingComponentCreate.entity_type` from `Literal` to `str` + `@field_validator`
- [x] Change `GlazingUnitCreate.glazing_type` from `Literal` to `str` + `@field_validator`
- [x] Change `GlazingCalculationRequest.glazing_type` from `Literal` to `str` + `@field_validator`
- [x] Change `GlazingScopeResponse.glazing_types` default_factory to config loader

### 3.7 — Update `backend/app/services/product_definition/types.py`
- [x] Change `GlazingComponentData.component_type` pattern to `@field_validator`
- [x] Change `GlazingUnitData.glazing_type` pattern to `@field_validator`

### 3.8 — Update `backend/app/core/manufacturing_type_resolver.py`
- [x] Add `get_valid_page_types()` classmethod using `RuntimeConfigLoader.get_page_types()`
- [x] Update `validate_page_type()` to use `get_valid_page_types()`
- [x] Keep `VALID_PAGE_TYPES` class attribute for backward compat

### 3.9 — Update `backend/app/services/product_definition/factory.py`
- [x] Add `accessories` scope registration

### 3.10 — Update `backend/app/api/v1/endpoints/product_definitions/glazing.py`
- [x] Replace `Literal["single","double","triple"]` in `GlazingCalculationRequest` with `str` + `@field_validator`

---

## Phase 4 — UI Component Mappings + Relations Fields from YAML
> Estimated effort: 3 hours | Risk: LOW | Impact: 🟠 HIGH

### 4.1 — Create `backend/config/ui_components.yaml`
- [x] Add `aliases` section
- [x] Add `fallbacks_by_data_type` section
- [x] Add `relations_fields` section per page type

### 4.2 — Update `backend/app/services/entry.py` `create_field_definition()`
- [x] Add `page_type` parameter
- [x] Replace hardcoded alias block with `RuntimeConfigLoader.get_ui_component_aliases()`
- [x] Replace hardcoded fallback block with `RuntimeConfigLoader.get_ui_component_fallbacks()`
- [x] Replace hardcoded relations field list with `RuntimeConfigLoader.get_relations_fields(page_type)`
- [x] Update `generate_form_schema()` to pass `page_type` to `create_field_definition()`
- [x] Update `get_profile_schema()` to pass `page_type` to `generate_form_schema()`

---

## Phase 5 — Glazing Calculation Defaults from YAML
> Estimated effort: 2 hours | Risk: LOW | Impact: 🟠 HIGH

### 5.1 — Create `backend/config/glazing_defaults.yaml`
- [x] Add `calculation_defaults` section with all 9 fallback values

### 5.2 — Update `backend/app/services/product_definition/glazing.py`
- [x] Load defaults dict at top of `_calculate_glazing_properties()`
- [x] Replace all hardcoded fallback values with `d.get("key", fallback)`
- [x] Replace `combined_u_value *= 0.9` with YAML factor
- [x] Replace `combined_u_value = 5.8` default with YAML value

---

## Phase 6 — ProfileEntryData Schema Flexibility
> Estimated effort: 4 hours | Risk: MEDIUM | Impact: 🟡 MEDIUM

### 6.1 — Update `backend/app/schemas/entry.py` `ProfileEntryData`
- [x] Add `model_config = ConfigDict(extra="allow")`
- [x] Add `_load_upvc_default()` module-level helper
- [x] Replace `default=20.0` with `default_factory=_load_upvc_default`

### 6.2 — Update `backend/config/pages/profile.yaml`
- [x] Add `default: 20.0` to `upvc_profile_discount` attribute metadata section

---

## Phase 2 — Runtime Config Loader + Cross-Field Validation in YAML
> Estimated effort: 1 day | Risk: MEDIUM | Impact: 🔴 CRITICAL

### 2.1 — Create `backend/app/core/config_loader.py`
- [ ] Create `RuntimeConfigLoader` class
- [ ] Implement `load_page_config(page_type: str) -> dict` with file-mtime-based cache
- [ ] Implement `load_config(config_name: str) -> dict` for non-page configs (ui_components, glazing_defaults, etc.)
- [ ] Implement `get_attribute_config(page_type: str, field_name: str) -> dict | None`
- [ ] Implement `get_entity_types(scope: str) -> list[str]` — reads from `config/product_definition/{scope}.yaml`
- [ ] Implement `get_page_types() -> list[str]` — scans `config/pages/*.yaml` directory
- [ ] Implement `clear_cache()` for hot-reload support
- [ ] Add file path resolution that works from any working directory (use `__file__`-relative paths)
- [ ] Add graceful fallback if YAML file not found (log warning, return empty dict)

### 2.2 — Create `backend/app/core/validation_engine.py`
- [ ] Create `DynamicValidationEngine` class
- [ ] Implement `validate_field(field_name, field_value, form_data, field_config) -> str | None`
- [ ] Support `required_when` rule type — uses `ConditionEvaluator` to check condition, then checks if value is present
- [ ] Support `tolerance_check` rule type — `abs(field_value - compare_field_value) > max_difference`
- [ ] Support `formula_check` rule type — safe formula evaluation with `form_data` as context, then tolerance check
- [ ] Support template variables in `error_message` strings: `{field_label}`, `{max_difference}`, `{unit}`, `{tolerance}`, `{formula}`
- [ ] Implement `validate_form(form_data, page_type) -> dict[str, str]` — iterates all attributes in YAML config
- [ ] Add safe formula evaluator (whitelist of allowed operations: `+`, `-`, `*`, `/`, field names only — no `eval()` on arbitrary code)

### 2.3 — Extend `backend/config/pages/profile.yaml`
- [ ] Add `required_when` to `total_width` attribute validation_rules
- [ ] Add `required_when` to `flyscreen_track_height` attribute validation_rules
- [ ] Add `required_when` to `flying_mullion_horizontal_clearance` attribute validation_rules
- [ ] Add `required_when` to `flying_mullion_vertical_clearance` attribute validation_rules
- [ ] Add `tolerance_check` to `rear_height` attribute validation_rules (max_difference: 50, unit: mm)
- [ ] Add `formula_check` to `price_per_beam` attribute validation_rules (formula: `price_per_meter * length_of_beam`, tolerance: 0.1)
- [ ] Add `error_message` templates to all new validation rules

### 2.4 — Update `backend/app/services/entry.py`
- [ ] Replace `validate_cross_field_rules()` body with call to `DynamicValidationEngine.validate_form()`
- [ ] Keep `validate_cross_field_rules()` as a thin wrapper for backward compatibility (or rename and update callers)
- [ ] Import `RuntimeConfigLoader` and `DynamicValidationEngine` at top of file

### 2.5 — Verification
- [ ] Test: `builtin_flyscreen_track=true` without `total_width` → validation error
- [ ] Test: `builtin_flyscreen_track=true` with `total_width` → no error
- [ ] Test: `front_height=100, rear_height=200` → validation error (diff > 50mm)
- [ ] Test: `front_height=100, rear_height=140` → no error (diff = 40mm, within tolerance)
- [ ] Test: `price_per_meter=10, length_of_beam=6, price_per_beam=100` → error (expected 60, got 100, >10% diff)
- [ ] Test: `price_per_meter=10, length_of_beam=6, price_per_beam=62` → no error (within 10%)
- [ ] Test: change tolerance in YAML from 50 to 30, verify validation changes without code deploy

---

## Phase 3 — Entity Types from YAML
> Estimated effort: 4 hours | Risk: LOW | Impact: 🟠 HIGH

### 3.1 — Update `backend/app/services/product_definition/profile.py`
- [ ] Replace hardcoded `valid_types = ["company","material","opening_system","system_series","color"]` in `create_entity()` with `RuntimeConfigLoader.get_entity_types("profile")`
- [ ] Replace same hardcoded list in `_validate_entity_type()` with loader call
- [ ] Replace same hardcoded list in `get_dependent_options()` with loader call
- [ ] Ensure all 3 locations now read from the same single source

### 3.2 — Update `backend/app/services/product_definition/glazing.py`
- [ ] Replace `valid_types = ["glass_type","spacer","gas"]` in `_validate_entity_type()` with `RuntimeConfigLoader.get_entity_types("glazing")`
- [ ] Replace `"entity_types": ["glass_type","spacer","gas"]` in `get_scope_metadata()` with loader call
- [ ] Replace `"glazing_types": ["single","double","triple"]` in `get_scope_metadata()` with loader call (add `glazing_types` key to `config/product_definition/glazing.yaml`)

### 3.3 — Update `backend/config/product_definition/glazing.yaml`
- [ ] Add `glazing_types: [single, double, triple]` top-level key
- [ ] Add `entity_types: [glass_type, spacer, gas]` top-level key (for explicit loader access)

### 3.4 — Update `backend/config/product_definition/profile.yaml`
- [ ] Add `entity_types: [company, material, opening_system, system_series, color]` top-level key

### 3.5 — Update `backend/app/schemas/product_definition/profile.py`
- [ ] Change `ProfileEntityCreate.entity_type` from `pattern="^(company|...)"` to `str` with a custom `@field_validator` that calls `RuntimeConfigLoader.get_entity_types("profile")` at validation time
- [ ] Change `ProfileScopeResponse.entity_types` default from hardcoded lambda to a function that loads from config

### 3.6 — Update `backend/app/schemas/product_definition/glazing.py`
- [ ] Change `GlazingComponentCreate.entity_type` from `Literal["glass_type","spacer","gas"]` to `str` with validator
- [ ] Change `GlazingUnitCreate.glazing_type` from `Literal["single","double","triple"]` to `str` with validator
- [ ] Change `GlazingCalculationRequest.glazing_type` from `Literal` to `str` with validator
- [ ] Change `GlazingScopeResponse.glazing_types` default from hardcoded lambda to config loader

### 3.7 — Update `backend/app/services/product_definition/types.py`
- [ ] Change `GlazingComponentData.component_type` from `pattern="^(glass_type|spacer|gas)$"` to `str` with validator
- [ ] Change `GlazingUnitData.glazing_type` from `pattern="^(single|double|triple)$"` to `str` with validator

### 3.8 — Update `backend/app/core/manufacturing_type_resolver.py`
- [ ] Replace `VALID_PAGE_TYPES = {PAGE_TYPE_PROFILE, PAGE_TYPE_ACCESSORIES, PAGE_TYPE_GLAZING}` with dynamic set loaded from `RuntimeConfigLoader.get_page_types()`
- [ ] Keep the 3 string constants (`PAGE_TYPE_PROFILE` etc.) as convenience aliases — they're fine
- [ ] Update `validate_page_type()` to use the dynamic set

### 3.9 — Update `backend/app/services/product_definition/factory.py`
- [ ] Add `accessories` scope registration (currently missing — only `profile` and `glazing` registered)
- [ ] Consider auto-registration by scanning `config/product_definition/` directory

### 3.10 — Verification
- [ ] Test: create profile entity with `entity_type="company"` → succeeds
- [ ] Test: create profile entity with `entity_type="invalid_type"` → validation error with message listing valid types
- [ ] Test: add new entity type to `profile.yaml`, verify it's accepted without code change
- [ ] Test: create glazing component with `entity_type="glass_type"` → succeeds
- [ ] Test: `ManufacturingTypeResolver.validate_page_type("profile")` → True
- [ ] Test: `ManufacturingTypeResolver.validate_page_type("new_page")` → False (not in config)

---

## Phase 4 — UI Component Mappings + Relations Fields from YAML
> Estimated effort: 3 hours | Risk: LOW | Impact: 🟠 HIGH

### 4.1 — Create `backend/config/ui_components.yaml`
- [ ] Add `aliases` section: `input → text`, `text → text`, `string → text`, `textinput → text`, `multiselect → multi-select`, `multi_select → multi-select`, `file → picture-input`, `image → picture-input`, `picture → picture-input`, `pic → picture-input`
- [ ] Add `fallbacks_by_data_type` section: `boolean → checkbox`, `number → number`, `float → number`, `selection → dropdown`
- [ ] Add `relations_fields` section per page type: `profile: [system_series, company, material, opening_system, colours]`

### 4.2 — Update `backend/app/services/entry.py` `create_field_definition()`
- [ ] Replace the hardcoded `if ui_component in ["input", "text", "string", "textinput"]` block with a lookup against `RuntimeConfigLoader.load_config("ui_components")["aliases"]`
- [ ] Replace the hardcoded `elif not ui_component` fallback block with a lookup against `fallbacks_by_data_type`
- [ ] Replace the hardcoded `if node.name in ["system_series", "company", ...]` check with a lookup against `relations_fields[page_type]` from config
- [ ] Pass `page_type` into `create_field_definition()` (currently it doesn't receive it — need to thread it through from `generate_form_schema()`)

### 4.3 — Verification
- [ ] Test: node with `ui_component="input"` → field definition has `ui_component="text"`
- [ ] Test: node with `ui_component="multiselect"` → field definition has `ui_component="multi-select"`
- [ ] Test: node with `ui_component="file"` → field definition has `ui_component="picture-input"`
- [ ] Test: node with `ui_component=None, data_type="boolean"` → field definition has `ui_component="checkbox"`
- [ ] Test: add new alias to `ui_components.yaml`, verify it works without code change
- [ ] Test: `system_series` field gets options from relations system
- [ ] Test: add new field to `relations_fields.profile` in YAML, verify it uses relations system

---

## Phase 5 — Glazing Calculation Defaults from YAML
> Estimated effort: 2 hours | Risk: LOW | Impact: 🟠 HIGH

### 5.1 — Create `backend/config/glazing_defaults.yaml`
- [ ] Add `calculation_defaults` section:
  - `u_value_fallback: 5.8`
  - `single_glass_thickness: 6.0`
  - `inner_glass_thickness: 4.0`
  - `outer_weight_per_sqm: 15.0`
  - `inner_weight_per_sqm: 10.0`
  - `spacer_thickness_double: 16.0`
  - `spacer_thickness_triple: 12.0`
  - `gas_u_value_improvement_factor: 0.9`
  - `default_combined_u_value: 5.8`

### 5.2 — Update `backend/app/services/product_definition/glazing.py`
- [ ] Load defaults at top of `_calculate_glazing_properties()` via `RuntimeConfigLoader.load_config("glazing_defaults")["calculation_defaults"]`
- [ ] Replace all `or 5.8`, `or 6.0`, `or 4.0`, `or 15.0`, `or 10.0`, `or 16.0`, `or 12.0` fallbacks with loaded defaults
- [ ] Replace `combined_u_value *= 0.9` with `combined_u_value *= defaults["gas_u_value_improvement_factor"]`
- [ ] Replace `combined_u_value = 5.8` default with `defaults["default_combined_u_value"]`

### 5.3 — Verification
- [ ] Test: calculate single pane with no metadata → uses YAML defaults, not hardcoded values
- [ ] Test: change `u_value_fallback` in YAML to `6.0`, verify calculation changes
- [ ] Test: calculate double pane with gas → gas improvement factor applied from YAML

---

## Phase 6 — ProfileEntryData Schema Flexibility
> Estimated effort: 4 hours | Risk: MEDIUM | Impact: 🟡 MEDIUM

### 6.1 — Update `backend/app/schemas/entry.py` `ProfileEntryData`
- [ ] Add `model_config = ConfigDict(extra="allow")` so new YAML attributes are accepted without code changes
- [ ] Load `upvc_profile_discount` default value from `RuntimeConfigLoader.load_page_config("profile")` — find the attribute with `name="upvc_profile_discount"` and read its `metadata.default` value
- [ ] Add `default` key to `upvc_profile_discount` attribute in `profile.yaml` metadata section: `default: 20.0`
- [ ] Update `normalize_multi_select` validator — make it generic for any field with `ui_component: multi-select` rather than hardcoded for `colours` only (or keep as-is since it's a Pydantic validator limitation)

### 6.2 — Update `backend/config/pages/profile.yaml`
- [ ] Add `default: 20.0` to `upvc_profile_discount` attribute's `metadata` section

### 6.3 — Verification
- [ ] Test: submit form with a new field not in `ProfileEntryData` explicit fields → accepted (extra="allow")
- [ ] Test: `upvc_profile_discount` default is `20.0` (loaded from YAML)
- [ ] Test: change default in YAML to `15.0`, verify schema default changes

---

## Phase 7 — Tests Cleanup
> Estimated effort: 4 hours | Risk: LOW | Impact: 🟢 LOW

### 7.1 — `backend/tests/unit/services/test_entry.py`
- [x] Deleted `TestEntryServiceBusinessRules` class (tested deleted `evaluate_business_rules()`)
- [x] Deleted `test_get_field_display_value_with_business_rules` (tested old N/A logic)
- [x] Fixed `TestConditionEvaluator` class structure after deletion

### 7.2 — `backend/tests/unit/services/test_entry_schema_generation.py`
- [x] Replace `VALID_UI_COMPONENTS` hardcoded list with values loaded from `ui_components.yaml`
- [x] Fix `test_field_definition_creation` — `create_field_definition` is now async + takes `page_type`

### 7.3 — `backend/tests/unit/test_entry_validation.py`
- [x] Remove `reinforcement_steel_missing_thickness` scenario (was a business rule, not YAML cross-field)
- [x] Fix `height_difference_too_large` — load tolerance from YAML instead of hardcoding `200.0`
- [x] Updated docstring to reflect YAML-driven validation

### 7.4 — `backend/tests/unit/test_entry_csv_structure.py`
- [x] Replace hardcoded 29-field header list with `_load_profile_headers()` from YAML
- [x] Replace hardcoded header→field mapping with `_load_header_field_mapping()` from YAML

### 7.5 — `backend/tests/unit/test_entry_preview_sync.py`
- [x] Replace hardcoded header→field mapping with YAML-loaded mapping

### 7.6 — `backend/tests/unit/test_entry_null_handling_properties.py`
- [x] Replace hardcoded optional field list with `_get_optional_profile_fields()` from YAML

### 7.7 — `backend/tests/unit/test_entry_data_persistence.py`
- [x] Replace hardcoded field list in `attribute_node_data()` with `_get_all_profile_fields()` from YAML
- [x] Replace both hardcoded inline field lists with YAML-loaded list

### 7.8 — Files verified as NOT needing changes
- `test_entry_error_recovery_properties.py` — uses generic FieldDefinition mocks, not hardcoded profile fields
- `test_entry_validation_properties.py` — tests generic validation logic, not hardcoded business rules
- `test_entry_data_persistence_properties.py` — only references `upvc_profile_discount` as a float field, still valid
- `test_entry_null_handling.py` — generates data using field names directly, compatible with `extra="allow"`

---

## Cross-Cutting Concerns (all phases)

### Error Handling
- [ ] All `RuntimeConfigLoader` calls have try/except with meaningful fallback behavior
- [ ] Missing YAML file → log warning, use empty dict (don't crash)
- [ ] Malformed YAML → log error with file path and line number, raise on startup
- [ ] Missing key in config → use sensible default, log debug message

### Caching Strategy
- [ ] Config files cached in memory after first load
- [ ] Cache invalidated when file mtime changes (hot-reload)
- [ ] Cache cleared on test setup/teardown
- [ ] Cache is per-process (class-level dict), not per-request

### Path Resolution
- [ ] All config paths resolved relative to `backend/` directory using `Path(__file__).resolve()`
- [ ] Works when running from project root (`python manage.py`)
- [ ] Works when running from `backend/` directory (`python scripts/setup_hierarchy.py`)
- [ ] Works in Docker/devcontainer environments

### Backward Compatibility
- [ ] All existing API endpoints continue to work unchanged
- [ ] All existing tests pass after each phase
- [ ] No database migrations required (all changes are in Python/YAML layer)
- [ ] `setup_hierarchy.py` script continues to work unchanged

---

## Final Verification Checklist

### Functional
- [ ] Profile form schema generated correctly from DB (populated from YAML)
- [ ] All 11 display conditions evaluated correctly at runtime
- [ ] All cross-field validation rules work from YAML config
- [ ] Entity type validation works for profile scope (5 types)
- [ ] Entity type validation works for glazing scope (3 types + 3 glazing types)
- [ ] UI component mapping works for all aliases
- [ ] Relations fields load options from relations system
- [ ] Glazing calculations use YAML defaults when component metadata missing

### Configuration-Driven
- [ ] Adding new attribute to `profile.yaml` + running `setup_hierarchy.py` → attribute appears in form, no code change
- [ ] Adding new display condition to YAML attribute → condition evaluated at runtime, no code change
- [ ] Adding new cross-field validation rule to YAML → validation applied, no code change
- [ ] Changing tolerance value in YAML → validation behavior changes, no code change
- [ ] Adding new entity type to `profile.yaml` → type accepted in API, no code change
- [ ] Adding new page type YAML file → page type recognized by resolver, no code change

### Performance
- [ ] Config files loaded once and cached (not re-read on every request)
- [ ] Cache hit rate > 99% in normal operation
- [ ] No measurable latency increase on API endpoints

### Code Quality
- [ ] Zero hardcoded entity type lists in service layer
- [ ] Zero hardcoded field visibility rules in service layer
- [ ] Zero hardcoded tolerance values in service layer
- [ ] Zero hardcoded UI component aliases in service layer
- [ ] Zero hardcoded relations field lists in service layer
- [ ] All removed code has corresponding YAML entries
