# Requirements Document: Critical Fixes Consolidation

## Introduction

This specification consolidates all critical fixes needed across the Windx application to ensure type safety, proper imports, repository pattern consistency, enhanced CLI management, and comprehensive testing. The fixes address scattered issues that impact code quality, maintainability, and developer experience.

## Glossary

- **CLI**: Command-Line Interface - A text-based interface for interacting with the system
- **Type Hints**: Python annotations that specify expected types for variables, parameters, and return values
- **Repository Pattern**: Data access layer pattern that separates business logic from data access
- **LTREE Extension**: PostgreSQL extension for hierarchical data structures
- **Forward References**: String-based type annotations used when the type is not yet defined
- **TYPE_CHECKING**: Python constant that is True during static type checking but False at runtime
- **Playwright**: Browser automation framework for end-to-end testing
- **PBT**: Property-Based Testing - Testing approach that verifies properties hold across many inputs

## Requirements

### Requirement 1: Enhanced CLI Management System

**User Story:** As a developer, I want a unified CLI interface through manage.py with all administrative commands, so that I can manage the application without scattered scripts.

#### Acceptance Criteria

1. WHEN I run `manage.py` without arguments THEN the system SHALL display a help message listing all available commands
2. WHEN I run `manage.py create_tables` THEN the system SHALL create all database tables with LTREE extension enabled
3. WHEN I run `manage.py drop_tables` THEN the system SHALL prompt for confirmation before dropping all tables
4. WHEN I run `manage.py reset_db` THEN the system SHALL drop and recreate all tables in a single operation
5. WHEN I run `manage.py reset_password <username>` THEN the system SHALL prompt for a new password and update the user's hashed password
6. WHEN I run `manage.py check_env` THEN the system SHALL validate all required environment variables and database connectivity
7. WHEN I run `manage.py seed_data` THEN the system SHALL create sample data for development
8. WHEN all functionality is migrated THEN the `scripts/` directory SHALL be deleted
9. WHEN commands execute THEN they SHALL use `.venv\Scripts\python` on Windows and `.venv/bin/python` on Unix
10. WHEN destructive operations are requested THEN the system SHALL require confirmation unless --force is specified

### Requirement 2: SQLAlchemy Type Safety Fixes

**User Story:** As a developer, I want all SQLAlchemy model relationships to have correct type hints, so that my IDE can provide accurate autocomplete and catch type errors.

#### Acceptance Criteria

1. WHEN importing model classes THEN the system SHALL use `from __future__ import annotations` to enable forward references
2. WHEN defining relationships to other models THEN the system SHALL use TYPE_CHECKING imports to avoid circular imports
3. WHEN AttributeNode defines parent relationship THEN it SHALL use `Mapped["AttributeNode | None"]` type hint
4. WHEN AttributeNode defines children relationship THEN it SHALL use `Mapped[list["AttributeNode"]]` type hint
5. WHEN Configuration references ManufacturingType THEN it SHALL use TYPE_CHECKING import
6. WHEN ConfigurationSelection references Configuration and AttributeNode THEN it SHALL use TYPE_CHECKING imports
7. WHEN IDE analyzes the code THEN all relationship type hints SHALL resolve without errors
8. WHEN self-referential relationships are defined THEN remote_side and foreign_keys SHALL be correctly specified

### Requirement 3: Missing Import and Compatibility Fixes

**User Story:** As a developer, I want all imports to be available and correct, so that example scripts and modules can run without import errors.

#### Acceptance Criteria

1. WHEN `get_async_session` is imported from `app.database.connection` THEN it SHALL be available as an alias for `get_db`
2. WHEN example scripts import database functions THEN they SHALL use the correct import paths
3. WHEN modules import from each other THEN circular imports SHALL be avoided using TYPE_CHECKING
4. WHEN imports are added THEN they SHALL be organized according to PEP 8 (stdlib, third-party, local)
5. WHEN `examples/hierarchy_insertion.py` runs THEN it SHALL execute without import errors

### Requirement 4: Repository Pattern Enhancements

**User Story:** As a developer, I want enhanced base repository methods and consistent patterns, so that I can implement features efficiently.

#### Acceptance Criteria

1. WHEN querying by any field THEN BaseRepository SHALL provide `get_by_field(field_name, value)` method
2. WHEN checking record existence THEN BaseRepository SHALL provide `exists(id)` method
3. WHEN counting records THEN BaseRepository SHALL provide `count(filters)` method
4. WHEN ConfigurationTemplateRepository needs popular templates THEN it SHALL provide `get_popular(limit)` method
5. WHEN repositories accept schemas THEN they SHALL use proper Pydantic type hints
6. WHEN repositories return models THEN they SHALL use proper SQLAlchemy model type hints
7. WHEN field transformations are needed THEN models SHALL be created directly in the service layer
8. WHEN using repository.create() THEN schema fields SHALL map 1:1 to model fields without transformation

### Requirement 5: Template Service User Parameter Fix

