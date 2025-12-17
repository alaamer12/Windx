# RBAC-First Template Enhancement Design

## Overview

This design document outlines a pragmatic approach to enhancing Windx HTML templates with comprehensive RBAC integration while leveraging the existing robust authorization system. Instead of a complete refactoring, this solution focuses on systematic RBAC integration and selective component creation for the most common patterns.

The enhancement addresses current issues including:
- Inconsistent RBAC permission checks across templates
- Manual permission checking in each template
- Duplicated RBAC logic in template rendering
- Lack of systematic template context injection
- Missing RBAC helpers in template context

## Architecture

### RBAC-First Template Middleware

The core architecture centers around automatic RBAC context injection:

```python
class RBACTemplateMiddleware:
    """Middleware for automatic RBAC context injection into templates."""
    
    def __init__(self, templates: Jinja2Templates):
        self.templates = templates
        self.rbac_service = RBACService()
    
    async def render_with_rbac(self, template_name: str, request: Request, context: dict = None):
        """Render template with automatic RBAC context injection."""
        user = get_current_user(request)
        
        rbac_helper = RBACHelper(user)
        
        enhanced_context = {
            **(context or {}),
            'current_user': user,
            'rbac': rbac_helper,
            'can': rbac_helper.can,
            'has': rbac_helper.has
        }
        
        return self.templates.TemplateResponse(template_name, {
            "request": request,
            **enhanced_context
        })
```

### Selective Component Strategy

Focus on creating macros only for the most duplicated patterns:

```
Templates/
├── components/
│   ├── rbac_helpers.html.jinja    # RBAC-aware helper macros
│   ├── navigation.html.jinja      # Navigation components with RBAC
│   ├── tables.html.jinja          # Data table components
│   └── forms.html.jinja           # Form components with permissions
├── admin/                         # Enhanced admin templates
├── dashboard/                     # Enhanced dashboard templates  
└── entry/                         # Enhanced entry templates
```

### Enhanced Base Template System

Improve existing base templates rather than replacing them:

```jinja2
{# Enhanced admin/base.html.jinja with automatic RBAC #}
<!DOCTYPE html>
<html lang="en">
<head>
    <!-- existing head content -->
</head>
<body>
    {% if current_user %}
        {{ rbac_navbar() }}
        {% if has.admin_access() %}
            {{ rbac_sidebar(active_page) }}
        {% endif %}
    {% endif %}
    
    <main class="main-content {% if not has.admin_access() %}no-sidebar{% endif %}">
        {% block content %}{% endblock %}
    </main>
    
    {% block scripts %}{% endblock %}
</body>
</html>
```

### Template Usage Examples

The new API provides a much cleaner and more intuitive syntax:

```jinja2
{# Clean permission checks #}
{% if can('customer:read') %}
    <a href="/customers">View Customers</a>
{% endif %}

{# Convenient CRUD shortcuts #}
{% if can.create('order') %}
    <button>New Order</button>
{% endif %}

{# Role-based UI sections #}
{% if has.role('SUPERADMIN') %}
    <div class="admin-panel">...</div>
{% endif %}

{# Multiple role checks #}
{% if has.any_role('SALESMAN', 'PARTNER') %}
    <div class="sales-tools">...</div>
{% endif %}

{# Resource access checks #}
{% if can.access('customer', customer.id) %}
    <button>Edit Customer</button>
{% endif %}

{# Protected content blocks #}
{% call protected_content('customer:delete', fallback_message='Insufficient permissions') %}
    <button class="btn-danger">Delete Customer</button>
{% endcall %}
```

## Components and Interfaces

### RBAC Helper Components

#### Core RBAC Macros (`components/rbac_helpers.html.jinja`)

