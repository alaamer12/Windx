# RBAC Template Components

This directory contains reusable Jinja2 macros for building RBAC-aware UI components in the Windx admin dashboard.

## Overview

The component library provides four main categories of macros:

1. **RBAC Helpers** (`rbac_helpers.html.jinja`) - Core RBAC-aware UI elements
2. **Navigation** (`navigation.html.jinja`) - Navigation components with automatic permission filtering
3. **Tables** (`tables.html.jinja`) - Data table components with RBAC-aware actions
4. **Buttons** (`buttons.html.jinja`) - Professional button components with comprehensive styling

## Prerequisites

All macros assume the following context variables are available:

- `current_user` - The authenticated user object
- `can` - Permission checking helper (e.g., `can('customer:read')`)
- `has` - Role checking helper (e.g., `has.role('SUPERADMIN')`)

These are automatically injected by the `RBACTemplateMiddleware`.

## Button Components

### button

Renders a professional button with comprehensive styling and state management.

**Parameters:**
- `text` (required) - Button text to display (default: "Button")
- `type` (optional) - Button type: "button", "submit", "reset" (default: "button")
- `variant` (optional) - Style variant: "primary", "outline", "ghost", "danger", "success", "warning", "tab" (default: "primary")
- `size` (optional) - Size: "xs", "sm", "md", "lg", "xl" (default: "md")
- `href` (optional) - URL to link to (renders as `<a>` instead of `<button>`)
- `onclick` (optional) - JavaScript onclick handler
- `disabled` (optional) - Boolean to disable the button (default: false)
- `loading` (optional) - Boolean to show loading spinner (default: false)
- `icon` (optional) - FontAwesome icon class (e.g., "fas fa-save")
- `icon_position` (optional) - Icon position: "left", "right" (default: "left")
- `icon_only` (optional) - Boolean to show only icon, no text (default: false)
- `class` (optional) - Additional CSS classes
- `style` (optional) - Inline styles
- `id` (optional) - Element ID
- `title` (optional) - Tooltip text
- `target` (optional) - Link target for href buttons (default: "_self")
- `form` (optional) - Form ID for submit buttons
- `alpine_attrs` (optional) - Alpine.js attributes (e.g., '@click="handler()"')
- `data_attrs` (optional) - Data attributes
- `aria_label` (optional) - Accessibility label

**Examples:**

```jinja2
{% from "components/buttons.html.jinja" import button %}

{# Basic buttons #}
{{ button("Save Changes", variant="primary") }}
{{ button("Cancel", variant="outline") }}
{{ button("Delete", variant="danger") }}

{# Buttons with icons #}
{{ button("Save", variant="primary", icon="fas fa-save") }}
{{ button("Download", variant="outline", icon="fas fa-download", icon_position="right") }}
{{ button("Settings", variant="ghost", icon="fas fa-cog", icon_only=true, title="Open Settings") }}

{# Different sizes #}
{{ button("Small", size="sm") }}
{{ button("Large", size="lg") }}

{# States #}
{{ button("Disabled", disabled=true) }}
{{ button("Loading...", loading=true, disabled=true) }}

{# Link buttons #}
{{ button("Go to Dashboard", href="/admin", variant="primary") }}
{{ button("External Link", href="https://example.com", target="_blank") }}

{# Form buttons #}
{{ button("Submit", type="submit", variant="primary") }}
{{ button("Reset", type="reset", variant="outline") }}

{# With Alpine.js #}
{{ button("Save", variant="primary", alpine_attrs='@click="save()" :disabled="saving"') }}

{# With onclick handler #}
{{ button("Confirm", variant="danger", onclick="confirm('Are you sure?')") }}

{# Tab buttons #}
{{ button("Input", variant="tab", icon="fas fa-edit", class="active") }}
{{ button("Preview", variant="tab", icon="fas fa-eye") }}
```

### button_group

Creates a group of buttons with proper spacing and alignment.

**Parameters:**
- `align` (optional) - Alignment: "left", "center", "right" (default: "left")
- `gap` (optional) - Gap size: "xs", "sm", "md", "lg" (default: "md")
- `class` (optional) - Additional CSS classes
- `style` (optional) - Inline styles

**Examples:**

