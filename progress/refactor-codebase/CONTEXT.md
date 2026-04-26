# Codebase Context — YAML-Driven Runtime Migration

> This document captures the complete state of the codebase as of the analysis date.
> Use it as the reference when implementing each phase.

---

## Project Overview

WindX is a window/door product configurator. The backend is a FastAPI + SQLAlchemy async Python app.
The frontend consumes a dynamic form schema from the API and renders entry pages for three product types:
**profile**, **accessories**, and **glazing**.

A previous migration moved database *setup* scripts from hardcoded Python to YAML configuration files.
That migration is complete. What remains is making the *runtime application layer* read from those
same YAML files instead of duplicating the data as hardcoded Python.

---

## Directory Structure (relevant paths)

```
windx/
├── manage.py                          # CLI management commands (3019 lines)
├── backend/
│   ├── config/
│   │   ├── pages/
│   │   │   ├── profile.yaml           # 29 profile attributes with display_conditions, validation_rules
│   │   │   ├── accessories.yaml       # 15 accessory attributes
│   │   │   └── glazing.yaml           # 20 glazing attributes
│   │   ├── product_definition/
│   │   │   ├── profile.yaml           # Entity types, hierarchy, dependencies for profile scope
│   │   │   ├── glazing.yaml           # Entity types, hierarchy for glazing scope
│   │   │   └── hardware.yaml          # Hardware scope config
│   │   ├── rbac_model.conf
│   │   └── rbac_policy.csv
│   ├── scripts/
│   │   ├── setup_hierarchy.py         # Unified YAML→DB setup script (reads config/pages/*.yaml)
│   │   ├── seed_profile_data.py       # Seeds sample profile configurations
│   │   └── product_definition/
│   │       ├── setup_profile.py       # Sets up profile scope entities
│   │       ├── setup_glazing.py       # Sets up glazing scope entities
│   │       └── debug_*.py             # Debug scripts
│   └── app/
│       ├── core/
│       │   ├── config_loader.py       # ← DOES NOT EXIST YET (Phase 2)
│       │   ├── manufacturing_type_resolver.py  # Resolves mfg types by name
│       │   ├── exceptions.py
│       │   ├── rbac.py
│       │   └── security.py
│       ├── services/
│       │   ├── entry.py               # 2065 lines — main target for Phase 1 & 2
│       │   └── product_definition/
│       │       ├── base.py            # Abstract base — already loads YAML for scope metadata
│       │       ├── profile.py         # Profile scope service — has hardcoded entity type lists
│       │       ├── glazing.py         # Glazing scope service — has hardcoded entity types + calc defaults
│       │       ├── factory.py         # Service factory — missing accessories registration
│       │       ├── types.py           # Shared data types — has hardcoded patterns
│       │       └── __init__.py
│       ├── schemas/
│       │   ├── entry.py               # ProfileEntryData (29 hardcoded fields), ProfileSchema
│       │   └── product_definition/
│       │       ├── profile.py         # ProfileEntityCreate (hardcoded pattern), ProfileScopeResponse
│       │       ├── glazing.py         # GlazingComponentCreate (Literal types), GlazingUnitCreate
│       │       └── base.py
│       ├── api/v1/endpoints/
│       │   ├── entry.py               # Entry page API endpoints
│       │   └── product_definitions/
│       │       ├── profile.py         # Profile definition endpoints
│       │       ├── glazing.py         # Glazing definition endpoints
│       │       └── base.py
│       └── models/
│           └── attribute_node.py      # AttributeNode model — stores display_condition, validation_rules
```

---

## Key Classes and Their Roles

### `ConditionEvaluator` (entry.py, ~line 100)
Already fully implemented. Supports 20+ operators including `equals`, `contains`, `and`, `or`, `not`,
`in`, `is_not_empty`, etc. Used by `evaluate_display_conditions()` to evaluate `display_condition`
dicts stored in `AttributeNode.display_condition` (which came from YAML via setup script).

**This class is correct and complete. It just needs to be the ONLY evaluator — the hardcoded
`evaluate_business_rules()` must be deleted so it stops overwriting the correct results.**

