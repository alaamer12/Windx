# RBAC Architecture Analysis

## Overview

This document analyzes different approaches for implementing Role-Based Access Control (RBAC) in the Windx system, evaluating database-layer vs backend-layer implementations, schema changes, and tooling options.

## RBAC Implementation Approaches

### 1. Database Layer RBAC

#### PostgreSQL Row Level Security (RLS)
```sql
-- Enable RLS on configurations table
ALTER TABLE configurations ENABLE ROW LEVEL SECURITY;

-- Policy: Users can only see configurations of their associated customers
CREATE POLICY user_customer_configurations ON configurations
    FOR ALL TO authenticated_users
    USING (
        customer_id IN (
            SELECT c.id FROM customers c 
            WHERE c.email = current_user_email()
        )
        OR current_user_role() = 'superadmin'
    );

-- Policy: Salesmen can only see assigned customers
CREATE POLICY salesman_assigned_customers ON configurations
    FOR ALL TO authenticated_users
    USING (
        current_user_role() = 'salesman' AND
        customer_id IN (
            SELECT customer_id FROM user_customer_assignments 
            WHERE user_id = current_user_id()
        )
    );
```

**Pros:**
- ✅ **Security at the data layer** - Cannot be bypassed by application bugs
- ✅ **Performance** - Database engine optimizes access patterns
- ✅ **Consistency** - All database access automatically enforced
- ✅ **Audit trail** - Database logs all access attempts
- ✅ **Multi-application support** - Works across different apps/services

**Cons:**
- ❌ **Complexity** - Complex policy management and debugging
- ❌ **Limited flexibility** - Hard to implement complex business rules
- ❌ **PostgreSQL specific** - Vendor lock-in
- ❌ **Migration difficulty** - Hard to change policies in production
- ❌ **Testing complexity** - Requires database-level test setup

### 2. Backend Layer RBAC

#### Service-Level Authorization
```python
class AuthorizationService:
    async def check_configuration_access(self, user: User, config_id: int) -> bool:
        """Check if user can access configuration."""
        config = await self.config_repo.get(config_id)
        
        if user.role == UserRole.SUPERADMIN:
            return True
        elif user.role == UserRole.SALESMAN:
            assigned_customers = await self.get_assigned_customers(user)
            return config.customer_id in assigned_customers
        elif user.role == UserRole.CUSTOMER:
            user_customer = await self.get_customer_for_user(user)
            return config.customer_id == user_customer.id
        
        return False
```

**Pros:**
- ✅ **Flexibility** - Complex business logic easily implemented
- ✅ **Testability** - Easy to unit test authorization logic
- ✅ **Database agnostic** - Works with any database
- ✅ **Gradual rollout** - Can be implemented incrementally
- ✅ **Clear debugging** - Application-level logs and debugging

**Cons:**
- ❌ **Security risk** - Can be bypassed by bugs or direct DB access
- ❌ **Performance overhead** - Additional queries for each authorization check
- ❌ **Consistency risk** - Must be implemented in every service
- ❌ **Maintenance burden** - Authorization logic scattered across codebase

### 3. Hybrid Approach (Recommended)

#### Database + Backend Combination
```python
# Backend: Business logic authorization
class RBACService:
    async def authorize_action(self, user: User, resource: str, action: str) -> bool:
        """High-level business authorization."""
        
# Database: Data-level security as backup
-- RLS policies as safety net for critical tables
CREATE POLICY backup_security ON configurations
    FOR ALL TO authenticated_users
    USING (customer_id IN (SELECT get_user_accessible_customers(current_user_id())));
```

## Recommended Architecture: Hybrid RBAC

### Why Hybrid?
1. **Defense in Depth** - Multiple security layers
2. **Flexibility + Security** - Business logic flexibility with data-level backup
3. **Performance Balance** - Optimize critical paths while maintaining security
4. **Gradual Implementation** - Start with backend, add database policies later

### Implementation Strategy

#### Phase 1: Backend RBAC Foundation
```python
# 1. Role-based authorization decorators
@require_role(UserRole.SUPERADMIN, UserRole.SALESMAN)
async def manage_customers():
    pass

# 2. Resource-based permissions
@require_permission("configuration:read")
async def get_configuration():
    pass

# 3. Context-aware authorization
@require_customer_access
async def update_configuration(config_id: int, user: User):
    pass
```

