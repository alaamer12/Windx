# Implementation Plan

## Overview

This implementation plan addresses the critical architectural issue where `user.id` is incorrectly used as `customer_id` in configurations, violating business model integrity and database constraints. The plan systematically updates all affected services to use proper User ↔ Customer relationships and implements a professional Casbin-based RBAC system with advanced decorator patterns for enterprise-grade authorization.

---

## Task List

- [x] 1. Core RBAC Infrastructure and User Model Setup
  - Install casbin and casbin-sqlalchemy-adapter dependencies
  - Create Casbin model configuration file (`config/rbac_model.conf`)
  - Create initial policy file with full privileges for salesman, data_entry, partner roles (`config/rbac_policy.csv`)
  - Setup Casbin database adapter for policy storage
  - Create RBACService with Casbin enforcer
  - Create Role enum with bitwise operations support (`Role.SALESMAN | Role.PARTNER`)
  - Create Permission class for resource-action definitions
  - Create ResourceOwnership class for ownership validation
  - Create Privilege class for reusable authorization bundles
  - Implement `@require()` decorator with multiple pattern support
  - Add context extraction logic for customer ownership
  - Add RBACQueryFilter for automatic query filtering
  - Add role field to User model with Role enum
  - Create database migration for role field
  - Set default role as 'customer' for existing users
  - Add role validation and constraints
  - Update User schema to include role field
  - Configure initial policies with full privileges for salesman, data_entry, partner
  - _Requirements: 3.1, 3.2, 3.3, 6.1, 6.2, 6.4, 9.1, 9.2, 9.3_

  - [ ] 1.1 Write property test for decorator authorization consistency
    - **Property: Multiple decorator OR logic evaluation**
    - **Validates: Requirements 9.1, 9.2**

  - [ ] 1.2 Write property test for role assignment validity
    - **Property 6: Role assignment validity**
    - **Validates: Requirements 3.3, 6.4**

  - [ ] 1.3 Write unit tests for Casbin policy evaluation
    - Test basic role-based permissions
    - Test customer-context permissions
    - Test policy loading and saving
    - _Requirements: 3.1, 3.2, 6.1_

  - [ ] 1.4 Write unit tests for advanced RBAC decorators
    - Test multiple `@require` decorators with OR logic
    - Test role composition with bitwise operators
    - Test Privilege object functionality
    - Test context extraction and customer ownership
    - Test ResourceOwnership automatic parameter detection
    - _Requirements: 9.1, 9.2, 9.3, 9.5_

  - [ ] 1.5 Write unit tests for User model role functionality
    - Test role enum validation with bitwise operations
    - Test default role assignment
    - Test role field constraints
    - Test Casbin policy integration
    - _Requirements: 3.3, 6.1, 6.2_