```jinja2
{# Simple RBAC-aware button #}
{% macro rbac_button(text, href, permission=None, role=None, class="btn btn-primary", icon=None) %}
  {% if not permission or can(permission) %}
    {% if not role or has.role(role) %}
      <a href="{{ href }}" class="{{ class }}">
        {% if icon %}<i class="{{ icon }}"></i> {% endif %}{{ text }}
      </a>
    {% endif %}
  {% endif %}
{% endmacro %}

{# RBAC-aware navigation item #}
{% macro rbac_nav_item(text, href, permission=None, role=None, active=False, icon=None) %}
  {% if not permission or can(permission) %}
    {% if not role or has.role(role) %}
      <a href="{{ href }}" class="nav-link {% if active %}active{% endif %}">
        {% if icon %}<span class="nav-icon">{{ icon }}</span>{% endif %}
        <span class="nav-text">{{ text }}</span>
      </a>
    {% endif %}
  {% endif %}
{% endmacro %}

{# Protected content wrapper #}
{% macro protected_content(permission=None, role=None, fallback_message=None) %}
  {% if not permission or can(permission) %}
    {% if not role or has.role(role) %}
      {{ caller() }}
    {% elif fallback_message %}
      <div class="text-gray-500 italic">{{ fallback_message }}</div>
    {% endif %}
  {% elif fallback_message %}
    <div class="text-gray-500 italic">{{ fallback_message }}</div>
  {% endif %}
{% endmacro %}
```

#### Enhanced Navigation (`components/navigation.html.jinja`)

```jinja2
{# RBAC-aware sidebar using existing structure #}
{% macro rbac_sidebar(active_page=None) %}
  <aside class="sidebar">
    <div class="sidebar-header">
      <a href="/api/v1/admin/dashboard" class="logo">WindX Admin</a>
    </div>
    
    <nav class="sidebar-nav">
      {{ rbac_nav_item('Dashboard', '/api/v1/admin/dashboard', active=(active_page == 'dashboard'), icon='📊') }}
      {{ rbac_nav_item('Manufacturing Types', '/api/v1/admin/manufacturing-types', permission='manufacturing_type:read', active=(active_page == 'manufacturing'), icon='🏭') }}
      {{ rbac_nav_item('Hierarchy Editor', '/api/v1/admin/hierarchy', permission='attribute_node:read', active=(active_page == 'hierarchy'), icon='🌳') }}
      {{ rbac_nav_item('Customers', '/api/v1/admin/customers', permission='customer:read', active=(active_page == 'customers'), icon='👥') }}
      {{ rbac_nav_item('Orders', '/api/v1/admin/orders', permission='order:read', active=(active_page == 'orders'), icon='📦') }}
      {{ rbac_nav_item('Settings', '/api/v1/admin/settings', role='SUPERADMIN', active=(active_page == 'settings'), icon='⚙️') }}
      {{ rbac_nav_item('Documentation', '/api/v1/admin/documentation', active=(active_page == 'documentation'), icon='📚') }}
    </nav>
    
    <div class="sidebar-footer">
      <div class="user-info">
        <span class="user-icon">👤</span>
        <span class="user-name">{{ current_user.username if current_user else 'Admin' }}</span>
      </div>
      <a href="/api/v1/admin/logout" class="logout-btn">Logout</a>
    </div>
  </aside>
{% endmacro %}

{# RBAC-aware navbar #}
{% macro rbac_navbar() %}
  <nav class="navbar">
    <div class="navbar-brand">
      <a href="/api/v1/admin/dashboard" class="logo">WindX Admin</a>
    </div>
    <div class="navbar-user">
      <span class="user-icon">👤</span>
      <span class="user-name">{{ current_user.username if current_user else 'Admin' }}</span>
    </div>
  </nav>
{% endmacro %}
```

#### Enhanced Table Components (`components/tables.html.jinja`)

```jinja2
{# Simple RBAC-aware table actions #}
{% macro rbac_table_actions(item, actions) %}
  <div class="flex justify-end gap-2">
    {% for action in actions %}
      {% if not action.get('permission') or can(action.permission) %}
        {% if not action.get('role') or has.role(action.role) %}
          <a href="{{ action.url.format(id=item.id) if action.url is string else action.url(item) }}" 
             class="btn btn-sm btn-outline"
             title="{{ action.title }}">
            {{ action.icon }}
          </a>
        {% endif %}
      {% endif %}
    {% endfor %}
  </div>
{% endmacro %}

{# Page header with RBAC-aware actions #}
{% macro rbac_page_header(title, subtitle=None, actions=[]) %}
  <div class="page-header">
    <div>
      <h1 class="page-title">{{ title }}</h1>
      {% if subtitle %}
        <p class="text-gray-500 mt-1">{{ subtitle }}</p>
      {% endif %}
    </div>
    {% if actions %}
      <div class="flex gap-2">
        {% for action in actions %}
          {{ rbac_button(action.text, action.href, action.get('permission'), action.get('role'), action.get('class', 'btn btn-primary'), action.get('icon')) }}
        {% endfor %}
      </div>
    {% endif %}
  </div>
{% endmacro %}
```