**User Story:** As a developer, I want the template service to properly handle user parameters, so that template application works correctly.

#### Acceptance Criteria

1. WHEN applying a template THEN the service SHALL accept a user parameter
2. WHEN creating a configuration from template THEN the user.id SHALL be used for customer_id
3. WHEN tracking template usage THEN the user.id SHALL be passed correctly
4. WHEN the template service creates configurations THEN it SHALL pass the user to the configuration service
5. WHEN type hints are checked THEN the user parameter SHALL have proper type annotations

### Requirement 6: Currency Support

**User Story:** As a developer, I want currency handling in the application, so that prices can be displayed with proper currency symbols.

#### Acceptance Criteria

1. WHEN settings are loaded THEN they SHALL include currency and currency_symbol fields
2. WHEN currency is not specified THEN it SHALL default to "USD" with symbol "$"
3. WHEN Pydantic schemas return prices THEN they SHALL include currency information
4. WHEN API responses include prices THEN they SHALL include the currency field
5. WHEN templates render prices THEN they SHALL use the configured currency symbol

### Requirement 7: Node Class Audit and Decision

**User Story:** As a developer, I want clarity on the Node class usage, so that there's no confusion about which class to use.

#### Acceptance Criteria

1. WHEN searching the codebase THEN all usages of `class Node` SHALL be identified
2. WHEN Node class is found THEN a decision SHALL be made to either use it consistently or remove it
3. WHEN AttributeNode is the primary model THEN any redundant Node class SHALL be removed
4. WHEN Node class is kept THEN its purpose SHALL be clearly documented
5. WHEN the decision is made THEN all code SHALL be updated to reflect the chosen approach

### Requirement 8: Playwright End-to-End Tests

**User Story:** As a QA engineer, I want comprehensive E2E tests for admin functionality, so that I can ensure the UI works correctly.

#### Acceptance Criteria

1. WHEN testing attribute node creation THEN the test SHALL navigate to admin hierarchy page and create a node
2. WHEN testing attribute node editing THEN the test SHALL update a node and verify the changes
3. WHEN testing attribute node deletion THEN the test SHALL delete a node with confirmation
4. WHEN tests run THEN they SHALL use authenticated sessions
5. WHEN tests complete THEN they SHALL verify success messages are displayed
6. WHEN E2E tests are added THEN they SHALL be in `tests/e2e/` directory
7. WHEN Playwright is used THEN it SHALL be installed with `pip install playwright pytest-playwright`

### Requirement 9: Admin Template Styling Consistency

**User Story:** As a developer, I want consistent styling across all admin templates, so that the UI is cohesive and maintainable.

#### Acceptance Criteria

1. WHEN reviewing admin templates THEN they SHALL use Bootstrap 5 only (no mixed frameworks)
2. WHEN creating reusable components THEN they SHALL be in `app/templates/admin/components/`
3. WHEN components are created THEN they SHALL include navbar.html.jinja, sidebar.html.jinja, and alerts.html.jinja
4. WHEN custom styles are needed THEN they SHALL be in `app/static/css/admin.css`
5. WHEN templates are rendered THEN they SHALL extend a consistent `base.html.jinja`
6. WHEN alerts are displayed THEN they SHALL use the shared alerts component
7. WHEN navigation is rendered THEN it SHALL use the shared navbar component

### Requirement 10: Testing Infrastructure and Coverage

**User Story:** As a developer, I want comprehensive test coverage with proper fixtures, so that I can ensure code quality.

#### Acceptance Criteria

1. WHEN running unit tests THEN they SHALL execute with `.venv\Scripts\python -m pytest tests/unit/ -v`
2. WHEN running integration tests THEN they SHALL execute with `.venv\Scripts\python -m pytest tests/integration/ -v`
3. WHEN running E2E tests THEN they SHALL execute with `.venv\Scripts\python -m pytest tests/e2e/ -v`
4. WHEN all tests run THEN they SHALL execute with `.venv\Scripts\python -m pytest -v`
5. WHEN tests need database cleanup THEN fixtures SHALL handle proper teardown
6. WHEN tests need sample data THEN factories SHALL be available for all models
7. WHEN tests fail THEN error messages SHALL be clear and actionable

## Command Mapping Reference

| Old Script | New Command | Notes |
|------------|-------------|-------|
| `scripts/create_tables.py` | `manage.py create_tables` | Includes LTREE extension setup |
| `scripts/create_superuser.py` | `manage.py create_superuser` | Already exists, keep as is |
| `scripts/reset_admin_password.py` | `manage.py reset_password <username>` | Renamed for clarity |
| `scripts/check_env.py` | `manage.py check_env` | Enhanced validation |
| `scripts/reset_and_migrate.py` | `manage.py reset_db` | Combined drop and create |
| `scripts/migrate.py` | Removed | Use Alembic directly |
| `scripts/reset_test_db.py` | `manage.py reset_db --test` | Test database variant |

## Type Hint Patterns Reference

