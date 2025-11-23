# Backend API - Postman Collections

This directory contains comprehensive Postman collections for testing all Backend API endpoints.

## 📦 Collections

### 1. **Backend-API.Health.postman_collection.json**
Health check and monitoring endpoints.

**Endpoints:**
- `GET /` - Root endpoint
- `GET /health` - Health check with database status

**Authentication:** None required

---

### 2. **Backend-API.Authentication.postman_collection.json**
User authentication and profile management.

**Endpoints:**
- `POST /api/v1/auth/register` - Register new user
- `POST /api/v1/auth/login` - Login and get JWT token
- `GET /api/v1/auth/me` - Get current user profile
- `POST /api/v1/auth/logout` - Logout user

**Authentication:** Bearer token (except register and login)

**Features:**
- Automatic token storage after login
- Token cleanup after logout
- Rate limiting tests
- Response validation

---

### 3. **Backend-API.Users.postman_collection.json**
User management endpoints.

**Endpoints:**
- `GET /api/v1/users/` - List all users (paginated)
- `GET /api/v1/users/{user_id}` - Get user by ID
- `PATCH /api/v1/users/{user_id}` - Update user
- `DELETE /api/v1/users/{user_id}` - Delete user

**Authentication:** Bearer token required
**Permissions:** Most endpoints require superuser access

**Features:**
- Pagination support
- Cache validation
- Permission checks
- Data validation tests

---

### 4. **Backend-API.Dashboard.postman_collection.json**
Admin dashboard endpoints.

**Endpoints:**
- `GET /api/v1/dashboard/` - Dashboard HTML page
- `GET /api/v1/dashboard/stats` - Real-time statistics (JSON)
- `GET /api/v1/dashboard/data-entry` - Data entry form HTML

**Authentication:** Bearer token required
**Permissions:** Superuser only

**Features:**
- Real-time statistics validation
- HTML response checks
- Timestamp verification

---

### 5. **Backend-API.Export.postman_collection.json**
Data export endpoints.

**Endpoints:**
- `GET /api/v1/export/my-data` - Export own data (GDPR)
- `GET /api/v1/export/users/json` - Export all users (JSON)
- `GET /api/v1/export/users/csv` - Export all users (CSV)

**Authentication:** Bearer token required
**Permissions:** User data export for own data, superuser for all users

**Features:**
- GDPR compliance validation
- CSV format verification
- JSON structure validation
- File download headers check

---

## 🚀 Getting Started

### 1. Import Collections

**Option A: Import all collections**
1. Open Postman
2. Click "Import" button
3. Select all `.json` files from this directory
4. Click "Import"

**Option B: Import individually**
1. Open Postman
2. Click "Import"
3. Select the collection file you want
4. Click "Import"

### 2. Import Environment

1. Click "Import" in Postman
2. Select `Backend-API.Environment.postman_environment.json`
3. Click "Import"
4. Select "Backend API - Local Development" from the environment dropdown

### 3. Configure Environment Variables

The environment includes these variables:

| Variable | Default Value | Description |
|----------|---------------|-------------|
| `base_url` | `http://localhost:8000` | API base URL |
| `access_token` | (empty) | JWT token (auto-populated on login) |
| `superuser_username` | `johwqen_doe` | Superuser username |
| `superuser_password` | `SecurePaswqes123!` | Superuser password |

**To modify:**
1. Click the eye icon (👁️) next to environment dropdown
2. Click "Edit" on "Backend API - Local Development"
3. Update values as needed
4. Click "Save"

---

## 🔐 Authentication Flow

### Quick Start Authentication

1. **Login to get token:**
   - Open "Backend-API.Authentication" collection
   - Run "Login User" request
   - Token is automatically saved to `access_token` variable

2. **Use authenticated endpoints:**
   - All other collections use `{{access_token}}` automatically
   - No manual token copying needed!

3. **Logout when done:**
   - Run "Logout User" request
   - Token is automatically cleared

### Manual Token Setup

If you have a token from elsewhere:

1. Click environment dropdown
2. Select "Backend API - Local Development"
3. Click eye icon (👁️)
4. Click "Edit"
5. Set `access_token` value
6. Click "Save"

---

## 📊 Running Tests

### Run Single Request

1. Select a collection
2. Click on a request
3. Click "Send"
4. View response and test results

### Run Entire Collection

1. Click "..." on collection name
2. Select "Run collection"
3. Click "Run Backend API - [Collection Name]"
4. View test results summary

### Run All Collections (Recommended Order)

1. **Health** - Verify API is running
2. **Authentication** - Login and get token
3. **Users** - Test user management
4. **Dashboard** - Test admin features
5. **Export** - Test data export

---

## ✅ Test Coverage

