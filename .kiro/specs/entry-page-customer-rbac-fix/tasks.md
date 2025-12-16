# Implementation Plan

## Overview

This implementation plan addresses the critical architectural issue where `user.id` is incorrectly used as `customer_id` in configurations, violating business model integrity and database constraints. The plan systematically updates all affected services to use proper User ↔ Customer relationships and establishes a foundation for Role-Based Access Control (RBAC).

---

## Task List

- [ ] 1. Update User Model with Role Support
  - Add role field to User model with UserRole enum
  - Create database migration for role field
  - Set default role as 'customer' for existing users
  - Add role validation and constraints
  - Update User schema to include role field
  - _Requirements: 3.1, 3.2, 3.3, 3.4_

  - [ ] 1.1 Write property test for role assignment validity
    - **Property 6: Role assignment validity**
    - **Validates: Requirements 3.3, 3.4**

  - [ ] 1.2 Write unit tests for User model role functionality
    - Test role enum validation
    - Test default role assignment
    - Test role field constraints
    - _Requirements: 3.1, 3.2, 3.3_

- [ ] 2. Fix Entry Service Customer Relationships
  - Implement `_get_or_create_customer_for_user()` method in EntryService
  - Update `save_profile_configuration()` to use customer.id instead of user.id
  - Update `generate_preview_data()` authorization to use customer mapping
  - Add `_find_customer_by_email()` helper method
  - Add `_create_customer_from_user()` helper method
  - Add proper error handling for customer creation failures
  - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 2.1, 2.2_

  - [ ] 2.1 Write property test for customer relationship integrity
    - **Property 1: Customer relationship integrity**
    - **Validates: Requirements 1.2, 1.5**

  - [ ] 2.2 Write property test for user-customer mapping consistency
    - **Property 2: User-customer mapping consistency**
    - **Validates: Requirements 1.1, 1.3, 1.4**

  - [ ] 2.3 Write property test for customer auto-creation idempotency
    - **Property 4: Customer auto-creation idempotency**
    - **Validates: Requirements 1.4, 5.3**

  - [ ] 2.4 Write unit tests for Entry Service customer methods
    - Test customer auto-creation with various user data
    - Test customer lookup by email
    - Test error handling for duplicate emails and constraint violations
    - Test customer data mapping from user fields
    - _Requirements: 1.1, 1.3, 1.4, 7.1, 7.2_

- [ ] 3. Update Configuration Service Customer Usage
  - Update `create_configuration()` to use proper customer relationships
  - Fix authorization checks to use User-Customer mapping instead of direct user.id comparison
  - Update `get_configurations()` filtering to use customer relationships
  - Update `update_configuration()` and `delete_configuration()` authorization
  - Add customer lookup helper methods
  - _Requirements: 2.1, 2.2, 2.3, 2.4, 6.1, 6.2_

  - [ ] 3.1 Write property test for authorization customer ownership
    - **Property 3: Authorization customer ownership**
    - **Validates: Requirements 2.3, 6.1**

  - [ ] 3.2 Write unit tests for Configuration Service updates
    - Test configuration creation with customer relationships
    - Test authorization with User-Customer mapping
    - Test filtering by customer ownership
    - _Requirements: 2.1, 2.2, 2.3, 6.1_

- [ ] 4. Update Quote Service Customer References
  - Update quote creation to use customer.id from configurations
  - Fix quote authorization to use customer ownership
  - Update quote filtering to use customer relationships
  - Ensure quote-customer relationship consistency
  - _Requirements: 2.1, 2.2, 2.5, 6.1_

  - [ ] 4.1 Write unit tests for Quote Service customer updates
    - Test quote creation with proper customer references
    - Test quote authorization with customer ownership
    - Test quote filtering by customer relationships
    - _Requirements: 2.1, 2.2, 6.1_

- [ ] 5. Update Order Service Customer References
  - Update order creation to maintain customer relationships from quotes
  - Fix order authorization to use customer ownership through quotes
  - Update order filtering to use customer relationships
  - Ensure order-customer relationship consistency
  - _Requirements: 2.1, 2.2, 2.5, 6.1_

  - [ ] 5.1 Write unit tests for Order Service customer updates
    - Test order creation with customer relationship inheritance
    - Test order authorization through quote-customer relationships
    - Test order filtering by customer ownership
    - _Requirements: 2.1, 2.2, 6.1_

- [ ] 6. Update Template Service Customer Usage
  - Update `apply_template_to_configuration()` to use customer relationships
  - Fix template usage tracking to use proper customer associations
  - Update template authorization to use User-Customer mapping
  - _Requirements: 2.1, 2.2, 2.3_

  - [ ] 6.1 Write unit tests for Template Service customer updates
    - Test template application with customer relationships
    - Test template usage tracking with proper customer associations
    - _Requirements: 2.1, 2.2_

