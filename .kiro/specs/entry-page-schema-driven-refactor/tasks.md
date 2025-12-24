# Implementation Plan

## Overview

Convert the Entry Page Schema-Driven Refactor design into a series of implementation tasks that eliminate hardcoded mappings, fix field ordering inconsistencies, implement proper business rules, and create reusable components. Each task builds incrementally toward a fully unified schema-driven architecture.

**Critical Problems Being Fixed:**
- Hardcoded 29-column preview headers array in `profile-entry.js`
- Hardcoded `HEADER_MAPPING` dictionary in `entry.py`
- Field ordering inconsistency (Material vs Company)
- Broken business rules (`isFieldValidForCurrentContext()` always returns `true`)
- Generic error messages despite detailed backend errors available
- Template code duplication preventing easy creation of new entry types

---

## Task List

- [x] 1. Backend Schema Enhancement and Dynamic Header Generation






  - Remove hardcoded `HEADER_MAPPING` dictionary from `app/services/entry.py`
  - Implement `generate_preview_headers()` method in EntryService to create headers from attribute nodes
  - Implement `generate_header_mapping()` method to create field mappings dynamically
  - Add new API endpoint `/api/v1/admin/entry/profile/headers/{manufacturing_type_id}` 
  - Ensure all generated headers respect database `sort_order` consistently
  - Fix field ordering so Material (sort_order=4) appears before Company (sort_order=3) everywhere
  - Add caching for generated headers and mappings to improve performance
  - Update existing preview endpoints to use dynamic headers instead of hardcoded mappings
  - _Requirements: 1.1, 1.2, 1.3, 7.1, 7.2, 7.3, 7.4, 7.5_

  - [ ]* 1.1 Write property test for dynamic header generation
    - **Property 1: Dynamic Schema Generation**
    - **Validates: Requirements 1.1, 1.2, 1.3, 1.5**

  - [ ]* 1.2 Write property test for field ordering consistency
    - **Property 2: Field Ordering Consistency**
    - **Validates: Requirements 1.4, 7.1, 7.2, 7.3, 7.4, 7.5**

  - [ ]* 1.3 Write unit tests for header generation and mapping
    - Test header generation with various attribute node configurations
    - Test field ordering with different sort_order values
    - Test mapping generation with different field types
    - _Requirements: 1.1, 1.2, 7.1_

- [x] 2. Frontend Dynamic Headers Implementation










  - Replace hardcoded `previewHeaders` array in `app/static/js/profile-entry.js`
  - Implement `loadDynamicHeaders()` method to fetch headers from new backend endpoint
  - Update `getPreviewValue()` method to use dynamic header mapping
  - Ensure preview table adapts to any number of columns (not fixed at 29)
  - Fix field ordering inconsistency by using backend-provided header order
  - Add loading states and error handling for header loading
  - Implement dynamic column count support in table rendering
  - Update all hardcoded header references to use dynamic headers
  - _Requirements: 1.1, 1.2, 1.3, 1.5, 7.1, 7.2, 7.3, 7.4, 7.5_

  - [ ]* 2.1 Write property test for dynamic column count support
    - **Property 1: Dynamic Schema Generation**
    - **Validates: Requirements 1.1, 1.2, 1.3, 1.5**

  - [ ]* 2.2 Write unit tests for frontend header loading
    - Test header loading from backend endpoint
    - Test table rendering with different column counts
    - Test error handling when header loading fails
    - _Requirements: 1.1, 1.2, 1.3_


- [x] 3. Business Rules Engine Implementation




- Continue, from where you stopped run git status to know where you have stopped





  - Fix broken `isFieldValidForCurrentContext()` method in `profile-entry.js`
  - Implement proper evaluation of `display_condition` JSONB rules from attribute nodes
  - Add real-time field enabling/disabling based on Type selection and other conditions
  - Implement business rules for specific cases from CSV:
    - "Renovation only for frame" → Only when Type = "Frame"
    - "builtin Flyscreen track only for sliding frame" → Only for sliding frames
    - "Sash overlap only for sashs" → Only when Type = "sash"
    - "Flying mullion clearances" → Only when Type = "Flying mullion"
    - "Glazing undercut height only for glazing bead" → Only when Type = "glazing bead"
  - Update `updateFieldVisibility()` method to use proper business rule evaluation
  - Add backend business rule validation to prevent invalid field combinations
  - Implement "N/A" display in preview for fields that don't apply to current type
  - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 3.1, 3.2, 3.3, 3.4, 3.5_

  - [ ]* 3.1 Write property test for business rules field availability
    - **Property 3: Business Rules Field Availability**
    - **Validates: Requirements 2.1, 2.2, 2.3, 2.4, 2.5**

  - [ ]* 3.2 Write unit tests for business rule evaluation
    - Test field visibility with different Type selections
    - Test conditional field logic with complex conditions
    - Test "N/A" display for invalid field combinations
    - _Requirements: 2.1, 2.2, 2.3, 3.1, 3.2, 3.3_


