# Data Export API

## Overview

The export API provides endpoints for exporting user data in various formats (JSON, CSV) with proper permission controls and GDPR compliance.

## Endpoints

### Export My Data (GDPR Compliance)

**Endpoint**: `GET /api/v1/export/my-data`  
**Authentication**: Required  
**Permission**: Any authenticated user  
**Response Format**: JSON

Export the authenticated user's personal data for GDPR compliance.

**Example Request**:
```bash
curl -X GET "http://localhost:8000/api/v1/export/my-data" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Example Response**:
```json
{
  "id": 1,
  "email": "user@example.com",
  "username": "john_doe",
  "full_name": "John Doe",
  "is_active": true,
  "is_superuser": false,
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-01T00:00:00Z"
}
```

### Export All Users (JSON)

**Endpoint**: `GET /api/v1/export/users/json`  
**Authentication**: Required  
**Permission**: Superuser only  
**Response Format**: JSON

Export all users data in JSON format.

**Example Request**:
```bash
curl -X GET "http://localhost:8000/api/v1/export/users/json" \
  -H "Authorization: Bearer SUPERUSER_TOKEN"
```

**Example Response**:
```json
{
  "exported_at": "2024-01-01T12:00:00Z",
  "total_users": 2,
  "users": [
    {
      "id": 1,
      "email": "user1@example.com",
      "username": "user1",
      "full_name": "User One",
      "is_active": true,
      "is_superuser": false,
      "created_at": "2024-01-01T00:00:00Z",
      "updated_at": "2024-01-01T00:00:00Z"
    },
    {
      "id": 2,
      "email": "admin@example.com",
      "username": "admin",
      "full_name": "Admin User",
      "is_active": true,
      "is_superuser": true,
      "created_at": "2024-01-01T00:00:00Z",
      "updated_at": "2024-01-01T00:00:00Z"
    }
  ]
}
```

### Export All Users (CSV)

**Endpoint**: `GET /api/v1/export/users/csv`  
**Authentication**: Required  
**Permission**: Superuser only  
**Response Format**: CSV file download

Export all users data as a downloadable CSV file.

**Example Request**:
```bash
curl -X GET "http://localhost:8000/api/v1/export/users/csv" \
  -H "Authorization: Bearer SUPERUSER_TOKEN" \
  -o users_export.csv
```

**CSV Format**:
```csv
id,email,username,full_name,is_active,is_superuser,created_at,updated_at
1,user@example.com,john_doe,John Doe,true,false,2024-01-01T00:00:00Z,2024-01-01T00:00:00Z
2,admin@example.com,admin,Admin User,true,true,2024-01-01T00:00:00Z,2024-01-01T00:00:00Z
```

## Response Models

### Standard Error Response

All endpoints use consistent error response format:

```json
{
  "message": "Error message",
  "details": [
    {
      "detail": "Detailed error description",
      "error_code": "ERROR_CODE",
      "field": "field_name"
    }
  ],
  "request_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

### Common HTTP Status Codes

| Code | Description | Example |
|------|-------------|---------|
| 200 | Success | Data exported successfully |
| 401 | Unauthorized | Missing or invalid token |
| 403 | Forbidden | Insufficient permissions |
| 500 | Server Error | Internal server error |

## Permission Matrix

| Endpoint | Regular User | Superuser |
|----------|--------------|-----------|
| `GET /export/my-data` | ✅ Own data | ✅ Own data |
| `GET /export/users/json` | ❌ | ✅ |
| `GET /export/users/csv` | ❌ | ✅ |

## GDPR Compliance

### Right to Data Portability

The `/export/my-data` endpoint implements GDPR Article 20 (Right to data portability):

- Users can export their personal data
- Data is provided in JSON format (machine-readable)
- No authentication required beyond normal login
- Includes all personal information stored

### Data Included

- User ID
- Email address
- Username
- Full name
- Account status
- Account creation date
- Last update date

### Data Excluded

- Password (hashed or plain)
- Internal system data
- Other users' data

## Usage Examples

### Python (httpx)

```python
import httpx

async def export_my_data(token: str):
    async with httpx.AsyncClient() as client:
        response = await client.get(
            "http://localhost:8000/api/v1/export/my-data",
            headers={"Authorization": f"Bearer {token}"}
        )
        return response.json()

async def export_users_csv(token: str):
    async with httpx.AsyncClient() as client:
        response = await client.get(
            "http://localhost:8000/api/v1/export/users/csv",
            headers={"Authorization": f"Bearer {token}"}
        )
        with open("users_export.csv", "wb") as f:
            f.write(response.content)
```

### JavaScript (fetch)

```javascript
// Export my data
async function exportMyData(token) {
  const response = await fetch('http://localhost:8000/api/v1/export/my-data', {
    headers: {
      'Authorization': `Bearer ${token}`
    }
  });
  return await response.json();
}

// Export users CSV
async function exportUsersCsv(token) {
  const response = await fetch('http://localhost:8000/api/v1/export/users/csv', {
    headers: {
      'Authorization': `Bearer ${token}`
    }
  });
  const blob = await response.blob();
  const url = window.URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = 'users_export.csv';
  a.click();
}
```

### cURL

```bash
# Export my data
curl -X GET "http://localhost:8000/api/v1/export/my-data" \
  -H "Authorization: Bearer YOUR_TOKEN"

# Export users JSON
curl -X GET "http://localhost:8000/api/v1/export/users/json" \
  -H "Authorization: Bearer SUPERUSER_TOKEN"

# Export users CSV
curl -X GET "http://localhost:8000/api/v1/export/users/csv" \
  -H "Authorization: Bearer SUPERUSER_TOKEN" \
  -o users_export.csv
```

## Error Handling

### 401 Unauthorized

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

### 403 Forbidden

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

### 500 Internal Server Error

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

## Best Practices

### For Users

1. **Export regularly** - Keep backups of your data
2. **Verify data** - Check exported data is complete
3. **Secure storage** - Store exported data securely

### For Administrators

1. **Monitor exports** - Track export frequency
2. **Audit logs** - Log all export operations
3. **Rate limiting** - Prevent abuse
4. **Data minimization** - Only export necessary data

## Security Considerations

### Authentication

- All endpoints require valid JWT token
- Tokens must not be expired
- Tokens must belong to active users

### Authorization

- Regular users can only export their own data
- Superusers can export all users data
- Permission checks are enforced at service layer

### Data Protection

- Passwords are never included in exports
- Sensitive data is filtered
- Exports are logged for audit

## Testing

See [test_export.py](../tests/integration/test_export.py) for comprehensive tests:

```bash
# Run export tests
pytest tests/integration/test_export.py -v

# Test specific endpoint
pytest tests/integration/test_export.py::TestExportMyDataEndpoint -v
```

## References

- [GDPR Article 20](https://gdpr-info.eu/art-20-gdpr/)
- [OpenAPI Documentation](http://localhost:8000/docs)
- [Response Models](./RESPONSE_MODELS.md)
