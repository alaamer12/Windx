# Requirements Document: Windx Configurator Integration

ALAWAY RUN FROM `.venv` -> `.venv\scripts\python` not `python`

## Introduction

This document outlines the requirements for integrating the Windx automated window & door configurator system into the existing FastAPI backend application. The Windx system is a highly flexible, hierarchical product configuration platform that enables customers to design, customize, and order windows, doors, and other manufactured products through a dynamic attribute system.

The integration will add a complete product configuration subsystem to the existing user authentication and management platform, maintaining the current architectural patterns (repository pattern, service layer, SQLAlchemy 2.0, Pydantic V2) while introducing new domain models for manufacturing types, attribute hierarchies, configurations, templates, quotes, and orders.

## Requirements

### Requirement 1: Documentation Creation

**User Story:** As a developer, I want comprehensive documentation of the Windx system, so that I can understand the architecture, SQL design, and integration approach.

#### Acceptance Criteria

1. WHEN reviewing the project THEN the global README.md SHALL accurately describe the Windx configurator system
2. WHEN a new developer joins THEN a `docs/windx-overview.md` file SHALL provide complete system understanding without needing to see code
3. WHEN analyzing the SQL schema THEN a `docs/windx-sql-traits.md` file SHALL document what is unique in our SQL code, what is standard, assessments of good/bad patterns, optimization opportunities, and future steps
4. WHEN understanding data flow THEN a `docs/windx-sql-explanations.md` file SHALL provide high-level ERD explanations of why we designed tables this way, what columns are for, and how data flows
5. WHEN planning integration THEN a complete integration plan SHALL exist showing all steps needed to integrate SQL with SQLAlchemy and Pydantic v2

**Note**: These are NEW files to be created, not updates to existing spec files.

### Requirement 2: Database Schema Integration

**User Story:** As a backend developer, I want the Windx SQL schema integrated with SQLAlchemy 2.0 models, so that I can leverage ORM capabilities while maintaining the hierarchical attribute system's flexibility.

#### Acceptance Criteria

1. WHEN defining models THEN all tables from full.sql.txt SHALL be represented as SQLAlchemy 2.0 models with Mapped columns
2. WHEN using LTREE paths THEN PostgreSQL LTREE extension SHALL be properly configured and indexed
3. WHEN creating relationships THEN SQLAlchemy relationships SHALL correctly represent one-to-many and many-to-many associations
4. WHEN storing JSON data THEN JSONB columns SHALL use SQLAlchemy's JSON type with proper type hints
5. WHEN creating schema THEN all tables, indexes, triggers, and functions SHALL be created from the SQL schema
6. WHEN querying hierarchies THEN LTREE operators SHALL be accessible through SQLAlchemy expressions

### Requirement 3: Repository Pattern Implementation

**User Story:** As a backend developer, I want repositories for all Windx domain entities, so that data access follows the established architectural pattern and remains testable.

#### Acceptance Criteria

1. WHEN accessing manufacturing types THEN a ManufacturingTypeRepository SHALL provide CRUD operations and custom queries
2. WHEN accessing attribute nodes THEN an AttributeNodeRepository SHALL support hierarchical queries using LTREE paths
3. WHEN accessing configurations THEN a ConfigurationRepository SHALL handle configuration lifecycle and selections
4. WHEN accessing templates THEN a TemplateRepository SHALL support template creation, usage tracking, and metrics
5. WHEN accessing customers THEN a CustomerRepository SHALL provide customer management operations
6. WHEN accessing quotes THEN a QuoteRepository SHALL handle quote generation with snapshots
7. WHEN accessing orders THEN an OrderRepository SHALL manage order lifecycle and items
8. WHEN querying hierarchies THEN repositories SHALL provide methods for ancestor/descendant queries using LTREE
9. WHEN repositories are created THEN they SHALL inherit from BaseRepository and follow existing patterns

