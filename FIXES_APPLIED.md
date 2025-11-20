# Test Fixes Applied - Summary

## Issues Fixed

### 1. ✅ Bcrypt/Passlib Compatibility Issue
**Problem**: passlib 1.7.4 incompatible with bcrypt 5.x, causing password hashing to fail during initialization.

**Solution**: Replaced passlib's CryptContext with direct bcrypt usage:
```python
# Before (using passlib)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
return pwd_context.hash(password)

# After (using bcrypt directly)
import bcrypt as _bcrypt
salt = _bcrypt.gensalt()
hashed = _bcrypt.hashpw(password.encode('utf-8'), salt)
return hashed.decode('utf-8')
```

**Files Modified**: `app/core/security.py`

### 2. ✅ Repository Create Method Type Safety
**Problem**: The service was passing a `dict` to `repository.create()`, but the method expects a Pydantic schema with `model_dump()` method.

**Root Cause**: When hashing passwords, we need to:
1. Take `UserCreate` schema (has `password` field)
2. Remove `password` field
3. Add `hashed_password` field
4. This transformation creates a dict, not a schema

**Solution**: Create the User model instance directly in the service (type-safe approach):
```python
# Type-safe approach - Create model directly
user_data = user_in.model_dump(exclude={"password"})
user = User(
    **user_data,
    hashed_password=hashed_password,
)
self.user_repo.db.add(user)
await self.commit()
```

**Why This is Better**:
- ✅ Type-safe: We're creating a proper SQLAlchemy model instance
- ✅ Clear intent: Shows we're transforming the schema (UserCreate → User model)
- ✅ Follows separation of concerns: Service handles business logic (password hashing)
- ✅ Repository stays generic: `create()` method keeps its type contract

**Files Modified**: `app/services/user.py`

### 3. ✅ SQLite In-Memory Database Issue
**Problem**: aiosqlite with `:memory:` creates separate databases per connection.

**Solution**: Changed to file-based test database (`test.db`) with automatic cleanup.

**Files Modified**: `tests/conftest.py`

### 4. ✅ Environment Variable Loading
**Problem**: Tests couldn't load `.env.test` file.

**Solution**: Added `python-dotenv` loading before importing the app.

**Files Modified**: `tests/conftest.py`

### 5. ✅ Model Registration
**Problem**: SQLAlchemy didn't know about User/Session tables.

**Solution**: Imported models in conftest to register them with Base.metadata.

**Files Modified**: `tests/conftest.py`

## Design Pattern: When to Use Repository.create() vs Direct Model Creation

### Use `repository.create(schema)` when:
- ✅ The schema fields map 1:1 to model fields
- ✅ No transformation needed
- ✅ Example: Simple CRUD operations

```python
# Good use case
user_in = UserCreate(email="test@example.com", username="test", password="pass123")
user = await user_repo.create(user_in)  # Direct mapping
```

### Use direct model creation when:
- ✅ You need to transform/add fields (like hashing passwords)
- ✅ Schema doesn't match model exactly
- ✅ Business logic requires field manipulation

```python
# Good use case - transformation needed
user_data = user_in.model_dump(exclude={"password"})
user = User(**user_data, hashed_password=hashed_password)
self.user_repo.db.add(user)
```

## Test Results

**All 16 tests passing!** ✅

```
tests/unit/test_user_service.py::TestUserServiceCreateUser::test_create_user_success PASSED
tests/unit/test_user_service.py::TestUserServiceCreateUser::test_create_user_duplicate_email PASSED
tests/unit/test_user_service.py::TestUserServiceCreateUser::test_create_user_duplicate_username PASSED
tests/unit/test_user_service.py::TestUserServiceCreateUser::test_create_user_password_is_hashed PASSED
tests/unit/test_user_service.py::TestUserServiceGetUser::test_get_user_success PASSED
tests/unit/test_user_service.py::TestUserServiceGetUser::test_get_user_not_found PASSED
tests/unit/test_user_service.py::TestUserServiceUpdateUser::test_update_own_user PASSED
tests/unit/test_user_service.py::TestUserServiceUpdateUser::test_update_other_user_as_regular_user PASSED
tests/unit/test_user_service.py::TestUserServiceUpdateUser::test_update_other_user_as_superuser PASSED
tests/unit/test_user_service.py::TestUserServiceUpdateUser::test_update_email_to_existing PASSED
tests/unit/test_user_service.py::TestUserServiceUpdateUser::test_update_username_to_existing PASSED
tests/unit/test_user_service.py::TestUserServiceDeleteUser::test_delete_user_as_superuser PASSED
tests/unit/test_user_service.py::TestUserServiceDeleteUser::test_delete_user_as_regular_user PASSED
tests/unit/test_user_service.py::TestUserServicePermissionCheck::test_get_own_user PASSED
tests/unit/test_user_service.py::TestUserServicePermissionCheck::test_get_other_user_as_regular_user PASSED
tests/unit/test_user_service.py::TestUserServicePermissionCheck::test_get_other_user_as_superuser PASSED

============================= 16 passed in 43.62s =============================
```

## Key Takeaways

1. **Type Safety Matters**: Don't pass dicts when methods expect schemas
2. **Direct Model Creation is OK**: When business logic requires transformation, create models directly
3. **Repository Pattern**: Keep repositories generic, handle transformations in services
4. **Bcrypt Direct Usage**: More reliable than passlib for simple password hashing
5. **Test Database**: Use file-based SQLite for async tests, not in-memory