#### Phase 2: Database RLS for Critical Tables
```sql
-- Only for most sensitive tables
ALTER TABLE configurations ENABLE ROW LEVEL SECURITY;
ALTER TABLE quotes ENABLE ROW LEVEL SECURITY;
ALTER TABLE orders ENABLE ROW LEVEL SECURITY;
```

## Schema Changes Required

### 1. User Role Support
```sql
-- Add role to users table
ALTER TABLE users ADD COLUMN role VARCHAR(50) DEFAULT 'customer';
CREATE INDEX idx_users_role ON users(role);

-- Role enum constraint
ALTER TABLE users ADD CONSTRAINT check_user_role 
    CHECK (role IN ('superadmin', 'salesman', 'data_entry', 'partner', 'customer'));
```

### 2. Customer Assignments (Future)
```sql
-- For salesman/partner customer assignments
CREATE TABLE user_customer_assignments (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    customer_id INTEGER NOT NULL REFERENCES customers(id) ON DELETE CASCADE,
    assigned_by INTEGER REFERENCES users(id),
    assigned_at TIMESTAMP DEFAULT NOW(),
    is_active BOOLEAN DEFAULT TRUE,
    UNIQUE(user_id, customer_id)
);

CREATE INDEX idx_user_customer_assignments_user ON user_customer_assignments(user_id);
CREATE INDEX idx_user_customer_assignments_customer ON user_customer_assignments(customer_id);
```

### 3. Permissions Framework (Optional)
```sql
-- Fine-grained permissions (if needed later)
CREATE TABLE permissions (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL,
    description TEXT,
    resource VARCHAR(50) NOT NULL,
    action VARCHAR(50) NOT NULL
);

CREATE TABLE role_permissions (
    role VARCHAR(50) NOT NULL,
    permission_id INTEGER NOT NULL REFERENCES permissions(id),
    PRIMARY KEY (role, permission_id)
);
```

## Tooling and Libraries

### 1. Backend Authorization Libraries

#### Option A: Custom RBAC Service (Recommended)
```python
# Pros: Full control, Windx-specific business logic
# Cons: More development effort

class WindxRBAC:
    """Custom RBAC implementation for Windx business logic."""
    
    async def check_permission(self, user: User, resource: str, action: str, context: dict = None) -> bool:
        """Check if user has permission for action on resource."""
        
    async def get_accessible_customers(self, user: User) -> list[int]:
        """Get list of customer IDs user can access."""
        
    async def filter_query_by_access(self, query: Select, user: User, resource: str) -> Select:
        """Add access filters to SQLAlchemy query."""
```

#### Option B: FastAPI-Users + Permissions
```python
# Pros: Battle-tested, community support
# Cons: May not fit Windx's customer-centric model

from fastapi_users import FastAPIUsers
from fastapi_users.db import SQLAlchemyUserDatabase

# Would require significant adaptation for customer relationships
```

#### Option C: Casbin (Policy Engine)
```python
# Pros: Powerful policy engine, flexible
# Cons: Learning curve, may be overkill

import casbin

# Policy example:
# p, salesman, configuration, read, customer_assigned
# p, superadmin, *, *, *
# g, john@company.com, salesman
```

### 2. Database Tools

#### PostgreSQL RLS Functions
```sql
-- Helper functions for RLS policies
CREATE OR REPLACE FUNCTION current_user_id() RETURNS INTEGER AS $$
BEGIN
    RETURN current_setting('app.user_id')::INTEGER;
EXCEPTION
    WHEN OTHERS THEN RETURN NULL;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

CREATE OR REPLACE FUNCTION current_user_role() RETURNS TEXT AS $$
BEGIN
    RETURN current_setting('app.user_role');
EXCEPTION
    WHEN OTHERS THEN RETURN 'customer';
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;
```

#### Database Session Context
```python
# Set user context for RLS policies
async def set_db_user_context(db: AsyncSession, user: User):
    """Set user context for database session."""
    await db.execute(text("SET app.user_id = :user_id"), {"user_id": user.id})
    await db.execute(text("SET app.user_role = :role"), {"role": user.role})
```