### Self-Referential Relationship Pattern
```python
from __future__ import annotations
from typing import TYPE_CHECKING
from sqlalchemy.orm import Mapped, relationship

class AttributeNode(Base):
    parent: Mapped["AttributeNode | None"] = relationship(
        "AttributeNode",
        remote_side=[id],
        back_populates="children",
        foreign_keys="AttributeNode.parent_node_id",
    )
    children: Mapped[list["AttributeNode"]] = relationship(
        "AttributeNode",
        back_populates="parent",
        foreign_keys="AttributeNode.parent_node_id",
        cascade="all, delete-orphan",
    )
```

### Cross-Model Relationship Pattern
```python
from __future__ import annotations
from typing import TYPE_CHECKING
from sqlalchemy.orm import Mapped, relationship

if TYPE_CHECKING:
    from app.models.manufacturing_type import ManufacturingType
    from app.models.customer import Customer

class Configuration(Base):
    manufacturing_type: Mapped["ManufacturingType"] = relationship(
        "ManufacturingType",
        back_populates="configurations",
    )
    customer: Mapped["Customer"] = relationship(
        "Customer",
        back_populates="configurations",
    )
```

## Files to Modify

### Phase 1: Critical Type Safety
- `app/models/attribute_node.py` - Fix self-referential relationships
- `app/models/configuration.py` - Add TYPE_CHECKING imports
- `app/models/configuration_selection.py` - Add TYPE_CHECKING imports
- `app/models/configuration_template.py` - Add TYPE_CHECKING imports
- `app/models/template_selection.py` - Add TYPE_CHECKING imports
- `app/models/quote.py` - Add TYPE_CHECKING imports
- `app/models/order.py` - Add TYPE_CHECKING imports
- `app/models/order_item.py` - Add TYPE_CHECKING imports

### Phase 2: Import Fixes
- `app/database/connection.py` - Add get_async_session alias
- `examples/hierarchy_insertion.py` - Fix imports

### Phase 3: Repository Enhancements
- `app/repositories/base.py` - Add get_by_field, exists, count methods
- `app/repositories/configuration_template.py` - Add get_popular method

### Phase 4: Service Fixes
- `app/services/template.py` - Fix user parameter in apply_template_to_configuration

### Phase 5: CLI Enhancement
- `manage.py` - Add all commands (create_tables, drop_tables, reset_db, reset_password, check_env, seed_data)
- Delete `scripts/` directory after migration

### Phase 6: Configuration
- `app/core/config.py` - Add currency and currency_symbol fields

### Phase 7: Testing
- `tests/e2e/test_attribute_nodes.py` - Create E2E tests
- `tests/conftest.py` - Enhance fixtures

### Phase 8: Templates
- `app/templates/admin/components/navbar.html.jinja` - Create shared navbar
- `app/templates/admin/components/sidebar.html.jinja` - Create shared sidebar
- `app/templates/admin/components/alerts.html.jinja` - Create shared alerts
- `app/static/css/admin.css` - Create unified styles
- Update all templates in `app/templates/admin/` to use components

## Success Metrics

- ✅ Zero unresolved type reference warnings in IDE
- ✅ All imports resolve without errors
- ✅ All repository methods exist and are properly typed
- ✅ manage.py has all required commands
- ✅ scripts/ directory is deleted
- ✅ E2E tests pass
- ✅ Templates have consistent styling
- ✅ All unit, integration, and E2E tests pass
- ✅ Currency support is implemented
- ✅ Node class decision is documented and implemented

## Testing Commands

```bash
# Always use .venv\Scripts\python on Windows

# Unit tests
.venv\Scripts\python -m pytest tests/unit/ -v

# Integration tests
.venv\Scripts\python -m pytest tests/integration/ -v

# E2E tests (install first: pip install playwright pytest-playwright)
.venv\Scripts\python -m playwright install
.venv\Scripts\python -m pytest tests/e2e/ -v

# Run all tests
.venv\Scripts\python -m pytest -v

# Run with coverage
.venv\Scripts\python -m pytest --cov=app --cov-report=html
```

## Implementation Priority

### Phase 1: Critical (Do First)
1. Fix SQLAlchemy type hints in all models
2. Add get_popular method to ConfigurationTemplateRepository
3. Fix missing user parameter in template service
4. Fix import issues (add get_async_session)
5. Fix self-referential relationships in AttributeNode

### Phase 2: Code Quality
1. Enhance manage.py with all commands
2. Delete scripts directory
3. Enhance base repository with common methods
4. Add currency support
5. Audit Node class usage

### Phase 3: Testing & UI
1. Set up Playwright E2E tests
2. Implement node CRUD tests
3. Unify admin template styling
4. Create reusable components

## Notes

- Use `.venv\Scripts\python` not `python` on Windows
- Follow repository pattern from fix.md steering rule
- Keep type safety throughout
- Test after each fix
- Commit atomically
- All changes must maintain backward compatibility
- Documentation must be updated alongside code changes
