# Practice

---

## 1. Use **`try/except` locally** when:

- You’re calling code that may fail in a **predictable, recoverable way** (e.g. database fetch, external API, business logic).
- You want to handle **specific exceptions** (not everything) and **transform them** into meaningful domain or HTTP errors.
- You need **fine-grained control**: e.g. retry logic, fallback, cleanup, or side-effects in the same route.
- The error context is local and not generic: different routes may need different behavior even for the same error type.

**Example (local `try/except`):**

```python
@app.get("/user/{user_id}")
async def get_user(user_id: int):
    try:
        user = await db.fetch_user(user_id)
    except UserNotFoundError:
        raise HTTPException(status_code=404, detail="User not found")
    except DatabaseError as e:
        # maybe log, wrap, or convert to a 500
        raise HTTPException(status_code=500, detail="Database error")
    return user

```

Using `try/except` in this way avoids leaking internal stack traces, gives custom messages per-route, and allows recovery logic when needed.

---

## 2. Use **`@app.exception_handler(...)` globally** when:

- You want **consistent error responses** across many routes (same format, logging, status codes).
- You want to **centralize logic** for certain exception types (e.g. `RequestValidationError`, custom domain errors, HTTPExceptions).
- You want to **avoid duplicating error handling** in every route.
- You want to handle *unexpected/unhandled exceptions* in a **uniform, safe way** (e.g. generic `Exception` fallback).

**Example (global handler):**

```python
from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

@app.exception_handler(RequestValidationError)
async def validation_error_handler(request: Request, exc: RequestValidationError):
    # Produce consistent JSON structure, log, mask details, etc.
    return JSONResponse(
        status_code=422,
        content={"errors": exc.errors(), "body": exc.body}
    )

@app.exception

```

Let’s restate the complete answer cleanly (since the previous one was cut off):

---

## 🧭 Best Practice: When to Use `try/except` vs. `@app.exception_handler` in FastAPI

*(written in prompt-engineering style — short, directive, and reasoning-driven)*

---

### 🎯 **Local Control → Use `try/except`**

> You want to handle something that belongs only to this route, this function, this context.
> 

**Use `try/except` when:**

- You expect a *specific and recoverable* failure (e.g. a missing record, timeout, invalid API response).
- You need to perform **cleanup, rollback, or retries** immediately.
- The **response or recovery** should differ depending on where it happens.
- You want to **translate** an internal error (like `ValueError`) into a FastAPI `HTTPException`.

**Pattern:**

```python
@app.get("/items/{id}")
async def read_item(id: int):
    try:
        return await get_item(id)
    except ItemNotFound:
        raise HTTPException(status_code=404, detail="Item not found")
    except ExternalServiceError:
        raise HTTPException(status_code=502, detail="External API unavailable")

```

✅ *Best when you need context-aware reactions and want to continue execution.*

---

### 🌍 **Global Consistency → Use `@app.exception_handler`**

> You want one definition to rule them all.
> 

**Use FastAPI’s global handlers when:**

- You want **uniform error formatting** for certain exception types.
- You want to **log, mask, or standardize** internal errors automatically.
- You’re handling **framework-level** or **domain-wide** exceptions (like `ValidationError`, `IntegrityError`, or `CustomAppError`).
- You don’t want to repeat the same error logic in every route.

**Pattern:**

```python
@app.exception_handler(RequestValidationError)
async def validation_error_handler(request, exc):
    return JSONResponse(
        status_code=422,
        content={"error": "Validation failed", "details": exc.errors()}
    )

@app.exception_handler(Exception)
async def global_handler(request, exc):
    return JSONResponse(
        status_code=500,
        content={"error": "Internal Server Error"}
    )

```

✅ *Best for enforcing global structure, logging, and safety.*

---

### ⚖️ **Blended Strategy**

Use **`try/except` for business logic**

and

**`@app.exception_handler` for application consistency.**

- **Local** → focus on *what failed* and *what to do next*
- **Global** → focus on *how failures are reported*

Think of it as **“route safety nets vs. system policy.”**

---