```jinja2
{% from "components/buttons.html.jinja" import button, button_group %}

{# Basic button group #}
{% call button_group() %}
  {{ button("First", variant="outline") }}
  {{ button("Second", variant="outline") }}
  {{ button("Third", variant="primary") }}
{% endcall %}

{# Right-aligned with custom gap #}
{% call button_group(align="right", gap="sm") %}
  {{ button("Cancel", variant="outline") }}
  {{ button("Save", variant="primary") }}
{% endcall %}

{# Form button group #}
{% call button_group(align="right", gap="md", class="pt-4 border-t") %}
  {{ button("Reset", type="reset", variant="outline") }}
  {{ button("Save", type="submit", variant="primary", icon="fas fa-save") }}
{% endcall %}
```

### fab (Floating Action Button)

Creates a floating action button for primary actions.

**Parameters:**
- `text` (required) - Button text (shown on hover)
- `icon` (optional) - FontAwesome icon class (default: "fas fa-plus")
- `onclick` (optional) - JavaScript onclick handler
- `href` (optional) - URL to link to
- `position` (optional) - Position: "bottom-right", "bottom-left", "top-right", "top-left" (default: "bottom-right")
- `class` (optional) - Additional CSS classes
- `style` (optional) - Inline styles

**Examples:**

```jinja2
{% from "components/buttons.html.jinja" import fab %}

{# Basic FAB #}
{{ fab("Add New Item") }}

{# Custom icon and position #}
{{ fab("Create", icon="fas fa-plus", position="bottom-left") }}

{# With onclick handler #}
{{ fab("Quick Action", onclick="openModal()") }}

{# As link #}
{{ fab("New Customer", href="/customers/new") }}
```

## Button Styling System

The button component uses a comprehensive CSS system with the following features:

### Variants
- **Primary**: Blue background, white text - for main actions
- **Outline**: Transparent background, colored border - for secondary actions
- **Ghost**: Transparent background, no border - for subtle actions
- **Danger**: Red background, white text - for destructive actions
- **Success**: Green background, white text - for positive actions
- **Warning**: Orange background, white text - for warning actions
- **Tab**: Transparent background, bottom border - for tab navigation

### Sizes
- **xs**: Extra small (0.25rem padding, 0.75rem font)
- **sm**: Small (0.375rem padding, 0.8125rem font)
- **md**: Medium (0.625rem padding, 0.875rem font) - default
- **lg**: Large (0.75rem padding, 1rem font)
- **xl**: Extra large (1rem padding, 1.125rem font)

### States
- **Normal**: Default interactive state
- **Hover**: Enhanced styling with subtle animations
- **Active**: Pressed state with reduced elevation
- **Disabled**: Reduced opacity, no interactions
- **Loading**: Animated spinner, disabled interactions
- **Focus**: Accessibility-compliant focus indicators

### Features
- Smooth transitions and micro-animations
- Consistent spacing and typography
- Icon support with proper alignment
- Loading states with spinners
- Accessibility compliance (ARIA labels, focus management)
- Alpine.js integration
- Form integration
- Link button support

## RBAC Helpers

### rbac_button

Renders a button/link only if the user has required permissions or role.

**Parameters:**
- `text` (required) - Button text to display
- `href` (required) - URL to link to
- `permission` (optional) - Permission string (e.g., "customer:read")
- `role` (optional) - Role requirement (e.g., "SUPERADMIN")
- `class` (optional) - CSS classes (default: "btn btn-primary")
- `icon` (optional) - Icon to display before text
- `onclick` (optional) - JavaScript onclick handler

**Examples:**

```jinja2
{% from "components/rbac_helpers.html.jinja" import rbac_button %}

{# Simple button with permission check #}
{{ rbac_button("New Customer", "/customers/new", permission="customer:create") }}

{# Button with icon and custom class #}
{{ rbac_button("Settings", "/settings", role="SUPERADMIN", class="btn btn-outline", icon="⚙️") }}

{# Button with onclick handler #}
{{ rbac_button("Delete", "#", permission="customer:delete", class="btn btn-danger", onclick="confirmDelete()") }}
```

### rbac_nav_item

Renders a navigation link only if the user has required permissions or role.