### `EntryService` (entry.py, ~line 230)
The main service. Key methods:
- `get_profile_schema()` — loads AttributeNodes from DB, calls `generate_form_schema()`
- `generate_form_schema()` — builds `ProfileSchema` with `conditional_logic` dict (field_name → display_condition)
- `create_field_definition()` — maps AttributeNode → FieldDefinition, has hardcoded UI component aliases
- `evaluate_display_conditions()` — correctly uses ConditionEvaluator BUT then overwrites with hardcoded rules
- `evaluate_business_rules()` — ❌ MUST BE DELETED — duplicates YAML display_conditions
- `validate_business_rules()` — ❌ MUST BE DELETED — duplicates YAML display_conditions as validation
- `validate_cross_field_rules()` — ❌ MUST BE REPLACED — has hardcoded 50mm/10% tolerances
- `validate_profile_data()` — orchestrates validation, calls both methods above
- `get_field_display_value()` — calls `evaluate_business_rules()` for N/A display — must be fixed

### `BaseProductDefinitionService` (product_definition/base.py)
Already has `_load_scope_metadata_from_yaml()` which reads `config/product_definition/{scope}.yaml`.
This is the existing runtime YAML loading infrastructure. The `RuntimeConfigLoader` in Phase 2
will be a more general version of this pattern.

### `ProfileProductDefinitionService` (product_definition/profile.py)
Has 3 separate hardcoded copies of `["company","material","opening_system","system_series","color"]`.
The `config/product_definition/profile.yaml` already has a `hierarchy` section with these types.