## Data Models

### Enhanced Template Context System

```python
class Can:
    """Helper class for permission checks in templates."""
    
    def __init__(self, user: User, rbac_service: RBACService):
        self.user = user
        self.rbac_service = rbac_service
    
    def __call__(self, permission: str) -> bool:
        """Check if user has specific permission: can('customer:read')"""
        try:
            resource, action = permission.split(':')
            return asyncio.run(
                self.rbac_service.check_permission(self.user, resource, action)
            )
        except Exception:
            return False
    
    def access(self, resource_type: str, resource_id: int) -> bool:
        """Check if user can access specific resource: can.access('customer', 123)"""
        try:
            return asyncio.run(
                self.rbac_service.check_resource_ownership(
                    self.user, resource_type, resource_id
                )
            )
        except Exception:
            return False
    
    def create(self, resource: str) -> bool:
        """Check if user can create resource: can.create('customer')"""
        return self(f"{resource}:create")
    
    def read(self, resource: str) -> bool:
        """Check if user can read resource: can.read('customer')"""
        return self(f"{resource}:read")
    
    def update(self, resource: str) -> bool:
        """Check if user can update resource: can.update('customer')"""
        return self(f"{resource}:update")
    
    def delete(self, resource: str) -> bool:
        """Check if user can delete resource: can.delete('customer')"""
        return self(f"{resource}:delete")

class Has:
    """Helper class for role checks in templates."""
    
    def __init__(self, user: User):
        self.user = user
    
    def role(self, role: str) -> bool:
        """Check if user has specific role: has.role('SALESMAN')"""
        return self.user.role == role or self.user.role == 'SUPERADMIN'
    
    def any_role(self, *roles: str) -> bool:
        """Check if user has any of the specified roles: has.any_role('SALESMAN', 'PARTNER')"""
        return any(self.role(role) for role in roles)
    
    def admin_access(self) -> bool:
        """Check if user has admin-level access: has.admin_access()"""
        return self.role('SUPERADMIN') or self.role('SALESMAN') or self.role('DATA_ENTRY')
    
    def customer_access(self) -> bool:
        """Check if user is a customer: has.customer_access()"""
        return self.role('CUSTOMER')

class RBACHelper:
    """Main RBAC helper that provides Can and Has instances."""
    
    def __init__(self, user: User):
        self.user = user
        self.rbac_service = RBACService()
        self.can = Can(user, self.rbac_service)
        self.has = Has(user)

# Global template middleware instance
rbac_templates = RBACTemplateMiddleware(templates)

# Enhanced route decorator pattern
def rbac_route(permission: str = None, role: str = None):
    """Decorator for routes with automatic RBAC template rendering."""
    def decorator(func):
        @wraps(func)
        async def wrapper(request: Request, *args, **kwargs):
            user = get_current_user(request)
            
            # Apply RBAC check if specified
            if permission and not await rbac_service.check_permission(user, permission):
                raise HTTPException(403, "Insufficient permissions")
            if role and not (user.role == role or user.role == 'SUPERADMIN'):
                raise HTTPException(403, "Insufficient role")
            
            # Call original function
            result = await func(request, user, *args, **kwargs)
            
            # If result is a template response, enhance with RBAC
            if isinstance(result, dict) and 'template' in result:
                return await rbac_templates.render_with_rbac(
                    result['template'], request, result.get('context', {})
                )
            
            return result
        return wrapper
    return decorator
```

### Simplified Action Configuration

```python
@dataclass
class PageAction:
    """Simple configuration for page actions."""
    text: str
    href: str
    permission: Optional[str] = None
    role: Optional[str] = None
    class_: str = "btn btn-primary"
    icon: Optional[str] = None

@dataclass
class TableAction:
    """Simple configuration for table row actions."""
    title: str
    icon: str
    url: Union[str, Callable[[Any], str]]  # Format string or function
    permission: Optional[str] = None
    role: Optional[str] = None
```

## Data Flow Through the System

### Enhanced Route Pattern

