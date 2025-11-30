# Windx Integration Plan

Complete implementation plan for integrating the Windx SQL schema with SQLAlchemy and FastAPI.

## Table of Contents

1. [Overview](#overview)
2. [Models to Create](#models-to-create)
3. [Repositories to Create](#repositories-to-create)
4. [Services to Create](#services-to-create)
5. [API Endpoints to Create](#api-endpoints-to-create)
6. [Testing Approach](#testing-approach)
7. [Implementation Phases](#implementation-phases)

---

## Overview

This plan integrates the Windx product configuration system into the existing FastAPI application. The system uses a hybrid adjacency list + LTREE pattern for hierarchical attribute management with dynamic pricing, formulas, and configuration templates.

**Key Architecture Decisions:**
- **No migrations needed** - Fresh database setup
- **Hybrid pattern**: Adjacency list (`parent_node_id`) + LTREE (`ltree_path`) + depth cache
- **PostgreSQL-specific**: Uses LTREE extension for efficient hierarchical queries
- **EAV-style flexibility**: Attributes defined as data rows, not schema columns
- **Rich metadata**: JSONB for conditions, validation rules, pricing, formulas

---

## Models to Create

All models follow SQLAlchemy 2.0 patterns with `Mapped[T]` and `mapped_column()`.

### Core Domain Models

#### 1. ManufacturingType
**File**: `app/models/manufacturing_type.py`

**Purpose**: Product categories (Window, Door, Table)

**Key Fields**:
- `id`: Primary key
- `name`: Unique product category name
- `description`: Detailed description
- `base_category`: High-level grouping
- `image_url`: Product image
- `base_price`: Starting price
- `base_weight`: Base weight in kg
- `is_active`: Availability flag

**Relationships**:
- `attribute_nodes`: One-to-many with AttributeNode
- `configurations`: One-to-many with Configuration
- `templates`: One-to-many with ConfigurationTemplate

**Indexes**:
- Primary key on `id`
- Unique index on `name`
- Index on `is_active` (partial, WHERE is_active = true)

---

#### 2. AttributeNode
**File**: `app/models/attribute_node.py`

**Purpose**: Hierarchical product configuration system

**Key Fields**:
- `id`: Primary key
- `manufacturing_type_id`: Foreign key to ManufacturingType
- `parent_node_id`: Self-referential foreign key (adjacency list)
- `name`: Display name
- `node_type`: Enum ('category', 'attribute', 'option', 'component', 'technical_spec')
- `data_type`: Enum ('string', 'number', 'boolean', 'formula', 'dimension', 'selection')
- `display_condition`: JSONB for conditional display rules
- `validation_rules`: JSONB for input validation
- `required`: Boolean flag
- `price_impact_type`: Enum ('fixed', 'percentage', 'formula')
- `price_impact_value`: Decimal for fixed price adjustment
- `price_formula`: Text for dynamic price calculation
- `weight_impact`: Decimal for fixed weight addition
- `weight_formula`: Text for dynamic weight calculation
- `technical_property_type`: Type of technical property
- `technical_impact_formula`: Technical calculation formula
- `ltree_path`: LTREE for efficient path storage
- `depth`: Integer nesting level
- `sort_order`: Display order
- `ui_component`: UI control type
- `description`: Help text
- `help_text`: Additional guidance

**Relationships**:
- `manufacturing_type`: Many-to-one with ManufacturingType
- `parent`: Self-referential many-to-one
- `children`: Self-referential one-to-many
- `configuration_selections`: One-to-many with ConfigurationSelection
- `template_selections`: One-to-many with TemplateSelection

**Indexes**:
- Primary key on `id`
- Index on `manufacturing_type_id`
- Index on `parent_node_id`
- GIST index on `ltree_path`
- Index on `technical_property_type` (partial, WHERE NOT NULL)

---

#### 3. Customer
**File**: `app/models/customer.py`

**Purpose**: Customer management

**Key Fields**:
- `id`: Primary key
- `company_name`: Business name
- `contact_person`: Primary contact
- `email`: Unique contact email
- `phone`: Contact phone
- `address`: JSONB for flexible address storage
- `customer_type`: Type (residential, commercial, contractor)
- `tax_id`: Tax identification
- `payment_terms`: Payment agreement
- `is_active`: Active status
- `notes`: Internal notes

**Relationships**:
- `configurations`: One-to-many with Configuration
- `quotes`: One-to-many with Quote
- `template_usages`: One-to-many with TemplateUsage

**Indexes**:
- Primary key on `id`
- Unique index on `email`
- Index on `company_name`

---

#### 4. Configuration
**File**: `app/models/configuration.py`

**Purpose**: Individual product designs

**Key Fields**:
- `id`: Primary key
- `manufacturing_type_id`: Foreign key to ManufacturingType
- `customer_id`: Optional foreign key to Customer
- `name`: Configuration name
- `description`: Customer notes
- `status`: Enum ('draft', 'saved', 'quoted', 'ordered')
- `reference_code`: Unique identifier
- `base_price`: Base price from manufacturing type
- `total_price`: Final price including options
- `calculated_weight`: Total weight
- `calculated_technical_data`: JSONB for product-specific specs

**Relationships**:
- `manufacturing_type`: Many-to-one with ManufacturingType
- `customer`: Many-to-one with Customer
- `selections`: One-to-many with ConfigurationSelection
- `quotes`: One-to-many with Quote
- `snapshots`: One-to-many with ConfigurationSnapshot
- `order_items`: One-to-many with OrderItem
- `template_usages`: One-to-many with TemplateUsage

**Indexes**:
- Primary key on `id`
- Unique index on `reference_code`
- Index on `manufacturing_type_id`
- Index on `customer_id`
- GIN index on `calculated_technical_data`

---

#### 5. ConfigurationSelection
**File**: `app/models/configuration_selection.py`

**Purpose**: Individual attribute choices for configurations

**Key Fields**:
- `id`: Primary key
- `configuration_id`: Foreign key to Configuration
- `attribute_node_id`: Foreign key to AttributeNode
- `string_value`: Text selections
- `numeric_value`: Numerical inputs
- `boolean_value`: True/false choices
- `json_value`: Complex structured data
- `calculated_price_impact`: Price effect
- `calculated_weight_impact`: Weight effect
- `calculated_technical_impact`: JSONB for technical effects
- `selection_path`: LTREE for hierarchy context

**Relationships**:
- `configuration`: Many-to-one with Configuration
- `attribute_node`: Many-to-one with AttributeNode

**Indexes**:
- Primary key on `id`
- Unique composite index on (`configuration_id`, `attribute_node_id`)
- Index on `configuration_id`
- Index on `attribute_node_id`
- GIST index on `selection_path`

---

### Template System Models

#### 6. ConfigurationTemplate
**File**: `app/models/configuration_template.py`

**Purpose**: Pre-defined common configurations

**Key Fields**:
- `id`: Primary key
- `name`: Template name
- `description`: Template description
- `manufacturing_type_id`: Foreign key to ManufacturingType
- `template_type`: Type ('standard', 'premium', 'economy', 'custom')
- `is_public`: Customer visibility flag
- `usage_count`: Times template was used
- `success_rate`: Conversion rate to orders
- `estimated_price`: Quick reference price
- `estimated_weight`: Quick reference weight
- `created_by`: Foreign key to User
- `is_active`: Active status

**Relationships**:
- `manufacturing_type`: Many-to-one with ManufacturingType
- `creator`: Many-to-one with User
- `selections`: One-to-many with TemplateSelection
- `usages`: One-to-many with TemplateUsage
- `categories`: Many-to-many with TemplateCategory (through TemplateCategoryAssignment)

**Indexes**:
- Primary key on `id`
- Index on `manufacturing_type_id`
- Partial index on `is_public` (WHERE is_public = true)
- Partial index on `is_active` (WHERE is_active = true)

---

#### 7. TemplateSelection
**File**: `app/models/template_selection.py`

**Purpose**: Pre-defined attribute choices for templates

**Key Fields**:
- `id`: Primary key
- `template_id`: Foreign key to ConfigurationTemplate
- `attribute_node_id`: Foreign key to AttributeNode
- `string_value`: Text selections
- `numeric_value`: Numerical inputs
- `boolean_value`: True/false choices
- `json_value`: Complex structured data
- `selection_path`: LTREE for hierarchy context

**Relationships**:
- `template`: Many-to-one with ConfigurationTemplate
- `attribute_node`: Many-to-one with AttributeNode

**Indexes**:
- Primary key on `id`
- Unique composite index on (`template_id`, `attribute_node_id`)
- Index on `template_id`
- Index on `attribute_node_id`
- GIST index on `selection_path`

---

#### 8. TemplateUsage
**File**: `app/models/template_usage.py`

**Purpose**: Track template usage and conversions

**Key Fields**:
- `id`: Primary key
- `template_id`: Foreign key to ConfigurationTemplate
- `configuration_id`: Foreign key to Configuration
- `customer_id`: Optional foreign key to Customer
- `used_by`: Foreign key to User
- `usage_type`: Type ('customer_start', 'sales_assist', 'quick_quote')
- `converted_to_quote`: Boolean flag
- `converted_to_order`: Boolean flag

**Relationships**:
- `template`: Many-to-one with ConfigurationTemplate
- `configuration`: Many-to-one with Configuration
- `customer`: Many-to-one with Customer
- `user`: Many-to-one with User

**Indexes**:
- Primary key on `id`
- Index on `template_id`
- Index on `configuration_id`
- Partial index on `converted_to_order` (WHERE converted_to_order = true)

---

#### 9. TemplateCategory
**File**: `app/models/template_category.py`

**Purpose**: Organize templates into categories

**Key Fields**:
- `id`: Primary key
- `name`: Unique category name
- `description`: Category description
- `parent_category_id`: Self-referential foreign key
- `sort_order`: Display order
- `is_active`: Active status

**Relationships**:
- `parent`: Self-referential many-to-one
- `children`: Self-referential one-to-many
- `templates`: Many-to-many with ConfigurationTemplate (through TemplateCategoryAssignment)

**Indexes**:
- Primary key on `id`
- Unique index on `name`
- Index on `parent_category_id`

---

#### 10. TemplateCategoryAssignment
**File**: `app/models/template_category_assignment.py`

**Purpose**: Junction table for templates and categories

**Key Fields**:
- `template_id`: Foreign key to ConfigurationTemplate (composite PK)
- `category_id`: Foreign key to TemplateCategory (composite PK)
- `assigned_by`: Foreign key to User
- `assigned_at`: Timestamp

**Relationships**:
- `template`: Many-to-one with ConfigurationTemplate
- `category`: Many-to-one with TemplateCategory
- `assigner`: Many-to-one with User

**Indexes**:
- Composite primary key on (`template_id`, `category_id`)

---

### Quote and Order Models

#### 11. Quote
**File**: `app/models/quote.py`

**Purpose**: Quotation system

**Key Fields**:
- `id`: Primary key
- `configuration_id`: Foreign key to Configuration
- `customer_id`: Foreign key to Customer
- `quote_number`: Unique quote identifier
- `subtotal`: Price before tax and discounts
- `tax_rate`: Applicable tax rate
- `tax_amount`: Calculated tax
- `discount_amount`: Applied discounts
- `total_amount`: Final amount
- `technical_requirements`: JSONB for customer-specific needs
- `valid_until`: Quote expiration date
- `status`: Enum ('draft', 'sent', 'accepted', 'expired')

**Relationships**:
- `configuration`: Many-to-one with Configuration
- `customer`: Many-to-one with Customer
- `orders`: One-to-many with Order
- `snapshots`: One-to-many with ConfigurationSnapshot

**Indexes**:
- Primary key on `id`
- Unique index on `quote_number`
- Index on `configuration_id`
- Index on `customer_id`

---

#### 12. Order
**File**: `app/models/order.py`

**Purpose**: Order management

**Key Fields**:
- `id`: Primary key
- `quote_id`: Foreign key to Quote
- `order_number`: Unique order identifier
- `order_date`: When order was placed
- `required_date`: Requested delivery date
- `status`: Enum ('confirmed', 'production', 'shipped', 'installed')
- `special_instructions`: Customer requests
- `installation_address`: JSONB for delivery location

**Relationships**:
- `quote`: Many-to-one with Quote
- `items`: One-to-many with OrderItem

**Indexes**:
- Primary key on `id`
- Unique index on `order_number`
- Index on `quote_id`

---

#### 13. OrderItem
**File**: `app/models/order_item.py`

**Purpose**: Multiple configurations per order

**Key Fields**:
- `id`: Primary key
- `order_id`: Foreign key to Order
- `configuration_id`: Foreign key to Configuration
- `quantity`: Item quantity (CHECK > 0)
- `unit_price`: Price per unit
- `total_price`: Total line item price
- `production_status`: Status ('pending', 'in_production', 'completed')

**Relationships**:
- `order`: Many-to-one with Order
- `configuration`: Many-to-one with Configuration

**Indexes**:
- Primary key on `id`
- Index on `order_id`
- Index on `configuration_id`

---

### History and Audit Models

#### 14. ConfigurationSnapshot
**File**: `app/models/configuration_snapshot.py`

**Purpose**: Historical records of configurations

**Key Fields**:
- `id`: Primary key
- `configuration_id`: Foreign key to Configuration
- `quote_id`: Optional foreign key to Quote
- `base_price`: Base price at snapshot time
- `total_price`: Total price at snapshot time
- `calculated_weight`: Weight at snapshot time
- `price_breakdown`: JSONB for cost components
- `weight_breakdown`: JSONB for weight components
- `technical_snapshot`: JSONB for complete technical data
- `snapshot_type`: Type ('price_quote', 'technical_calculation', 'order_confirmation')
- `snapshot_reason`: Why snapshot was created
- `valid_until`: Snapshot expiration for quotes

**Relationships**:
- `configuration`: Many-to-one with Configuration
- `quote`: Many-to-one with Quote

**Indexes**:
- Primary key on `id`
- Composite index on (`configuration_id`, `created_at`)
- Index on `quote_id`

---

#### 15. ManufacturingTypePriceHistory
**File**: `app/models/manufacturing_type_price_history.py`

**Purpose**: Track price and weight changes for manufacturing types

**Key Fields**:
- `id`: Primary key
- `manufacturing_type_id`: Foreign key to ManufacturingType
- `old_base_price`: Previous base price
- `new_base_price`: New base price
- `old_base_weight`: Previous base weight
- `new_base_weight`: New base weight
- `change_reason`: Reason for change
- `effective_date`: When change took effect
- `changed_by`: Who made the change

**Relationships**:
- `manufacturing_type`: Many-to-one with ManufacturingType

**Indexes**:
- Primary key on `id`
- Composite index on (`manufacturing_type_id`, `effective_date`)

---

#### 16. AttributeNodeHistory
**File**: `app/models/attribute_node_history.py`

**Purpose**: Track attribute node changes

**Key Fields**:
- `id`: Primary key
- `attribute_node_id`: Foreign key to AttributeNode
- `old_price_impact`: Previous price impact
- `new_price_impact`: New price impact
- `old_weight_impact`: Previous weight impact
- `new_weight_impact`: New weight impact
- `old_price_formula`: Previous price formula
- `new_price_formula`: New price formula
- `old_weight_formula`: Previous weight formula
- `new_weight_formula`: New weight formula
- `old_technical_impact_formula`: Previous technical formula
- `new_technical_impact_formula`: New technical formula
- `change_reason`: Reason for change
- `effective_date`: When change took effect
- `changed_by`: Who made the change

**Relationships**:
- `attribute_node`: Many-to-one with AttributeNode

**Indexes**:
- Primary key on `id`
- Composite index on (`attribute_node_id`, `effective_date`)

---

## Repositories to Create

All repositories follow the repository pattern and inherit from `BaseRepository`.

### Core Repositories

#### 1. ManufacturingTypeRepository
**File**: `app/repositories/manufacturing_type_repository.py`

**Custom Methods**:
- `get_by_name(name: str) -> ManufacturingType | None`
- `get_active() -> list[ManufacturingType]`
- `get_by_category(category: str) -> list[ManufacturingType]`
- `update_base_price(id: int, new_price: Decimal, reason: str) -> ManufacturingType`

---

#### 2. AttributeNodeRepository
**File**: `app/repositories/attribute_node_repository.py`

**Custom Methods**:
- `get_by_manufacturing_type(type_id: int) -> list[AttributeNode]`
- `get_root_nodes(type_id: int) -> list[AttributeNode]`
- `get_children(parent_id: int) -> list[AttributeNode]`
- `get_descendants(node_id: int) -> list[AttributeNode]` (uses LTREE)
- `get_ancestors(node_id: int) -> list[AttributeNode]` (uses LTREE)
- `get_by_path(path: str) -> AttributeNode | None` (uses LTREE)
- `get_by_depth(type_id: int, depth: int) -> list[AttributeNode]`
- `get_options_with_pricing(type_id: int) -> list[AttributeNode]`
- `search_by_name(type_id: int, query: str) -> list[AttributeNode]`

---

#### 3. CustomerRepository
**File**: `app/repositories/customer_repository.py`

**Custom Methods**:
- `get_by_email(email: str) -> Customer | None`
- `get_by_company_name(name: str) -> list[Customer]`
- `get_active() -> list[Customer]`
- `get_by_type(customer_type: str) -> list[Customer]`
- `search(query: str) -> list[Customer]`

---

#### 4. ConfigurationRepository
**File**: `app/repositories/configuration_repository.py`

**Custom Methods**:
- `get_by_reference_code(code: str) -> Configuration | None`
- `get_by_customer(customer_id: int) -> list[Configuration]`
- `get_by_manufacturing_type(type_id: int) -> list[Configuration]`
- `get_by_status(status: str) -> list[Configuration]`
- `calculate_totals(config_id: int) -> dict[str, Decimal]`
- `get_with_selections(config_id: int) -> Configuration`

---

#### 5. ConfigurationSelectionRepository
**File**: `app/repositories/configuration_selection_repository.py`

**Custom Methods**:
- `get_by_configuration(config_id: int) -> list[ConfigurationSelection]`
- `get_by_attribute_node(node_id: int) -> list[ConfigurationSelection]`
- `bulk_create(selections: list[dict]) -> list[ConfigurationSelection]`
- `delete_by_configuration(config_id: int) -> int`
- `get_price_impacts(config_id: int) -> list[dict]`

---

### Template Repositories

#### 6. ConfigurationTemplateRepository
**File**: `app/repositories/configuration_template_repository.py`

**Custom Methods**:
- `get_by_manufacturing_type(type_id: int) -> list[ConfigurationTemplate]`
- `get_public_templates() -> list[ConfigurationTemplate]`
- `get_active() -> list[ConfigurationTemplate]`
- `get_by_type(template_type: str) -> list[ConfigurationTemplate]`
- `increment_usage_count(template_id: int) -> None`
- `update_success_rate(template_id: int, rate: Decimal) -> None`
- `get_popular(limit: int = 10) -> list[ConfigurationTemplate]`

---

#### 7. TemplateSelectionRepository
**File**: `app/repositories/template_selection_repository.py`

**Custom Methods**:
- `get_by_template(template_id: int) -> list[TemplateSelection]`
- `bulk_create(selections: list[dict]) -> list[TemplateSelection]`
- `delete_by_template(template_id: int) -> int`

---

#### 8. TemplateUsageRepository
**File**: `app/repositories/template_usage_repository.py`

**Custom Methods**:
- `get_by_template(template_id: int) -> list[TemplateUsage]`
- `get_by_customer(customer_id: int) -> list[TemplateUsage]`
- `get_conversions(template_id: int) -> dict[str, int]`
- `mark_converted_to_quote(usage_id: int) -> TemplateUsage`
- `mark_converted_to_order(usage_id: int) -> TemplateUsage`

---

#### 9. TemplateCategoryRepository
**File**: `app/repositories/template_category_repository.py`

**Custom Methods**:
- `get_by_name(name: str) -> TemplateCategory | None`
- `get_root_categories() -> list[TemplateCategory]`
- `get_children(parent_id: int) -> list[TemplateCategory]`
- `get_active() -> list[TemplateCategory]`

---

### Quote and Order Repositories

#### 10. QuoteRepository
**File**: `app/repositories/quote_repository.py`

**Custom Methods**:
- `get_by_quote_number(number: str) -> Quote | None`
- `get_by_customer(customer_id: int) -> list[Quote]`
- `get_by_configuration(config_id: int) -> list[Quote]`
- `get_by_status(status: str) -> list[Quote]`
- `get_expired() -> list[Quote]`
- `get_valid() -> list[Quote]`

---

#### 11. OrderRepository
**File**: `app/repositories/order_repository.py`

**Custom Methods**:
- `get_by_order_number(number: str) -> Order | None`
- `get_by_quote(quote_id: int) -> Order | None`
- `get_by_status(status: str) -> list[Order]`
- `get_by_date_range(start: date, end: date) -> list[Order]`

---

#### 12. OrderItemRepository
**File**: `app/repositories/order_item_repository.py`

**Custom Methods**:
- `get_by_order(order_id: int) -> list[OrderItem]`
- `get_by_configuration(config_id: int) -> list[OrderItem]`
- `get_by_production_status(status: str) -> list[OrderItem]`

---

### History Repositories

#### 13. ConfigurationSnapshotRepository
**File**: `app/repositories/configuration_snapshot_repository.py`

**Custom Methods**:
- `get_by_configuration(config_id: int) -> list[ConfigurationSnapshot]`
- `get_by_quote(quote_id: int) -> ConfigurationSnapshot | None`
- `get_by_type(snapshot_type: str) -> list[ConfigurationSnapshot]`
- `get_latest(config_id: int) -> ConfigurationSnapshot | None`

---

#### 14. ManufacturingTypePriceHistoryRepository
**File**: `app/repositories/manufacturing_type_price_history_repository.py`

**Custom Methods**:
- `get_by_manufacturing_type(type_id: int) -> list[ManufacturingTypePriceHistory]`
- `get_by_date_range(type_id: int, start: date, end: date) -> list[ManufacturingTypePriceHistory]`

---

#### 15. AttributeNodeHistoryRepository
**File**: `app/repositories/attribute_node_history_repository.py`

**Custom Methods**:
- `get_by_attribute_node(node_id: int) -> list[AttributeNodeHistory]`
- `get_by_date_range(node_id: int, start: date, end: date) -> list[AttributeNodeHistory]`

---

## Services to Create

All services follow the service pattern and inherit from `BaseService`.

### Core Services

#### 1. ManufacturingTypeService
**File**: `app/services/manufacturing_type_service.py`

**Business Logic**:
- Create manufacturing type with validation
- Update base price with history tracking
- Deactivate manufacturing type (soft delete)
- Get active types with filtering
- Calculate price impact across configurations

**Key Methods**:
- `create_manufacturing_type(data: ManufacturingTypeCreate) -> ManufacturingType`
- `update_base_price(type_id: int, new_price: Decimal, reason: str, user: str) -> ManufacturingType`
- `deactivate(type_id: int) -> ManufacturingType`
- `get_active_types() -> list[ManufacturingType]`

---

#### 2. AttributeNodeService
**File**: `app/services/attribute_node_service.py`

**Business Logic**:
- Create attribute nodes with automatic LTREE path generation
- Update nodes with path recalculation for descendants
- Move nodes in hierarchy (update parent)
- Delete nodes with cascade handling
- Validate conditional display logic
- Calculate pricing impacts

**Key Methods**:
- `create_node(data: AttributeNodeCreate) -> AttributeNode`
- `update_node(node_id: int, data: AttributeNodeUpdate) -> AttributeNode`
- `move_node(node_id: int, new_parent_id: int) -> AttributeNode`
- `delete_node(node_id: int) -> None`
- `get_tree(type_id: int) -> list[dict]` (hierarchical structure)
- `validate_conditions(node_id: int, context: dict) -> bool`
- `calculate_price_impact(node_id: int, context: dict) -> Decimal`

---

#### 3. CustomerService
**File**: `app/services/customer_service.py`

**Business Logic**:
- Create customer with email uniqueness check
- Update customer information
- Deactivate customer (soft delete)
- Search customers with filters
- Get customer statistics (configurations, quotes, orders)

**Key Methods**:
- `create_customer(data: CustomerCreate) -> Customer`
- `update_customer(customer_id: int, data: CustomerUpdate) -> Customer`
- `deactivate(customer_id: int) -> Customer`
- `search_customers(query: str, filters: dict) -> list[Customer]`
- `get_customer_stats(customer_id: int) -> dict`

---

#### 4. ConfigurationService
**File**: `app/services/configuration_service.py`

**Business Logic**:
- Create configuration with reference code generation
- Add/update/remove selections
- Calculate total price and weight
- Calculate technical properties
- Validate configuration completeness
- Clone configuration
- Apply template to configuration

**Key Methods**:
- `create_configuration(data: ConfigurationCreate) -> Configuration`
- `add_selection(config_id: int, selection: SelectionCreate) -> ConfigurationSelection`
- `update_selection(selection_id: int, data: SelectionUpdate) -> ConfigurationSelection`
- `remove_selection(selection_id: int) -> None`
- `calculate_totals(config_id: int) -> dict[str, Decimal]`
- `validate_configuration(config_id: int) -> dict[str, bool]`
- `clone_configuration(config_id: int, new_name: str) -> Configuration`
- `apply_template(config_id: int, template_id: int) -> Configuration`

---

#### 5. ConfigurationTemplateService
**File**: `app/services/configuration_template_service.py`

**Business Logic**:
- Create template with selections
- Update template and selections
- Apply template to create configuration
- Track template usage
- Calculate success metrics
- Manage template categories

**Key Methods**:
- `create_template(data: TemplateCreate, selections: list[dict]) -> ConfigurationTemplate`
- `update_template(template_id: int, data: TemplateUpdate) -> ConfigurationTemplate`
- `apply_template(template_id: int, customer_id: int, name: str) -> Configuration`
- `track_usage(template_id: int, config_id: int, customer_id: int, user_id: int) -> TemplateUsage`
- `update_success_metrics(template_id: int) -> None`
- `assign_categories(template_id: int, category_ids: list[int]) -> None`

---

### Quote and Order Services

#### 6. QuoteService
**File**: `app/services/quote_service.py`

**Business Logic**:
- Create quote with snapshot
- Calculate pricing (subtotal, tax, discounts)
- Update quote status
- Check quote validity
- Convert quote to order
- Send quote to customer (integration point)

**Key Methods**:
- `create_quote(data: QuoteCreate) -> Quote`
- `calculate_pricing(config_id: int, tax_rate: Decimal, discount: Decimal) -> dict`
- `update_status(quote_id: int, status: str) -> Quote`
- `check_validity(quote_id: int) -> bool`
- `convert_to_order(quote_id: int, order_data: OrderCreate) -> Order`

---

#### 7. OrderService
**File**: `app/services/order_service.py`

**Business Logic**:
- Create order from quote
- Add order items
- Update order status
- Track production status
- Calculate order totals
- Manage delivery scheduling

**Key Methods**:
- `create_order(data: OrderCreate) -> Order`
- `add_item(order_id: int, item: OrderItemCreate) -> OrderItem`
- `update_status(order_id: int, status: str) -> Order`
- `update_item_production_status(item_id: int, status: str) -> OrderItem`
- `calculate_order_total(order_id: int) -> Decimal`

---

### Calculation and Snapshot Services

#### 8. CalculationService
**File**: `app/services/calculation_service.py`

**Business Logic**:
- Evaluate price formulas
- Evaluate weight formulas
- Evaluate technical formulas
- Calculate configuration totals
- Validate formula syntax
- Safe formula execution

**Key Methods**:
- `evaluate_price_formula(formula: str, context: dict) -> Decimal`
- `evaluate_weight_formula(formula: str, context: dict) -> Decimal`
- `evaluate_technical_formula(formula: str, context: dict) -> Any`
- `calculate_configuration_totals(config_id: int) -> dict`
- `validate_formula(formula: str) -> bool`

---

#### 9. SnapshotService
**File**: `app/services/snapshot_service.py`

**Business Logic**:
- Create configuration snapshots
- Generate price breakdowns
- Generate weight breakdowns
- Generate technical snapshots
- Compare snapshots
- Restore from snapshot

**Key Methods**:
- `create_snapshot(config_id: int, snapshot_type: str, reason: str) -> ConfigurationSnapshot`
- `create_quote_snapshot(config_id: int, quote_id: int) -> ConfigurationSnapshot`
- `generate_price_breakdown(config_id: int) -> dict`
- `generate_weight_breakdown(config_id: int) -> dict`
- `compare_snapshots(snapshot1_id: int, snapshot2_id: int) -> dict`

---

## API Endpoints to Create

All endpoints follow FastAPI best practices with proper documentation, validation, and error handling.

### Manufacturing Type Endpoints

**Router**: `app/api/v1/endpoints/manufacturing_types.py`
**Tag**: "Manufacturing Types"
**Prefix**: `/api/v1/manufacturing-types`

#### Endpoints:
1. `GET /` - List all manufacturing types (with filters)
2. `GET /{type_id}` - Get manufacturing type by ID
3. `POST /` - Create new manufacturing type (admin only)
4. `PATCH /{type_id}` - Update manufacturing type (admin only)
5. `DELETE /{type_id}` - Deactivate manufacturing type (admin only)
6. `PATCH /{type_id}/price` - Update base price with history (admin only)
7. `GET /{type_id}/history` - Get price history

---

### Attribute Node Endpoints

**Router**: `app/api/v1/endpoints/attribute_nodes.py`
**Tag**: "Attribute Nodes"
**Prefix**: `/api/v1/attribute-nodes`

#### Endpoints:
1. `GET /` - List attribute nodes (with filters)
2. `GET /{node_id}` - Get attribute node by ID
3. `GET /tree/{type_id}` - Get complete attribute tree for manufacturing type
4. `GET /{node_id}/children` - Get child nodes
5. `GET /{node_id}/descendants` - Get all descendants (LTREE)
6. `GET /{node_id}/ancestors` - Get all ancestors (LTREE)
7. `POST /` - Create new attribute node (admin only)
8. `PATCH /{node_id}` - Update attribute node (admin only)
9. `DELETE /{node_id}` - Delete attribute node (admin only)
10. `PATCH /{node_id}/move` - Move node to new parent (admin only)

---

### Customer Endpoints

**Router**: `app/api/v1/endpoints/customers.py`
**Tag**: "Customers"
**Prefix**: `/api/v1/customers`

#### Endpoints:
1. `GET /` - List customers (paginated, with search)
2. `GET /{customer_id}` - Get customer by ID
3. `POST /` - Create new customer
4. `PATCH /{customer_id}` - Update customer
5. `DELETE /{customer_id}` - Deactivate customer (admin only)
6. `GET /{customer_id}/configurations` - Get customer configurations
7. `GET /{customer_id}/quotes` - Get customer quotes
8. `GET /{customer_id}/orders` - Get customer orders
9. `GET /{customer_id}/stats` - Get customer statistics

---

### Configuration Endpoints

**Router**: `app/api/v1/endpoints/configurations.py`
**Tag**: "Configurations"
**Prefix**: `/api/v1/configurations`

#### Endpoints:
1. `GET /` - List configurations (paginated, with filters)
2. `GET /{config_id}` - Get configuration by ID
3. `GET /reference/{reference_code}` - Get configuration by reference code
4. `POST /` - Create new configuration
5. `PATCH /{config_id}` - Update configuration
6. `DELETE /{config_id}` - Delete configuration
7. `POST /{config_id}/clone` - Clone configuration
8. `GET /{config_id}/selections` - Get configuration selections
9. `POST /{config_id}/selections` - Add selection to configuration
10. `PATCH /selections/{selection_id}` - Update selection
11. `DELETE /selections/{selection_id}` - Remove selection
12. `GET /{config_id}/calculate` - Calculate totals (price, weight, technical)
13. `GET /{config_id}/validate` - Validate configuration completeness
14. `POST /{config_id}/apply-template` - Apply template to configuration

---

### Configuration Template Endpoints

**Router**: `app/api/v1/endpoints/configuration_templates.py`
**Tag**: "Configuration Templates"
**Prefix**: `/api/v1/templates`

#### Endpoints:
1. `GET /` - List templates (with filters)
2. `GET /public` - List public templates
3. `GET /popular` - Get popular templates
4. `GET /{template_id}` - Get template by ID
5. `POST /` - Create new template (admin only)
6. `PATCH /{template_id}` - Update template (admin only)
7. `DELETE /{template_id}` - Deactivate template (admin only)
8. `GET /{template_id}/selections` - Get template selections
9. `POST /{template_id}/apply` - Apply template to create configuration
10. `GET /{template_id}/usage` - Get template usage statistics
11. `POST /{template_id}/categories` - Assign categories to template (admin only)

---

### Template Category Endpoints

**Router**: `app/api/v1/endpoints/template_categories.py`
**Tag**: "Template Categories"
**Prefix**: `/api/v1/template-categories`

#### Endpoints:
1. `GET /` - List template categories
2. `GET /{category_id}` - Get category by ID
3. `GET /{category_id}/templates` - Get templates in category
4. `POST /` - Create new category (admin only)
5. `PATCH /{category_id}` - Update category (admin only)
6. `DELETE /{category_id}` - Delete category (admin only)

---

### Quote Endpoints

**Router**: `app/api/v1/endpoints/quotes.py`
**Tag**: "Quotes"
**Prefix**: `/api/v1/quotes`

#### Endpoints:
1. `GET /` - List quotes (paginated, with filters)
2. `GET /{quote_id}` - Get quote by ID
3. `GET /number/{quote_number}` - Get quote by quote number
4. `POST /` - Create new quote
5. `PATCH /{quote_id}` - Update quote
6. `PATCH /{quote_id}/status` - Update quote status
7. `GET /{quote_id}/snapshot` - Get quote snapshot
8. `POST /{quote_id}/convert-to-order` - Convert quote to order
9. `POST /{quote_id}/send` - Send quote to customer (integration point)

---

### Order Endpoints

**Router**: `app/api/v1/endpoints/orders.py`
**Tag**: "Orders"
**Prefix**: `/api/v1/orders`

#### Endpoints:
1. `GET /` - List orders (paginated, with filters)
2. `GET /{order_id}` - Get order by ID
3. `GET /number/{order_number}` - Get order by order number
4. `POST /` - Create new order
5. `PATCH /{order_id}` - Update order
6. `PATCH /{order_id}/status` - Update order status
7. `GET /{order_id}/items` - Get order items
8. `POST /{order_id}/items` - Add item to order
9. `PATCH /items/{item_id}/status` - Update item production status

---

### Snapshot Endpoints

**Router**: `app/api/v1/endpoints/snapshots.py`
**Tag**: "Snapshots"
**Prefix**: `/api/v1/snapshots`

#### Endpoints:
1. `GET /configuration/{config_id}` - Get configuration snapshots
2. `GET /{snapshot_id}` - Get snapshot by ID
3. `POST /` - Create manual snapshot
4. `GET /{snapshot_id}/compare/{other_snapshot_id}` - Compare two snapshots

---

### Calculation Endpoints

**Router**: `app/api/v1/endpoints/calculations.py`
**Tag**: "Calculations"
**Prefix**: `/api/v1/calculations`

#### Endpoints:
1. `POST /validate-formula` - Validate formula syntax
2. `POST /evaluate-formula` - Evaluate formula with context
3. `POST /configuration/{config_id}/calculate` - Calculate configuration totals

---

## Testing Approach

### Unit Testing Strategy

#### Model Tests
**Location**: `tests/unit/models/`

**Coverage**:
- Model creation and validation
- Relationship loading
- Computed properties
- Enum validation
- JSONB field handling

**Example Tests**:
- `test_manufacturing_type_creation`
- `test_attribute_node_ltree_path`
- `test_configuration_selection_unique_constraint`
- `test_customer_address_jsonb`

---

#### Repository Tests
**Location**: `tests/unit/repositories/`

**Coverage**:
- CRUD operations
- Custom query methods
- LTREE operations
- Filtering and searching
- Pagination

**Example Tests**:
- `test_attribute_node_get_descendants`
- `test_configuration_calculate_totals`
- `test_template_get_popular`
- `test_quote_get_expired`

**Mocking Strategy**:
- Mock database session
- Use in-memory SQLite for fast tests
- Factory pattern for test data

---

#### Service Tests
**Location**: `tests/unit/services/`

**Coverage**:
- Business logic validation
- Error handling
- Transaction management
- Formula evaluation
- Price calculations

**Example Tests**:
- `test_configuration_service_apply_template`
- `test_calculation_service_evaluate_formula`
- `test_quote_service_create_with_snapshot`
- `test_attribute_node_service_move_node`

**Mocking Strategy**:
- Mock repository methods
- Mock external dependencies
- Test business logic in isolation

---

### Integration Testing Strategy

#### API Endpoint Tests
**Location**: `tests/integration/api/`

**Coverage**:
- Full HTTP request/response cycle
- Authentication and authorization
- Request validation
- Response formatting
- Error responses

**Example Tests**:
- `test_create_configuration_with_selections`
- `test_apply_template_creates_configuration`
- `test_create_quote_generates_snapshot`
- `test_unauthorized_access_returns_401`

**Testing Tools**:
- `httpx.AsyncClient` for HTTP testing
- Real database (test database)
- Transaction rollback after each test

---

#### Database Integration Tests
**Location**: `tests/integration/database/`

**Coverage**:
- LTREE operations
- Triggers and functions
- Complex queries
- Transaction handling
- Cascade deletes

**Example Tests**:
- `test_ltree_descendant_query`
- `test_configuration_update_trigger`
- `test_template_usage_metrics_update`
- `test_cascade_delete_attribute_node`

---

### Test Data Management

#### Factories
**Location**: `tests/factories/`

**Factory Classes**:
- `ManufacturingTypeFactory`
- `AttributeNodeFactory`
- `CustomerFactory`
- `ConfigurationFactory`
- `ConfigurationSelectionFactory`
- `ConfigurationTemplateFactory`
- `QuoteFactory`
- `OrderFactory`

**Usage**:
```python
# Create test manufacturing type
mfg_type = ManufacturingTypeFactory.create(name="Window")

# Create attribute tree
root = AttributeNodeFactory.create(
    manufacturing_type=mfg_type,
    parent_node_id=None,
    name="Hardness"
)
child = AttributeNodeFactory.create(
    manufacturing_type=mfg_type,
    parent_node_id=root.id,
    name="Scale"
)

# Create configuration with selections
config = ConfigurationFactory.create(manufacturing_type=mfg_type)
selection = ConfigurationSelectionFactory.create(
    configuration=config,
    attribute_node=child
)
```

---

#### Fixtures
**Location**: `tests/conftest.py`

**Common Fixtures**:
- `db_session`: Database session for tests
- `client`: HTTP client for API tests
- `test_user`: Authenticated user
- `test_admin`: Admin user
- `sample_manufacturing_type`: Pre-created manufacturing type
- `sample_attribute_tree`: Pre-created attribute hierarchy
- `sample_configuration`: Pre-created configuration

---

### Performance Testing

#### Load Tests
**Location**: `tests/performance/`

**Coverage**:
- LTREE query performance
- Configuration calculation speed
- Bulk insert operations
- Complex filtering queries

**Example Tests**:
- `test_ltree_query_with_1000_nodes`
- `test_calculate_configuration_with_100_selections`
- `test_bulk_create_1000_configurations`

---

### Test Coverage Goals

**Overall Coverage**: 80%+
- **Models**: 90%+
- **Repositories**: 85%+
- **Services**: 90%+
- **API Endpoints**: 80%+

**Coverage Tools**:
- `pytest-cov` for coverage reporting
- CI/CD integration for coverage checks

---

### Testing Best Practices

1. **AAA Pattern**: Arrange, Act, Assert
2. **Descriptive Names**: `test_create_quote_with_invalid_config_raises_not_found`
3. **One Assertion Per Test**: Focus on single behavior
4. **Isolation**: Tests should not depend on each other
5. **Fast Execution**: Unit tests < 100ms, integration tests < 1s
6. **Cleanup**: Use fixtures and rollback for database cleanup

---

## Implementation Phases

### Phase 1: Database Foundation (Tasks 1.1-1.5)

**Goal**: Set up database schema and core models

**Tasks**:
1. Enable LTREE extension
2. Create all SQLAlchemy models (16 models)
3. Define relationships and indexes
4. Create Pydantic schemas (Base, Create, Update, Response)
5. Set up database initialization script

**Deliverables**:
- All model files in `app/models/`
- All schema files in `app/schemas/`
- Database initialization script
- Model documentation

**Testing**:
- Model creation tests
- Relationship loading tests
- JSONB field tests
- Enum validation tests

---

### Phase 2: Repository Layer (Tasks 2.1-2.5)

**Goal**: Implement data access layer

**Tasks**:
1. Create base repository patterns
2. Implement core repositories (5 repositories)
3. Implement template repositories (4 repositories)
4. Implement quote/order repositories (3 repositories)
5. Implement history repositories (3 repositories)

**Deliverables**:
- 15 repository files in `app/repositories/`
- Custom query methods
- LTREE query implementations
- Repository documentation

**Testing**:
- CRUD operation tests
- Custom query tests
- LTREE operation tests
- Filtering and pagination tests

---

### Phase 3: Service Layer (Tasks 3.1-3.5)

**Goal**: Implement business logic

**Tasks**:
1. Create core services (5 services)
2. Implement calculation service
3. Implement snapshot service
4. Implement template service
5. Add formula evaluation logic

**Deliverables**:
- 9 service files in `app/services/`
- Business logic implementation
- Formula evaluation engine
- Service documentation

**Testing**:
- Business logic tests
- Formula evaluation tests
- Transaction management tests
- Error handling tests

---

### Phase 4: API Layer (Tasks 4.1-4.5)

**Goal**: Create REST API endpoints

**Tasks**:
1. Create manufacturing type endpoints
2. Create attribute node endpoints
3. Create customer endpoints
4. Create configuration endpoints
5. Create template endpoints
6. Create quote/order endpoints
7. Create calculation endpoints

**Deliverables**:
- 10 endpoint files in `app/api/v1/endpoints/`
- OpenAPI documentation
- Request/response validation
- Error handling

**Testing**:
- API endpoint tests
- Authentication tests
- Validation tests
- Error response tests

---

### Phase 5: Advanced Features (Tasks 5.1-5.5)

**Goal**: Implement advanced functionality

**Tasks**:
1. Formula evaluation engine
2. Conditional display logic
3. Template application system
4. Snapshot comparison
5. Price history tracking

**Deliverables**:
- Formula parser and evaluator
- Condition validator
- Template application logic
- Snapshot comparison tool
- History tracking system

**Testing**:
- Formula evaluation tests
- Condition validation tests
- Template application tests
- Snapshot comparison tests

---

### Phase 6: Integration and Polish (Tasks 6.1-6.5)

**Goal**: Integration testing and documentation

**Tasks**:
1. End-to-end integration tests
2. Performance optimization
3. API documentation
4. User guides
5. Deployment preparation

**Deliverables**:
- Integration test suite
- Performance benchmarks
- Complete API documentation
- User documentation
- Deployment scripts

**Testing**:
- Full integration tests
- Performance tests
- Load tests
- Security tests

---

## Summary

### Total Implementation Scope

**Models**: 16 SQLAlchemy models
**Repositories**: 15 repository classes
**Services**: 9 service classes
**API Endpoints**: ~70 endpoints across 10 routers
**Tests**: ~200+ test cases

### Key Technical Decisions

1. **Hybrid Pattern**: Adjacency list + LTREE for optimal performance
2. **No Migrations**: Fresh database setup (as specified)
3. **JSONB Usage**: Flexible storage for conditions, formulas, and metadata
4. **Formula Evaluation**: Safe expression parser for dynamic calculations
5. **Snapshot System**: Historical tracking for quotes and configurations
6. **Template System**: Reusable configurations with usage tracking

### Dependencies

**Required**:
- PostgreSQL with LTREE extension
- SQLAlchemy 2.0+
- Pydantic V2
- FastAPI
- httpx (for testing)
- pytest

**Optional**:
- Redis (for caching)
- Celery (for async tasks)

### Estimated Timeline

- **Phase 1**: 2-3 days
- **Phase 2**: 3-4 days
- **Phase 3**: 3-4 days
- **Phase 4**: 4-5 days
- **Phase 5**: 3-4 days
- **Phase 6**: 2-3 days

**Total**: 17-23 days (3-4 weeks)

---

## Next Steps

1. Review this integration plan
2. Confirm scope and priorities
3. Begin Phase 1: Database Foundation
4. Implement models and schemas
5. Set up testing infrastructure
6. Proceed through phases sequentially

---

*This integration plan provides a complete roadmap for implementing the Windx product configuration system. Each phase builds on the previous one, ensuring a solid foundation before adding complexity.*
