# Quick Start Guide - Postman Collections

Get up and running with the Backend API Postman collections in 5 minutes!

## 🚀 5-Minute Setup

### Step 1: Import Everything (1 minute)

1. Open Postman
2. Click **"Import"** button (top left)
3. Drag and drop ALL files from the `postman/` directory
4. Click **"Import"**

✅ You should now see:
- 5 Collections (Health, Authentication, Users, Dashboard, Export)
- 1 Environment (Backend API - Local Development)

---

### Step 2: Select Environment (30 seconds)

1. Look for the environment dropdown (top right)
2. Select **"Backend API - Local Development"**
3. Verify `base_url` is set to `http://localhost:8000`

---

### Step 3: Start Your API (1 minute)

```bash
# Make sure your API is running
python -m uvicorn main:app --reload
```

Verify it's running:
- Open browser: `http://localhost:8000/health`
- Should see: `{"status": "healthy", ...}`

---

### Step 4: Test Health (30 seconds)

1. Open **"Backend-API.Health"** collection
2. Click **"Health Check"** request
3. Click **"Send"**

✅ Expected: Status 200, all tests pass ✅

---

### Step 5: Login (1 minute)

1. Open **"Backend-API.Authentication"** collection
2. Click **"Login User"** request
3. Click **"Send"**

✅ Expected:
- Status 200
- Response has `access_token`
- Token automatically saved to environment

---

### Step 6: Test Authenticated Endpoint (1 minute)

1. Stay in **"Backend-API.Authentication"** collection
2. Click **"Get Current User Profile"** request
3. Click **"Send"**

✅ Expected:
- Status 200
- Your user profile data
- All tests pass

---

## 🎉 You're Ready!

You can now:
- ✅ Test all API endpoints
- ✅ Run automated tests
- ✅ Export data
- ✅ Manage users

---

## 📋 Common Workflows

### Workflow 1: Create New User

```
1. Authentication → "Register New User"
   - Edit request body with new user data
   - Send

2. Authentication → "Login User"
   - Use new credentials
   - Send (token auto-saved)

3. Authentication → "Get Current User Profile"
   - Verify new user data
   - Send
```

---

### Workflow 2: View Dashboard Stats

```
1. Authentication → "Login User"
   - Use superuser credentials
   - Send

2. Dashboard → "Get Dashboard Statistics (JSON)"
   - View real-time stats
   - Send

3. Dashboard → "Get Dashboard HTML"
   - View full dashboard
   - Send
```

---

### Workflow 3: Export User Data

```
1. Authentication → "Login User"
   - Use superuser credentials
   - Send

2. Export → "Export All Users (JSON)"
   - Get JSON export
   - Send

3. Export → "Export All Users (CSV)"
   - Download CSV file
   - Send
```

---

### Workflow 4: Manage Users

```
1. Authentication → "Login User"
   - Use superuser credentials
   - Send

2. Users → "List All Users (Paginated)"
   - View all users
   - Send

3. Users → "Get User by ID"
   - Change user_id in URL
   - Send

4. Users → "Update User"
   - Edit request body
   - Send

5. Users → "Delete User"
   - Change user_id in URL
   - Send
```

---

## 🔧 Quick Fixes

### "Could not get response"
```bash
# Check if API is running
curl http://localhost:8000/health

# If not, start it:
python -m uvicorn main:app --reload
```

### "401 Unauthorized"
```
1. Run: Authentication → "Login User"
2. Verify token is saved (check environment variables)
3. Try request again
```

### "403 Forbidden"
```
This endpoint requires superuser access.

1. Logout current user
2. Login with superuser credentials:
   - Username: johwqen_doe
   - Password: SecurePaswqes123!
3. Try request again
```

---

## 📊 Run All Tests

### Option 1: Collection Runner (Recommended)

1. Click "..." on any collection
2. Select "Run collection"
3. Click "Run [Collection Name]"
4. View results

### Option 2: Command Line (Advanced)

```bash
# Install Newman (Postman CLI)
npm install -g newman

# Run a collection
newman run postman/Backend-API.Health.postman_collection.json \
  -e postman/Backend-API.Environment.postman_environment.json

# Run all collections
newman run postman/Backend-API.Health.postman_collection.json -e postman/Backend-API.Environment.postman_environment.json
newman run postman/Backend-API.Authentication.postman_collection.json -e postman/Backend-API.Environment.postman_environment.json
newman run postman/Backend-API.Users.postman_collection.json -e postman/Backend-API.Environment.postman_environment.json
newman run postman/Backend-API.Dashboard.postman_collection.json -e postman/Backend-API.Environment.postman_environment.json
newman run postman/Backend-API.Export.postman_collection.json -e postman/Backend-API.Environment.postman_environment.json
```

---

## 🎯 Pro Tips

### Tip 1: Use Variables
Instead of hardcoding IDs, use variables:
```
URL: {{base_url}}/api/v1/users/{{user_id}}

Then set in environment:
user_id = 1
```

### Tip 2: Chain Requests
Save data from one request to use in another:
```javascript
// In Tests tab of first request:
pm.environment.set("user_id", pm.response.json().id);

// Use in next request:
{{user_id}}
```

### Tip 3: Bulk Testing
Use Collection Runner to test multiple scenarios:
1. Create test data file (CSV/JSON)
2. Run collection with data file
3. Each row = one test run

### Tip 4: Monitor API
Set up Postman Monitor:
1. Click "..." on collection
2. Select "Monitor collection"
3. Set schedule (e.g., every hour)
4. Get alerts if tests fail

---

## 📚 Next Steps

1. ✅ Read full [README.md](README.md) for detailed documentation
2. ✅ Explore API docs: `http://localhost:8000/docs`
3. ✅ Customize collections for your needs
4. ✅ Add new requests as API grows
5. ✅ Set up monitoring for production

---

## 🆘 Need Help?

1. Check [README.md](README.md) troubleshooting section
2. Review API documentation at `/docs`
3. Check application logs
4. Review test scripts in requests

---

**Happy Testing! 🚀**

*Last updated: 2025-11-23*