- [ ] 7. Update Integration Tests for Customer Relationships
  - Fix `test_entry_api.py` to use proper customer fixtures and relationships
  - Update `test_quotes.py` to use customer relationships consistently
  - Update `test_orders.py` to use customer relationships
  - Update `test_configurations.py` to use customer relationships
  - Add comprehensive customer auto-creation test scenarios
  - _Requirements: 4.1, 4.2, 4.3, 4.4_

  - [ ] 7.1 Write property test for foreign key constraint satisfaction
    - **Property 5: Foreign key constraint satisfaction**
    - **Validates: Requirements 1.5, 2.1**

  - [ ] 7.2 Write property test for backward compatibility preservation
    - **Property 7: Backward compatibility preservation**
    - **Validates: Requirements 5.1, 5.2, 5.5**

  - [ ] 7.3 Write property test for customer data consistency
    - **Property 8: Customer data consistency**
    - **Validates: Requirements 1.3, 4.2**

  - [ ] 7.4 Write comprehensive integration tests for customer workflows
    - Test complete entry page workflow with customer auto-creation
    - Test cross-service customer relationship consistency
    - Test mixed scenarios with existing and new customer relationships
    - Test performance impact of customer lookups
    - _Requirements: 4.1, 4.2, 4.3, 8.1, 8.2_

- [ ] 8. Add Enhanced Error Handling and Logging
  - Implement CustomerAuthorizationException for clear error messages
  - Add detailed logging for customer auto-creation operations
  - Add error handling for foreign key constraint violations
  - Add diagnostic information for User-Customer mapping failures
  - Add audit logging for customer relationship changes
  - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5_

  - [ ] 8.1 Write unit tests for error handling scenarios
    - Test customer creation failure handling
    - Test foreign key constraint violation handling
    - Test authorization failure scenarios
    - Test race condition handling in customer creation
    - _Requirements: 7.1, 7.2, 7.3, 7.4_

- [ ] 9. Performance Optimization and Database Indexes
  - Add database index for customers.email lookup
  - Add database index for users.role filtering
  - Add composite index for configurations by customer_id and status
  - Implement efficient customer lookup queries
  - Add request-scoped caching for customer lookups
  - _Requirements: 8.1, 8.2, 8.3, 8.4_

  - [ ] 9.1 Write performance tests for customer operations
    - Test customer lookup performance with large datasets
    - Test configuration filtering performance by customer
    - Test impact of customer auto-creation on response times
    - _Requirements: 8.1, 8.2, 8.4, 8.5_

- [ ] 10. Update API Documentation and Schemas
  - Update Entry API documentation to reflect customer relationship changes
  - Update Configuration API documentation for customer ownership
  - Update authentication documentation to include role information
  - Add customer auto-creation documentation
  - Update error response documentation for customer-related errors
  - _Requirements: 6.4, 7.4_

- [ ] 11. Final Integration Testing and Validation
  - Run complete test suite to ensure no regressions
  - Test backward compatibility with existing data
  - Validate foreign key constraint enforcement
  - Test role assignment and basic role functionality
  - Perform security audit of customer relationship changes
  - _Requirements: 4.5, 5.4, 5.5, 6.1, 6.2_

  - [ ] 11.1 Write end-to-end workflow tests
    - Test complete user registration → customer creation → configuration → quote → order workflow
    - Test multi-user scenarios with shared customers
    - Test superuser access across all customer data
    - _Requirements: 5.1, 5.2, 5.5, 6.1, 6.2_

- [ ] 12. Final checkpoint - Ensure all tests pass, ask the user if questions arise

---

## Implementation Notes

### Development Approach
- **Incremental Updates**: Update services one at a time to minimize risk
- **Test-Driven**: Write property-based tests to validate core behaviors
- **Backward Compatible**: Maintain existing functionality during transition
- **Performance-Focused**: Optimize customer lookups and database queries

### Key Dependencies
- Existing User and Customer models
- Configuration, Quote, and Order models with foreign key relationships
- Entry Service with profile data operations
- Authentication system with role support
- Database migration capabilities

### Success Criteria
- All configurations use proper customer.id references
- User-Customer mapping works consistently across services
- Foreign key constraints are satisfied
- Authorization uses customer ownership correctly
- Role foundation is established for future RBAC
- All property-based tests pass with 100+ iterations
- No performance degradation in customer operations
- Backward compatibility maintained for existing functionality

### Critical Path
1. User model role support (enables future RBAC)
2. Entry Service customer relationships (fixes core issue)
3. Service updates (maintains consistency)
4. Integration tests (validates correctness)
5. Performance optimization (ensures scalability)