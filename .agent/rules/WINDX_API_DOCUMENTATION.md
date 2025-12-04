---
trigger: always_on
---

# Windx API Documentation

Complete API documentation for the Windx product configuration system with request/response examples, authentication requirements, and authorization rules.

## Table of Contents

1. [Authentication & Authorization](#authentication--authorization)
2. [Manufacturing Types API](#manufacturing-types-api)
3. [Attribute Nodes API](#attribute-nodes-api)
4. [Configurations API](#configurations-api)
5. [Templates API](#templates-api)
6. [Quotes API](#quotes-api)
7. [Orders API](#orders-api)
8. [Customers API](#customers-api)
9. [Error Responses](#error-responses)

---

## Authentication & Authorization

### Authentication

All API endpoints require authentication via JWT Bearer token.

**Header Format:**
```http
Authorization: Bearer <your_jwt_token>
```

**Example:**
```http
GET /api/v1/manufacturing-types
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

### Authorization Roles

The Windx API uses role-based access control (RBAC) with the following roles:

| Role | Description | Permissions |
|------|-------------|-------------|
| **User** | Regular authenticated user | - View public templates<br>- Create/manage own configurations<br>- Create quotes for own configurations<br>- View own quotes and orders |
| **Superuser** | Administrator | - All user permissions<br>- Manage manufacturing types<br>- Manage attribute nodes<br>- Manage customers<br>- Create/manage templates<br>- View all configurations, quotes, orders |

### Authorization Rules by Endpoint

| Endpoint | Required Role | Notes |
|----------|---------------|-------|
| Manufacturing Types (GET) | User | All authenticated users |
| Manufacturing Types (POST/PATCH/DELETE) | Superuser | Admin only |
| Attribute Nodes (GET) | User | All authenticated users |
| Attribute Nodes (POST/PATCH/DELETE) | Superuser | Admin only |
| Configurations (GET/POST/PATCH/DELETE) | User | Users see only their own |
| Templates (GET) | User | Public templates only |
| Templates (POST) | Superuser | Admin only |
| Templates (Apply) | User | All authenticated users |
| Quotes (GET/POST) | User | Users see only their own |
| Orders (GET/POST) | User | Users see only their own |
| Customers (All) | Superuser | Admin only |

---

## Manufacturing Types API

### List Manufacturing Types

**Endpoint:** `GET /api/v1/manufacturing-types`

**Authentication:** Required (User or Superuser)

**Authorization:** All authenticated users can list manufacturing types

**Description:** List all manufacturing types with optional filtering by active status and category. Supports pagination and sorting.

**Query Parameters:**

| Parameter | Type | Required | Description | Example |
|-----------|------|----------|-------------|---------|
| `page` | integer | No | Page number (default: 1) | `1` |
| `size` | integer | No | Items per page (default: 50, max: 100) | `20` |
| `is_active` | boolean | No | Filter by active status | `true` |
| `base_category` | string | No | Filter by category | `window` |
| `search` | string | No | Search in name/description | `casement` |
| `sort_by` | string | No | Sort column (created_at, name, base_price) | `name` |
| `sort_order` | string | No | Sort direction (asc, desc) | `asc` |

**Request Example:**
```http
GET /api/v1/manufacturing-types?is_active=true&base_category=window&sort_by=name&sort_order=asc
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Success Response (200 OK):**
```json
{
  "items": [
    {
      "id": 1,
      "name": "Casement Window",
      "description": "Energy-efficient casement windows with superior ventilation",
      "base_category": "window",
      "image_url": "/images/casement.jpg",
      "base_price": "200.00",
      "base_weight": "15.00",
      "is_active": true,
      "created_at": "2024-01-01T00:00:00Z",
      "updated_at": "2024-01-01T00:00:00Z"
    },
    {
      "id": 2,
      "name": "Double-Hung Window",
      "description": "Classic double-hung windows with easy cleaning",
      "base_category": "window",
      "image_url": "/images/double-hung.jpg",
      "base_price": "180.00",
      "base_weight": "14.00",
      "is_active": true,
      "created_at": "2024-01-02T00:00:00Z",
      "updated_at": "2024-01-02T00:00:00Z"
    }
  ],
  "total": 10,
  "page": 1,
  "size": 50,
  "pages": 1
}
```

**Error Responses:**

- **401 Unauthorized:** Missing or invalid authentication token
```json
{
  "message": "Could not validate credentials",
  "details": [
    {
      "detail": "Invalid or expired authentication token"
    }
  ]
}
```

- **500 Internal Server Error:** Server error
```json
{
  "message": "Internal Server Error",
  "details": [
    {
      "detail": "An unexpected error occurred. Please try again later."
    }
  ]
}
```

---

### Get Manufacturing Type

**Endpoint:** `GET /api/v1/manufacturing-types/{type_id}`

**Authentication:** Required (User or Superuser)

**Authorization:** All authenticated users can view manufacturing types

**Description:** Get a single manufacturing type by ID with complete details.

**Path Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `type_id` | integer | Yes | Manufacturing type ID |

**Request Example:**
```http
GET /api/v1/manufacturing-types/1
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Success Response (200 OK):**
```json
{
  "id": 1,
  "name": "Casement Window",
  "description": "Energy-efficient casement windows with superior ventilation and modern design",
  "base_category": "window",
  "image_url": "/images/casement.jpg",
  "base_price": "200.00",
  "base_weight": "15.00",
  "is_active": true,
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-01T00:00:00Z"
}
```

**Error Responses:**

- **401 Unauthorized:** Missing or invalid authentication token
- **404 Not Found:** Manufacturing type not found
```json
{
  "message": "Manufacturing type not found"
}
```
- **500 Internal Server Error:** Server error

---

### Create Manufacturing Type

**Endpoint:** `POST /api/v1/manufacturing-types`

**Authentication:** Required (Superuser only)

**Authorization:** Only superusers can create manufacturing types

**Description:** Create a new manufacturing type. The name must be unique.

**Request Body:**
```json
{
  "name": "Sliding Glass Door",
  "description": "Modern sliding glass doors with energy-efficient glazing",
  "base_category": "door",
  "image_url": "/images/sliding-door.jpg",
  "base_price": "450.00",
  "base_weight": "35.00",
  "is_active": true
}
```

**Request Example:**
```http
POST /api/v1/manufacturing-types
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json

{
  "name": "Sliding Glass Door",
  "description": "Modern sliding glass doors with energy-efficient glazing",
  "base_category": "door",
  "base_price": "450.00",
  "base_weight": "35.00"
}
```

**Success Response (201 Created):**
```json
{
  "id": 5,
  "name": "Sliding Glass Door",
  "description": "Modern sliding glass doors with energy-efficient glazing",
  "base_category": "door",
  "image_url": "/images/sliding-door.jpg",
  "base_price": "450.00",
  "base_weight": "35.00",
  "is_active": true,
  "created_at": "2024-01-27T10:30:00Z",
  "updated_at": "2024-01-27T10:30:00Z"
}
```

**Error Responses:**

- **401 Unauthorized:** Missing or invalid authentication token
- **403 Forbidden:** User is not a superuser
```json
{
  "message": "Forbidden",
  "details": [
    {
      "detail": "You don't have permission to access this resource"
    }
  ]
}
```
- **409 Conflict:** Name already exists
```json
{
  "message": "Manufacturing type with this name already exists"
}
```
- **422 Validation Error:** Invalid request data
```json
{
  "message": "Validation Error",
  "details": [
    {
      "detail": "Field is required",
      "field": "name",
      "error_code": "value_error.missing"
    }
  ]
}
```
- **500 Internal Server Error:** Server error

---

### Update Manufacturing Type

**Endpoint:** `PATCH /api/v1/manufacturing-types/{type_id}`

**Authentication:** Required (Superuser only)

**Authorization:** Only superusers can update manufacturing types

**Description:** Update an existing manufacturing type. Only provided fields will be updated.

**Path Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `type_id` | integer | Yes | Manufacturing type ID |

**Request Body (all fields optional):**
```json
{
  "description": "Updated description with new features",
  "base_price": "210.00",
  "base_weight": "15.50",
  "is_active": true
}
```

**Request Example:**
```http
PATCH /api/v1/manufacturing-types/1
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json

{
  "description": "Updated description",
  "base_price": "210.00"
}
```

**Success Response (200 OK):**
```json
{
  "id": 1,
  "name": "Casement Window",
  "description": "Updated description",
  "base_category": "window",
  "image_url": "/images/casement.jpg",
  "base_price": "210.00",
  "base_weight": "15.00",
  "is_active": true,
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-27T10:45:00Z"
}
```

**Error Responses:**

- **401 Unauthorized:** Missing or invalid authentication token
- **403 Forbidden:** User is not a superuser
- **404 Not Found:** Manufacturing type not found
- **409 Conflict:** Name already exists (if name is being updated)
- **422 Validation Error:** Invalid request data
- **500 Internal Server Error:** Server error

---

### Delete Manufacturing Type

**Endpoint:** `DELETE /api/v1/manufacturing-types/{type_id}`

**Authentication:** Required (Superuser only)

**Authorization:** Only superusers can delete manufacturing types

**Description:** Soft delete a manufacturing type by setting `is_active` to false. The record remains in the database for historical purposes.

**Path Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `type_id` | integer | Yes | Manufacturing type ID |

**Request Example:**
```http
DELETE /api/v1/manufacturing-types/1
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Success Response (204 No Content):**
```
(No response body)
```

**Error Responses:**

- **401 Unauthorized:** Missing or invalid authentication token
- **403 Forbidden:** User is not a superuser
- **404 Not Found:** Manufacturing type not found
- **500 Internal Server Error:** Server error

---

## Attribute Nodes API

### List Attribute Nodes

**Endpoint:** `GET /api/v1/attribute-nodes`

**Authentication:** Required (User or Superuser)

**Authorization:** All authenticated users can list attribute nodes

**Description:** List attribute nodes with optional filtering by manufacturing type, parent node, and node type.

**Query Parameters:**

| Parameter | Type | Required | Description | Example |
|-----------|------|----------|-------------|---------|
| `page` | integer | No | Page number (default: 1) | `1` |
| `size` | integer | No | Items per page (default: 50) | `20` |
| `manufacturing_type_id` | integer | No | Filter by manufacturing type | `1` |
| `parent_node_id` | integer | No | Filter by parent node (null for root) | `5` |
| `node_type` | string | No | Filter by type (category, attribute, option) | `option` |

**Request Example:**
```http
GET /api/v1/attribute-nodes?manufacturing_type_id=1&node_type=option
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Success Response (200 OK):**
```json
{
  "items": [
    {
      "id": 3,
      "manufacturing_type_id": 1,
      "parent_node_id": 2,
      "name": "Aluminum",
      "node_type": "option",
      "data_type": "string",
      "display_condition": null,
      "validation_rules": null,
      "required": false,
      "price_impact_type": "fixed",
      "price_impact_value": "50.00",
      "price_formula": null,
      "weight_impact": "2.00",
      "weight_formula": null,
      "technical_property_type": null,
      "technical_impact_formula": null,
      "ltree_path": "frame_options.material_type.aluminum",
      "depth": 2,
      "sort_order": 1,
      "ui_component": "radio",
      "description": "Durable aluminum frame",
      "help_text": "Best for coastal areas",
      "created_at": "2024-01-01T00:00:00Z",
      "updated_at": "2024-01-01T00:00:00Z"
    }
  ],
  "total": 50,
  "page": 1,
  "size": 50,
  "pages": 1
}
```

**Error Responses:**

- **401 Unauthorized:** Missing or invalid authentication token
- **500 Internal Server Error:** Server error

---

### Get Attribute Node

**Endpoint:** `GET /api/v1/attribute-nodes/{node_id}`

**Authentication:** Required (User or Superuser)

**Authorization:** All authenticated users can view attribute nodes

**Description:** Get a single attribute node by ID with complete details.

**Path Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `node_id` | integer | Yes | Attribute node ID |

**Request Example:**
```http
GET /api/v1/attribute-nodes/3
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Success Response (200 OK):**
```json
{
  "id": 3,
  "manufacturing_type_id": 1,
  "parent_node_id": 2,
  "name": "Aluminum",
  "node_type": "option",
  "data_type": "string",
  "display_condition": null,
  "validation_rules": null,
  "required": false,
  "price_impact_type": "fixed",
  "price_impact_value": "50.00",
  "price_formula": null,
  "weight_impact": "2.00",
  "weight_formula": null,
  "technical_property_type": null,
  "technical_impact_formula": null,
  "ltree_path": "frame_options.material_type.aluminum",
  "depth": 2,
  "sort_order": 1,
  "ui_component": "radio",
  "description": "Durable aluminum frame material",
  "help_text": "Aluminum is lightweight and corrosion-resistant",
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-01T00:00:00Z"
}
```

**Error Responses:**

- **401 Unauthorized:** Missing or invalid authentication token
- **404 Not Found:** Attribute node not found
- **500 Internal Server Error:** Server error

---

### Get Child Nodes

**Endpoint:** `GET /api/v1/attribute-nodes/{node_id}/children`

**Authentication:** Required (User or Superuser)

**Authorization:** All authenticated users can view child nodes

**Description:** Get direct children of an attribute node.

**Path Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `node_id` | integer | Yes | Parent node ID |

**Request Example:**
```http
GET /api/v1/attribute-nodes/1/children
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Success Response (200 OK):**
```json
[
  {
    "id": 2,
    "manufacturing_type_id": 1,
    "parent_node_id": 1,
    "name": "Material Type",
    "node_type": "attribute",
    "data_type": "string",
    "ltree_path": "frame_options.material_type",
    "depth": 1,
    "sort_order": 1,
    "created_at": "2024-01-01T00:00:00Z",
    "updated_at": "2024-01-01T00:00:00Z"
  }
]
```

**Error Responses:**

- **401 Unauthorized:** Missing or invalid authentication token
- **404 Not Found:** Parent node not found
- **500 Internal Server Error:** Server error

---

### Get Node Subtree

**Endpoint:** `GET /api/v1/attribute-nodes/{node_id}/tree`

**Authentication:** Required (User or Superuser)

**Authorization:** All authenticated users can view node subtrees

**Description:** Get full hierarchical subtree of descendants for an attribute node using LTREE for efficient querying.

**Path Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `node_id` | integer | Yes | Root node ID |

**Request Example:**
```http
GET /api/v1/attribute-nodes/1/tree
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Success Response (200 OK):**
```json
[
  {
    "id": 1,
    "name": "Frame Options",
    "node_type": "category",
    "ltree_path": "frame_options",
    "depth": 0,
    "children": [
      {
        "id": 2,
        "name": "Material Type",
        "node_type": "attribute",
        "ltree_path": "frame_options.material_type",
        "depth": 1,
        "children": [
          {
            "id": 3,
            "name": "Aluminum",
            "node_type": "option",
            "ltree_path": "frame_options.material_type.aluminum",
            "depth": 2,
            "price_impact_value": "50.00",
            "weight_impact": "2.00",
            "children": []
          },
          {
            "id": 4,
            "name": "Vinyl",
            "node_type": "option",
            "ltree_path": "frame_options.material_type.vinyl",
            "depth": 2,
            "price_impact_value": "30.00",
            "weight_impact": "1.50",
            "children": []
          }
        ]
      }
    ]
  }
]
```

**Error Responses:**

- **401 Unauthorized:** Missing or invalid authentication token
- **404 Not Found:** Node not found
- **500 Internal Server Error:** Server error

---

### Create Attribute Node

**Endpoint:** `POST /api/v1/attribute-nodes`

**Authentication:** Required (Superuser only)

**Authorization:** Only superusers can create attribute nodes

**Description:** Create a new attribute node. The LTREE path and depth are automatically calculated based on the parent node.

**Request Body:**
```json
{
  "manufacturing_type_id": 1,
  "parent_node_id": 2,
  "name": "Wood",
  "node_type": "option",
  "data_type": "string",
  "required": false,
  "price_impact_type": "fixed",
  "price_impact_value": "100.00",
  "weight_impact": "3.00",
  "sort_order": 3,
  "ui_component": "radio",
  "description": "Natural wood frame",
  "help_text": "Premium wood option"
}
```

**Request Example:**
```http
POST /api/v1/attribute-nodes
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json

{
  "manufacturing_type_id": 1,
  "parent_node_id": 2,
  "name": "Wood",
  "node_type": "option",
  "data_type": "string",
  "price_impact_type": "fixed",
  "price_impact_value": "100.00",
  "weight_impact": "3.00"
}
```

**Success Response (201 Created):**
```json
{
  "id": 5,
  "manufacturing_type_id": 1,
  "parent_node_id": 2,
  "name": "Wood",
  "node_type": "option",
  "data_type": "string",
  "price_impact_type": "fixed",
  "price_impact_value": "100.00",
  "weight_impact": "3.00",
  "ltree_path": "frame_options.material_type.wood",
  "depth": 2,
  "sort_order": 3,
  "created_at": "2024-01-27T11:00:00Z",
  "updated_at": "2024-01-27T11:00:00Z"
}
```

**Error Responses:**

- **401 Unauthorized:** Missing or invalid authentication token
- **403 Forbidden:** User is not a superuser
- **404 Not Found:** Parent node or manufacturing type not found
- **422 Validation Error:** Invalid request data
- **500 Internal Server Error:** Server error

---

### Update Attribute Node

**Endpoint:** `PATCH /api/v1/attribute-nodes/{node_id}`

**Authentication:** Required (Superuser only)

**Authorization:** Only superusers can update attribute nodes

**Description:** Update an existing attribute node. If parent_node_id is changed, the LTREE path and depth are automatically recalculated for this node and all descendants.

**Path Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `node_id` | integer | Yes | Attribute node ID |

**Request Body (all fields optional):**
```json
{
  "name": "Updated Name",
  "description": "Updated description",
  "price_impact_value": "55.00",
  "weight_impact": "2.20"
}
```

**Request Example:**
```http
PATCH /api/v1/attribute-nodes/3
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json

{
  "price_impact_value": "55.00",
  "description": "Updated aluminum frame description"
}
```

**Success Response (200 OK):**
```json
{
  "id": 3,
  "manufacturing_type_id": 1,
  "parent_node_id": 2,
  "name": "Aluminum",
  "node_type": "option",
  "data_type": "string",
  "price_impact_type": "fixed",
  "price_impact_value": "55.00",
  "weight_impact": "2.00",
  "ltree_path": "frame_options.material_type.aluminum",
  "depth": 2,
  "description": "Updated aluminum frame description",
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-27T11:15:00Z"
}
```

**Error Responses:**

- **401 Unauthorized:** Missing or invalid authentication token
- **403 Forbidden:** User is not a superuser
- **404 Not Found:** Attribute node not found
- **422 Validation Error:** Invalid request data
- **500 Internal Server Error:** Server error

---

### Delete Attribute Node

**Endpoint:** `DELETE /api/v1/attribute-nodes/{node_id}`

**Authentication:** Required (Superuser only)

**Authorization:** Only superusers can delete attribute nodes

**Description:** Delete an attribute node and all its descendants. This is a cascade delete that removes the node and all child nodes from the database.

**Path Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `node_id` | integer | Yes | Attribute node ID |

**Request Example:**
```http
DELETE /api/v1/attribute-nodes/1
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Success Response (204 No Content):**
```
(No response body)
```

**Error Responses:**

- **401 Unauthorized:** Missing or invalid authentication token
- **403 Forbidden:** User is not a superuser
- **404 Not Found:** Attribute node not found
- **500 Internal Server Error:** Server error

---

## Configurations API

### List Configurations

**Endpoint:** `GET /api/v1/configurations`

**Authentication:** Required (User or Superuser)

**Authorization:** 
- Regular users see only their own configurations
- Superusers can see all configurations

**Description:** List user's configurations with optional filtering by manufacturing type and status.

**Query Parameters:**

| Parameter | Type | Required | Description | Example |
|-----------|------|----------|-------------|---------|
| `page` | integer | No | Page number (default: 1) | `1` |
| `size` | integer | No | Items per page (default: 50) | `20` |
| `manufacturing_type_id` | integer | No | Filter by manufacturing type | `1` |
| `status` | string | No | Filter by status (draft, saved, quoted, ordered) | `draft` |

**Request Example:**
```http
GET /api/v1/configurations?status=draft&manufacturing_type_id=1
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Success Response (200 OK):**
```json
{
  "items": [
    {
      "id": 123,
      "manufacturing_type_id": 1,
      "customer_id": 42,
      "name": "Living Room Window",
      "description": "Bay window facing south",
      "status": "draft",
      "reference_code": "WIN-2024-001",
      "base_price": "200.00",
      "total_price": "525.00",
      "calculated_weight": "23.00",
      "calculated_technical_data": {
        "u_value": 0.28,
        "shgc": 0.35
      },
      "created_at": "2024-01-20T09:00:00Z",
      "updated_at": "2024-01-20T14:30:00Z"
    }
  ],
  "total": 10,
  "page": 1,
  "size": 50,
  "pages": 1
}
```

**Error Responses:**

- **401 Unauthorized:** Missing or invalid authentication token
- **500 Internal Server Error:** Server error

---

### Get Configuration

**Endpoint:** `GET /api/v1/configurations/{config_id}`

**Authentication:** Required (User or Superuser)

**Authorization:**
- Users can only access their own configurations
- Superusers can access all configurations

**Description:** Get a configuration with all its attribute selections.

**Path Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `config_id` | integer | Yes | Configuration ID |

**Request Example:**
```http
GET /api/v1/configurations/123
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Success Response (200 OK):**
```json
{
  "id": 123,
  "manufacturing_type_id": 1,
  "customer_id": 42,
  "name": "Living Room Window",
  "description": "Bay window facing south",
  "status": "draft",
  "reference_code": "WIN-2024-001",
  "base_price": "200.00",
  "total_price": "525.00",
  "calculated_weight": "23.00",
  "calculated_technical_data": {
    "u_value": 0.28,
    "shgc": 0.35,
    "vt": 0.65
  },
  "created_at": "2024-01-20T09:00:00Z",
  "updated_at": "2024-01-20T14:30:00Z",
  "selections": [
    {
      "id": 1,
      "configuration_id": 123,
      "attribute_node_id": 3,
      "string_value": "Aluminum",
      "numeric_value": null,
      "boolean_value": null,
      "json_value": null,
      "calculated_price_impact": "50.00",
      "calculated_weight_impact": "2.00",
      "calculated_technical_impact": null,
      "selection_path": "frame_options.material_type.aluminum",
      "created_at": "2024-01-20T09:15:00Z"
    },
    {
      "id": 2,
      "configuration_id": 123,
      "attribute_node_id": 12,
      "string_value": null,
      "numeric_value": 48.5,
      "boolean_value": null,
      "json_value": null,
      "calculated_price_impact": "242.50",
      "calculated_weight_impact": "5.00",
      "calculated_technical_impact": null,
      "selection_path": "dimensions.width",
      "created_at": "2024-01-20T09:20:00Z"
    }
  ]
}
```

**Error Responses:**

- **401 Unauthorized:** Missing or invalid authentication token
- **403 Forbidden:** Not authorized to access this configuration
```json
{
  "message": "Forbidden",
  "details": [
    {
      "detail": "You don't have permission to access this resource"
    }
  ]
}
```
- **404 Not Found:** Configuration not found
- **500 Internal Server Error:** Server error

---

### Create Configuration

**Endpoint:** `POST /api/v1/configurations`

**Authentication:** Required (User or Superuser)

**Authorization:** All authenticated users can create configurations

**Description:** Create a new product configuration. The configuration is automatically associated with the authenticated user.

**Request Body:**
```json
{
  "manufacturing_type_id": 1,
  "name": "Living Room Window",
  "description": "Bay window facing south",
  "selections": []
}
```

**Request Example:**
```http
POST /api/v1/configurations
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json

{
  "manufacturing_type_id": 1,
  "name": "Living Room Window",
  "description": "Bay window facing south"
}
```

**Success Response (201 Created):**
```json
{
  "id": 123,
  "manufacturing_type_id": 1,
  "customer_id": 42,
  "name": "Living Room Window",
  "description": "Bay window facing south",
  "status": "draft",
  "reference_code": "WIN-20240127-001",
  "base_price": "200.00",
  "total_price": "200.00",
  "calculated_weight": "15.00",
  "calculated_technical_data": {},
  "created_at": "2024-01-27T12:00:00Z",
  "updated_at": "2024-01-27T12:00:00Z"
}
```

**Error Responses:**

- **401 Unauthorized:** Missing or invalid authentication token
- **404 Not Found:** Manufacturing type not found
- **422 Validation Error:** Invalid request data
- **500 Internal Server Error:** Server error

---

### Update Configuration

**Endpoint:** `PATCH /api/v1/configurations/{config_id}`

**Authentication:** Required (User or Superuser)

**Authorization:**
- Users can only update their own configurations
- Superusers can update all configurations

**Description:** Update configuration name and description. Use the selections endpoint to update attribute selections.

**Path Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `config_id` | integer | Yes | Configuration ID |

**Request Body (all fields optional):**
```json
{
  "name": "Updated Window Name",
  "description": "Updated description",
  "status": "saved"
}
```

**Request Example:**
```http
PATCH /api/v1/configurations/123
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json

{
  "name": "Updated Window Name",
  "description": "Updated description"
}
```

**Success Response (200 OK):**
```json
{
  "id": 123,
  "manufacturing_type_id": 1,
  "customer_id": 42,
  "name": "Updated Window Name",
  "description": "Updated description",
  "status": "draft",
  "reference_code": "WIN-2024-001",
  "base_price": "200.00",
  "total_price": "525.00",
  "calculated_weight": "23.00",
  "calculated_technical_data": {},
  "created_at": "2024-01-20T09:00:00Z",
  "updated_at": "2024-01-27T12:15:00Z"
}
```

**Error Responses:**

- **401 Unauthorized:** Missing or invalid authentication token
- **403 Forbidden:** Not authorized to update this configuration
- **404 Not Found:** Configuration not found
- **422 Validation Error:** Invalid request data
- **500 Internal Server Error:** Server error

---

### Update Configuration Selections

**Endpoint:** `PATCH /api/v1/configurations/{config_id}/selections`

**Authentication:** Required (User or Superuser)

**Authorization:**
- Users can only update selections for their own configurations
- Superusers can update selections for all configurations

**Description:** Update attribute selections for a configuration. This replaces all existing selections with the provided list. The total price and weight are automatically recalculated.

**Path Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `config_id` | integer | Yes | Configuration ID |

**Request Body:**
```json
[
  {
    "attribute_node_id": 3,
    "string_value": "Aluminum"
  },
  {
    "attribute_node_id": 12,
    "numeric_value": 48.5
  },
  {
    "attribute_node_id": 15,
    "boolean_value": true
  }
]
```

**Request Example:**
```http
PATCH /api/v1/configurations/123/selections
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json

[
  {
    "attribute_node_id": 3,
    "string_value": "Aluminum"
  },
  {
    "attribute_node_id": 12,
    "numeric_value": 48.5
  }
]
```

**Success Response (200 OK):**
```json
{
  "id": 123,
  "manufacturing_type_id": 1,
  "customer_id": 42,
  "name": "Living Room Window",
  "description": "Bay window facing south",
  "status": "draft",
  "reference_code": "WIN-2024-001",
  "base_price": "200.00",
  "total_price": "492.50",
  "calculated_weight": "22.00",
  "calculated_technical_data": {},
  "created_at": "2024-01-20T09:00:00Z",
  "updated_at": "2024-01-27T12:30:00Z",
  "selections": [
    {
      "id": 10,
      "configuration_id": 123,
      "attribute_node_id": 3,
      "string_value": "Aluminum",
      "calculated_price_impact": "50.00",
      "calculated_weight_impact": "2.00",
      "selection_path": "frame_options.material_type.aluminum",
      "created_at": "2024-01-27T12:30:00Z"
    },
    {
      "id": 11,
      "configuration_id": 123,
      "attribute_node_id": 12,
      "numeric_value": 48.5,
      "calculated_price_impact": "242.50",
      "calculated_weight_impact": "5.00",
      "selection_path": "dimensions.width",
      "created_at": "2024-01-27T12:30:00Z"
    }
  ]
}
```

**Error Responses:**

- **401 Unauthorized:** Missing or invalid authentication token
- **403 Forbidden:** Not authorized to update this configuration
- **404 Not Found:** Configuration or attribute node not found
- **422 Validation Error:** Invalid request data
- **500 Internal Server Error:** Server error

---

### Delete Configuration

**Endpoint:** `DELETE /api/v1/configurations/{config_id}`

**Authentication:** Required (User or Superuser)

**Authorization:**
- Users can only delete their own configurations
- Superusers can delete all configurations

**Description:** Delete a configuration and all its selections. This is a permanent delete.

**Path Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `config_id` | integer | Yes | Configuration ID |

**Request Example:**
```http
DELETE /api/v1/configurations/123
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Success Response (204 No Content):**
```
(No response body)
```

**Error Responses:**

- **401 Unauthorized:** Missing or invalid authentication token
- **403 Forbidden:** Not authorized to delete this configuration
- **404 Not Found:** Configuration not found
- **500 Internal Server Error:** Server error

---

## Templates API

### List Templates

**Endpoint:** `GET /api/v1/templates`

**Authentication:** Required (User or Superuser)

**Authorization:**
- Regular users see only public templates
- Superusers can see all templates (public and private)

**Description:** List configuration templates with optional filtering by manufacturing type and template type.

**Query Parameters:**

| Parameter | Type | Required | Description | Example |
|-----------|------|----------|-------------|---------|
| `page` | integer | No | Page number (default: 1) | `1` |
| `size` | integer | No | Items per page (default: 50) | `20` |
| `manufacturing_type_id` | integer | No | Filter by manufacturing type | `1` |
| `template_type` | string | No | Filter by type (standard, premium, economy, custom) | `standard` |

**Request Example:**
```http
GET /api/v1/templates?manufacturing_type_id=1&template_type=standard
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Success Response (200 OK):**
```json
{
  "items": [
    {
      "id": 10,
      "name": "Standard Casement Window",
      "description": "Most popular configuration for residential use",
      "manufacturing_type_id": 1,
      "template_type": "standard",
      "is_public": true,
      "usage_count": 47,
      "success_rate": "25.50",
      "estimated_price": "450.00",
      "estimated_weight": "20.00",
      "created_by": 1,
      "is_active": true,
      "created_at": "2024-01-01T00:00:00Z",
      "updated_at": "2024-01-20T00:00:00Z"
    }
  ],
  "total": 15,
  "page": 1,
  "size": 50,
  "pages": 1
}
```

**Error Responses:**

- **401 Unauthorized:** Missing or invalid authentication token
- **500 Internal Server Error:** Server error

---

### Get Template

**Endpoint:** `GET /api/v1/templates/{template_id}`

**Authentication:** Required (User or Superuser)

**Authorization:** All authenticated users can view public templates

**Description:** Get a template with all its pre-configured selections.

**Path Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `template_id` | integer | Yes | Template ID |

**Request Example:**
```http
GET /api/v1/templates/10
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Success Response (200 OK):**
```json
{
  "id": 10,
  "name": "Standard Casement Window",
  "description": "Most popular configuration for residential use",
  "manufacturing_type_id": 1,
  "template_type": "standard",
  "is_public": true,
  "usage_count": 47,
  "success_rate": "25.50",
  "estimated_price": "450.00",
  "estimated_weight": "20.00",
  "created_by": 1,
  "is_active": true,
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-20T00:00:00Z",
  "selections": [
    {
      "id": 1,
      "template_id": 10,
      "attribute_node_id": 4,
      "string_value": "Vinyl",
      "selection_path": "frame_options.material_type.vinyl",
      "created_at": "2024-01-01T00:00:00Z"
    },
    {
      "id": 2,
      "template_id": 10,
      "attribute_node_id": 8,
      "string_value": "Double Pane",
      "selection_path": "glass_options.pane_count.double_pane",
      "created_at": "2024-01-01T00:00:00Z"
    }
  ]
}
```

**Error Responses:**

- **401 Unauthorized:** Missing or invalid authentication token
- **404 Not Found:** Template not found
- **500 Internal Server Error:** Server error

---

### Create Template

**Endpoint:** `POST /api/v1/templates`

**Authentication:** Required (Superuser only)

**Authorization:** Only superusers can create templates

**Description:** Create a new configuration template. Templates can be created from scratch or based on existing configurations.

**Request Body:**
```json
{
  "name": "Premium Energy-Efficient Window",
  "description": "High-performance window with triple-pane glass",
  "manufacturing_type_id": 1,
  "template_type": "premium",
  "is_public": true,
  "estimated_price": "750.00",
  "estimated_weight": "28.00"
}
```

**Request Example:**
```http
POST /api/v1/templates
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json

{
  "name": "Premium Energy-Efficient Window",
  "description": "High-performance window with triple-pane glass",
  "manufacturing_type_id": 1,
  "template_type": "premium",
  "is_public": true
}
```

**Success Response (201 Created):**
```json
{
  "id": 15,
  "name": "Premium Energy-Efficient Window",
  "description": "High-performance window with triple-pane glass",
  "manufacturing_type_id": 1,
  "template_type": "premium",
  "is_public": true,
  "usage_count": 0,
  "success_rate": "0.00",
  "estimated_price": "750.00",
  "estimated_weight": "28.00",
  "created_by": 1,
  "is_active": true,
  "created_at": "2024-01-27T13:00:00Z",
  "updated_at": "2024-01-27T13:00:00Z"
}
```

**Error Responses:**

- **401 Unauthorized:** Missing or invalid authentication token
- **403 Forbidden:** User is not a superuser
- **404 Not Found:** Manufacturing type not found
- **422 Validation Error:** Invalid request data
- **500 Internal Server Error:** Server error

---

### Apply Template

**Endpoint:** `POST /api/v1/templates/{template_id}/apply`

**Authentication:** Required (User or Superuser)

**Authorization:** All authenticated users can apply templates

**Description:** Apply a template to create a new configuration. All template selections are copied to the new configuration, which can then be customized.

**Path Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `template_id` | integer | Yes | Template ID |

**Query Parameters:**

| Parameter | Type | Required | Description | Example |
|-----------|------|----------|-------------|---------|
| `configuration_name` | string | No | Name for the new configuration | `My Custom Window` |

**Request Example:**
```http
POST /api/v1/templates/10/apply?configuration_name=My Custom Window
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Success Response (200 OK):**
```json
{
  "configuration_id": 124,
  "message": "Template applied successfully"
}
```

**Error Responses:**

- **401 Unauthorized:** Missing or invalid authentication token
- **404 Not Found:** Template not found
- **422 Validation Error:** Invalid request data
- **500 Internal Server Error:** Server error

---

## Quotes API

### List Quotes

**Endpoint:** `GET /api/v1/quotes`

**Authentication:** Required (User or Superuser)

**Authorization:**
- Regular users see only their own quotes
- Superusers can see all quotes

**Description:** List user's quotes with optional filtering by status.

**Query Parameters:**

| Parameter | Type | Required | Description | Example |
|-----------|------|----------|-------------|---------|
| `page` | integer | No | Page number (default: 1) | `1` |
| `size` | integer | No | Items per page (default: 50) | `20` |
| `status` | string | No | Filter by status (draft, sent, accepted, expired) | `sent` |

**Request Example:**
```http
GET /api/v1/quotes?status=sent
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Success Response (200 OK):**
```json
{
  "items": [
    {
      "id": 501,
      "configuration_id": 123,
      "customer_id": 42,
      "quote_number": "Q-20240120-001",
      "subtotal": "525.00",
      "tax_rate": "8.50",
      "tax_amount": "44.63",
      "discount_amount": "0.00",
      "total_amount": "569.63",
      "technical_requirements": null,
      "valid_until": "2024-02-19",
      "status": "sent",
      "created_at": "2024-01-20T15:00:00Z",
      "updated_at": "2024-01-20T15:00:00Z"
    }
  ],
  "total": 5,
  "page": 1,
  "size": 50,
  "pages": 1
}
```

**Error Responses:**

- **401 Unauthorized:** Missing or invalid authentication token
- **500 Internal Server Error:** Server error

---

### Get Quote

**Endpoint:** `GET /api/v1/quotes/{quote_id}`

**Authentication:** Required (User or Superuser)

**Authorization:**
- Users can only access their own quotes
- Superusers can access all quotes

**Description:** Get a single quote by ID with complete details.

**Path Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `quote_id` | integer | Yes | Quote ID |

**Request Example:**
```http
GET /api/v1/quotes/501
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Success Response (200 OK):**
```json
{
  "id": 501,
  "configuration_id": 123,
  "customer_id": 42,
  "quote_number": "Q-20240120-001",
  "subtotal": "525.00",
  "tax_rate": "8.50",
  "tax_amount": "44.63",
  "discount_amount": "0.00",
  "total_amount": "569.63",
  "technical_requirements": {
    "installation": "professional",
    "warranty": "10_years"
  },
  "valid_until": "2024-02-19",
  "status": "sent",
  "created_at": "2024-01-20T15:00:00Z",
  "updated_at": "2024-01-20T15:00:00Z"
}
```

**Error Responses:**

- **401 Unauthorized:** Missing or invalid authentication token
- **403 Forbidden:** Not authorized to access this quote
- **404 Not Found:** Quote not found
- **500 Internal Server Error:** Server error

---

### Generate Quote

**Endpoint:** `POST /api/v1/quotes`

**Authentication:** Required (User or Superuser)

**Authorization:**
- Users can only create quotes for their own configurations
- Superusers can create quotes for all configurations

**Description:** Generate a quote from a configuration with automatic price calculation. Creates a configuration snapshot to preserve pricing even if base prices change later.

**Request Body:**
```json
{
  "configuration_id": 123,
  "tax_rate": "8.50",
  "discount_amount": "0.00",
  "technical_requirements": {
    "installation": "professional",
    "warranty": "10_years"
  },
  "valid_days": 30
}
```

**Field Descriptions:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `configuration_id` | integer | Yes | Configuration to quote |
| `tax_rate` | decimal | No | Tax rate percentage (default: 0.00) |
| `discount_amount` | decimal | No | Discount amount (default: 0.00) |
| `technical_requirements` | object | No | Custom technical requirements |
| `valid_days` | integer | No | Quote validity in days (default: 30) |

**Request Example:**
```http
POST /api/v1/quotes
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json

{
  "configuration_id": 123,
  "tax_rate": "8.50",
  "discount_amount": "0.00"
}
```

**Success Response (201 Created):**
```json
{
  "id": 502,
  "configuration_id": 123,
  "customer_id": 42,
  "quote_number": "Q-20250127-002",
  "subtotal": "525.00",
  "tax_rate": "8.50",
  "tax_amount": "44.63",
  "discount_amount": "0.00",
  "total_amount": "569.63",
  "technical_requirements": null,
  "valid_until": "2025-02-26",
  "status": "draft",
  "created_at": "2025-01-27T14:00:00Z",
  "updated_at": "2025-01-27T14:00:00Z"
}
```

**Pricing Calculation:**
```
subtotal = configuration.total_price
tax_amount = subtotal * (tax_rate / 100)
total_amount = subtotal + tax_amount - discount_amount
```

**Error Responses:**

- **401 Unauthorized:** Missing or invalid authentication token
- **403 Forbidden:** Not authorized to create quote for this configuration
- **404 Not Found:** Configuration not found
- **422 Validation Error:** Invalid request data (e.g., negative tax rate or discount)
```json
{
  "message": "Validation Error",
  "details": [
    {
      "detail": "Tax rate must be between 0 and 100",
      "field": "tax_rate",
      "error_code": "value_error.number.not_ge"
    }
  ]
}
```
- **500 Internal Server Error:** Server error

---

## Orders API

### List Orders

**Endpoint:** `GET /api/v1/orders`

**Authentication:** Required (User or Superuser)

**Authorization:**
- Regular users see only their own orders (via quote ownership)
- Superusers can see all orders

**Description:** List user's orders with optional filtering by status.

**Query Parameters:**

| Parameter | Type | Required | Description | Example |
|-----------|------|----------|-------------|---------|
| `page` | integer | No | Page number (default: 1) | `1` |
| `size` | integer | No | Items per page (default: 50) | `20` |
| `status` | string | No | Filter by status (confirmed, production, shipped, installed) | `production` |

**Request Example:**
```http
GET /api/v1/orders?status=production
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Success Response (200 OK):**
```json
{
  "items": [
    {
      "id": 301,
      "quote_id": 501,
      "order_number": "O-20240125-001",
      "order_date": "2024-01-25",
      "required_date": "2024-02-15",
      "status": "production",
      "special_instructions": "Call before delivery",
      "installation_address": {
        "street": "123 Main St",
        "city": "Springfield",
        "state": "IL",
        "zip": "62701",
        "country": "USA"
      },
      "created_at": "2024-01-25T10:00:00Z",
      "updated_at": "2024-01-26T14:30:00Z"
    }
  ],
  "total": 3,
  "page": 1,
  "size": 50,
  "pages": 1
}
```

**Error Responses:**

- **401 Unauthorized:** Missing or invalid authentication token
- **500 Internal Server Error:** Server error

---

### Get Order

**Endpoint:** `GET /api/v1/orders/{order_id}`

**Authentication:** Required (User or Superuser)

**Authorization:**
- Users can only access their own orders
- Superusers can access all orders

**Description:** Get a single order by ID with all order items.

**Path Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `order_id` | integer | Yes | Order ID |

**Request Example:**
```http
GET /api/v1/orders/301
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Success Response (200 OK):**
```json
{
  "id": 301,
  "quote_id": 501,
  "order_number": "O-20240125-001",
  "order_date": "2024-01-25",
  "required_date": "2024-02-15",
  "status": "production",
  "special_instructions": "Call before delivery. Customer prefers morning installation.",
  "installation_address": {
    "street": "123 Main St",
    "city": "Springfield",
    "state": "IL",
    "zip": "62701",
    "country": "USA",
    "contact_name": "John Doe",
    "contact_phone": "555-1234"
  },
  "created_at": "2024-01-25T10:00:00Z",
  "updated_at": "2024-01-26T14:30:00Z",
  "items": [
    {
      "id": 1,
      "order_id": 301,
      "configuration_id": 123,
      "quantity": 3,
      "unit_price": "569.63",
      "total_price": "1708.89",
      "production_status": "in_production",
      "created_at": "2024-01-25T10:00:00Z",
      "updated_at": "2024-01-26T14:30:00Z"
    },
    {
      "id": 2,
      "order_id": 301,
      "configuration_id": 124,
      "quantity": 2,
      "unit_price": "450.00",
      "total_price": "900.00",
      "production_status": "pending",
      "created_at": "2024-01-25T10:00:00Z",
      "updated_at": "2024-01-25T10:00:00Z"
    }
  ]
}
```

**Error Responses:**

- **401 Unauthorized:** Missing or invalid authentication token
- **403 Forbidden:** Not authorized to access this order
- **404 Not Found:** Order not found
- **500 Internal Server Error:** Server error

---

### Create Order

**Endpoint:** `POST /api/v1/orders`

**Authentication:** Required (User or Superuser)

**Authorization:**
- Users can only create orders for their own quotes
- Superusers can create orders for all quotes

**Description:** Create an order from an accepted quote. The quote must be in 'accepted' status and must not already have an order.

**Request Body:**
```json
{
  "quote_id": 501,
  "required_date": "2024-02-15",
  "special_instructions": "Call before delivery",
  "installation_address": {
    "street": "123 Main St",
    "city": "Springfield",
    "state": "IL",
    "zip": "62701",
    "country": "USA",
    "contact_name": "John Doe",
    "contact_phone": "555-1234"
  }
}
```

**Field Descriptions:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `quote_id` | integer | Yes | Quote to convert to order |
| `required_date` | date | No | Requested delivery date |
| `special_instructions` | string | No | Custom instructions for production/delivery |
| `installation_address` | object | No | Delivery/installation address (defaults to customer address) |

**Request Example:**
```http
POST /api/v1/orders
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json

{
  "quote_id": 501,
  "required_date": "2024-02-15",
  "special_instructions": "Call before delivery"
}
```

**Success Response (201 Created):**
```json
{
  "id": 302,
  "quote_id": 501,
  "order_number": "O-20250127-002",
  "order_date": "2025-01-27",
  "required_date": "2024-02-15",
  "status": "confirmed",
  "special_instructions": "Call before delivery",
  "installation_address": {
    "street": "123 Main St",
    "city": "Springfield",
    "state": "IL",
    "zip": "62701",
    "country": "USA"
  },
  "created_at": "2025-01-27T15:00:00Z",
  "updated_at": "2025-01-27T15:00:00Z"
}
```

**Order Status Progression:**
1. `confirmed` - Order placed and confirmed
2. `production` - Items being manufactured
3. `shipped` - Items in transit
4. `installed` - Installation complete

**Error Responses:**

- **401 Unauthorized:** Missing or invalid authentication token
- **403 Forbidden:** Not authorized to create order for this quote
- **404 Not Found:** Quote not found
```json
{
  "message": "Quote not found"
}
```
- **422 Validation Error:** Quote not accepted or order already exists
```json
{
  "message": "Validation Error",
  "details": [
    {
      "detail": "Quote must be in 'accepted' status to create an order",
      "error_code": "INVALID_QUOTE_STATUS"
    }
  ]
}
```
```json
{
  "message": "Validation Error",
  "details": [
    {
      "detail": "An order already exists for this quote",
      "error_code": "ORDER_ALREADY_EXISTS"
    }
  ]
}
```
- **500 Internal Server Error:** Server error

---

## Customers API

### List Customers

**Endpoint:** `GET /api/v1/customers`

**Authentication:** Required (Superuser only)

**Authorization:** Only superusers can list customers

**Description:** List all customers with optional filtering by active status and customer type.

**Query Parameters:**

| Parameter | Type | Required | Description | Example |
|-----------|------|----------|-------------|---------|
| `page` | integer | No | Page number (default: 1) | `1` |
| `size` | integer | No | Items per page (default: 50) | `20` |
| `is_active` | boolean | No | Filter by active status | `true` |
| `customer_type` | string | No | Filter by type (residential, commercial, contractor) | `commercial` |

**Request Example:**
```http
GET /api/v1/customers?is_active=true&customer_type=commercial
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Success Response (200 OK):**
```json
{
  "items": [
    {
      "id": 42,
      "company_name": "ABC Construction",
      "contact_person": "John Doe",
      "email": "john@abc.com",
      "phone": "555-1234",
      "address": {
        "street": "456 Business Ave",
        "city": "Chicago",
        "state": "IL",
        "zip": "60601",
        "country": "USA"
      },
      "customer_type": "commercial",
      "tax_id": "12-3456789",
      "payment_terms": "net_30",
      "is_active": true,
      "notes": "Preferred contractor for large projects",
      "created_at": "2024-01-01T00:00:00Z",
      "updated_at": "2024-01-15T00:00:00Z"
    }
  ],
  "total": 25,
  "page": 1,
  "size": 50,
  "pages": 1
}
```

**Error Responses:**

- **401 Unauthorized:** Missing or invalid authentication token
- **403 Forbidden:** User is not a superuser
- **500 Internal Server Error:** Server error

---

### Get Customer

**Endpoint:** `GET /api/v1/customers/{customer_id}`

**Authentication:** Required (Superuser only)

**Authorization:** Only superusers can view customer details

**Description:** Get a single customer by ID with complete details.

**Path Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `customer_id` | integer | Yes | Customer ID |

**Request Example:**
```http
GET /api/v1/customers/42
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Success Response (200 OK):**
```json
{
  "id": 42,
  "company_name": "ABC Construction",
  "contact_person": "John Doe",
  "email": "john@abc.com",
  "phone": "555-1234",
  "address": {
    "street": "456 Business Ave",
    "suite": "Suite 200",
    "city": "Chicago",
    "state": "IL",
    "zip": "60601",
    "country": "USA"
  },
  "customer_type": "commercial",
  "tax_id": "12-3456789",
  "payment_terms": "net_30",
  "is_active": true,
  "notes": "Preferred contractor for large projects. Volume discount applied.",
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-15T00:00:00Z"
}
```

**Error Responses:**

- **401 Unauthorized:** Missing or invalid authentication token
- **403 Forbidden:** User is not a superuser
- **404 Not Found:** Customer not found
- **500 Internal Server Error:** Server error

---

### Create Customer

**Endpoint:** `POST /api/v1/customers`

**Authentication:** Required (Superuser only)

**Authorization:** Only superusers can create customers

**Description:** Create a new customer. The email must be unique.

**Request Body:**
```json
{
  "company_name": "XYZ Builders",
  "contact_person": "Jane Smith",
  "email": "jane@xyz.com",
  "phone": "555-5678",
  "address": {
    "street": "789 Construction Blvd",
    "city": "Springfield",
    "state": "IL",
    "zip": "62701",
    "country": "USA"
  },
  "customer_type": "contractor",
  "tax_id": "98-7654321",
  "payment_terms": "net_15",
  "notes": "New contractor, requires credit check"
}
```

**Field Descriptions:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `company_name` | string | No | Company name (required for commercial/contractor) |
| `contact_person` | string | Yes | Primary contact name |
| `email` | string | Yes | Unique email address |
| `phone` | string | No | Contact phone number |
| `address` | object | No | Customer address |
| `customer_type` | string | Yes | Type: residential, commercial, contractor |
| `tax_id` | string | No | Tax identification number |
| `payment_terms` | string | No | Payment terms (e.g., net_30, net_15, cod) |
| `notes` | string | No | Internal notes |

**Request Example:**
```http
POST /api/v1/customers
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json

{
  "company_name": "XYZ Builders",
  "contact_person": "Jane Smith",
  "email": "jane@xyz.com",
  "customer_type": "contractor"
}
```

**Success Response (201 Created):**
```json
{
  "id": 43,
  "company_name": "XYZ Builders",
  "contact_person": "Jane Smith",
  "email": "jane@xyz.com",
  "phone": null,
  "address": null,
  "customer_type": "contractor",
  "tax_id": null,
  "payment_terms": null,
  "is_active": true,
  "notes": null,
  "created_at": "2025-01-27T16:00:00Z",
  "updated_at": "2025-01-27T16:00:00Z"
}
```

**Error Responses:**

- **401 Unauthorized:** Missing or invalid authentication token
- **403 Forbidden:** User is not a superuser
- **409 Conflict:** Email already exists
```json
{
  "message": "Customer with this email already exists"
}
```
- **422 Validation Error:** Invalid request data
```json
{
  "message": "Validation Error",
  "details": [
    {
      "detail": "Field is required",
      "field": "email",
      "error_code": "value_error.missing"
    }
  ]
}
```
- **500 Internal Server Error:** Server error

---

### Update Customer

**Endpoint:** `PATCH /api/v1/customers/{customer_id}`

**Authentication:** Required (Superuser only)

**Authorization:** Only superusers can update customers

**Description:** Update an existing customer. Only provided fields will be updated.

**Path Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `customer_id` | integer | Yes | Customer ID |

**Request Body (all fields optional):**
```json
{
  "contact_person": "Jane Doe",
  "phone": "555-9999",
  "payment_terms": "net_30",
  "notes": "Updated payment terms approved"
}
```

**Request Example:**
```http
PATCH /api/v1/customers/42
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json

{
  "phone": "555-9999",
  "payment_terms": "net_30"
}
```

**Success Response (200 OK):**
```json
{
  "id": 42,
  "company_name": "ABC Construction",
  "contact_person": "John Doe",
  "email": "john@abc.com",
  "phone": "555-9999",
  "address": {
    "street": "456 Business Ave",
    "city": "Chicago",
    "state": "IL",
    "zip": "60601",
    "country": "USA"
  },
  "customer_type": "commercial",
  "tax_id": "12-3456789",
  "payment_terms": "net_30",
  "is_active": true,
  "notes": "Preferred contractor for large projects",
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2025-01-27T16:15:00Z"
}
```

**Error Responses:**

- **401 Unauthorized:** Missing or invalid authentication token
- **403 Forbidden:** User is not a superuser
- **404 Not Found:** Customer not found
- **409 Conflict:** Email already exists (if email is being updated)
- **422 Validation Error:** Invalid request data
- **500 Internal Server Error:** Server error

---

## Error Responses

All API endpoints follow a consistent error response format for better error handling and debugging.

### Standard Error Response Format

```json
{
  "message": "Human-readable error message",
  "details": [
    {
      "detail": "Specific error description",
      "error_code": "MACHINE_READABLE_CODE",
      "field": "field_name"
    }
  ],
  "request_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

### Common HTTP Status Codes

| Status Code | Description | When It Occurs |
|-------------|-------------|----------------|
| 200 | OK | Successful GET, PATCH request |
| 201 | Created | Successful POST request |
| 204 | No Content | Successful DELETE request |
| 400 | Bad Request | Malformed request syntax |
| 401 | Unauthorized | Missing or invalid authentication token |
| 403 | Forbidden | Insufficient permissions |
| 404 | Not Found | Resource does not exist |
| 409 | Conflict | Resource conflict (e.g., duplicate email) |
| 422 | Validation Error | Request validation failed |
| 429 | Too Many Requests | Rate limit exceeded |
| 500 | Internal Server Error | Unexpected server error |
| 503 | Service Unavailable | Service temporarily unavailable |

---

### 401 Unauthorized

**When:** Missing or invalid authentication token

**Example Response:**
```json
{
  "message": "Could not validate credentials",
  "details": [
    {
      "detail": "Invalid or expired authentication token"
    }
  ]
}
```

**How to Fix:**
- Ensure you're including the `Authorization` header
- Check that your JWT token is valid and not expired
- Request a new token if expired

---

### 403 Forbidden

**When:** User lacks required permissions

**Example Response:**
```json
{
  "message": "Forbidden",
  "details": [
    {
      "detail": "You don't have permission to access this resource"
    }
  ]
}
```

**Common Causes:**
- Regular user trying to access superuser-only endpoint
- User trying to access another user's resources
- User trying to perform admin operations

---

### 404 Not Found

**When:** Requested resource does not exist

**Example Response:**
```json
{
  "message": "Manufacturing type not found"
}
```

**Common Causes:**
- Invalid ID in URL path
- Resource was deleted
- Typo in endpoint URL

---

### 409 Conflict

**When:** Resource conflict (duplicate, constraint violation)

**Example Response:**
```json
{
  "message": "Manufacturing type with this name already exists"
}
```

**Common Causes:**
- Duplicate email address
- Duplicate name (manufacturing types, templates)
- Unique constraint violation

---

### 422 Validation Error

**When:** Request data fails validation

**Example Response:**
```json
{
  "message": "Validation Error",
  "details": [
    {
      "detail": "Field is required",
      "field": "email",
      "error_code": "value_error.missing"
    },
    {
      "detail": "Value must be greater than 0",
      "field": "base_price",
      "error_code": "value_error.number.not_gt"
    }
  ]
}
```

**Common Validation Errors:**

| Error Code | Description | Example |
|------------|-------------|---------|
| `value_error.missing` | Required field missing | Missing `name` field |
| `value_error.email` | Invalid email format | `invalid-email` |
| `value_error.number.not_gt` | Number not greater than | `base_price` must be > 0 |
| `value_error.number.not_ge` | Number not greater than or equal | `tax_rate` must be >= 0 |
| `value_error.number.not_le` | Number not less than or equal | `tax_rate` must be <= 100 |
| `value_error.str.max_length` | String too long | `name` exceeds 200 chars |
| `value_error.str.min_length` | String too short | `password` less than 8 chars |

---

### 429 Too Many Requests

**When:** Rate limit exceeded

**Example Response:**
```json
{
  "message": "Too Many Requests",
  "details": [
    {
      "detail": "Rate limit exceeded. Please try again later."
    }
  ]
}
```

**Rate Limits:**
- Default: 100 requests per minute per user
- Burst: 20 requests per second

**How to Handle:**
- Implement exponential backoff
- Cache responses when possible
- Reduce request frequency

---

### 500 Internal Server Error

**When:** Unexpected server error

**Example Response:**
```json
{
  "message": "Internal Server Error",
  "details": [
    {
      "detail": "An unexpected error occurred. Please try again later."
    }
  ],
  "request_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

**What to Do:**
- Retry the request after a short delay
- If error persists, contact support with the `request_id`
- Check API status page for known issues

---

### 503 Service Unavailable

**When:** Service temporarily unavailable

**Example Response:**
```json
{
  "message": "Service Unavailable",
  "details": [
    {
      "detail": "The service is temporarily unavailable. Please try again later."
    }
  ]
}
```

**Common Causes:**
- Scheduled maintenance
- Database connection issues
- Service overload

---

## Best Practices

### Authentication

1. **Store tokens securely:** Never store JWT tokens in localStorage (XSS risk). Use httpOnly cookies or secure storage.

2. **Handle token expiration:** Implement automatic token refresh before expiration.

3. **Include token in all requests:**
```javascript
const headers = {
  'Authorization': `Bearer ${token}`,
  'Content-Type': 'application/json'
};
```

### Error Handling

1. **Check status codes:** Always check HTTP status codes before parsing response.

2. **Parse error details:** Use the `details` array for specific error information.

3. **Display user-friendly messages:** Show the `message` field to users, log `details` for debugging.

4. **Implement retry logic:** For 429 and 500 errors, implement exponential backoff.

Example error handling:
```javascript
try {
  const response = await fetch('/api/v1/configurations', {
    headers: { 'Authorization': `Bearer ${token}` }
  });
  
  if (!response.ok) {
    const error = await response.json();
    
    switch (response.status) {
      case 401:
        // Redirect to login
        redirectToLogin();
        break;
      case 403:
        // Show permission error
        showError(error.message);
        break;
      case 422:
        // Show validation errors
        showValidationErrors(error.details);
        break;
      case 429:
        // Retry with backoff
        await retryWithBackoff();
        break;
      default:
        showError(error.message);
    }
    return;
  }
  
  const data = await response.json();
  // Handle success
} catch (err) {
  // Handle network errors
  showError('Network error. Please check your connection.');
}
```

### Pagination

1. **Use appropriate page sizes:** Default is 50, max is 100. Smaller pages for mobile.

2. **Cache results:** Cache paginated results to reduce API calls.

3. **Handle empty results:** Check `total` field to determine if there are results.

### Rate Limiting

1. **Implement client-side throttling:** Don't exceed rate limits.

2. **Use batch operations:** When possible, batch multiple operations.

3. **Cache responses:** Reduce redundant API calls with caching.

---

## API Versioning

The Windx API uses URL-based versioning:

- Current version: `v1`
- Base URL: `/api/v1/`

**Version Support:**
- Current version (v1): Fully supported
- Previous versions: Supported for 12 months after new version release
- Deprecated versions: 6-month notice before removal

**Breaking Changes:**
Breaking changes will only be introduced in new major versions (v2, v3, etc.). Minor updates within a version will be backward compatible.

---

## Support

For API support, please contact:

- **Documentation:** https://docs.windx.example.com
- **API Status:** https://status.windx.example.com
- **Support Email:** api-support@windx.example.com
- **GitHub Issues:** https://github.com/windx/api/issues

---

**Last Updated:** January 27, 2025  
**API Version:** v1.0.0