**Parameters:**
- `text` (required) - Navigation item text
- `href` (required) - URL to link to
- `permission` (optional) - Permission string
- `role` (optional) - Role requirement
- `active` (optional) - Boolean indicating active page
- `icon` (optional) - Icon to display
- `badge` (optional) - Badge text (e.g., "Beta", "Soon")
- `disabled` (optional) - Boolean to render as disabled

**Examples:**

```jinja2
{% from "components/rbac_helpers.html.jinja" import rbac_nav_item %}

{# Active navigation item #}
{{ rbac_nav_item("Dashboard", "/dashboard", active=True, icon="📊") }}

{# Navigation item with permission check #}
{{ rbac_nav_item("Customers", "/customers", permission="customer:read", icon="👥") }}

{# Navigation item with badge #}
{{ rbac_nav_item("Orders", "/orders", permission="order:read", icon="📦", badge="Beta") }}

{# Disabled navigation item #}
{{ rbac_nav_item("Reports", "#", icon="📈", badge="Soon", disabled=True) }}
```

### protected_content

Wraps content that should only be visible with required permissions or role.

**Parameters:**
- `permission` (optional) - Permission string
- `role` (optional) - Role requirement
- `fallback_message` (optional) - Message to show when access is denied

**Examples:**

```jinja2
{% from "components/rbac_helpers.html.jinja" import protected_content %}

{# Protect content with permission check #}
{% call protected_content(permission="customer:delete") %}
  <button class="btn-danger">Delete Customer</button>
{% endcall %}

{# Protect content with fallback message #}
{% call protected_content(permission="order:update", fallback_message="You don't have permission to edit orders") %}
  <form>...</form>
{% endcall %}

{# Protect content with role check #}
{% call protected_content(role="SUPERADMIN") %}
  <div class="admin-panel">...</div>
{% endcall %}
```

### rbac_page_header

Renders a page header with title, subtitle, and conditional action buttons.

**Parameters:**
- `title` (required) - Page title
- `subtitle` (optional) - Subtitle text
- `actions` (optional) - List of action configurations

**Action Configuration:**
- `text` - Button text
- `href` - Button URL
- `permission` (optional) - Permission requirement
- `role` (optional) - Role requirement
- `class` (optional) - CSS classes
- `icon` (optional) - Icon to display

**Examples:**

```jinja2
{% from "components/rbac_helpers.html.jinja" import rbac_page_header %}

{# Simple page header #}
{{ rbac_page_header("Manufacturing Types") }}

{# Page header with subtitle #}
{{ rbac_page_header("Customers", subtitle="Manage customer accounts") }}

{# Page header with actions #}
{{ rbac_page_header(
  "Manufacturing Types",
  subtitle="Manage product categories",
  actions=[
    {
      "text": "New Type",
      "href": "/types/new",
      "permission": "manufacturing_type:create",
      "icon": "➕"
    },
    {
      "text": "Import",
      "href": "/types/import",
      "permission": "manufacturing_type:create",
      "class": "btn btn-outline",
      "icon": "📥"
    }
  ]
) }}
```

## Navigation Components

### rbac_sidebar

Renders the admin sidebar with automatic RBAC filtering of menu items.

**Parameters:**
- `active_page` (optional) - String indicating the currently active page

**Examples:**

```jinja2
{% from "components/navigation.html.jinja" import rbac_sidebar %}

{# Render sidebar with active page #}
{{ rbac_sidebar(active_page="dashboard") }}

{# Render sidebar for manufacturing page #}
{{ rbac_sidebar(active_page="manufacturing") }}
```

**Active Page Values:**
- `dashboard` - Dashboard page
- `manufacturing` - Manufacturing Types page
- `hierarchy` - Hierarchy Editor page
- `customers` - Customers page
- `orders` - Orders page
- `settings` - Settings page
- `documentation` - Documentation page

### rbac_navbar

Renders the top navigation bar with user context.

**Parameters:**
None - uses `current_user` from context

**Examples:**

```jinja2
{% from "components/navigation.html.jinja" import rbac_navbar %}

{# Render navbar #}
{{ rbac_navbar() }}
```

## Table Components

### rbac_table_actions

Renders table row action buttons with automatic RBAC filtering.

**Parameters:**
- `item` (required) - The data item (row) being acted upon
- `actions` (required) - List of action configurations