### Requirement 4: Pydantic Schema Definitions

**User Story:** As an API developer, I want Pydantic V2 schemas for all Windx entities, so that request/response validation follows modern Pydantic patterns with proper type safety.

#### Acceptance Criteria

1. WHEN defining schemas THEN all entities SHALL have Base, Create, Update, and Response schema variants
2. WHEN using semantic types THEN schemas SHALL use PositiveInt, EmailStr, and other Pydantic semantic types
3. WHEN handling JSON fields THEN schemas SHALL properly type JSONB columns with nested models or dict types
4. WHEN validating hierarchies THEN schemas SHALL include path validation for LTREE fields
5. WHEN composing schemas THEN inheritance SHALL be used to avoid duplication
6. WHEN documenting fields THEN Field() SHALL include descriptions and examples
7. WHEN configuring schemas THEN ConfigDict SHALL use from_attributes=True for ORM compatibility

### Requirement 5: Service Layer Business Logic

**User Story:** As a backend developer, I want service classes for Windx business operations, so that workflows like configuration creation and quote generation are properly encapsulated.

#### Acceptance Criteria

1. WHEN creating configurations THEN a ConfigurationService SHALL handle attribute selection and price calculation
2. WHEN generating quotes THEN a QuoteService SHALL create quotes with price snapshots
3. WHEN calculating prices THEN services SHALL sum base price and option prices
4. WHEN services are created THEN they SHALL inherit from BaseService and manage transactions

**Note**: Start with core services (Configuration, Quote). Add Template and Order services later if needed.

### Requirement 6: API Endpoints

**User Story:** As a frontend developer, I want RESTful API endpoints for Windx operations, so that I can build the configurator UI.

#### Acceptance Criteria

1. WHEN accessing manufacturing types THEN endpoints SHALL provide list, get, create, update, delete operations
2. WHEN accessing attribute nodes THEN endpoints SHALL support hierarchical queries
3. WHEN managing configurations THEN endpoints SHALL support configuration CRUD and selection updates
4. WHEN generating quotes THEN endpoints SHALL create quotes with snapshots
5. WHEN endpoints are defined THEN they SHALL include basic OpenAPI documentation
6. WHEN endpoints are organized THEN they SHALL use /api/v1/ prefix

**Note**: Start with core endpoints. Add template, customer, and order endpoints later if needed.

### Requirement 7: Testing Infrastructure

**User Story:** As a QA engineer, I want tests for the Windx system, so that I can verify core functionality.

#### Acceptance Criteria

1. WHEN testing repositories THEN unit tests SHALL verify CRUD operations with test database
2. WHEN testing services THEN unit tests SHALL verify business logic with mocked repositories
3. WHEN testing endpoints THEN integration tests SHALL verify HTTP-to-database flow using httpx AsyncClient
4. WHEN testing calculations THEN tests SHALL verify price calculations
5. WHEN testing quotes THEN tests SHALL verify snapshot creation

**Note**: Focus on critical paths (70% coverage). Don't aim for 100% coverage initially.

### Requirement 8: Database Schema Creation

**User Story:** As a DevOps engineer, I want a clear schema creation strategy, so that I can deploy the Windx system to fresh database environments.

#### Acceptance Criteria

1. WHEN creating schema THEN all tables SHALL be defined in SQLAlchemy models
2. WHEN initializing database THEN PostgreSQL LTREE extension SHALL be enabled
3. WHEN creating indexes THEN GiST indexes SHALL be created for LTREE columns
4. WHEN creating triggers THEN database triggers SHALL be created for path maintenance and price history
5. WHEN creating functions THEN PostgreSQL functions SHALL be created for calculations and snapshots
6. WHEN deploying THEN schema creation SHALL be idempotent

### Requirement 9: Configuration and Environment

**User Story:** As a system administrator, I want proper configuration for the Windx system, so that I can control behavior through environment variables.

#### Acceptance Criteria