- [x] 12. Enhanced Error Handling and User Feedback









  - Fix generic "Validation Error" messages in frontend error handling
  - Parse detailed field errors from backend responses in `recordConfiguration()` method
  - Display specific error messages for each invalid field instead of generic messages
  - Highlight invalid fields in both input and preview tabs
  - Implement field-specific error highlighting in preview table during inline editing
  - Add error message parsing for different error response formats (array vs object)
  - Improve `scrollToFirstError()` method to work with field-specific errors
  - Add error clearing when fields are corrected
  - Implement better error recovery and user guidance
  - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 6.1, 6.2, 6.3, 6.4, 6.5_

  - [ ]* 4.1 Write property test for field-specific error validation
    - **Property 4: Field-Specific Error Validation**
    - **Validates: Requirements 3.1, 3.2, 3.3, 3.4, 3.5**

  - [ ]* 4.2 Write property test for error recovery and user experience
    - **Property 10: Error recovery and user experience**
    - **Validates: Requirements 6.5**

  - [ ]* 4.3 Write unit tests for error handling
    - Test parsing of different error response formats
    - Test field highlighting for validation errors
    - Test error clearing when fields are corrected
    - _Requirements: 3.1, 3.2, 3.3, 6.1, 6.2_

- [x] 5. Search and Filter Functionality Implementation





  - Add search input to preview table template in `profile.html.jinja`
  - Implement real-time search across all columns in preview table
  - Add column-specific filtering capabilities
  - Implement search functionality that adapts to dynamic schema changes
  - Add "no results" messaging when search returns empty results
  - Ensure search works with any number of columns (not just 29)
  - Add search state persistence and URL parameter support
  - Implement search highlighting and result count display
  - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5_

  - [ ]* 5.1 Write property test for real-time search and filter
    - **Property 5: Real-Time Search and Filter**
    - **Validates: Requirements 4.1, 4.2, 4.3, 4.5**

  - [ ]* 5.2 Write unit tests for search functionality
    - Test search across different column types
    - Test filtering with various criteria
    - Test search adaptation to schema changes
    - _Requirements: 4.1, 4.2, 4.3_

- [-] 6. Enhanced Inline Edit Validation






  - Implement field-type aware inline editing to replace generic text inputs
  - Utilise the validation rules used by the input view tab, in order to have one source of truth in validation
  - Add field-specific error messages during inline editing
  - Prevent saving of invalid edits and show specific error messages
  - Update `startEditing()`, `saveInlineEdit()`, and related methods
  - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5_

  - [ ]* 6.1 Write property test for type-aware inline editing
    - **Property 6: Type-Aware Inline Editing**
    - **Validates: Requirements 5.1, 5.2, 5.3, 5.4, 5.5**

  - [ ]* 6.2 Write unit tests for inline editing
    - Test different input control types
    - Test validation during inline editing
    - Test error handling for invalid edits
    - _Requirements: 5.1, 5.2, 5.3, 5.5_

- [ ] 7. Template and JavaScript Reusability Refactor
  - Create reusable base template `app/templates/admin/entry/entry.html.jinja`
  - Refactor existing `profile.html.jinja` to extend base template (reduce from 400+ lines)
  - Create parameterized Alpine.js app that works with any entry type
  - Replace hardcoded `profileEntryApp` with generic `entryApp(options)`
  - Implement dynamic API endpoints based on entry type parameter
  - Create scaffold pages for accessories and glazing using base template
  - Add navigation tab configuration through template parameters
  - Ensure new entry types require minimal code changes
  - Test template reusability with accessories and glazing pages
  - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5_

  - [ ]* 7.1 Write property test for template and component reusability
    - **Property 7: Template and Component Reusability**
    - **Validates: Requirements 6.1, 6.2, 6.3, 6.4, 6.5**

  - [ ]* 7.2 Write unit tests for template reusability
    - Test base template with different entry types
    - Test parameterized JavaScript app functionality
    - Test navigation configuration
    - _Requirements: 6.1, 6.2, 6.3, 6.4_

