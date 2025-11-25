# Implementation Plan: Windx Configurator Integration

ALAWAY RUN FROM `.venv` -> `.venv\scripts\python` not `python`

This implementation plan converts the Windx design into actionable coding tasks. The plan is organized into phases, starting with documentation and analysis, then moving to database integration, repositories, services, and API endpoints.

## Phase 1: Database Foundation

check file #database/test_ltree_type.py

- [x] 1. Enable PostgreSQL LTREE extension and add type support






  - Add SQLAlchemy LTREE type support in `app/database/types.py`
  - Create custom LTREE column type with operators (ancestor_of, descendant_of, lquery)
  - Add SQL script to enable LTREE extension in database
  - _Requirements: 2.2, 2.6, 8.2_

- [x] 1.1 Create ManufacturingType model and schema




  - Create `app/models/manufacturing_type.py` with SQLAlchemy 2.0 Mapped columns
  - Create `app/schemas/manufacturing_type.py` with Base, Create, Update, Response schemas
  - Add model to `app/models/__init__.py` and schema to `app/schemas/__init__.py`
  - Define table with all columns, indexes, and constraints
  - _Requirements: 2.1, 4.1, 4.2, 8.1_

- [x] 1.2 Create AttributeNode model with LTREE hierarchy





  - Create `app/models/attribute_node.py` with hierarchical structure
  - Include ltree_path, depth, parent_node_id columns with proper types
  - Add JSONB columns for display_condition, validation_rules
  - Add pricing and weight impact fields (price_impact_type, price_formula, weight_impact)
  - Create `app/schemas/attribute_node.py` with composed schemas
  - Define GiST index on ltree_path in model
  - _Requirements: 2.1, 2.2, 2.3, 2.4, 4.1, 4.3, 4.4, 8.3_

- [x] 1.3 Create Configuration and ConfigurationSelection models





  - Create `app/models/configuration.py` with status tracking
  - Create `app/models/configuration_selection.py` with flexible value storage
  - Add calculated fields (total_price, calculated_weight, calculated_technical_data)
  - Create corresponding Pydantic schemas with proper composition
  - Define all tables with indexes and constraints
  - _Requirements: 2.1, 2.4, 4.1, 4.2_

- [-] 1.4 Create Customer model and schema


  - Create `app/models/customer.py` with JSONB address field
  - Create `app/schemas/customer.py` with composed schemas
  - Define table with all columns and indexes
  - _Requirements: 2.1, 2.4, 4.1_

- [ ] 1.5 Create Quote model and schema
  - Create `app/models/quote.py` with pricing breakdown fields
  - Create `app/schemas/quote.py` with composed schemas
  - Define table with all columns and indexes
  - _Requirements: 2.1, 4.1_

- [ ] 1.6 Create Template models and schemas
  - Create `app/models/configuration_template.py` and `app/models/template_selection.py`
  - Create corresponding Pydantic schemas
  - Define tables with all columns and indexes
  - _Requirements: 2.1, 4.1_

- [ ] 1.7 Create Order models and schemas
  - Create `app/models/order.py` and `app/models/order_item.py`
  - Create corresponding Pydantic schemas
  - Define tables with all columns and indexes
  - _Requirements: 2.1, 4.1_

## Phase 2: Repository Layer

- [ ] 2. Create HierarchicalRepository base class
  - Create `app/repositories/windx_base.py` extending BaseRepository
  - Implement get_descendants() using LTREE descendant_of operator
  - Implement get_ancestors() using LTREE ancestor_of operator
  - Implement get_children() for direct children
  - Implement get_tree() for full tree structure
  - _Requirements: 3.2, 3.8, 3.9_

- [ ] 2.1 Create ManufacturingTypeRepository
  - Create `app/repositories/manufacturing_type.py` extending BaseRepository
  - Implement get_by_name() method
  - Implement get_active() method for active types only
  - Implement get_by_category() method
  - Add to `app/repositories/__init__.py`
  - _Requirements: 3.1, 3.9_

- [ ] 2.2 Create AttributeNodeRepository with hierarchy support
  - Create `app/repositories/attribute_node.py` extending HierarchicalRepository
  - Implement get_by_manufacturing_type() method
  - Implement get_root_nodes() for top-level nodes
  - Implement search_by_path_pattern() using LTREE lquery
  - Add to `app/repositories/__init__.py`
  - _Requirements: 3.2, 3.8, 3.9_