- [ ] 2. Service Layer Updates with Customer Relationships and Casbin RBAC
  - Implement `_get_or_create_customer_for_user()` method in EntryService
  - Update `save_profile_configuration()` to use customer.id instead of user.id
  - Add Casbin decorators to Entry Service methods (`@require(Permission(...))`, `@require(Privilege(...))`)
  - Update `generate_preview_data()` authorization to use Casbin decorators
  - Add `_find_customer_by_email()` helper method
  - Add `_create_customer_from_user()` helper method
  - Add proper error handling for customer creation failures
  - Define reusable Privilege objects for Entry Service operations
  - Add Casbin decorators to all Configuration Service methods
  - Update `create_configuration()` to use proper customer relationships
  - Replace manual authorization checks with Casbin decorators
  - Update `get_configurations()` to use RBACQueryFilter for automatic filtering
  - Add multiple `@require` decorators for different role access patterns
  - Define ConfigurationManagement and other Privilege objects
  - Integrate customer context extraction for ownership checks
  - Add Casbin decorators to all Quote Service methods
  - Update quote creation to use customer.id from configurations
  - Use RBACQueryFilter for automatic quote filtering by customer access
  - Define QuoteManagement Privilege objects
  - Ensure quote-customer relationship consistency
  - Add Casbin decorators to all Order Service methods
  - Update order creation to maintain customer relationships from quotes
  - Use RBACQueryFilter for automatic order filtering by customer access
  - Define OrderManagement Privilege objects
  - Ensure order-customer relationship consistency through quotes
  - Add Casbin decorators to Template Service methods
  - Update `apply_template_to_configuration()` to use customer relationships
  - Fix template usage tracking to use proper customer associations
  - Define TemplateManagement Privilege objects
  - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 2.1, 2.2, 2.3, 2.4, 2.5, 7.1, 7.2, 9.1, 9.3_

  - [ ] 2.1 Write property test for customer relationship integrity
    - **Property 1: Customer relationship integrity**
    - **Validates: Requirements 1.2, 1.5**

  - [ ] 2.2 Write property test for user-customer mapping consistency
    - **Property 2: User-customer mapping consistency**
    - **Validates: Requirements 1.1, 1.3, 1.4**

  - [ ] 2.3 Write property test for customer auto-creation idempotency
    - **Property 4: Customer auto-creation idempotency**
    - **Validates: Requirements 1.4, 5.3**

  - [ ] 2.4 Write property test for Casbin authorization customer ownership
    - **Property 3: Authorization customer ownership with Casbin**
    - **Validates: Requirements 2.3, 7.1, 9.1**

  - [ ] 2.5 Write unit tests for Entry Service with Casbin decorators
    - Test customer auto-creation with various user data
    - Test Casbin decorator authorization on Entry Service methods
    - Test Privilege object evaluation
    - Test customer lookup by email
    - Test error handling for duplicate emails and constraint violations
    - Test customer data mapping from user fields
    - _Requirements: 1.1, 1.3, 1.4, 8.1, 8.2, 9.3_

  - [ ] 2.6 Write unit tests for Configuration Service with Casbin
    - Test configuration creation with customer relationships
    - Test Casbin decorator authorization on all methods
    - Test RBACQueryFilter automatic filtering
    - Test multiple decorator patterns (OR logic)
    - Test customer context extraction and ownership validation
    - _Requirements: 2.1, 2.2, 2.3, 8.1, 9.1, 9.2_

  - [ ] 2.7 Write unit tests for Quote Service with Casbin
    - Test quote creation with proper customer references
    - Test Casbin decorator authorization on quote operations
    - Test RBACQueryFilter for quote filtering by customer relationships
    - Test Privilege object evaluation
    - _Requirements: 2.1, 2.2, 8.1, 9.1, 9.3_

  - [ ] 2.8 Write unit tests for Order Service with Casbin
    - Test order creation with customer relationship inheritance
    - Test Casbin decorator authorization through quote-customer relationships
    - Test RBACQueryFilter for order filtering by customer ownership
    - Test role composition and Privilege objects
    - _Requirements: 2.1, 2.2, 8.1, 9.1, 9.3_

  - [ ] 2.9 Write unit tests for Template Service with Casbin
    - Test template application with customer relationships
    - Test Casbin decorator authorization on template operations
    - Test template usage tracking with proper customer associations
    - Test Privilege object functionality
    - _Requirements: 2.1, 2.2, 9.1, 9.3_

