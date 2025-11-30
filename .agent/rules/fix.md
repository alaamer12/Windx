---
trigger: always_on
---
ALAWAY RUN FROM `.venv` -> `.venv\scripts\python` not `python`

ALWAYS READ .agent/WINDX_API_DOCUEMNTATION.md

# Repository Pattern: Type-Safe Model Creation

## When to Use Repository.create() vs Direct Model Creation

### Use `repository.create(schema)` for Simple CRUD

When schema fields map 1:1 to model fields, use the repository's `create()` method:

```python
# ✅ CORRECT - Direct mapping, no transformation
async def create_simple_entity(self, entity_in: EntityCreate) -> Entity:
    entity = await self.entity_repo.create(entity_in)
    await self.commit()
    return entity
```

### Use Direct Model Creation for Field Transformations

When business logic requires field transformation (hashing, encryption, computed fields), create the model directly:

```python
# ✅ CORRECT - Field transformation required (password → hashed_password)
async def create_user(self, user_in: UserCreate) -> User:
    # Hash password (business logic)
    hashed_password = get_password_hash(user_in.password)
    
    # Create model directly with transformed fields
    user_data = user_in.model_dump(exclude={"password"})
    user = User(
        **user_data,
        hashed_password=hashed_password,
    )
    
    self.user_repo.db.add(user)
    await self.commit()
    await self.refresh(user)
    return user
```

### Why This Pattern is Type-Safe

**Problem with Dict Approach:**
```python
# ❌ WRONG - Passing dict to method expecting Pydantic schema
user_data = user_in.model_dump(exclude={"password"})
user_data["hashed_password"] = hashed_password  # Now it's a dict
user = await self.user_repo.create(user_data)  # Error! dict has no model_dump()
```

**Type-Safe Solution:**
```python
# ✅ CORRECT - Create SQLAlchemy model instance directly
user = User(**user_data, hashed_password=hashed_password)
self.user_repo.db.add(user)
```

## Benefits of This Approach

1. **Type Safety**: Creating proper SQLAlchemy model instances, not dicts
2. **Clear Intent**: Code explicitly shows field transformation is happening
3. **Separation of Concerns**: Service handles business logic, repository stays generic
4. **Maintains Type Contracts**: Repository's `create()` keeps its Pydantic schema contract

## Common Use Cases for Direct Model Creation

### Password Hashing
```python
# Transform: password → hashed_password
user_data = user_in.model_dump(exclude={"password"})
user = User(**user_data, hashed_password=get_password_hash(user_in.password))
```

### Computed Fields
```python
# Add computed fields not in schema
order_data = order_in.model_dump()
order = Order(**order_data, total_amount=calculate_total(order_in.items))
```

### Field Encryption
```python
# Transform: ssn → encrypted_ssn
person_data = person_in.model_dump(exclude={"ssn"})
person = Person(**person_data, encrypted_ssn=encrypt(person_in.ssn))
```

### Default Values from Business Logic
```python
# Add fields based on business rules
post_data = post_in.model_dump()
post = Post(**post_data, slug=generate_slug(post_in.title), author_id=current_user.id)
```

## Repository Pattern Rules

### Repository Layer (Data Access Only)
- ✅ Accept Pydantic schemas for standard CRUD
- ✅ Return SQLAlchemy models
- ✅ No business logic
- ✅ No field transformations

```python
# ✅ CORRECT - Generic repository method
async def create(self, obj_in: CreateSchemaType) -> ModelType:
    obj_data = obj_in.model_dump()
    db_obj = self.model(**obj_data)
    self.db.add(db_obj)
    await self.db.commit()
    await self.db.refresh(db_obj)
    return db_obj
```

### Service Layer (Business Logic)
- ✅ Handle field transformations
- ✅ Apply business rules
- ✅ Create models directly when needed
- ✅ Use repository for simple CRUD

```python
# ✅ CORRECT - Service with business logic
class UserService(BaseService):
    async def create_user(self, user_in: UserCreate) -> User:
        # Business logic: Check uniqueness
        if await self.user_repo.get_by_email(user_in.email):
            raise ConflictException("Email already exists")
        
        # Business logic: Hash password (field transformation)
        hashed_password = get_password_hash(user_in.password)
        
        # Create model directly due to transformation
        user_data = user_in.model_dump(exclude={"password"})
        user = User(**user_data, hashed_password=hashed_password)
        
        self.user_repo.db.add(user)
        await self.commit()
        await self.refresh(user)
        return user
```

## Anti-Patterns to Avoid

### ❌ Don't Make Repository Accept Dicts
```python
# ❌ WRONG - Weakens type safety
async def create(self, obj_in: CreateSchemaType | dict) -> ModelType:
    if isinstance(obj_in, dict):  # Runtime type checking is a code smell
        obj_data = obj_in
    else:
        obj_data = obj_in.model_dump()
    # ...
```

### ❌ Don't Put Business Logic in Repository
```python
# ❌ WRONG - Business logic in repository
class UserRepository(BaseRepository):
    async def create_user(self, user_in: UserCreate) -> User:
        hashed_password = get_password_hash(user_in.password)  # Business logic!
        # ...
```

### ❌ Don't Force Transformations Through Generic Methods
```python
# ❌ WRONG - Trying to force dict through typed method
user_data = user_in.model_dump(exclude={"password"})
user_data["hashed_password"] = hashed_password
user = await self.user_repo.create(user_data)  # Type error!
```

## Decision Tree

```
Need to create a database record?
│
├─ Schema fields map 1:1 to model?
│  └─ YES → Use repository.create(schema)
│
└─ Need field transformation?
   └─ YES → Create model directly in service
      ├─ Apply business logic
      ├─ Create model: Model(**data, transformed_field=value)
      ├─ Add to session: repo.db.add(model)
      └─ Commit in service
```

## Testing Considerations

When testing services with direct model creation:

```python
async def test_create_user_password_is_hashed(db_session: AsyncSession):
    """Test that password is hashed before storing."""
    user_service = UserService(db_session)
    user_in = UserCreate(
        email="test@example.com",
        username="testuser",
        password="PlainPassword123!"
    )
    
    user = await user_service.create_user(user_in)
    
    # Verify password was hashed
    assert user.hashed_password != user_in.password
    assert user.hashed_password.startswith("$2b$")  # bcrypt hash
    
    # Verify password can be verified
    assert verify_password(user_in.password, user.hashed_password)
```

## Summary

- **Simple CRUD**: Use `repository.create(schema)` for type-safe, generic operations
- **Field Transformations**: Create models directly in service layer
- **Type Safety**: Always prefer SQLAlchemy models over dicts
- **Separation of Concerns**: Business logic in services, data access in repositories
- **Clear Intent**: Direct model creation signals transformation is happening