```python
# Before: Manual RBAC and template rendering
@router.get("/customers")
@require(Permission("customer", "read"))
async def list_customers(request: Request, user: User = Depends(get_current_user)):
    customers = await customer_service.get_all()
    return templates.TemplateResponse("admin/customers_list.html.jinja", {
        "request": request,
        "customers": customers,
        "current_user": user  # Manual context injection
    })

# After: Automatic RBAC context injection
@router.get("/customers")
@require(Permission("customer", "read"))
async def list_customers(request: Request, user: User = Depends(get_current_user)):
    customers = await customer_service.get_accessible_customers(user)
    return await rbac_templates.render_with_rbac("admin/customers_list.html.jinja", request, {
        "customers": customers,
        "page_actions": [
            PageAction("New Customer", "/api/v1/admin/customers/new", permission="customer:create", icon="➕")
        ]
    })
```

### Template Enhancement Flow

```
1. Route Handler (Enhanced)
   ├── Apply existing @require decorators
   ├── Get filtered data based on user permissions
   ├── Define page-specific actions with RBAC
   └── Use rbac_templates.render_with_rbac()

2. RBAC Template Middleware
   ├── Extract user from request
   ├── Create RBAC helper functions (can, has_role, can_access)
   ├── Inject enhanced context automatically
   └── Render template with full RBAC context

3. Enhanced Templates
   ├── Use RBAC helper macros (rbac_button, rbac_nav_item)
   ├── Apply conditional rendering with can() and has_role()
   ├── Leverage existing styling and structure
   └── Generate RBAC-aware HTML
```

### Migration Strategy

```python
# Step 1: Create RBAC middleware
rbac_templates = RBACTemplateMiddleware(templates)

# Step 2: Update routes incrementally
# Old route (keep working)
@router.get("/manufacturing-types")
async def old_route(request: Request):
    return templates.TemplateResponse("admin/manufacturing_list.html.jinja", {...})

# New route (enhanced)
@router.get("/manufacturing-types-new")
async def new_route(request: Request, user: User = Depends(get_current_user)):
    return await rbac_templates.render_with_rbac("admin/manufacturing_list.html.jinja", request, {...})

# Step 3: Update templates to use RBAC macros
# Replace hardcoded navigation with {{ rbac_sidebar(active_page) }}
# Replace action buttons with {{ rbac_button(...) }}
```

## Error Handling

### Permission Denied Scenarios

```jinja2
{# Graceful degradation for missing permissions #}
{% macro protected_content(permission, fallback_message=None) %}
  {% if rbac.has_permission(permission) %}
    {{ caller() }}
  {% elif fallback_message %}
    <div class="text-gray-500 italic">{{ fallback_message }}</div>
  {% endif %}
{% endmacro %}

{# Usage example #}
{% call protected_content('customer:read', 'You do not have permission to view customers') %}
  <div class="customer-list">
    <!-- Customer content here -->
  </div>
{% endcall %}
```

### Component Error Handling

```jinja2
{# Safe component rendering with error boundaries #}
{% macro safe_component(component_name, **kwargs) %}
  {% try %}
    {{ component_name(**kwargs) }}
  {% except %}
    <div class="component-error">
      <i class="fas fa-exclamation-triangle text-yellow-500"></i>
      Component "{{ component_name }}" failed to render
    </div>
  {% endtry %}
{% endmacro %}
```

## Testing Strategy

*A property is a characteristic or behavior that should hold true across all valid executions of a system-essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

Now I need to complete the prework analysis before writing the correctness properties:

<function_calls>
<invoke name="prework">
<parameter name="featureName">template-refactor-rbac

### Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system-essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

Based on the revised RBAC-first approach, the following correctness properties ensure the system works correctly:

**Property 1: RBAC Context Automatic Injection**
*For any* template rendered through rbac_templates.render_with_rbac(), RBAC helper objects (can, has) should be available in the template context
**Validates: Requirements 1.1, 6.1**

**Property 2: Navigation RBAC Filtering**
*For any* user and navigation configuration, only menu items the user has permission to access should be rendered by rbac_nav_item macro
**Validates: Requirements 2.1**

**Property 3: Action Button RBAC Filtering**
*For any* user and button configuration, rbac_button macro should only render if the user has the required permission or role
**Validates: Requirements 2.2**