### `GlazingProductDefinitionService` (product_definition/glazing.py)
Has hardcoded `["glass_type","spacer","gas"]` and `["single","double","triple"]`.
Has hardcoded fallback values in `_calculate_glazing_properties()` (u_value=5.8, thickness=6.0, etc.).
The `get_scope_metadata()` method is fully hardcoded (doesn't call `_load_scope_metadata_from_yaml()`).

### `ManufacturingTypeResolver` (core/manufacturing_type_resolver.py)
Has `VALID_PAGE_TYPES = {PAGE_TYPE_PROFILE, PAGE_TYPE_ACCESSORIES, PAGE_TYPE_GLAZING}` as a hardcoded
class-level set. Should be derived from scanning `config/pages/*.yaml` at startup.

---

## YAML Files — What They Already Contain

### `config/pages/profile.yaml`
- 29 attributes with full metadata
- `display_condition` on 11 attributes (renovation, builtin_flyscreen_track, total_width,
  flyscreen_track_height, renovation_height, glazing_undercut_height, sash_overlap,
  flying_mullion_horizontal_clearance, flying_mullion_vertical_clearance, steel_material_thickness,
  coating_position [glazing], air_gap [glazing])
- `validation_rules` with `min`, `max`, `min_length`, `max_length`, `options` on most attributes
- `calculated_field` on `price_per_meter` and `price_per_beam`
- `ui_component` on all attributes
- `options` list on `type` attribute (10 options)
- **MISSING:** `required_when`, `tolerance_check`, `formula_check` in validation_rules (Phase 2 adds these)
- **MISSING:** `default` in metadata for `upvc_profile_discount` (Phase 6 adds this)

### `config/product_definition/profile.yaml`
- `entities` section with 5 entity types: company, material, opening_system, system_series, color
- `hierarchy` section: `0: company, 1: material, 2: opening_system, 3: system_series, 4: color`
- `dependencies` section for auto-fill rules
- **MISSING:** top-level `entity_types` list (Phase 3 adds this)

### `config/product_definition/glazing.yaml`
- `entities` section with 3 entity types: glass_unit, spacer, gas
- `hierarchy` section
- **MISSING:** top-level `entity_types` and `glazing_types` lists (Phase 3 adds these)
- **NOTE:** The glazing.yaml uses `glass_unit` but the service uses `glass_type` — this discrepancy
  needs to be resolved in Phase 3

---

## The Core Problem Explained

```
YAML files (config/pages/*.yaml)
    ↓ [setup_hierarchy.py — one-time]
AttributeNode table (PostgreSQL)
    ↓ [EntryService.get_profile_schema() — every request]
ProfileSchema.conditional_logic  ← ✅ display_conditions ARE here
    ↓ [EntryService.evaluate_display_conditions()]
ConditionEvaluator.evaluate_condition()  ← ✅ evaluates correctly
    ↓ BUT THEN...
evaluate_business_rules()  ← ❌ OVERWRITES with hardcoded Python
```

The fix for Phase 1 is simply removing the last step. The infrastructure is already correct.

---

## Violation Inventory — Complete Reference

### 🔴 CRITICAL (Phase 1 & 2)

| ID | File | Method | Lines | Description |
|----|------|--------|-------|-------------|
| C1 | entry.py | `evaluate_business_rules()` | ~594–651 | 9 hardcoded field visibility rules |
| C2 | entry.py | `validate_business_rules()` | ~860–930 | Same 9 rules as validation errors |
| C3 | entry.py | `get_field_display_value()` | ~660–680 | Calls C1 for N/A display logic |
| C4 | entry.py | `evaluate_display_conditions()` | ~570–590 | Calls C1, overwrites YAML results |
| C5 | entry.py | `validate_cross_field_rules()` | ~959–1023 | 50mm tolerance, 10% price tolerance, required fields |
| C6 | entry.py | `create_field_definition()` | ~394 | Hardcoded relations field list |
| C7 | entry.py | `create_field_definition()` | ~371–390 | Hardcoded UI component alias mapping |

### 🟠 HIGH (Phase 3, 4, 5)

| ID | File | Location | Description |
|----|------|----------|-------------|
| H1 | product_definition/profile.py | `create_entity()` line 121 | `valid_types` list #1 |
| H2 | product_definition/profile.py | `_validate_entity_type()` line 419 | `valid_types` list #2 |
| H3 | product_definition/profile.py | `get_dependent_options()` line 393 | `valid_types` list #3 |
| H4 | product_definition/glazing.py | `_validate_entity_type()` line 596 | `valid_types = ["glass_type","spacer","gas"]` |
| H5 | product_definition/glazing.py | `get_scope_metadata()` lines 547–548 | entity_types + glazing_types hardcoded |
| H6 | schemas/product_definition/profile.py | `ProfileEntityCreate` line 38 | regex pattern for entity_type |
| H7 | schemas/product_definition/profile.py | `ProfileScopeResponse` line 156 | hardcoded entity_types default |
| H8 | schemas/product_definition/glazing.py | `GlazingComponentCreate` line 37 | `Literal["glass_type","spacer","gas"]` |
| H9 | schemas/product_definition/glazing.py | `GlazingUnitCreate` line 130 | `Literal["single","double","triple"]` |
| H10 | schemas/product_definition/glazing.py | `GlazingCalculationRequest` line 213 | `Literal["single","double","triple"]` |
| H11 | schemas/product_definition/glazing.py | `GlazingScopeResponse` line 274 | hardcoded glazing_types default |
| H12 | services/product_definition/types.py | `GlazingComponentData` line 92 | pattern for component_type |
| H13 | services/product_definition/types.py | `GlazingUnitData` line 110 | pattern for glazing_type |
| H14 | core/manufacturing_type_resolver.py | `VALID_PAGE_TYPES` line 35 | hardcoded set of page types |
| H15 | services/product_definition/factory.py | `_services` dict lines 18–21 | accessories scope missing |
| H16 | product_definition/glazing.py | `_calculate_glazing_properties()` | 8 hardcoded fallback values |

### 🟡 MEDIUM (Phase 6)

| ID | File | Location | Description |
|----|------|----------|-------------|
| M1 | schemas/entry.py | `ProfileEntryData` | All 29 fields explicitly typed — new YAML attrs need code change |
| M2 | schemas/entry.py | `ProfileEntryData` line 580 | `default=20.0` for upvc_profile_discount |
| M3 | schemas/entry.py | `ProfileEntryData` | `normalize_multi_select` hardcoded for `colours` only |
| M4 | api/v1/endpoints/entry.py | 5 endpoints | `page_type: str = "profile"` default |
| M5 | _create_entry_pages.py | lines 162, 180 | `page_type="accessories"`, `page_type="glazing"` |
| M6 | tests/ | 50+ locations | raw page type strings |
| M7 | schemas/product_definition/profile.py | `ProfileScopeResponse` | hardcoded scope/label strings |

### 🟢 LOW (Phase 7)

| ID | File | Description |
|----|------|-------------|
| L1 | tests/unit/services/test_entry_schema_generation.py | `VALID_UI_COMPONENTS` hardcoded list |
| L2 | tests/unit/test_entry_validation.py | `rear_height: 200.0` hardcoded tolerance test value |
| L3 | tests/unit/test_entry_csv_structure.py | All 29 field names hardcoded |
| L4 | tests/unit/test_entry_preview_sync.py | All 29 field names hardcoded |
| L5 | _manager_factory.py | `PRICE_IMPACT_TYPE_WEIGHTS = [0.7, 0.2, 0.1]` |
| L6 | _manager_utils.py | `random.uniform(0.01, 0.15)` price/weight formula factors |

---

## What Already Works Correctly (Do Not Break)

- `ConditionEvaluator` — complete, correct, 20+ operators
- `setup_hierarchy.py` — reads YAML, populates DB correctly
- `generate_form_schema()` — correctly builds `conditional_logic` from DB
- `validate_field_value()` — correctly validates min/max/pattern/length from DB validation_rules
- Options loading from child nodes (`_extract_options_from_children()`)
- Options loading from relations system (`_extract_options_from_relations()`)
- Calculated field metadata passthrough (`calculated_field` on FieldDefinition)
- `BaseProductDefinitionService._load_scope_metadata_from_yaml()` — existing YAML loader pattern
- All RBAC/auth logic
- All database models and migrations
- All existing API endpoint signatures

---

## Important Gotchas

### Case sensitivity in display conditions
The YAML `display_condition` values use `"frame"` (lowercase) but the `type` field options are
`"Frame"` (title case). The `ConditionEvaluator` `equals` operator does exact match — this is a
known issue already handled by `setup_hierarchy.py`'s `validate_configuration()` method which
warns about mismatches. The hardcoded `evaluate_business_rules()` uses `.lower()` which masks this.
After Phase 1, ensure the YAML display_conditions use the exact same case as the option values.

### `colours` vs `color` entity type
In `entry.py`, the field name `colours` maps to entity type `color` in the relations system.
This mapping is in `_extract_options_from_relations()` via `field_to_entity_type` dict.
This dict is also hardcoded and should move to `ui_components.yaml` in Phase 4.

### `glazing.yaml` entity type discrepancy
`config/product_definition/glazing.yaml` uses `glass_unit` as entity type but the service code
uses `glass_type`. This needs to be reconciled in Phase 3 — either update the YAML or the service.
The `config/pages/glazing.yaml` uses `glass_type` in its attribute definitions.

### Pydantic `Literal` types
Pydantic `Literal` types are evaluated at class definition time, not at validation time.
You cannot make them truly dynamic. The approach for Phase 3 is to change `Literal[...]` to `str`
and add a `@field_validator` that loads valid values from YAML at validation time.
This maintains runtime validation while allowing YAML-driven configuration.

### `ProfileEntryData` extra fields
Adding `model_config = ConfigDict(extra="allow")` in Phase 6 means unknown fields are accepted
but not typed. They'll be accessible via `model.model_extra["field_name"]`. The `save_profile_configuration()`
method already handles this correctly — it iterates `form_data.items()` and looks up each field
in `field_to_node` dict, so new fields will be saved if they have a corresponding AttributeNode.

### `base.py` already loads YAML
`BaseProductDefinitionService._load_scope_metadata_from_yaml()` already reads
`config/product_definition/{scope}.yaml`. The new `RuntimeConfigLoader` should be consistent
with this existing pattern. Consider whether `RuntimeConfigLoader` should replace or wrap this
existing method.

---

## Test Infrastructure

Tests use pytest with async support. Key test files:
- `tests/conftest.py` — shared fixtures including DB session
- `tests/unit/services/test_entry_unit.py` — unit tests for EntryService
- `tests/unit/services/test_entry_schema_generation.py` — schema generation tests
- `tests/unit/test_entry_validation.py` — validation tests (has hardcoded tolerance values)
- `tests/unit/test_entry_csv_structure.py` — CSV structure tests (has all 29 field names)
- `tests/integration/test_entry_api.py` — API integration tests

Run tests with:
```bash
cd backend
python -m pytest tests/unit/ -v
python -m pytest tests/integration/ -v
```

---

## Environment

- Python 3.11
- FastAPI + SQLAlchemy async
- PostgreSQL with LTREE extension
- Pydantic v2
- PyYAML already installed (used by setup_hierarchy.py)
- Windows development environment (bash shell)
- `.venv` in project root