**Action Configuration:**
- `title` - Tooltip text
- `icon` - Icon or text to display
- `url` - URL string with `{id}` placeholder OR callable function
- `permission` (optional) - Permission requirement
- `role` (optional) - Role requirement
- `class` (optional) - CSS classes (default: "btn btn-sm btn-outline")
- `onclick` (optional) - JavaScript onclick handler

**Examples:**

```jinja2
{% from "components/tables.html.jinja" import rbac_table_actions %}

{# Simple table actions #}
{{ rbac_table_actions(customer, [
  {
    "title": "Edit",
    "icon": "✏️",
    "url": "/customers/{id}/edit",
    "permission": "customer:update"
  },
  {
    "title": "Delete",
    "icon": "🗑️",
    "url": "/customers/{id}/delete",
    "permission": "customer:delete",
    "class": "btn btn-sm btn-danger"
  }
]) }}

{# Table actions with onclick handlers #}
{{ rbac_table_actions(type, [
  {
    "title": "Edit",
    "icon": "Edit",
    "url": "/types/{id}/edit",
    "permission": "manufacturing_type:update",
    "class": "btn btn-outline"
  },
  {
    "title": "Hierarchy",
    "icon": "Hierarchy",
    "url": "/hierarchy?type_id={id}",
    "permission": "attribute_node:read",
    "class": "btn btn-outline"
  },
  {
    "title": "Delete",
    "icon": "Delete",
    "url": "#",
    "permission": "manufacturing_type:delete",
    "class": "btn btn-danger",
    "onclick": "confirmDelete({}, '{}')".format(type.id, type.name)
  }
]) }}
```

### rbac_table_header

Renders a table header row with optional sortable columns.

**Parameters:**
- `columns` (required) - List of column configurations

**Column Configuration:**
- `label` - Column header text
- `key` (optional) - Data key for sorting
- `sortable` (optional) - Boolean indicating if sortable
- `align` (optional) - Text alignment ("left", "center", "right")
- `width` (optional) - Width specification

**Examples:**

```jinja2
{% from "components/tables.html.jinja" import rbac_table_header %}

{# Simple table header #}
{{ rbac_table_header([
  {"label": "Name"},
  {"label": "Email"},
  {"label": "Status"},
  {"label": "Actions", "align": "right"}
]) }}

{# Table header with sortable columns #}
{{ rbac_table_header([
  {"label": "Name", "key": "name", "sortable": True},
  {"label": "Created", "key": "created_at", "sortable": True},
  {"label": "Actions", "align": "right", "width": "150px"}
]) }}
```

### empty_state

Renders an empty state message for tables with no data.

**Parameters:**
- `icon` (required) - Emoji or icon to display
- `title` (required) - Main heading text
- `message` (required) - Descriptive message
- `action_text` (optional) - Button text
- `action_href` (optional) - Button URL
- `action_permission` (optional) - Permission for action button

**Examples:**

```jinja2
{% from "components/tables.html.jinja" import empty_state %}

{# Simple empty state #}
{{ empty_state(
  icon="🏭",
  title="No Manufacturing Types",
  message="Create your first product type to get started."
) }}

{# Empty state with action button #}
{{ empty_state(
  icon="👥",
  title="No Customers",
  message="Add your first customer to begin.",
  action_text="Add Customer",
  action_href="/customers/new",
  action_permission="customer:create"
) }}
```

### status_badge

Renders a status badge with appropriate styling.

**Parameters:**
- `status` (required) - Status value (e.g., "active", "inactive")
- `label` (optional) - Custom label (defaults to status)
- `type` (optional) - Badge type ("success", "warning", "error", "info")

**Examples:**

```jinja2
{% from "components/tables.html.jinja" import status_badge %}

{# Simple status badge #}
{{ status_badge("active") }}

{# Status badge with custom label #}
{{ status_badge("pending", label="In Progress", type="warning") }}

{# Status badge with explicit type #}
{{ status_badge("inactive", type="error") }}
```

## Usage in Templates

### Basic Template Structure