**Property 4: Protected Content Conditional Rendering**
*For any* protected_content macro call, content should only be rendered if the user meets the permission or role requirements
**Validates: Requirements 2.4, 6.2**

**Property 5: Can Helper Function Correctness**
*For any* user and permission string, the can(permission) helper should return the same result as the underlying RBAC service
**Validates: Requirements 6.4**

**Property 6: Has Helper Role Check Consistency**
*For any* user and role string, the has.role(role) helper should return true if the user has that role or is SUPERADMIN
**Validates: Requirements 5.1, 5.2, 5.3, 5.4, 5.5**

**Property 7: Can Helper CRUD Shortcuts**
*For any* resource and CRUD operation, can.create(resource) should be equivalent to can('resource:create')
**Validates: Requirements 6.4**

**Property 8: Can Helper Access Method**
*For any* user, resource type, and resource ID, can.access(resource_type, resource_id) should return the same result as the RBAC service ownership check
**Validates: Requirements 6.4**

**Property 9: Template Backward Compatibility**
*For any* existing template not using RBAC macros, the template should continue to render correctly with enhanced context
**Validates: Requirements 6.1**

**Property 10: RBAC Macro Styling Consistency**
*For any* RBAC macro (rbac_button, rbac_nav_item), the rendered output should use consistent CSS classes and styling
**Validates: Requirements 1.2, 7.1**

**Property 11: Permission Evaluation Safety**
*For any* invalid permission string or RBAC service error, helper functions should fail safely and return false
**Validates: Requirements 6.5**

**Property 12: Template Context Enhancement**
*For any* template rendered with rbac_templates, the context should include current_user, can helper object, and has helper object
**Validates: Requirements 6.1, 6.4**

**Property 13: Incremental Migration Support**
*For any* route using either old templates.TemplateResponse or new rbac_templates.render_with_rbac, the template should render correctly
**Validates: Requirements 1.5**

**Property 14: RBAC Macro Parameter Validation**
*For any* RBAC macro call with invalid parameters, the macro should fail gracefully without breaking the template
**Validates: Requirements 6.5**

### Unit Testing Strategy

The testing approach will combine unit tests for specific component behaviors with property-based tests for universal correctness properties:

**Unit Tests:**
- Component macro rendering with various parameter combinations
- RBAC helper function behavior with different user roles
- Template context injection and inheritance
- Error handling for invalid parameters or missing permissions

**Property-Based Tests:**
- Component consistency across all macro types
- RBAC filtering behavior across all user role combinations
- Template rendering correctness across all component configurations
- Documentation completeness across all component definitions

**Integration Tests:**
- Full page rendering with RBAC context
- Component interaction within complex layouts
- Template inheritance chains with permission checking
- Cross-component styling consistency

The property-based testing framework will use Hypothesis for Python to generate random component configurations, user roles, and template hierarchies to verify that all correctness properties hold across the entire system.

## Implementation Strategy

### Incremental Enhancement Approach

This approach allows for gradual migration without breaking existing functionality:

**Phase 1: RBAC Middleware Foundation**
- Create RBACTemplateMiddleware class
- Implement RBAC helper functions (can, has_role, can_access)
- Set up automatic context injection system
- Test with one existing route

**Phase 2: Core RBAC Macros**
- Create rbac_helpers.html.jinja with basic macros
- Implement rbac_button, rbac_nav_item, protected_content
- Create enhanced navigation components
- Update base templates to use RBAC macros

**Phase 3: Selective Route Migration**
- Migrate high-traffic admin routes to use rbac_templates
- Update corresponding templates to use RBAC macros
- Enhance existing templates rather than replacing them
- Maintain backward compatibility

**Phase 4: Testing and Refinement**
- Add comprehensive tests for RBAC template functionality
- Create documentation for RBAC macro usage
- Performance testing and optimization
- Complete migration of remaining routes

### Benefits of This Approach

1. **Non-Breaking**: Existing templates continue to work
2. **Incremental**: Can be implemented route by route
3. **Testable**: Each phase can be thoroughly tested
4. **Reversible**: Easy to rollback if issues arise
5. **Pragmatic**: Focuses on actual RBAC needs, not theoretical completeness

### Success Metrics

- All admin routes use consistent RBAC checking
- Templates automatically adapt to user permissions
- No manual RBAC context injection required
- Reduced code duplication in templates
- Improved maintainability of permission logic