- [ ] 2.3 Create ConfigurationRepository
  - Create `app/repositories/configuration.py` extending BaseRepository
  - Implement get_by_customer() with optional status filter
  - Implement get_by_status() method
  - Implement get_with_selections() with eager loading
  - Add to `app/repositories/__init__.py`
  - _Requirements: 3.3, 3.9_

- [ ] 2.4 Create CustomerRepository
  - Create `app/repositories/customer.py` extending BaseRepository
  - Implement get_by_email() method
  - Implement get_active() method
  - Add to `app/repositories/__init__.py`
  - _Requirements: 3.5, 3.9_

- [ ] 2.5 Create QuoteRepository
  - Create `app/repositories/quote.py` extending BaseRepository
  - Implement get_by_quote_number() method
  - Implement get_by_customer() method
  - Implement get_by_configuration() method
  - Add to `app/repositories/__init__.py`
  - _Requirements: 3.6, 3.9_

- [ ] 2.6 Create TemplateRepository
  - Create `app/repositories/configuration_template.py` extending BaseRepository
  - Implement get_public_templates() method
  - Implement get_by_manufacturing_type() method
  - Implement increment_usage_count() method
  - Add to `app/repositories/__init__.py`
  - _Requirements: 3.4, 3.9_

- [ ] 2.7 Create OrderRepository
  - Create `app/repositories/order.py` extending BaseRepository
  - Implement get_by_order_number() method
  - Implement get_by_quote() method
  - Implement get_with_items() with eager loading
  - Add to `app/repositories/__init__.py`
  - _Requirements: 3.7, 3.9_

## Phase 3: Service Layer

- [ ] 3. Create PricingService for price calculations
  - Create `app/services/pricing.py` extending BaseService
  - Implement calculate_configuration_price() method
  - Implement calculate_selection_impact() for individual selections
  - Implement evaluate_price_formula() with safe formula evaluation
  - Handle fixed, percentage, and formula-based pricing
  - _Requirements: 5.1, 5.3_

- [ ] 3.1 Create ConfigurationService
  - Create `app/services/configuration.py` extending BaseService
  - Inject ConfigurationRepository, ConfigurationSelectionRepository, PricingService
  - Implement create_configuration() with initial selections
  - Implement update_selections() to modify attribute choices
  - Implement calculate_totals() to update price and weight
  - Implement get_configuration_with_details() with full selection data
  - _Requirements: 5.1, 5.3, 5.4_

- [ ] 3.2 Create QuoteService
  - Create `app/services/quote.py` extending BaseService
  - Inject QuoteRepository, ConfigurationRepository
  - Implement generate_quote() with price snapshot
  - Implement create_configuration_snapshot() for quote history
  - Implement calculate_quote_totals() with tax and discounts
  - _Requirements: 5.2, 5.3, 5.4_

- [ ] 3.3 Create TemplateService
  - Create `app/services/template.py` extending BaseService
  - Inject TemplateRepository, ConfigurationService
  - Implement create_template_from_configuration()
  - Implement apply_template_to_configuration()
  - Implement track_template_usage()
  - _Requirements: 5.4_

## Phase 4: API Endpoints

- [ ] 4. Create ManufacturingType endpoints
  - Create `app/api/v1/endpoints/manufacturing_types.py`
  - Implement GET /manufacturing-types (list with pagination)
  - Implement GET /manufacturing-types/{id} (get single)
  - Implement POST /manufacturing-types (create - superuser only)
  - Implement PATCH /manufacturing-types/{id} (update - superuser only)
  - Implement DELETE /manufacturing-types/{id} (delete - superuser only)
  - Add router to `app/api/v1/router.py`
  - Include OpenAPI documentation with examples
  - _Requirements: 6.1, 6.5, 6.6, 11.2_

- [ ] 4.1 Create AttributeNode endpoints
  - Create `app/api/v1/endpoints/attribute_nodes.py`
  - Implement GET /attribute-nodes (list with manufacturing_type_id filter)
  - Implement GET /attribute-nodes/{id} (get single)
  - Implement GET /attribute-nodes/{id}/children (get direct children)
  - Implement GET /attribute-nodes/{id}/tree (get full subtree)
  - Implement POST /attribute-nodes (create - superuser only)
  - Implement PATCH /attribute-nodes/{id} (update - superuser only)
  - Implement DELETE /attribute-nodes/{id} (delete - superuser only)
  - Add router to `app/api/v1/router.py`
  - _Requirements: 6.2, 6.5, 6.6, 11.3_

