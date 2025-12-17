# Implementation Plan

## Overview

Convert the RBAC-first template enhancement design into a series of incremental implementation tasks. This approach focuses on automatic RBAC context injection using Can and Has helper classes, selective macro creation, and gradual migration without breaking existing functionality.

## Tasks

- [x] 1. RBAC Foundation and Middleware Infrastructure
  - Implement Can helper class with permission checking methods
  - Implement Has helper class with role checking methods  
  - Create RBACHelper main class that provides Can and Has instances
  - Add comprehensive error handling for permission evaluation failures
  - Implement RBACTemplateMiddleware class for automatic context injection
  - Create render_with_rbac method that enhances template context
  - Integrate with existing Jinja2Templates system
  - Add proper user extraction from request context
  - _Requirements: 1.1, 6.1, 6.4_

- [x] 1.1 Implement Can helper class
  - Create Can class with __call__ method for basic permission checking
  - Add convenience methods: create(), read(), update(), delete()
  - Implement access() method for resource ownership checking
  - Add proper error handling and safe fallbacks
  - _Requirements: 6.4_

- [x] 1.2 Implement Has helper class  
  - Create Has class with role() method for basic role checking
  - Add convenience methods: any_role(), admin_access(), customer_access()
  - Implement SUPERADMIN bypass logic consistently
  - Add role composition support for multiple role checks
  - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5_

- [x] 1.3 Implement RBACTemplateMiddleware class
  - Create middleware class that wraps existing Jinja2Templates
  - Implement automatic user extraction from request
  - Add RBAC helper instantiation and context injection
  - Ensure backward compatibility with existing template rendering
  - _Requirements: 6.1_

- [x] 1.4 Create enhanced template context system
  - Inject current_user, can, and has objects into all template contexts
  - Maintain existing context data while adding RBAC helpers
  - Add proper error handling for missing user context
  - Test context inheritance in template extends and includes
  - _Requirements: 6.1, 6.3_

- [ ]* 1.5 Write property tests for RBAC helpers
  - **Property 5: Can Helper Function Correctness**
  - **Validates: Requirements 6.4**

- [ ]* 1.6 Write property tests for Has helper
  - **Property 6: Has Helper Role Check Consistency** 
  - **Validates: Requirements 5.1, 5.2, 5.3, 5.4, 5.5**

- [ ]* 1.7 Write property tests for template middleware
  - **Property 1: RBAC Context Automatic Injection**
  - **Validates: Requirements 1.1, 6.1**

- [x] 2. RBAC Macros and Component Library
  - Implement rbac_button macro with permission and role checking
  - Create rbac_nav_item macro for navigation with automatic filtering
  - Build protected_content macro with fallback message support
  - Add rbac_page_header macro for page headers with conditional actions
  - Implement rbac_sidebar macro using existing sidebar structure
  - Create rbac_navbar macro with user context display
  - Create rbac_table_actions macro for table row actions with RBAC filtering
  - Create components directory structure and organize macro files
  - _Requirements: 3.1, 3.2, 3.3, 3.4, 4.1, 2.1_

- [x] 2.1 Implement rbac_button macro
  - Create macro that renders buttons only if user has required permissions
  - Support both permission strings and role requirements
  - Add consistent CSS class application and icon support
  - Include proper href and onclick handling
  - _Requirements: 3.1_

- [x] 2.2 Implement rbac_nav_item macro
  - Create navigation item macro with automatic RBAC filtering
  - Support active state detection and icon display
  - Add consistent navigation styling and behavior
  - Include proper link generation and accessibility
  - _Requirements: 2.1, 4.1_

- [x] 2.3 Implement protected_content macro
  - Create content wrapper macro with permission checking
  - Support both permission and role-based protection
  - Add fallback message display for unauthorized users
  - Include proper content block handling with caller()
  - _Requirements: 2.4, 6.2_

- [x] 2.4 Implement rbac_page_header macro
  - Create page header macro with conditional action buttons
  - Support title, subtitle, and multiple action configurations
  - Add RBAC filtering for action button display
  - Include consistent header styling and layout
  - _Requirements: 4.4_

- [x] 2.5 Implement rbac_sidebar macro
  - Create sidebar macro that reuses existing HTML structure
  - Replace hardcoded navigation items with rbac_nav_item calls
  - Add proper permission checking for each menu item
  - Maintain existing sidebar footer and user info display
  - _Requirements: 4.1_

- [x] 2.6 Implement rbac_navbar macro
  - Create navbar macro with user context and branding
  - Add consistent styling with existing navbar structure
  - Include user information display and logout functionality
  - Support responsive design and accessibility features
  - _Requirements: 4.1_

- [x] 2.7 Create rbac_table_actions macro
  - Implement table row actions with RBAC filtering
  - Support multiple action configurations with permissions
  - Add consistent action button styling and behavior
  - Include proper URL generation for both strings and functions
  - _Requirements: 2.3_

- [x] 2.8 Create components directory structure
  - Create app/templates/components/ directory
  - Add rbac_helpers.html.jinja with core RBAC macros
  - Add navigation.html.jinja with navigation components
  - Add tables.html.jinja with table-related macros
  - _Requirements: 1.3_

- [ ]* 2.9 Write property tests for RBAC macros
  - **Property 2: Navigation RBAC Filtering**
  - **Validates: Requirements 2.1**

- [ ]* 2.10 Write property tests for button filtering
  - **Property 3: Action Button RBAC Filtering**
  - **Validates: Requirements 2.2**

- [ ]* 2.11 Write property tests for navigation components
  - **Property 16: Navigation Organism RBAC Integration**
  - **Validates: Requirements 4.1**