- [ ] 3. Testing, Integration, and Template RBAC Implementation
  - Fix `test_entry_api.py` to use proper customer fixtures and Casbin authorization
  - Update `test_quotes.py` to test Casbin decorators and customer relationships
  - Update `test_orders.py` to test Casbin authorization and customer relationships
  - Update `test_configurations.py` to test Casbin decorators and customer relationships
  - Add comprehensive Casbin policy testing scenarios
  - Add customer auto-creation test scenarios with RBAC
  - Test multiple decorator patterns and Privilege objects
  - Create RBAC template context processor with Casbin integration
  - Implement template functions: `rbac.can()`, `rbac.has_role()`, `rbac.owns()`, `rbac.has_privilege()`
  - Add request-scoped caching for template permission checks
  - Update HTML templates to use RBAC functions for conditional rendering
  - Create template helper functions for complex permission patterns
  - Add template RBAC documentation and examples
  - _Requirements: 4.1, 4.2, 4.3, 4.4, 9.1, 9.2, 9.3, 10.1, 10.2, 10.3, 10.4, 10.5_

  - [ ] 3.1 Write property test for foreign key constraint satisfaction
    - **Property 5: Foreign key constraint satisfaction**
    - **Validates: Requirements 1.5, 2.1**

  - [ ] 3.2 Write property test for backward compatibility preservation
    - **Property 7: Backward compatibility preservation**
    - **Validates: Requirements 5.1, 5.2, 5.5**

  - [ ] 3.3 Write property test for customer data consistency
    - **Property 8: Customer data consistency**
    - **Validates: Requirements 1.3, 4.2**

  - [ ] 3.4 Write property test for Casbin policy consistency
    - **Property 9: Casbin policy consistency**
    - **Validates: Requirements 3.1, 8.1, 9.1**

  - [ ] 3.5 Write property test for advanced decorator patterns
    - **Property 10: Multiple decorator OR logic evaluation**
    - **Validates: Requirements 9.1, 9.2**

  - [ ] 3.6 Write property test for template RBAC function consistency
    - **Property 11: Template RBAC function consistency**
    - **Validates: Requirements 10.1, 10.2, 10.3**

  - [ ] 3.7 Write comprehensive integration tests for Casbin RBAC workflows
    - Test complete entry page workflow with customer auto-creation and RBAC
    - Test cross-service Casbin authorization consistency
    - Test role-based access patterns (superadmin, salesman, customer, etc.)
    - Test customer assignment workflows for salesmen and partners
    - Test multiple decorator patterns and Privilege objects
    - Test mixed scenarios with existing and new customer relationships
    - Test performance impact of Casbin policy evaluation
    - _Requirements: 4.1, 4.2, 4.3, 9.1, 9.2, 9.3, 10.1, 10.2_

  - [ ] 3.8 Write unit tests for template RBAC functions
    - Test template context processor functionality
    - Test RBAC function accuracy against Casbin policies
    - Test request-scoped caching behavior
    - Test template rendering with different user roles
    - _Requirements: 10.1, 10.2, 10.3, 10.5_

- [ ] 4. System Optimization, Policy Management, and Error Handling
  - Implement CasbinAuthorizationException for clear RBAC error messages
  - Add detailed logging for Casbin policy evaluation
  - Add detailed logging for customer auto-creation operations
  - Add error handling for foreign key constraint violations
  - Add diagnostic information for User-Customer mapping failures
  - Add audit logging for customer relationship changes and policy updates
  - Add error handling for Privilege object evaluation failures
  - Add database index for customers.email lookup
  - Add database index for users.role filtering
  - Add composite index for configurations by customer_id and status
  - Optimize Casbin policy storage and retrieval
  - Implement efficient customer lookup queries
  - Add request-scoped caching for customer lookups and Casbin evaluations
  - Add caching for Privilege object evaluations
  - Create PolicyManager class for dynamic policy updates
  - Implement customer assignment management for salesmen/partners
  - Add API endpoints for policy management (superadmin only)
  - Create initial policy seeding for default roles with full privileges
  - Add policy backup and restore functionality
  - Add Privilege object management interface
  - _Requirements: 6.1, 6.2, 6.3, 8.1, 8.2, 8.3, 8.4, 8.5, 9.3, 11.1, 11.2, 11.3, 11.4_

  - [ ] 4.1 Write unit tests for Casbin error handling scenarios
    - Test Casbin authorization failure handling
    - Test customer creation failure handling
    - Test foreign key constraint violation handling
    - Test Casbin policy loading failures
    - Test Privilege object evaluation errors
    - Test race condition handling in customer creation
    - _Requirements: 8.1, 8.2, 8.3, 8.4_

  - [ ] 4.2 Write performance tests for Casbin and customer operations
    - Test Casbin policy evaluation performance with large policy sets
    - Test customer lookup performance with large datasets
    - Test RBACQueryFilter performance impact
    - Test configuration filtering performance by customer
    - Test impact of customer auto-creation on response times
    - Test Privilege object evaluation performance
    - _Requirements: 11.1, 11.2, 11.4, 11.5_

  - [ ] 4.3 Write unit tests for policy management
    - Test dynamic customer assignment to salesmen
    - Test policy addition and removal
    - Test policy backup and restore
    - Test Privilege object creation and management
    - _Requirements: 6.1, 6.2, 6.3, 9.3_