Each request includes comprehensive tests:

### Standard Tests (All Requests)
- ✅ Status code validation
- ✅ Response time check (< 2s)
- ✅ Response structure validation

### Authentication Tests
- ✅ Token format validation
- ✅ Automatic token storage
- ✅ User data structure
- ✅ Rate limiting

### User Management Tests
- ✅ Pagination validation
- ✅ Data integrity checks
- ✅ Permission validation
- ✅ Cache behavior

### Dashboard Tests
- ✅ Statistics accuracy
- ✅ Real-time updates
- ✅ HTML response validation
- ✅ Timestamp format

### Export Tests
- ✅ GDPR compliance
- ✅ File format validation
- ✅ CSV structure
- ✅ Download headers

---

## 🔧 Troubleshooting

### Issue: "Could not get response"

**Solution:**
1. Verify API is running: `http://localhost:8000/health`
2. Check `base_url` in environment matches your API
3. Ensure no firewall blocking localhost

### Issue: "401 Unauthorized"

**Solution:**
1. Run "Login User" request first
2. Verify `access_token` is set in environment
3. Check token hasn't expired (30 minutes default)
4. Re-login if needed

### Issue: "403 Forbidden"

**Solution:**
1. Endpoint requires superuser access
2. Login with superuser credentials
3. Verify user has `is_superuser: true`

### Issue: "429 Too Many Requests"

**Solution:**
1. Rate limit exceeded
2. Wait for rate limit window to reset
3. Check endpoint rate limits in collection description

### Issue: Tests Failing

**Solution:**
1. Check API is latest version
2. Verify environment variables are set
3. Check response body for error details
4. Ensure database has required data

---

## 📝 Collection Variables

Each collection uses these variables:

### Global Variables
- `{{base_url}}` - API base URL
- `{{access_token}}` - JWT authentication token

### Request-Specific Variables
Some requests use path variables:
- `{{user_id}}` - User ID for user-specific operations

**To set path variables:**
1. Edit the request URL
2. Replace the ID with your desired value
3. Or use `{{variable_name}}` and set in environment

---

## 🎯 Best Practices

### 1. Use Environment Variables
- Never hardcode URLs or tokens
- Use `{{base_url}}` for all requests
- Store sensitive data in environment

### 2. Run Tests Regularly
- Run collections after code changes
- Verify all tests pass before deployment
- Use collection runner for full test suite

### 3. Keep Collections Updated
- Update when API changes
- Add tests for new endpoints
- Document breaking changes

### 4. Organize Requests
- Group related requests in folders
- Use descriptive names
- Add detailed descriptions

### 5. Monitor Performance
- Check response times in tests
- Identify slow endpoints
- Optimize as needed

---

## 📚 Additional Resources

### API Documentation
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`
- OpenAPI JSON: `http://localhost:8000/openapi.json`

### Rate Limits

| Endpoint | Limit | Window |
|----------|-------|--------|
| Register | 5 requests | 1 hour |
| Login | 10 requests | 5 minutes |
| Get User | 20 requests | 1 minute |
| Update User | 10 requests | 1 minute |
| Delete User | 5 requests | 1 minute |
| Get Profile | 30 requests | 1 minute |

### Response Codes

| Code | Meaning | Action |
|------|---------|--------|
| 200 | Success | Request completed successfully |
| 201 | Created | Resource created successfully |
| 204 | No Content | Success with no response body |
| 400 | Bad Request | Check request format |
| 401 | Unauthorized | Login required |
| 403 | Forbidden | Insufficient permissions |
| 404 | Not Found | Resource doesn't exist |
| 409 | Conflict | Duplicate resource |
| 422 | Validation Error | Check request data |
| 429 | Too Many Requests | Rate limit exceeded |
| 500 | Server Error | Contact support |

---

## 🤝 Contributing

### Adding New Requests

1. Open the appropriate collection
2. Right-click folder → "Add Request"
3. Configure request details
4. Add tests in "Tests" tab
5. Add description
6. Save

### Adding New Collections

1. Create new collection
2. Follow naming convention: `Backend-API.[Feature].postman_collection.json`
3. Add comprehensive tests
4. Document in this README
5. Export and commit

---

## 📞 Support

### Issues
- Check troubleshooting section above
- Review API documentation
- Check application logs

### Questions
- Review endpoint descriptions
- Check test scripts for examples
- Consult API documentation

---

## 📄 License

These Postman collections are part of the Backend API project.

---

## 🔄 Version History

### v1.0.0 (2025-11-23)
- ✅ Initial release
- ✅ 5 comprehensive collections
- ✅ 18 total endpoints
- ✅ Full test coverage
- ✅ Environment configuration
- ✅ Complete documentation

---

**Happy Testing! 🚀**