- [ ] 4.2 Create Configuration endpoints
  - Create `app/api/v1/endpoints/configurations.py`
  - Implement GET /configurations (list user's configurations with pagination)
  - Implement GET /configurations/{id} (get with selections)
  - Implement POST /configurations (create new configuration)
  - Implement PATCH /configurations/{id} (update name/description)
  - Implement PATCH /configurations/{id}/selections (update attribute selections)
  - Implement DELETE /configurations/{id} (delete configuration)
  - Add authorization checks (users see only their own)
  - Add router to `app/api/v1/router.py`
  - _Requirements: 6.3, 6.5, 6.6, 11.1_

- [ ] 4.3 Create Quote endpoints
  - Create `app/api/v1/endpoints/quotes.py`
  - Implement GET /quotes (list user's quotes with pagination)
  - Implement GET /quotes/{id} (get single quote)
  - Implement POST /quotes (generate quote from configuration)
  - Add authorization checks (users see only their own)
  - Add router to `app/api/v1/router.py`
  - _Requirements: 6.4, 6.5, 6.6, 11.5_

- [ ] 4.4 Create Template endpoints
  - Create `app/api/v1/endpoints/templates.py`
  - Implement GET /templates (list public templates with pagination)
  - Implement GET /templates/{id} (get template with selections)
  - Implement POST /templates (create from configuration - data entry users)
  - Implement POST /templates/{id}/apply (apply template to new configuration)
  - Add authorization checks (public read, restricted write)
  - Add router to `app/api/v1/router.py`
  - _Requirements: 6.5, 6.6, 11.4_

- [ ] 4.5 Create Customer endpoints
  - Create `app/api/v1/endpoints/customers.py`
  - Implement GET /customers (list - superuser only)
  - Implement GET /customers/{id} (get single - superuser only)
  - Implement POST /customers (create - superuser only)
  - Implement PATCH /customers/{id} (update - superuser only)
  - Add router to `app/api/v1/router.py`
  - _Requirements: 6.5, 6.6_

- [ ] 4.6 Create Order endpoints
  - Create `app/api/v1/endpoints/orders.py`
  - Implement GET /orders (list user's orders with pagination)
  - Implement GET /orders/{id} (get order with items)
  - Implement POST /orders (create order from quote)
  - Add authorization checks (users see only their own)
  - Add router to `app/api/v1/router.py`
  - _Requirements: 6.5, 6.6, 11.6_

## Phase 5: Database Triggers and Functions

- [ ] 5. Create LTREE path maintenance trigger
  - Create PostgreSQL function to update ltree_path when parent_node_id changes
  - Create trigger on attribute_nodes table for INSERT and UPDATE
  - Update all descendant paths when node is moved
  - Add SQL script in `app/database/sql/` directory
  - _Requirements: 2.2, 8.4_

- [ ] 5.1 Create depth calculation trigger
  - Create PostgreSQL function to calculate depth from ltree_path
  - Create trigger on attribute_nodes table for INSERT and UPDATE
  - Add SQL script in `app/database/sql/` directory
  - _Requirements: 8.4_

- [ ] 5.2 Create price history trigger
  - Create PostgreSQL function to log price changes
  - Create trigger on configurations table for UPDATE
  - Add SQL script in `app/database/sql/` directory
  - _Requirements: 8.4_

## Phase 6: Type Aliases and Dependencies

- [ ] 6. Add Windx repository type aliases to app/api/types.py
  - Create factory functions for all Windx repositories
  - Create type aliases (ManufacturingTypeRepo, AttributeNodeRepo, ConfigurationRepo, etc.)
  - Add comprehensive docstrings with usage examples
  - Add to __all__ exports
  - _Requirements: 6.5_

## Phase 7: Configuration and Environment

- [ ] 7. Add Windx configuration settings
  - Add WindxSettings class to `app/core/config.py`
  - Add environment variables for formula evaluation safety
  - Add snapshot retention policy settings
  - Add template usage tracking settings
  - Update Settings class to include WindxSettings
  - _Requirements: 9.1, 9.3, 9.4, 9.5_

- [ ] 7.1 Update environment files
  - Add Windx settings to `.env.example`
  - Add Windx settings to `.env.example.production`
  - Document all new environment variables
  - _Requirements: 9.1_

## Phase 8: Performance Optimization

- [ ] 8. Add essential indexes
  - Review all foreign key columns and add indexes in model definitions
  - Add indexes on frequently filtered columns (status, is_active, customer_id)
  - Add indexes on frequently sorted columns (created_at, sort_order)
  - Define indexes in SQLAlchemy models using index=True or Index()
  - _Requirements: 10.1, 10.2_

- [ ] 8.1 Implement eager loading for relationships
  - Update repository methods to use joinedload() for common relationships
  - Add get_with_selections() methods with eager loading
  - Add get_with_items() methods with eager loading
  - _Requirements: 10.4_

- [ ] 8.2 Add pagination to list endpoints
  - Apply pagination to all list endpoints using fastapi-pagination
  - Set reasonable default and maximum page sizes
  - Update response models to use Page[T]
  - _Requirements: 10.3_

## Phase 9: Error Handling and Validation

- [ ] 9. Add domain exceptions for Windx operations
  - Add InvalidConfigurationException to `app/core/exceptions.py`
  - Add InvalidFormulaException for formula evaluation errors
  - Add InvalidHierarchyException for path validation errors
  - Update exception handlers if needed
  - _Requirements: 12.1, 12.2, 12.3, 12.4_

- [ ] 9.1 Add validation for hierarchical operations
  - Validate ltree_path format in schemas
  - Validate parent_node_id doesn't create cycles
  - Validate formula syntax before storage
  - Add validation to service layer methods
  - _Requirements: 12.2, 12.3_

- [ ] 9.2 Add error handling for price calculations
  - Wrap formula evaluation in try/except
  - Handle division by zero and invalid operations
  - Return meaningful error messages
  - Add to PricingService methods
  - _Requirements: 12.4_

## Phase 10: Testing

- [ ]* 10. Create test fixtures and factories
  - Create ManufacturingTypeFactory in `tests/factories/`
  - Create AttributeNodeFactory with hierarchy support
  - Create ConfigurationFactory and ConfigurationSelectionFactory
  - Create CustomerFactory, QuoteFactory, TemplateFactory
  - _Requirements: 7.1, 7.2_

- [ ]* 10.1 Write repository unit tests
  - Test ManufacturingTypeRepository CRUD operations
  - Test AttributeNodeRepository hierarchy queries (descendants, ancestors)
  - Test ConfigurationRepository with selections
  - Test QuoteRepository and TemplateRepository
  - Aim for 85%+ repository coverage
  - _Requirements: 7.1_

- [ ]* 10.2 Write service unit tests
  - Test PricingService calculations with mocked repositories
  - Test ConfigurationService business logic
  - Test QuoteService snapshot creation
  - Test TemplateService template application
  - Aim for 90%+ service coverage
  - _Requirements: 7.2, 7.4, 7.5_

- [ ]* 10.3 Write API integration tests
  - Test manufacturing type endpoints (CRUD operations)
  - Test attribute node endpoints (hierarchy queries)
  - Test configuration endpoints (create, update selections)
  - Test quote generation endpoint
  - Test template application endpoint
  - Test authorization (users see only their own data)
  - Aim for 80%+ endpoint coverage
  - _Requirements: 7.3_


- [ ]* 10.4 Write price calculation tests
  - Test fixed price impacts
  - Test percentage price impacts
  - Test formula-based price calculations
  - Test error handling for invalid formulas
  - _Requirements: 7.4_

- [ ]* 10.5 Write quote snapshot tests
  - Test snapshot creation on quote generation
  - Test snapshot includes all configuration data
  - Test snapshot is immutable
  - _Requirements: 7.5_

## Phase 11: API Documentation

- [ ] 11. Create API documentation examples
  - Add request/response examples to all endpoints
  - Add error response examples
  - Document authentication requirements
  - Document authorization rules
  - _Requirements: 6.5_

## Notes

- **Phase 0 (Documentation) is PRIORITY** - Must be completed FIRST to understand the system
- **Optional tasks** (marked with *) focus on testing and can be skipped for MVP
- **Core tasks** must be completed for functional system
- Each task builds incrementally on previous tasks
- All tasks reference specific requirements from requirements.md
- Focus on working software over comprehensive documentation
- Optimize for current scale (800 users), not hypothetical future scale
- **NO MIGRATIONS NEEDED** - This is a fresh database setup, not a migration from existing schema