## Recommended Implementation Plan

### Phase 1: Backend RBAC (Current Iteration)
1. **Add role field to User model**
2. **Implement WindxRBAC service**
3. **Add authorization decorators**
4. **Update all services to use RBAC**
5. **Comprehensive testing**

### Phase 2: Database RLS (Future)
1. **Add RLS policies to critical tables**
2. **Implement database context setting**
3. **Add RLS helper functions**
4. **Performance testing and optimization**

### Phase 3: Advanced Features (Future)
1. **Customer assignment management**
2. **Fine-grained permissions**
3. **Audit logging**
4. **Role hierarchy**

## Performance Considerations

### Backend RBAC Optimization
```python
# Cache user permissions
@lru_cache(maxsize=1000, ttl=300)  # 5-minute cache
async def get_user_permissions(user_id: int) -> set[str]:
    """Cached user permissions lookup."""

# Batch authorization checks
async def check_multiple_permissions(user: User, checks: list[tuple]) -> dict:
    """Batch multiple permission checks for efficiency."""

# Query-level filtering
def add_customer_filter(query: Select, user: User) -> Select:
    """Add customer access filter to query."""
    if user.role == UserRole.SUPERADMIN:
        return query
    elif user.role == UserRole.SALESMAN:
        return query.where(Configuration.customer_id.in_(
            select(UserCustomerAssignment.customer_id)
            .where(UserCustomerAssignment.user_id == user.id)
        ))
```

### Database RLS Performance
```sql
-- Optimize RLS with proper indexes
CREATE INDEX idx_configurations_customer_user ON configurations(customer_id) 
    WHERE customer_id IS NOT NULL;

-- Materialized views for complex access patterns
CREATE MATERIALIZED VIEW user_accessible_configurations AS
SELECT u.id as user_id, c.id as configuration_id
FROM users u
JOIN customers cust ON cust.email = u.email
JOIN configurations c ON c.customer_id = cust.id;
```

## Security Best Practices

### 1. Principle of Least Privilege
```python
# Default deny, explicit allow
DEFAULT_PERMISSIONS = {
    UserRole.CUSTOMER: ["configuration:read_own", "quote:read_own"],
    UserRole.SALESMAN: ["configuration:read_assigned", "quote:create"],
    UserRole.DATA_ENTRY: ["template:manage", "manufacturing_type:read"],
    UserRole.PARTNER: ["configuration:read_assigned"],
    UserRole.SUPERADMIN: ["*:*"]  # All permissions
}
```

### 2. Input Validation
```python
async def authorize_configuration_access(user: User, config_id: int):
    """Validate and authorize configuration access."""
    # Validate input
    if not isinstance(config_id, int) or config_id <= 0:
        raise ValidationException("Invalid configuration ID")
    
    # Check authorization
    if not await rbac.check_permission(user, "configuration", "read", {"id": config_id}):
        raise AuthorizationException("Access denied")
```

### 3. Audit Logging
```python
async def log_access_attempt(user: User, resource: str, action: str, success: bool):
    """Log all access attempts for audit."""
    audit_log.info(
        "Access attempt",
        extra={
            "user_id": user.id,
            "user_role": user.role,
            "resource": resource,
            "action": action,
            "success": success,
            "timestamp": datetime.utcnow()
        }
    )
```

## Conclusion

### Recommended Approach: Hybrid RBAC

1. **Start with Backend RBAC** for flexibility and rapid development
2. **Add Database RLS** for critical tables as security backup
3. **Use Custom WindxRBAC Service** tailored to business needs
4. **Implement gradually** to minimize risk and allow testing

### Schema Changes Needed:
- ✅ Add `role` field to `users` table
- ✅ Create `user_customer_assignments` table (future)
- ❌ No complex permissions tables initially (YAGNI)

### Tools Selected:
- **Custom WindxRBAC Service** for business logic
- **PostgreSQL RLS** for data-level security
- **SQLAlchemy integration** for query filtering
- **Caching** for performance optimization

This approach provides the right balance of security, flexibility, and performance for the Windx system while allowing for future enhancements as business needs evolve.