1. WHEN configuring THEN environment variables SHALL control Windx-specific settings
2. WHEN using LTREE THEN PostgreSQL version compatibility SHALL be verified
3. WHEN calculating prices THEN formula evaluation safety SHALL be configurable
4. WHEN creating snapshots THEN snapshot retention policies SHALL be configurable
5. WHEN tracking metrics THEN template usage tracking SHALL be configurable

### Requirement 10: Performance Optimization

**User Story:** As a developer, I want the Windx system to perform adequately for current usage, so that users have a good experience.

#### Acceptance Criteria

1. WHEN querying hierarchies THEN GiST indexes on LTREE columns SHALL be used
2. WHEN filtering THEN essential indexes SHALL exist (foreign keys, lookups)
3. WHEN paginating lists THEN pagination SHALL be applied to list endpoints
4. WHEN loading relationships THEN eager loading SHALL be used to prevent N+1 queries

**Note**: Start with essential optimizations. Add more only if performance issues arise.

### Requirement 11: Security and Authorization

**User Story:** As a security engineer, I want proper authorization for Windx operations, so that customers can only access their own configurations and administrative operations are protected.

#### Acceptance Criteria

1. WHEN accessing configurations THEN users SHALL only see their own configurations unless they are superusers
2. WHEN managing manufacturing types THEN only superusers SHALL create, update, or delete types
3. WHEN managing attribute nodes THEN only superusers SHALL modify the attribute hierarchy
4. WHEN managing templates THEN data entry users SHALL create templates but customers SHALL only view public templates
5. WHEN generating quotes THEN users SHALL only generate quotes for their own configurations
6. WHEN processing orders THEN proper authorization SHALL verify quote ownership

### Requirement 12: Error Handling and Validation

**User Story:** As a frontend developer, I want consistent error handling, so that I can provide meaningful feedback to users when operations fail.

#### Acceptance Criteria

1. WHEN validation fails THEN domain exceptions SHALL be raised with descriptive messages
2. WHEN hierarchies are invalid THEN path validation SHALL prevent orphaned nodes
3. WHEN formulas are invalid THEN formula syntax SHALL be validated before storage
4. WHEN prices are calculated THEN calculation errors SHALL be caught and reported
5. WHEN snapshots are created THEN snapshot creation failures SHALL not prevent quote creation
6. WHEN errors occur THEN global exception handlers SHALL format errors consistently

## Non-Functional Requirements

### Performance (Pragmatic)
- Configuration list endpoints SHALL respond in < 500ms for current user base
- Hierarchy queries SHALL respond in < 300ms for typical trees (50 nodes)
- Price calculations SHALL complete in < 500ms for typical configurations (20 selections)

**Note**: These targets are sufficient for 800 users. Optimize further only if performance issues arise.

### Scalability (Current Needs)
- System SHALL support 100+ manufacturing types (current need)
- System SHALL support attribute hierarchies with 10 levels of nesting (typical use case)
- System SHALL support 5,000+ customer configurations (current scale)

**Note**: Build for current scale, not hypothetical future scale.

### Maintainability
- Code SHALL follow existing architectural patterns
- All code SHALL have type hints
- Critical code SHALL have docstrings
- Test coverage SHALL be > 70% (focus on critical paths)

### Compatibility
- System SHALL work with PostgreSQL 12+
- System SHALL work with existing Supabase and PostgreSQL configurations
- System SHALL not break existing user authentication functionality

## Success Criteria (Pragmatic)

1. Core Windx tables are represented as SQLAlchemy models
2. Repositories follow the established pattern
3. Services encapsulate business logic
4. Endpoints have basic OpenAPI documentation
5. Test coverage exceeds 70% for critical paths
6. Integration does not break existing functionality
7. System works for current user base (800 users)
8. Code is maintainable and follows existing patterns

**Note**: Focus on working software over perfect documentation and 100% test coverage.
