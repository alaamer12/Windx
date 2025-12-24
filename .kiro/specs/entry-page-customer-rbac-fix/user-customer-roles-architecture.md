# User vs Customer Architecture & RBAC Design

## Overview

This document explains the distinction between Users and Customers in the Windx system, the current implementation issues, and the new Role-Based Access Control (RBAC) system.

## Current Architecture Problem

### The Issue
The current entry page system incorrectly uses `user.id` as `customer_id` in configurations, which violates the business model and database foreign key constraints.

```python
# ❌ CURRENT (WRONG)
"customer_id": user.id  # References users table, breaks FK constraint

# ✅ CORRECT 
"customer_id": customer.id  # References customers table properly
```

## Entity Definitions

### User (System Account)
**Purpose**: Authentication, authorization, and system access control

**Attributes**:
- `id`, `email`, `username`, `hashed_password`
- `is_active`, `is_superuser`
- `created_at`, `updated_at`

**Role**: Controls WHO can access the system and WHAT they can do

### Customer (Business Entity)
**Purpose**: Business relationship, sales, billing, and order management

**Attributes**:
- `id`, `company_name`, `contact_person`, `email`, `phone`
- `address`, `customer_type`, `tax_id`, `payment_terms`
- `is_active`, `notes`

**Role**: Controls WHICH business entity owns configurations, quotes, and orders

### Relationship
```
User (1) ←→ (0..1) Customer
```
- A User can have an associated Customer (for entry page users)
- A Customer can have multiple Users (for company accounts)
- Users without Customers can still access the system (admins, data entry)

## Business Workflow

```
User Login → Customer Association → Configuration → Quote → Order
     ↓              ↓                    ↓         ↓       ↓
Authentication  Business Entity    Product Design  Pricing  Purchase
```

1. **User** logs in (authentication)
2. **Customer** is identified/created (business entity)
3. **Configuration** is owned by Customer (product design)
4. **Quote** is generated for Customer (pricing proposal)
5. **Order** is placed by Customer (purchase)

## New RBAC System

### Role Definitions

#### 1. Superadmin
- **Current**: `is_superuser = True`
- **Access**: Full system access
- **Capabilities**:
  - Manage all users, customers, configurations
  - Access admin panels
  - Manage manufacturing types and attribute hierarchies
  - View all data across the system

#### 2. Salesman
- **New Role**: Sales representative
- **Access**: Customer-focused operations
- **Capabilities**:
  - View and manage assigned customers
  - Create configurations for customers
  - Generate quotes and manage orders
  - Access customer data and sales reports
  - Cannot access system administration

#### 3. Data Entry Guy
- **New Role**: Content and template management
- **Access**: Product data management
- **Capabilities**:
  - Manage configuration templates
  - Update attribute hierarchies (with approval)
  - Manage manufacturing types
  - Cannot access customer data or sales operations

#### 4. Partner
- **New Role**: External partner/contractor
- **Access**: Limited customer operations
- **Capabilities**:
  - View assigned customer configurations
  - Create configurations for assigned customers
  - Limited quote generation
  - Cannot access other partners' data

### Role Implementation Strategy

#### Phase 1: Foundation (Current Iteration)
- Fix customer.id relationships
- Implement basic role structure
- All roles have full privileges (temporary)
- Establish User ↔ Customer mapping

#### Phase 2: Role Restrictions (Future)
- Implement role-based permissions
- Add customer assignment for salesmen/partners
- Restrict data access by role
- Add approval workflows for data entry

### Role Database Design

```sql
-- Add role field to users table
ALTER TABLE users ADD COLUMN role VARCHAR(50) DEFAULT 'customer';

-- Add customer assignments for salesmen/partners
CREATE TABLE user_customer_assignments (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    customer_id INTEGER REFERENCES customers(id),
    created_at TIMESTAMP DEFAULT NOW()
);
```

### Role Enum
```python
class UserRole(str, Enum):
    SUPERADMIN = "superadmin"
    SALESMAN = "salesman" 
    DATA_ENTRY = "data_entry"
    PARTNER = "partner"
    CUSTOMER = "customer"  # Default for entry page users
```

## Customer Creation Strategy

### Auto-Creation for Entry Page Users
When a user creates a configuration through the entry page:

1. **Check**: Does user have an associated customer?
2. **Find**: Look up customer by user.email
3. **Create**: If not found, auto-create customer:
   ```python
   customer = Customer(
       contact_person=user.full_name or user.username,
       email=user.email,
       customer_type="residential",
       is_active=True,
       notes=f"Auto-created from user: {user.username}"
   )
   ```

### Business Benefits
- **Proper Data Model**: Configurations owned by business entities
- **Sales Pipeline**: Clear customer → quote → order workflow  
- **Billing Integration**: Customer has tax_id, payment_terms
- **Multi-User Support**: Companies can have multiple user accounts
- **Role Separation**: System users vs business customers

## Migration Strategy

### 1. Update Entry Service
- Add `_get_or_create_customer_for_user()` method
- Use `customer.id` instead of `user.id` in configurations
- Update authorization checks

### 2. Update Other Services
- Configuration service
- Quote service  
- Order service
- Template service

### 3. Add Role Support
- Add role field to User model
- Create role enum and validation
- Update authentication to include role
- Prepare for future role restrictions

### 4. Update Tests
- Fix integration tests to use proper customer relationships
- Add role-based test scenarios
- Test customer auto-creation logic

## Security Considerations

### Current Access Control
```python
# Users can only see their own configurations
if not user.is_superuser and config.customer_id != user.id:  # ❌ Wrong
    raise AuthorizationException()
```

### Correct Access Control  
```python
# Users can only see configurations of their associated customer
user_customer = await get_customer_for_user(user)
if not user.is_superuser and config.customer_id != user_customer.id:  # ✅ Correct
    raise AuthorizationException()
```

### Future Role-Based Access
```python
# Role-based access control
if user.role == UserRole.SALESMAN:
    # Can only see assigned customers
    assigned_customers = await get_assigned_customers(user)
    if config.customer_id not in assigned_customers:
        raise AuthorizationException()
```

## Conclusion

This architecture change establishes:
1. **Proper business model**: Users ≠ Customers
2. **Correct data relationships**: Configurations owned by customers
3. **Scalable RBAC**: Foundation for role-based permissions
4. **Future flexibility**: Support for complex business scenarios

The implementation maintains backward compatibility while fixing fundamental design issues and preparing for advanced role-based access control.