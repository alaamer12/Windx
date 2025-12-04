# Requirements Document: Admin Routes Consistency and Testing

## Introduction

This specification addresses the need to ensure consistency across admin routes, properly implement the repository pattern, and add comprehensive testing for the newly added experimental features (customers and orders). The recent commit `dcc637f641d97f8c01c6e621b2ac841a2b31c57b` introduced admin pages for customers and orders, but there are inconsistencies in the implementation patterns and missing test coverage.

## Requirements

### Requirement 1: Repository Pattern Consistency

**User Story:** As a developer, I want all admin endpoints to follow the same repository pattern, so that the codebase is maintainable and predictable.

#### Acceptance Criteria

1. WHEN reviewing admin endpoint files THEN all endpoints SHALL use the repository pattern consistently
2. WHEN creating or updating entities THEN the service layer SHALL handle business logic and field transformations
3. WHEN repositories are used THEN they SHALL only handle data access operations
4. WHEN form data needs transformation THEN it SHALL be done in the endpoint handler before passing to repositories
5. IF field transformations are needed (like password hashing) THEN models SHALL be created directly in the service layer
6. WHEN using repository.create() THEN the schema fields SHALL map 1:1 to model fields without transformation

### Requirement 2: Admin Hierarchy Endpoint Refactoring

**User Story:** As a developer, I want the admin_hierarchy.py endpoint to follow the same patterns as other admin endpoints, so that it's easier to understand and maintain.

#### Acceptance Criteria

1. WHEN reviewing admin_hierarchy.py THEN it SHALL use the same dependency injection patterns as admin_customers.py and admin_orders.py
2. WHEN handling form submissions THEN validation SHALL be consistent with other admin endpoints
3. WHEN rendering templates THEN the context building SHALL use the shared get_admin_context function
4. WHEN errors occur THEN error handling SHALL follow the same pattern as other admin endpoints
5. WHEN database operations are performed THEN they SHALL use the repository pattern consistently

### Requirement 3: Shared Utilities and Context

**User Story:** As a developer, I want shared utilities to be centralized, so that there's no code duplication across admin endpoints.

#### Acceptance Criteria

1. WHEN building admin template context THEN all endpoints SHALL use the get_admin_context function from app.api.deps
2. WHEN checking feature flags THEN all endpoints SHALL use a consistent approach
3. WHEN handling redirects with messages THEN all endpoints SHALL use the same URL parameter pattern (success, error, warning, info)
4. WHEN formatting data for templates THEN shared formatting functions SHALL be available in a common module
5. WHEN validating form data THEN validation utilities SHALL be reusable across endpoints

### Requirement 4: Customer Management Testing

**User Story:** As a QA engineer, I want comprehensive tests for customer management, so that I can ensure the feature works correctly and regressions are caught early.

#### Acceptance Criteria

1. WHEN testing customer creation THEN tests SHALL verify successful creation with valid data
2. WHEN testing customer creation with invalid data THEN tests SHALL verify proper validation errors
3. WHEN testing customer listing THEN tests SHALL verify pagination, filtering, and search functionality
4. WHEN testing customer updates THEN tests SHALL verify successful updates and validation
5. WHEN testing customer deletion THEN tests SHALL verify successful deletion and error handling
6. WHEN testing customer detail view THEN tests SHALL verify all related data is loaded correctly
7. WHEN feature flag is disabled THEN tests SHALL verify proper redirect behavior
8. WHEN unauthorized users access customer endpoints THEN tests SHALL verify 403 responses

### Requirement 5: Order Management Testing

**User Story:** As a QA engineer, I want comprehensive tests for order management, so that I can ensure the feature works correctly and regressions are caught early.

#### Acceptance Criteria

1. WHEN testing order listing THEN tests SHALL verify pagination, filtering, and search functionality
2. WHEN testing order detail view THEN tests SHALL verify all related data (customer, items, quote) is loaded
3. WHEN testing order status updates THEN tests SHALL verify valid status transitions
4. WHEN testing order status updates with invalid status THEN tests SHALL verify proper error handling
5. WHEN feature flag is disabled THEN tests SHALL verify proper redirect behavior
6. WHEN unauthorized users access order endpoints THEN tests SHALL verify 403 responses
7. WHEN searching orders THEN tests SHALL verify search works across order number and customer fields

### Requirement 6: Integration Testing for Admin Workflows

**User Story:** As a QA engineer, I want integration tests that verify complete admin workflows, so that I can ensure the system works end-to-end.

#### Acceptance Criteria

1. WHEN testing customer-to-order workflow THEN tests SHALL verify creating a customer, configuration, quote, and order
2. WHEN testing hierarchy management workflow THEN tests SHALL verify creating manufacturing types and attribute nodes
3. WHEN testing admin authentication THEN tests SHALL verify login, session management, and logout
4. WHEN testing feature flag toggling THEN tests SHALL verify behavior changes based on flag state
5. WHEN testing error scenarios THEN tests SHALL verify proper error messages and recovery paths

### Requirement 7: Repository Pattern Documentation

**User Story:** As a developer, I want clear documentation on when to use repository.create() vs direct model creation, so that I can implement features correctly.

#### Acceptance Criteria

1. WHEN implementing new endpoints THEN documentation SHALL provide clear guidance on repository usage
2. WHEN field transformation is needed THEN documentation SHALL show the correct pattern
3. WHEN using Pydantic schemas THEN documentation SHALL explain the type safety benefits
4. WHEN creating models directly THEN documentation SHALL explain when and why this is appropriate
5. WHEN reviewing code THEN examples SHALL be available for common patterns

### Requirement 8: Error Handling Consistency

**User Story:** As a user, I want consistent error messages and handling across all admin pages, so that I can understand what went wrong and how to fix it.

#### Acceptance Criteria

1. WHEN validation errors occur THEN they SHALL be displayed in a consistent format
2. WHEN database errors occur THEN they SHALL be logged and user-friendly messages SHALL be shown
3. WHEN feature flags are disabled THEN redirect messages SHALL be clear and consistent
4. WHEN authorization fails THEN error messages SHALL be consistent across endpoints
5. WHEN form submission fails THEN the form SHALL be re-rendered with error messages and preserved data

### Requirement 9: Test Fixtures and Factories

**User Story:** As a test developer, I want reusable test fixtures and factories for customers and orders, so that I can write tests efficiently.

#### Acceptance Criteria

1. WHEN writing customer tests THEN a CustomerFactory SHALL be available
2. WHEN writing order tests THEN an OrderFactory SHALL be available
3. WHEN tests need related data THEN factories SHALL support creating related entities
4. WHEN tests need specific scenarios THEN factory traits SHALL be available (e.g., active_customer, pending_order)
5. WHEN tests need database cleanup THEN fixtures SHALL handle proper teardown

### Requirement 10: Code Quality and Type Safety

**User Story:** As a developer, I want type hints and validation throughout the admin code, so that errors are caught early and the code is self-documenting.

#### Acceptance Criteria

1. WHEN reviewing admin endpoints THEN all functions SHALL have proper type hints
2. WHEN using dependencies THEN they SHALL use Annotated types for clarity
3. WHEN handling form data THEN Pydantic models SHALL be used for validation
4. WHEN returning responses THEN response types SHALL be properly annotated
5. WHEN using repositories THEN generic types SHALL be properly specified