```jinja2
{% extends "admin/base.html.jinja" %}

{# Import macros you need #}
{% from "components/rbac_helpers.html.jinja" import rbac_page_header, rbac_button %}
{% from "components/tables.html.jinja" import rbac_table_actions, empty_state, status_badge %}

{% set active_page = "customers" %}

{% block content %}
  {# Page header with actions #}
  {{ rbac_page_header(
    "Customers",
    subtitle="Manage customer accounts",
    actions=[
      {"text": "New Customer", "href": "/customers/new", "permission": "customer:create", "icon": "➕"}
    ]
  ) }}

  <div class="card">
    {% if customers %}
      <table>
        <thead>
          <tr>
            <th>Name</th>
            <th>Email</th>
            <th>Status</th>
            <th style="text-align: right;">Actions</th>
          </tr>
        </thead>
        <tbody>
          {% for customer in customers %}
            <tr>
              <td>{{ customer.name }}</td>
              <td>{{ customer.email }}</td>
              <td>{{ status_badge(customer.status) }}</td>
              <td>
                {{ rbac_table_actions(customer, [
                  {"title": "Edit", "icon": "✏️", "url": "/customers/{id}/edit", "permission": "customer:update"},
                  {"title": "Delete", "icon": "🗑️", "url": "/customers/{id}/delete", "permission": "customer:delete", "class": "btn btn-sm btn-danger"}
                ]) }}
              </td>
            </tr>
          {% endfor %}
        </tbody>
      </table>
    {% else %}
      {{ empty_state(
        icon="👥",
        title="No Customers",
        message="Add your first customer to begin.",
        action_text="Add Customer",
        action_href="/customers/new",
        action_permission="customer:create"
      ) }}
    {% endif %}
  </div>
{% endblock %}
```

## Best Practices

1. **Always use RBAC macros for actions** - Never hardcode action buttons without permission checks
2. **Import only what you need** - Use specific imports to keep templates clean
3. **Use consistent active_page values** - Follow the documented active page naming convention
4. **Provide fallback messages** - Use fallback_message in protected_content for better UX
5. **Test with different roles** - Verify RBAC filtering works correctly for all user roles
6. **Keep action configurations DRY** - Define action lists as variables when reused

## Migration Guide

### Converting Existing Templates

**Before:**
```jinja2
<div class="page-header">
  <h1>Manufacturing Types</h1>
  <a href="/types/new" class="btn btn-primary">+ New Type</a>
</div>
```

**After:**
```jinja2
{% from "components/rbac_helpers.html.jinja" import rbac_page_header %}

{{ rbac_page_header(
  "Manufacturing Types",
  actions=[
    {"text": "New Type", "href": "/types/new", "permission": "manufacturing_type:create", "icon": "➕"}
  ]
) }}
```

**Before:**
```jinja2
<a href="/customers/{{ customer.id }}/edit" class="btn btn-outline">Edit</a>
<button onclick="deleteCustomer({{ customer.id }})" class="btn btn-danger">Delete</button>
```

**After:**
```jinja2
{% from "components/tables.html.jinja" import rbac_table_actions %}

{{ rbac_table_actions(customer, [
  {"title": "Edit", "icon": "Edit", "url": "/customers/{id}/edit", "permission": "customer:update", "class": "btn btn-outline"},
  {"title": "Delete", "icon": "Delete", "url": "#", "permission": "customer:delete", "class": "btn btn-danger", "onclick": "deleteCustomer({})".format(customer.id)}
]) }}
```

## Troubleshooting

### Macros not rendering

**Problem:** Macros don't appear in the rendered page.

**Solution:** Ensure you've imported the macro:
```jinja2
{% from "components/rbac_helpers.html.jinja" import rbac_button %}
```

### Permission checks not working

**Problem:** Elements appear for users without permissions.

**Solution:** Verify that:
1. The route uses `rbac_templates.render_with_rbac()` instead of `templates.TemplateResponse()`
2. The `can` and `has` helpers are available in the template context
3. Permission strings match the RBAC policy definitions

### Styling issues

**Problem:** Components don't match existing design.

**Solution:** 
1. Check that you're using the correct CSS classes
2. Verify that `admin.css` is loaded in the base template
3. Use browser dev tools to inspect the rendered HTML

## Support

For questions or issues with the component library, please refer to:
- Design document: `.kiro/specs/template-refactor-rbac/design.md`
- Requirements: `.kiro/specs/template-refactor-rbac/requirements.md`
- Implementation tasks: `.kiro/specs/template-refactor-rbac/tasks.md`
