# Performance Optimization Suggestions

## 1. Dashboard Stats Query Optimization

### Current Implementation (Inefficient)
```python
# Loads ALL users into memory
all_users = await user_service.list_users()
active_users = [u for u in all_users if u.is_active]
total_users = len(all_users)
```

**Problem:** With 10,000+ users, this loads all records into memory.

### Optimized Implementation (Recommended)
```python
from sqlalchemy import func, select
from datetime import UTC, datetime, timedelta

async def get_dashboard_stats_optimized(db: AsyncSession) -> dict:
    """Get dashboard statistics using database aggregation."""
    now = datetime.now(UTC)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    week_start = now - timedelta(days=7)
    
    # Single query with aggregations
    stats_query = select(
        func.count(User.id).label("total_users"),
        func.count(User.id).filter(User.is_active == True).label("active_users"),
        func.count(User.id).filter(User.is_active == False).label("inactive_users"),
        func.count(User.id).filter(User.is_superuser == True).label("superusers"),
        func.count(User.id).filter(User.created_at >= today_start).label("new_today"),
        func.count(User.id).filter(User.created_at >= week_start).label("new_week"),
    )
    
    result = await db.execute(stats_query)
    row = result.one()
    
    return {
        "total_users": row.total_users,
        "active_users": row.active_users,
        "inactive_users": row.inactive_users,
        "superusers": row.superusers,
        "new_users_today": row.new_today,
        "new_users_week": row.new_week,
        "timestamp": now.isoformat(),
    }
```

**Benefits:**
- ✅ Single database query instead of loading all records
- ✅ 100x faster with large datasets
- ✅ Constant memory usage regardless of user count
- ✅ Database does the aggregation (optimized)

---

## 2. Add Database Indexes

### Current Schema
```python
class User(Base):
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    is_active: Mapped[bool] = mapped_column(default=True)  # ❌ No index
    is_superuser: Mapped[bool] = mapped_column(default=False)  # ❌ No index
    created_at: Mapped[datetime] = mapped_column(default=...)  # ❌ No index
```

### Optimized Schema
```python
class User(Base):
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    is_active: Mapped[bool] = mapped_column(default=True, index=True)  # ✅ Indexed
    is_superuser: Mapped[bool] = mapped_column(default=False, index=True)  # ✅ Indexed
    created_at: Mapped[datetime] = mapped_column(default=..., index=True)  # ✅ Indexed
```

**Migration:**
```python
# alembic/versions/xxx_add_user_indexes.py
def upgrade():
    op.create_index('ix_users_is_active', 'users', ['is_active'])
    op.create_index('ix_users_is_superuser', 'users', ['is_superuser'])
    op.create_index('ix_users_created_at', 'users', ['created_at'])

def downgrade():
    op.drop_index('ix_users_created_at', 'users')
    op.drop_index('ix_users_is_superuser', 'users')
    op.drop_index('ix_users_is_active', 'users')
```

---

## 3. Add Request Timeout Middleware

### Implementation
```python
# app/core/middleware.py

import asyncio
from starlette.middleware.base import BaseHTTPMiddleware

class TimeoutMiddleware(BaseHTTPMiddleware):
    """Add timeout to all requests."""
    
    def __init__(self, app: ASGIApp, *, timeout: float = 30.0) -> None:
        super().__init__(app)
        self.timeout = timeout
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        try:
            return await asyncio.wait_for(
                call_next(request),
                timeout=self.timeout
            )
        except asyncio.TimeoutError:
            return JSONResponse(
                status_code=status.HTTP_504_GATEWAY_TIMEOUT,
                content={
                    "error": "request_timeout",
                    "message": f"Request exceeded {self.timeout}s timeout",
                }
            )

# In setup_middleware():
app.add_middleware(TimeoutMiddleware, timeout=30.0)
```

---

## 4. Enhanced Health Check

### Current Implementation
```python
@app.get("/health")
async def health_check(settings: Settings) -> dict:
    return {
        "status": "healthy",
        "app_name": settings.app_name,
        "version": settings.app_version,
    }
```

### Enhanced Implementation
```python
from sqlalchemy import text
import redis.asyncio as redis

@app.get("/health")
async def health_check(
    settings: Settings,
    db: DBSession,
) -> dict:
    """Enhanced health check with dependency checks."""
    health_status = {
        "status": "healthy",
        "app_name": settings.app_name,
        "version": settings.app_version,
        "checks": {}
    }
    
    # Check database
    try:
        await db.execute(text("SELECT 1"))
        health_status["checks"]["database"] = {
            "status": "healthy",
            "provider": settings.database.provider,
        }
    except Exception as e:
        health_status["status"] = "unhealthy"
        health_status["checks"]["database"] = {
            "status": "unhealthy",
            "error": str(e),
        }
    
    # Check Redis (cache)
    if settings.cache.enabled:
        try:
            redis_client = redis.from_url(str(settings.cache.redis_url))
            await redis_client.ping()
            await redis_client.close()
            health_status["checks"]["cache"] = {"status": "healthy"}
        except Exception as e:
            health_status["checks"]["cache"] = {
                "status": "unhealthy",
                "error": str(e),
            }
    
    # Check Redis (rate limiter)
    if settings.limiter.enabled:
        try:
            redis_client = redis.from_url(str(settings.limiter.redis_url))
            await redis_client.ping()
            await redis_client.close()
            health_status["checks"]["rate_limiter"] = {"status": "healthy"}
        except Exception as e:
            health_status["checks"]["rate_limiter"] = {
                "status": "unhealthy",
                "error": str(e),
            }
    
    # Set overall status
    if any(
        check.get("status") == "unhealthy"
        for check in health_status["checks"].values()
    ):
        health_status["status"] = "unhealthy"
    
    return health_status
```