- [ ] 8. Performance Optimization and Caching
  - Implement caching for generated schemas, headers, and mappings
  - Optimize database queries to minimize calls during schema generation
  - Add performance monitoring for schema generation (target < 100ms)
  - Add performance monitoring for UI updates (target < 50ms)
  - Implement efficient preview table rendering regardless of column count
  - Add loading states and progressive enhancement for better perceived performance
  - Optimize conditional logic evaluation for large schemas
  - Add query result caching for frequently accessed data
  - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5_

  - [ ]* 8.1 Write property test for system performance requirements
    - **Property 8: System Performance Requirements**
    - **Validates: Requirements 8.1, 8.2, 8.3, 8.4, 8.5**

  - [ ]* 8.2 Write unit tests for performance optimization
    - Test caching behavior for schema generation
    - Test query optimization
    - Test UI responsiveness
    - _Requirements: 8.1, 8.2, 8.3, 8.4_

- [ ] 9. Backward Compatibility and Migration
  - Ensure all existing configurations remain accessible after refactoring
  - Maintain API backward compatibility during transition period
  - Create database migrations to preserve existing data integrity
  - Implement feature flags for gradual rollout of new functionality
  - Add rollback capability to revert to previous functionality if needed
  - Test that existing workflows continue to work with new implementation
  - Validate that no data is lost during the refactoring process
  - Document migration process and rollback procedures
  - _Requirements: 9.1, 9.2, 9.3, 9.4, 9.5_

  - [ ]* 9.1 Write property test for backward compatibility preservation
    - **Property 9: Backward Compatibility Preservation**
    - **Validates: Requirements 9.1, 9.2, 9.3, 9.4, 9.5**

  - [ ]* 9.2 Write unit tests for migration and compatibility
    - Test existing configuration access
    - Test API backward compatibility
    - Test data integrity preservation
    - _Requirements: 9.1, 9.2, 9.3, 9.4_

- [ ] 10. Comprehensive Testing and Validation
  - Write comprehensive test coverage for dynamic schema generation
  - Add tests for business rule validation with all type-based field combinations
  - Create tests for template reusability across different entry types
  - Add tests for error handling and field-specific error display
  - Implement performance tests to verify response time requirements
  - Add integration tests for complete user workflows
  - Create end-to-end tests for the refactored system
  - Add regression tests to prevent future hardcoding issues
  - _Requirements: 10.1, 10.2, 10.3, 10.4, 10.5_

  - [ ]* 10.1 Write property test for comprehensive test coverage
    - **Property 10: Comprehensive Test Coverage**
    - **Validates: Requirements 10.1, 10.2, 10.3, 10.4, 10.5**

  - [ ]* 10.2 Write comprehensive integration tests
    - Test complete user workflows with dynamic schema
    - Test error scenarios and recovery
    - Test performance with large datasets
    - _Requirements: 10.1, 10.2, 10.3, 10.4, 10.5_

- [ ] 11. Final Integration and Validation
  - Ensure all hardcoded arrays and mappings are eliminated
  - Validate that field ordering is consistent across all components
  - Test business rules with all Type combinations from CSV data
  - Verify that new entry types can be created with minimal code
  - Confirm that system handles any number of fields gracefully
  - Test search and filter functionality across all columns
  - Validate that error messages are specific and actionable
  - Perform end-to-end testing of complete refactored system
  - _Requirements: All requirements_

  - [ ] 11.1 Final checkpoint - Ensure all tests pass, ask the user if questions arise

---

## Implementation Notes

### Development Approach
- **Incremental Refactoring**: Each task eliminates specific hardcoded elements
- **Backward Compatibility**: Maintain existing functionality during transition
- **Schema-Driven**: Everything generated from attribute hierarchy
- **Performance-Focused**: Caching and optimization throughout

### Key Dependencies
- Existing Windx authentication and RBAC system
- AttributeNode hierarchy with LTREE support and display_condition JSONB
- Configuration and ConfigurationSelection models
- Alpine.js for frontend interactivity
- Existing entry page infrastructure

### Success Criteria
- Zero hardcoded preview headers or field mappings
- Consistent field ordering across all components (Material before Company)
- Proper business rule enforcement (fields show/hide based on Type)
- Specific error messages instead of generic "Validation Error"
- Easy creation of new entry types with minimal code
- System handles any number of fields without breaking
- All property-based tests pass with 100+ iterations

### Risk Mitigation
- Implement with feature flags for gradual rollout
- Maintain backward compatibility during transition
- Comprehensive testing before deployment
- Rollback procedures documented and tested