- [ ] 5. Documentation and Final Validation
  - Update Entry API documentation to reflect customer relationship changes
  - Update Configuration API documentation for customer ownership
  - Update authentication documentation to include role information and Casbin policies
  - Add Casbin RBAC system documentation with decorator patterns
  - Add template RBAC integration documentation with examples
  - Add customer auto-creation documentation
  - Update error response documentation for Casbin authorization errors
  - Document policy management endpoints
  - Document Privilege objects and advanced decorator patterns
  - Document template context functions and usage patterns
  - Run complete test suite to ensure no regressions
  - Test backward compatibility with existing data
  - Validate foreign key constraint enforcement
  - Test Casbin policy evaluation and role functionality
  - Test template RBAC integration across all pages
  - Perform security audit of customer relationship changes and RBAC implementation
  - Validate Casbin policy storage and retrieval
  - Test all decorator patterns and Privilege objects
  - _Requirements: 4.5, 5.4, 5.5, 6.4, 8.1, 8.4, 9.1, 9.2, 10.1, 10.4_

  - [ ] 5.1 Write end-to-end Casbin RBAC workflow tests
    - Test complete user registration → role assignment → customer creation → configuration → quote → order workflow
    - Test multi-user scenarios with shared customers and different roles
    - Test superuser access across all customer data
    - Test salesman customer assignment and access restrictions
    - Test partner limited access scenarios
    - Test data_entry role restrictions
    - Test multiple decorator patterns in real workflows
    - Test Privilege object usage across services
    - Test template RBAC functions in rendered pages
    - Test UI element visibility based on user roles and permissions
    - _Requirements: 5.1, 5.2, 5.5, 8.1, 8.2, 9.1, 9.2, 9.3, 10.1, 10.2_

- [ ] 6. Final checkpoint - Ensure all tests pass, ask the user if questions arise

---

## Implementation Notes

### Development Approach
- **Casbin-First**: Implement Casbin RBAC infrastructure before service updates
- **Decorator-Driven**: Use `@require()` decorators for clean authorization
- **Incremental Updates**: Update services one at a time to minimize risk
- **Test-Driven**: Write property-based tests to validate core behaviors
- **Backward Compatible**: Maintain existing functionality during transition
- **Performance-Focused**: Optimize customer lookups, database queries, and Casbin evaluations

### Key Dependencies
- **Casbin**: Policy engine for RBAC (`pip install casbin casbin-sqlalchemy-adapter`)
- **PostgreSQL**: Database for policy storage and customer relationships
- **Template Engine**: Jinja2 or similar for template RBAC integration
- Existing User and Customer models
- Configuration, Quote, and Order models with foreign key relationships
- Entry Service with profile data operations
- Authentication system with role support
- Database migration capabilities
- HTML templates requiring RBAC-based conditional rendering

### Success Criteria
- **Casbin RBAC**: Professional authorization system with decorator syntax
- **Advanced Decorator Patterns**: Multiple `@require` decorators, role composition, Privilege objects
- **Template RBAC Integration**: Clean template syntax with `rbac.can()`, `rbac.has_role()`, `rbac.owns()` functions
- **Policy Management**: Dynamic role and permission management
- All configurations use proper customer.id references
- User-Customer mapping works consistently across services
- Foreign key constraints are satisfied
- Authorization uses Casbin decorators and customer ownership correctly
- Role-based access control fully functional for all user roles with initial full privileges
- Template-based UI elements conditionally rendered based on user permissions
- All property-based tests pass with 100+ iterations
- No performance degradation in customer operations or Casbin evaluations
- Backward compatibility maintained for existing functionality
- **Clean Code**: `@require(Role.ADMIN)`, `@require(Permission("resource", "action"))`, `@require(Privilege)` syntax
- **Clean Templates**: `{% if rbac.can('resource', 'action') %}` syntax

### Critical Path
1. **Casbin Infrastructure** (enables professional RBAC)
2. **Advanced RBAC Decorators** (provides clean authorization API with multiple patterns)
3. **User model role support** (enables role-based policies)
4. **Entry Service customer relationships** (fixes core issue)
5. **Service updates with decorators** (maintains consistency)
6. **Integration tests** (validates correctness)
7. **Performance optimization** (ensures scalability)

### Casbin Configuration Files
- `config/rbac_model.conf` - Casbin authorization model
- `config/rbac_policy.csv` - Initial policies with full privileges for salesman, data_entry, partner
- Database table `casbin_rule` - Persistent policy storage

### Initial Role Configuration
```
- superadmin: *, *, allow (unrestricted)
- salesman: *, *, allow (initially full privileges)  
- data_entry: *, *, allow (initially full privileges)
- partner: *, *, allow (initially full privileges)
- customer: limited privileges (configuration:read|create, quote:read)
```