- [x] 3. Template Integration and Migration
  - Update admin/base.html.jinja to use RBAC macros
  - Modify template to use has.admin_access() for sidebar display
  - Replace hardcoded navigation with rbac_sidebar and rbac_navbar
  - Ensure backward compatibility with existing template structure
  - Select manufacturing types route for initial migration
  - Update route to use rbac_templates.render_with_rbac()
  - Enhance template to use RBAC macros where appropriate
  - Test functionality and performance with new system
  - _Requirements: 6.1, 6.3, 7.1, 7.2_

- [x] 3.1 Update admin base template
  - Replace existing navbar include with rbac_navbar() call
  - Replace existing sidebar include with rbac_sidebar(active_page) call
  - Update main content area classes based on has.admin_access()
  - Maintain all existing CSS classes and JavaScript functionality
  - _Requirements: 6.1_

- [x] 3.2 Update template imports
  - Add proper macro imports to base templates
  - Ensure all RBAC macros are available where needed
  - Test template inheritance and macro availability
  - Add error handling for missing macro imports
  - _Requirements: 6.3_

- [x] 3.3 Update manufacturing types route
  - Modify route handler to use rbac_templates instead of templates
  - Add PageAction configuration for "New Type" button
  - Update template context to include page-specific actions
  - Test route functionality with RBAC context injection
  - _Requirements: 7.1_

- [x] 3.4 Enhance manufacturing types template
  - Update template to use rbac_page_header macro
  - Replace hardcoded action buttons with RBAC-aware macros
  - Update table actions to use rbac_table_actions macro
  - Maintain existing styling and JavaScript functionality
  - _Requirements: 7.2_

- [x] 3.5 Test migrated route thoroughly
  - Test with different user roles (SUPERADMIN, SALESMAN, DATA_ENTRY)
  - Verify RBAC filtering works correctly for all UI elements
  - Check performance impact of RBAC context injection
  - Ensure backward compatibility with existing functionality
  - _Requirements: 7.1, 7.2_

- [ ]* 3.6 Write property tests for template inheritance
  - **Property 9: Template Backward Compatibility**
  - **Validates: Requirements 6.1**

- [ ]* 3.7 Write integration tests for migrated route
  - **Property 13: Incremental Migration Support**
  - **Validates: Requirements 7.1**

- [ ] 4. Documentation, Testing, and Validation
  - Document Can and Has helper API with usage examples
  - Create RBAC macro documentation with parameter descriptions
  - Add migration guide for converting existing routes
  - Include troubleshooting guide for common RBAC issues
  - Run comprehensive test suite for all RBAC functionality
  - Perform cross-browser testing for enhanced templates
  - Validate performance impact of RBAC context injection
  - Test edge cases and error handling scenarios
  - _Requirements: 8.1, 8.2, 8.3, 8.4, 6.5_

- [ ] 4.1 Document RBAC helper APIs
  - Create comprehensive documentation for Can helper methods
  - Document Has helper methods and convenience functions
  - Add usage examples for common permission checking patterns
  - Include best practices for template RBAC integration
  - _Requirements: 8.1, 8.4_

- [ ] 4.2 Create RBAC macro documentation
  - Document all RBAC macros with parameter descriptions
  - Add usage examples for each macro with different configurations
  - Include styling guidelines and CSS class documentation
  - Create troubleshooting section for common macro issues
  - _Requirements: 8.2, 8.3_

- [ ] 4.3 Write migration guide
  - Create step-by-step guide for migrating existing routes
  - Document template enhancement patterns and best practices
  - Add examples of before/after code for common scenarios
  - Include testing strategies for verifying RBAC functionality
  - _Requirements: 8.4_

- [ ] 4.4 Run comprehensive RBAC test suite
  - Execute all property-based tests for RBAC helpers
  - Run integration tests for template rendering with RBAC
  - Test all RBAC macros with various parameter combinations
  - Validate error handling and graceful degradation
  - _Requirements: 6.5_

- [ ] 4.5 Performance testing and optimization
  - Measure template rendering performance with RBAC context
  - Profile RBAC helper function execution times
  - Optimize permission checking for frequently used helpers
  - Add caching where appropriate for performance improvement
  - _Requirements: 6.4_

- [ ] 4.6 Cross-browser and accessibility testing
  - Test enhanced templates across different browsers
  - Validate accessibility compliance for RBAC-aware components
  - Check responsive design with conditional RBAC elements
  - Test keyboard navigation and screen reader compatibility
  - _Requirements: 7.3_

- [ ]* 4.7 Write property tests for documentation
  - **Property 14: RBAC Macro Parameter Validation**
  - **Validates: Requirements 6.5**

- [ ]* 4.8 Write final integration tests
  - **Property 12: Template Context Enhancement**
  - **Validates: Requirements 6.1, 6.4**

## Implementation Notes

### Migration Strategy
- Start with one route (manufacturing types) to validate the approach
- Gradually migrate other admin routes once the pattern is proven
- Maintain backward compatibility throughout the migration process
- Test each migrated route thoroughly before moving to the next

### Testing Approach
- Property-based tests verify universal RBAC behavior across all scenarios
- Integration tests ensure template rendering works correctly with RBAC context
- Unit tests validate individual helper methods and macro functionality
- Performance tests ensure RBAC enhancements don't impact system performance

### Success Criteria
- All admin routes use automatic RBAC context injection
- Templates adapt automatically to user permissions without manual checks
- RBAC helper API is intuitive and well-documented
- Migration path is clear and non-breaking for existing functionality
- Performance impact is minimal and acceptable