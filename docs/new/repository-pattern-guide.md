# Repository Pattern Guide

## Overview

This guide explains when and how to use the repository pattern in the Windx application, with a focus on type-safe model creation and proper separation of concerns.

## Table of Contents

1. [When to Use Repository.create() vs Direct Model Creation](#when-to-use-repositorycreate-vs-direct-model-creation)
2. [Type Safety Benefits](#type-safety-benefits)
3. [Common Use Cases](#common-use-cases)
4. [Decision Tree](#decision-tree)
5. [Examples](#examples)
6. [Anti-Patterns to Avoid](#anti-patterns-to-avoid)

---

## When to Use Repository.create() vs Direct Model Creation

### Use `repository.create(schema)` for Simple CRUD

When schema fields map 1:1 to model fields with no transformation, use the repository's `create()` method:

```python
# ✅ CORRECT - Direct mapping, no transformation
async def create_simple_entity(self, entity_in: EntityCreate) -> Entity:
    entity = await self.entity_repo.create(entity_in)
    await self.commit()
    return entity
```

**When to use:**
- Schema fields match model fields exactly
- No business logic or field transformations needed
- No computed fields or derived values
- Standard CRUD operations

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

**When to use:**
- Field names differ between schema and model
- Values need transformation (hashing, encryption)
- Computed fields need to be added
- Business rules determine field values
- Multiple related entities need to be created together

---

## Type Safety Benefits

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

### Benefits

1. **Type Safety**: Creating proper SQLAlchemy model instances, not dicts
2. **Clear Intent**: Code explicitly shows field transformation is happening
3. **Separation of Concerns**: Service handles business logic, repository stays generic
4. **Maintains Type Contracts**: Repository's `create()` keeps its Pydantic schema contract
5. **IDE Support**: Better autocomplete and type checking
6. **Compile-Time Errors**: Catch errors during development, not runtime

---

## Common Use Cases

### 1. Password Hashing

```python
async def create_user(self, user_in: UserCreate) -> User:
    """Create user with hashed password."""
    # Transform: password → hashed_password
    user_data = user_in.model_dump(exclude={"password"})
    user = User(
        **user_data,
        hashed_password=get_password_hash(user_in.password)
    )
    
    self.user_repo.db.add(user)
    await self.commit()
    await self.refresh(user)
    return user
```

### 2. Computed Fields

```python
async def create_order(self, order_in: OrderCreate) -> Order:
    """Create order with computed total."""
    # Add computed fields not in schema
    order_data = order_in.model_dump()
    order = Order(
        **order_data,
        total_amount=self._calculate_total(order_in.items),
        order_number=self._generate_order_number(),
    )
    
    self.order_repo.db.add(order)
    await self.commit()
    await self.refresh(order)
    return order
```

### 3. Field Encryption

```python
async def create_person(self, person_in: PersonCreate) -> Person:
    """Create person with encrypted SSN."""
    # Transform: ssn → encrypted_ssn
    person_data = person_in.model_dump(exclude={"ssn"})
    person = Person(
        **person_data,
        encrypted_ssn=encrypt(person_in.ssn)
    )
    
    self.person_repo.db.add(person)
    await self.commit()
    await self.refresh(person)
    return person
```

### 4. Default Values from Business Logic

```python
async def create_post(
    self, 
    post_in: PostCreate, 
    current_user: User
) -> Post:
    """Create post with generated slug and author."""
    # Add fields based on business rules
    post_data = post_in.model_dump()
    post = Post(
        **post_data,
        slug=generate_slug(post_in.title),
        author_id=current_user.id,
        published_at=datetime.utcnow() if post_in.publish_now else None,
    )
    
    self.post_repo.db.add(post)
    await self.commit()
    await self.refresh(post)
    return post
```

### 5. Related Entity Creation

```python
async def create_configuration_with_selections(
    self,
    config_in: ConfigurationCreate,
    selections: list[SelectionCreate],
) -> Configuration:
    """Create configuration with initial selections."""
    # Create main entity
    config_data = config_in.model_dump()
    config = Configuration(**config_data)
    
    self.config_repo.db.add(config)
    await self.commit()
    await self.refresh(config)
    
    # Create related entities
    for selection_in in selections:
        selection = ConfigurationSelection(
            configuration_id=config.id,
            **selection_in.model_dump()
        )
        self.selection_repo.db.add(selection)
    
    await self.commit()
    return config
```

---

## Decision Tree

```
Need to create a database record?
│
├─ Schema fields map 1:1 to model?
│  └─ YES → Use repository.create(schema)
│     Example: await repo.create(entity_in)
│
└─ Need field transformation?
   └─ YES → Create model directly in service
      ├─ Apply business logic
      ├─ Create model: Model(**data, transformed_field=value)
      ├─ Add to session: repo.db.add(model)
      └─ Commit in service: await self.commit()
```

### Quick Reference

| Scenario | Method | Example |
|----------|--------|---------|
| Simple CRUD | `repository.create()` | `await repo.create(schema)` |
| Password hashing | Direct creation | `User(**data, hashed_password=hash(pwd))` |
| Computed fields | Direct creation | `Order(**data, total=calculate())` |
| Field encryption | Direct creation | `Person(**data, encrypted=encrypt())` |
| Generated values | Direct creation | `Post(**data, slug=generate())` |
| Related entities | Direct creation | Create parent, then children |

---

## Examples

### Example 1: Simple CRUD (Use Repository)

```python
class ManufacturingTypeService(BaseService):
    """Service for manufacturing type operations."""
    
    async def create_manufacturing_type(
        self,
        mfg_type_in: ManufacturingTypeCreate,
    ) -> ManufacturingType:
        """Create a new manufacturing type.
        
        No field transformations needed - schema maps 1:1 to model.
        """
        # ✅ Use repository.create() for simple CRUD
        mfg_type = await self.mfg_type_repo.create(mfg_type_in)
        await self.commit()
        return mfg_type
```

### Example 2: Field Transformation (Direct Creation)

```python
class UserService(BaseService):
    """Service for user operations."""
    
    async def create_user(
        self,
        user_in: UserCreate,
    ) -> User:
        """Create a new user with hashed password.
        
        Field transformation required: password → hashed_password
        """
        # Check uniqueness (business logic)
        if await self.user_repo.get_by_email(user_in.email):
            raise ConflictException("Email already exists")
        
        # Hash password (field transformation)
        hashed_password = get_password_hash(user_in.password)
        
        # ✅ Create model directly due to transformation
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

### Example 3: Multiple Transformations

```python
class QuoteService(BaseService):
    """Service for quote operations."""
    
    async def create_quote(
        self,
        quote_in: QuoteCreate,
        current_user: User,
    ) -> Quote:
        """Create quote with computed fields and generated number.
        
        Multiple transformations:
        - Generate quote number
        - Calculate tax amount
        - Calculate total amount
        - Set created_by from current user
        """
        # Business logic: validate configuration exists
        config = await self.config_repo.get(quote_in.configuration_id)
        if not config:
            raise NotFoundException("Configuration not found")
        
        # Compute fields
        subtotal = config.total_price
        tax_amount = subtotal * (quote_in.tax_rate / 100)
        total_amount = subtotal + tax_amount - quote_in.discount_amount
        
        # ✅ Create model directly with computed fields
        quote_data = quote_in.model_dump()
        quote = Quote(
            **quote_data,
            quote_number=self._generate_quote_number(),
            subtotal=subtotal,
            tax_amount=tax_amount,
            total_amount=total_amount,
            created_by=current_user.id,
        )
        
        self.quote_repo.db.add(quote)
        await self.commit()
        await self.refresh(quote)
        
        # Create snapshot for price protection
        await self._create_quote_snapshot(quote)
        
        return quote
    
    def _generate_quote_number(self) -> str:
        """Generate unique quote number."""
        from datetime import datetime
        timestamp = datetime.utcnow().strftime("%Y%m%d")
        # In production, use database sequence
        return f"Q-{timestamp}-{random.randint(1000, 9999)}"
```

---

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

**Why it's wrong:**
- Loses type safety
- Requires runtime type checking
- Makes API unclear
- Harder to maintain

### ❌ Don't Put Business Logic in Repository

```python
# ❌ WRONG - Business logic in repository
class UserRepository(BaseRepository):
    async def create_user(self, user_in: UserCreate) -> User:
        hashed_password = get_password_hash(user_in.password)  # Business logic!
        # ...
```

**Why it's wrong:**
- Violates separation of concerns
- Makes repository less reusable
- Harder to test business logic
- Couples data access to business rules

### ❌ Don't Force Transformations Through Generic Methods

```python
# ❌ WRONG - Trying to force dict through typed method
user_data = user_in.model_dump(exclude={"password"})
user_data["hashed_password"] = hashed_password
user = await self.user_repo.create(user_data)  # Type error!
```

**Why it's wrong:**
- Type error (dict vs Pydantic model)
- Loses type safety
- Confusing intent
- Will fail at runtime

### ❌ Don't Mix Patterns in Same Service

```python
# ❌ WRONG - Inconsistent pattern usage
class CustomerService(BaseService):
    async def create_customer(self, customer_in: CustomerCreate):
        # Sometimes using repository.create()
        return await self.customer_repo.create(customer_in)
    
    async def create_premium_customer(self, customer_in: CustomerCreate):
        # Sometimes creating directly
        customer = Customer(**customer_in.model_dump())
        self.customer_repo.db.add(customer)
        await self.commit()
        return customer
```

**Why it's wrong:**
- Inconsistent patterns confuse developers
- Harder to maintain
- No clear reason for different approaches
- Should use same pattern unless transformation needed

---

## Repository Pattern Rules

### Repository Layer (Data Access Only)

**Responsibilities:**
- ✅ Accept Pydantic schemas for standard CRUD
- ✅ Return SQLAlchemy models
- ✅ Handle database operations
- ✅ Provide query methods
- ❌ No business logic
- ❌ No field transformations
- ❌ No validation beyond database constraints

```python
# ✅ CORRECT - Generic repository method
class BaseRepository(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    """Base repository with generic CRUD operations."""
    
    async def create(self, obj_in: CreateSchemaType) -> ModelType:
        """Create new record from Pydantic schema."""
        obj_data = obj_in.model_dump()
        db_obj = self.model(**obj_data)
        self.db.add(db_obj)
        await self.db.commit()
        await self.db.refresh(db_obj)
        return db_obj
    
    async def get(self, id: int) -> ModelType | None:
        """Get record by ID."""
        result = await self.db.execute(
            select(self.model).where(self.model.id == id)
        )
        return result.scalar_one_or_none()
    
    async def get_multi(
        self,
        skip: int = 0,
        limit: int = 100,
    ) -> list[ModelType]:
        """Get multiple records with pagination."""
        result = await self.db.execute(
            select(self.model).offset(skip).limit(limit)
        )
        return list(result.scalars().all())
```

### Service Layer (Business Logic)

**Responsibilities:**
- ✅ Handle field transformations
- ✅ Apply business rules
- ✅ Validate business constraints
- ✅ Create models directly when needed
- ✅ Use repository for simple CRUD
- ✅ Coordinate multiple repositories
- ✅ Handle transactions

```python
# ✅ CORRECT - Service with business logic
class UserService(BaseService):
    """Service for user business logic."""
    
    async def create_user(self, user_in: UserCreate) -> User:
        """Create user with business logic."""
        # Business logic: Check uniqueness
        if await self.user_repo.get_by_email(user_in.email):
            raise ConflictException("Email already exists")
        
        # Business logic: Validate password strength
        if not self._is_strong_password(user_in.password):
            raise ValidationException("Password too weak")
        
        # Business logic: Hash password (field transformation)
        hashed_password = get_password_hash(user_in.password)
        
        # Create model directly due to transformation
        user_data = user_in.model_dump(exclude={"password"})
        user = User(
            **user_data,
            hashed_password=hashed_password,
            created_at=datetime.utcnow(),
        )
        
        self.user_repo.db.add(user)
        await self.commit()
        await self.refresh(user)
        
        # Business logic: Send welcome email
        await self._send_welcome_email(user)
        
        return user
    
    def _is_strong_password(self, password: str) -> bool:
        """Validate password strength (business logic)."""
        return (
            len(password) >= 8
            and any(c.isupper() for c in password)
            and any(c.islower() for c in password)
            and any(c.isdigit() for c in password)
        )
```

---

## Testing Considerations

### Testing Services with Direct Model Creation

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

### Testing Repository CRUD

```python
async def test_repository_create(db_session: AsyncSession):
    """Test repository create with simple schema."""
    repo = ManufacturingTypeRepository(db_session)
    
    mfg_type_in = ManufacturingTypeCreate(
        name="Test Window",
        description="Test description",
        base_category="window",
        base_price=Decimal("200.00"),
        base_weight=Decimal("15.00"),
    )
    
    mfg_type = await repo.create(mfg_type_in)
    await db_session.commit()
    
    assert mfg_type.id is not None
    assert mfg_type.name == "Test Window"
    assert mfg_type.is_active is True
```

---

## Summary

### Key Takeaways

1. **Simple CRUD**: Use `repository.create(schema)` for type-safe, generic operations
2. **Field Transformations**: Create models directly in service layer
3. **Type Safety**: Always prefer SQLAlchemy models over dicts
4. **Separation of Concerns**: Business logic in services, data access in repositories
5. **Clear Intent**: Direct model creation signals transformation is happening
6. **Consistency**: Follow the same pattern throughout the codebase

### Quick Decision Guide

**Use `repository.create(schema)` when:**
- Schema fields = Model fields (1:1 mapping)
- No transformations needed
- Standard CRUD operation
- No business logic required

**Use direct model creation when:**
- Field names differ (password → hashed_password)
- Values need transformation (hash, encrypt, compute)
- Business rules determine values
- Multiple related entities involved
- Computed fields needed

### Remember

> "The repository pattern is about data access, not business logic. When business logic is needed, create models directly in the service layer."

---

## Additional Resources

- [SQLAlchemy ORM Documentation](https://docs.sqlalchemy.org/en/20/orm/)
- [Pydantic Documentation](https://docs.pydantic.dev/)
- [FastAPI Dependency Injection](https://fastapi.tiangolo.com/tutorial/dependencies/)
- [Type Hints in Python](https://docs.python.org/3/library/typing.html)

## Questions?

If you have questions about:
- **When to use which pattern**: Review the [Decision Tree](#decision-tree)
- **Type safety**: See [Type Safety Benefits](#type-safety-benefits)
- **Common scenarios**: Check [Common Use Cases](#common-use-cases)
- **What not to do**: Review [Anti-Patterns to Avoid](#anti-patterns-to-avoid)
