# Requirements Document

## Introduction

This specification addresses critical architectural issues in the Windx entry page system where user.id is incorrectly used as customer_id, violating business model integrity and database constraints. The system will be updated to properly implement User ↔ Customer relationships and establish a foundation for Role-Based Access Control (RBAC).

## Glossary

- **User**: System account for authentication and authorization
- **Customer**: Business entity that owns configurations, quotes, and orders  
- **Configuration**: Product design owned by a customer
- **Entry_Service**: Service handling profile data entry operations
- **RBAC**: Role-Based Access Control system using Casbin policy engine
- **Auto_Creation**: Automatic customer record creation for users
- **Foreign_Key_Constraint**: Database constraint ensuring referential integrity
- **Casbin**: Professional policy engine for authorization decisions
- **Decorator_Pattern**: `@require()` syntax for method-level authorization
- **Resource_Ownership**: Validation that user owns or has access to specific resources
- **Privilege**: Reusable authorization object bundling roles, permissions, and ownership
- **Role_Composition**: Bitwise combination of roles for cleaner syntax
- **Template_Context_Functions**: RBAC functions available in HTML templates for conditional rendering
- **RBAC_Template_Integration**: Casbin integration with template engine for UI permission checks

## Requirements

### Requirement 1

**User Story:** As a system architect, I want proper User-Customer entity separation, so that the business model maintains data integrity and supports complex business scenarios.

#### Acceptance Criteria

1. WHEN a user creates a configuration through the entry page, THE Entry_Service SHALL create or retrieve an associated customer record
2. WHEN storing configuration data, THE Entry_Service SHALL use customer.id as customer_id instead of user.id
3. WHEN a customer record is auto-created, THE Entry_Service SHALL populate contact_person, email, and customer_type fields from user data
4. WHEN looking up existing customers, THE Entry_Service SHALL match by email address to prevent duplicates
5. WHEN a configuration is saved, THE Entry_Service SHALL ensure foreign key constraints are satisfied

### Requirement 2

**User Story:** As a developer, I want consistent customer relationship handling across all services, so that the system maintains data integrity throughout the application.

#### Acceptance Criteria

1. WHEN any service creates configurations, THE service SHALL use proper customer.id references
2. WHEN authorization checks are performed, THE service SHALL validate customer ownership through User-Customer mapping
3. WHEN users access configurations, THE service SHALL verify they have access to the associated customer
4. WHEN customer records are created, THE service SHALL maintain referential integrity with existing users
5. WHEN multiple services interact, THE customer relationship SHALL remain consistent across service boundaries

### Requirement 3

**User Story:** As a system administrator, I want a professional Casbin-based RBAC system with advanced decorator patterns, so that access control can be implemented systematically with maximum flexibility and maintainability.

#### Acceptance Criteria

1. WHEN the system implements RBAC, THE system SHALL use Casbin as the policy engine for authorization decisions
2. WHEN authorization decorators are used, THE system SHALL support multiple patterns: `@require(Role.ADMIN)`, `@require(Permission("resource", "action"))`, `@require(ResourceOwnership("resource"))`, and `@require(Privilege)`
3. WHEN user roles are defined, THE User_Model SHALL support superadmin, salesman, data_entry, partner, and customer roles with initial full privileges for salesman, data_entry, and partner roles
4. WHEN multiple authorization requirements exist, THE system SHALL support multiple `@require` decorators with OR logic between decorators and AND logic within decorators
5. WHEN role composition is needed, THE system SHALL support bitwise operators for role combinations (e.g., `Role.SALESMAN | Role.PARTNER`)

### Requirement 4

**User Story:** As a quality assurance engineer, I want comprehensive test coverage for customer relationships, so that the system reliability is maintained during the architectural changes.

#### Acceptance Criteria

1. WHEN integration tests run, THE tests SHALL verify proper customer.id usage in all entry page operations
2. WHEN customer auto-creation is tested, THE tests SHALL validate customer record creation and user association
3. WHEN authorization tests execute, THE tests SHALL verify User-Customer relationship enforcement
4. WHEN role-based tests run, THE tests SHALL validate role assignment and basic role functionality
5. WHEN database constraint tests execute, THE tests SHALL confirm foreign key integrity is maintained

### Requirement 5

**User Story:** As a data migration specialist, I want backward compatibility during the transition, so that existing system functionality remains unaffected.

#### Acceptance Criteria

1. WHEN existing configurations are accessed, THE system SHALL continue to function with current data
2. WHEN new configurations are created, THE system SHALL use the new customer relationship model
3. WHEN users without associated customers access the system, THE system SHALL auto-create customer records as needed
4. WHEN superusers access any configuration, THE system SHALL maintain existing superuser privileges
5. WHERE legacy data exists, THE system SHALL handle mixed customer relationship scenarios gracefully