---

## 5. Add Query Filters to List Endpoints

### Current Implementation
```python
@router.get("/users")
async def list_users(
    params: PaginationParams,
    user_repo: UserRepo,
) -> Page[UserSchema]:
    return await paginate(user_repo.get_multi(), params)
```

### Enhanced Implementation
```python
@router.get("/users")
async def list_users(
    params: PaginationParams,
    is_active: bool | None = None,
    is_superuser: bool | None = None,
    search: str | None = None,
    sort_by: Literal["created_at", "username", "email"] = "created_at",
    sort_order: Literal["asc", "desc"] = "desc",
    db: DBSession,
) -> Page[UserSchema]:
    """List users with filtering and sorting."""
    query = select(User)
    
    # Apply filters
    if is_active is not None:
        query = query.where(User.is_active == is_active)
    
    if is_superuser is not None:
        query = query.where(User.is_superuser == is_superuser)
    
    if search:
        query = query.where(
            or_(
                User.username.ilike(f"%{search}%"),
                User.email.ilike(f"%{search}%"),
                User.full_name.ilike(f"%{search}%"),
            )
        )
    
    # Apply sorting
    sort_column = getattr(User, sort_by)
    if sort_order == "desc":
        query = query.order_by(sort_column.desc())
    else:
        query = query.order_by(sort_column.asc())
    
    return await paginate(db, query, params)
```

---

## 6. Add Caching to Dashboard Stats

### Implementation
```python
from fastapi_cache.decorator import cache

@router.get("/stats")
@cache(expire=60)  # Cache for 1 minute
async def get_dashboard_stats(
    current_superuser: CurrentSuperuser,
    db: DBSession,
) -> dict:
    """Get dashboard statistics (cached)."""
    return await get_dashboard_stats_optimized(db)
```

**Benefits:**
- Reduces database load
- Faster response times
- Stats don't need to be real-time (1-minute delay acceptable)

---

## 7. Add Connection Pool Monitoring

### Implementation
```python
@router.get("/metrics/database")
async def database_metrics(
    current_superuser: CurrentSuperuser,
) -> dict:
    """Get database connection pool metrics."""
    engine = get_engine()
    pool = engine.pool
    
    return {
        "pool_size": pool.size(),
        "checked_in": pool.checkedin(),
        "checked_out": pool.checkedout(),
        "overflow": pool.overflow(),
        "total_connections": pool.size() + pool.overflow(),
    }
```

---

## 8. Add Bulk Operations

### Implementation
```python
@router.post("/users/bulk")
async def create_users_bulk(
    users_in: list[UserCreate],
    db: DBSession,
    current_superuser: CurrentSuperuser,
) -> list[UserSchema]:
    """Create multiple users in a single transaction."""
    user_service = UserService(db)
    created_users = []
    
    try:
        for user_in in users_in:
            user = await user_service.create_user(user_in)
            created_users.append(user)
        
        await db.commit()
        return created_users
    except Exception:
        await db.rollback()
        raise
```

---

## Performance Impact Summary

| Optimization | Impact | Effort | Priority |
|--------------|--------|--------|----------|
| Dashboard Stats Query | 🔥 High (100x faster) | Low (30 min) | ⭐⭐⭐ Critical |
| Add Indexes | 🔥 High (10x faster queries) | Low (15 min) | ⭐⭐⭐ Critical |
| Request Timeout | 🟡 Medium (prevents hangs) | Low (15 min) | ⭐⭐ High |
| Enhanced Health Check | 🟢 Low (better monitoring) | Low (20 min) | ⭐⭐ High |
| Query Filters | 🟡 Medium (better UX) | Medium (1 hour) | ⭐ Medium |
| Cache Dashboard Stats | 🟡 Medium (reduces load) | Low (5 min) | ⭐ Medium |
| Pool Monitoring | 🟢 Low (observability) | Low (15 min) | ⭐ Medium |
| Bulk Operations | 🟢 Low (convenience) | Medium (1 hour) | Low |

---

## Implementation Priority

### Phase 1: Critical (Do Now)
1. ✅ Optimize dashboard stats query
2. ✅ Add database indexes
3. ✅ Add request timeout

**Estimated Time:** 1 hour  
**Impact:** Massive performance improvement

### Phase 2: High Priority (This Week)
1. Enhanced health check
2. Cache dashboard stats
3. Query filters for list endpoints

**Estimated Time:** 2 hours  
**Impact:** Better monitoring and UX

### Phase 3: Nice to Have (Future)
1. Connection pool monitoring
2. Bulk operations
3. Advanced metrics

**Estimated Time:** 3 hours  
**Impact:** Enhanced features

---

## Testing After Optimization

```bash
# Test dashboard stats performance
time curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/v1/dashboard/stats

# Expected: < 50ms (vs 500ms+ before)

# Test with load
ab -n 1000 -c 10 \
  -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/v1/dashboard/stats

# Expected: 0% failures, < 100ms average
```

---

## Conclusion

These optimizations will:
- ✅ Improve response times by 10-100x
- ✅ Reduce database load significantly
- ✅ Enhance monitoring capabilities
- ✅ Improve user experience
- ✅ Prepare for scale

**Total Implementation Time:** 3-6 hours  
**Performance Gain:** 10-100x improvement