### Requirement 6

**User Story:** As a system administrator, I want initial role configuration with full privileges and gradual restriction capability, so that the system can be deployed safely and permissions can be refined over time.

#### Acceptance Criteria

1. WHEN the system is initially deployed, THE Casbin policies SHALL grant full privileges (`*, *, allow`) to superadmin, salesman, data_entry, and partner roles
2. WHEN customer role is assigned, THE system SHALL provide limited privileges for configuration creation and quote viewing only
3. WHEN role restrictions are needed later, THE system SHALL support dynamic policy updates to restrict specific roles to specific resources and actions
4. WHEN superadmin role is assigned, THE system SHALL maintain unrestricted access to all resources and actions
5. WHEN role-based restrictions are applied, THE system SHALL preserve existing functionality while enforcing new access controls

### Requirement 7

**User Story:** As a security analyst, I want Casbin-based authorization controls with automatic query filtering, so that data access is restricted to authorized users only and data leakage is prevented.

#### Acceptance Criteria

1. WHEN users access configurations, THE Casbin decorators SHALL automatically verify customer ownership through User-Customer mapping
2. WHEN database queries are executed, THE RBACQueryFilter SHALL automatically filter results based on user's accessible customers
3. WHEN superusers access any data, THE Casbin policies SHALL allow unrestricted access through policy configuration
4. WHEN authorization failures occur, THE Casbin decorators SHALL raise HTTPException with status 403 and clear error messages
5. WHEN salesmen or partners are assigned customers, THE Casbin policies SHALL enable dynamic customer access management

### Requirement 8

**User Story:** As a system maintainer, I want clear error handling and logging for Casbin RBAC and customer relationship operations, so that issues can be diagnosed and resolved quickly.

#### Acceptance Criteria

1. WHEN Casbin policy evaluation fails, THE system SHALL log detailed policy information and provide meaningful error messages
2. WHEN customer auto-creation fails, THE system SHALL log detailed error information and provide meaningful user feedback
3. WHEN foreign key constraint violations occur, THE system SHALL handle them gracefully and suggest corrective actions
4. WHEN Casbin authorization fails, THE system SHALL log security events with user, resource, and action details for audit purposes
5. WHEN policy loading or saving fails, THE system SHALL provide diagnostic information for troubleshooting

### Requirement 9

**User Story:** As a developer, I want advanced RBAC decorator patterns with privilege abstraction, so that authorization logic can be reusable, composable, and maintainable across the application.

#### Acceptance Criteria

1. WHEN different roles need different authorization rules, THE system SHALL support multiple `@require` decorators on the same function with OR logic evaluation
2. WHEN roles share the same authorization rules, THE system SHALL support role lists and role composition within a single `@require` decorator
3. WHEN privilege abstraction is needed, THE system SHALL provide `Privilege` objects that bundle roles, permissions, and resource ownership into reusable components
4. WHEN initial deployment occurs, THE system SHALL configure salesman, data_entry, and partner roles with full privileges (`*, *, allow`) for gradual restriction later
5. WHEN resource ownership validation is required, THE system SHALL automatically extract resource IDs from function parameters and validate ownership through User-Customer relationships

### Requirement 10

**User Story:** As a frontend developer, I want RBAC integration in HTML templates with clean syntax, so that UI elements can be conditionally displayed based on user permissions without complex logic in templates.

#### Acceptance Criteria

1. WHEN rendering HTML templates, THE system SHALL provide template context functions for permission checking (`rbac.can()`, `rbac.has_role()`, `rbac.owns()`)
2. WHEN template permission checks are performed, THE system SHALL integrate with Casbin for consistent authorization logic
3. WHEN UI elements need role-based visibility, THE system SHALL support clean template syntax like `{% if rbac.has_role('SALESMAN') %}`
4. WHEN resource ownership checks are needed in templates, THE system SHALL provide `rbac.owns(resource_type, resource_id)` functionality
5. WHEN template RBAC functions are called, THE system SHALL cache permission results within the request scope for performance

### Requirement 11

**User Story:** As a performance analyst, I want efficient Casbin policy evaluation and customer lookup with caching, so that RBAC and User-Customer mapping do not impact system performance.

#### Acceptance Criteria

1. WHEN Casbin policies are evaluated frequently, THE system SHALL implement efficient policy caching and optimization
2. WHEN customer lookups occur frequently, THE system SHALL implement efficient database queries with proper indexing
3. WHEN the same user accesses multiple resources, THE system SHALL cache Casbin evaluations and customer lookups
4. WHEN RBACQueryFilter is applied, THE system SHALL perform efficiently without significant query overhead
5. WHERE caching is beneficial, THE system SHALL implement appropriate caching strategies for both Casbin policies and customer relationships