# Middleware and Security Best Practices

## Overview

This application implements comprehensive middleware for security, logging, and performance using Starlette middleware components and custom implementations following FastAPI and Starlette best practices.

## Middleware Stack (Execution Order)

Middleware is applied in **reverse order** (last added = first executed):

```
8. LoggingMiddleware          ← Last (logs everything)
7. RequestIDMiddleware        ← Adds X-Request-ID
6. GZipMiddleware            ← Compresses responses
5. SecurityHeadersMiddleware  ← Adds security headers
4. CORSMiddleware            ← Handles CORS
3. HTTPSRedirectMiddleware   ← Redirects HTTP to HTTPS (prod)
2. TrustedHostMiddleware     ← Validates host headers (prod)
1. RequestSizeLimitMiddleware ← First (checks request size)
```

## Security Middleware

### 1. Security Headers Middleware

**Purpose**: Add OWASP-recommended security headers to all responses

```python
from app.core.middleware import SecurityHeadersMiddleware

app.add_middleware(
    SecurityHeadersMiddleware,
    hsts_max_age=31536000,  # 1 year
)
```

**Headers Added**:

| Header | Value | Purpose |
|--------|-------|---------|
| `X-Content-Type-Options` | `nosniff` | Prevent MIME sniffing |
| `X-XSS-Protection` | `1; mode=block` | Enable XSS protection |
| `X-Frame-Options` | `DENY` | Prevent clickjacking |
| `Referrer-Policy` | `strict-origin-when-cross-origin` | Control referrer info |
| `Permissions-Policy` | `geolocation=(), ...` | Restrict browser features |
| `Content-Security-Policy` | `default-src 'self'; ...` | Prevent XSS/injection |
| `Strict-Transport-Security` | `max-age=31536000; ...` | Force HTTPS (HTTPS only) |

### 2. Trusted Host Middleware

**Purpose**: Validate Host headers to prevent Host header injection attacks

```python
from starlette.middleware.trustedhost import TrustedHostMiddleware

app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["api.example.com", "*.example.com"],
)
```

**Benefits**:
- Prevents Host header injection attacks
- Validates incoming requests against allowed domains
- Automatic in production mode
- Extracts hosts from CORS origins

### 3. HTTPS Redirect Middleware

**Purpose**: Redirect all HTTP requests to HTTPS in production

```python
from starlette.middleware.httpsredirect import HTTPSRedirectMiddleware

if not settings.debug:
    app.add_middleware(HTTPSRedirectMiddleware)
```

**Benefits**:
- Ensures all traffic uses HTTPS
- Automatic 301 redirects
- Only enabled in production
- Protects against downgrade attacks

### 4. Request Size Limit Middleware

**Purpose**: Prevent DoS attacks by limiting request body size

```python
from app.core.middleware import RequestSizeLimitMiddleware

app.add_middleware(
    RequestSizeLimitMiddleware,
    max_size=16 * 1024 * 1024,  # 16MB
)
```

**Benefits**:
- Prevents large request DoS attacks
- Configurable size limits
- Early rejection (first middleware)
- Returns proper 413 status code

**Response Format**:
```json
{
  "error": "request_too_large",
  "message": "Request entity too large. Maximum size: 16777216 bytes",
  "details": [
    {
      "type": "request_too_large",
      "message": "Request size 20000000 exceeds limit 16777216",
      "field": null
    }
  ]
}
```

## Utility Middleware

### 1. Request ID Middleware

**Purpose**: Add unique request ID for tracking and debugging

```python
from app.core.middleware import RequestIDMiddleware

app.add_middleware(RequestIDMiddleware)
```

**Features**:
- Generates UUID for each request
- Uses existing `X-Request-ID` if provided
- Available in `request.state.request_id`
- Added to response headers
- Used in logging and error tracking

**Usage in Endpoints**:
```python
@router.get("/endpoint")
async def endpoint(request: Request):
    request_id = request.state.request_id
    logger.info(f"Processing request {request_id}")
    return {"request_id": request_id}
```

**Client Usage**:
```bash
# Send request with custom ID
curl -H "X-Request-ID: my-custom-id" https://api.example.com/endpoint

# Response includes the ID
X-Request-ID: my-custom-id
```

### 2. Logging Middleware

**Purpose**: Log all requests and responses with timing information

```python
from app.core.middleware import LoggingMiddleware

app.add_middleware(LoggingMiddleware)
```

**Logged Information**:
- Request method and path
- Query parameters
- Client IP and User-Agent
- Response status code
- Request duration
- Request ID for correlation

**Log Format**:
```
INFO Request started: GET /api/v1/users
INFO Request completed: GET /api/v1/users - 200 in 0.045s
ERROR Request failed: POST /api/v1/users - Error: Validation error in 0.023s
```

**Structured Logging**:
```python
{
    "request_id": "abc-123",
    "method": "GET",
    "path": "/api/v1/users",
    "query_params": "page=1&size=10",
    "client_ip": "192.168.1.1",
    "user_agent": "Mozilla/5.0...",
    "status_code": 200,
    "duration": 0.045
}
```

### 3. CORS Middleware

**Purpose**: Handle Cross-Origin Resource Sharing with security

```python
from starlette.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://example.com"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-Request-ID"],
    expose_headers=["X-Request-ID"],
    max_age=86400,  # 24 hours
)
```

**Security Features**:
- Restricted origins (no wildcards in production)
- Specific allowed methods
- Limited allowed headers
- Request ID exposure for debugging
- Credentials support for authenticated requests

**Configuration**:
```env
# .env
BACKEND_CORS_ORIGINS=["https://example.com","https://app.example.com"]
```

## Performance Middleware

### 1. Gzip Compression

**Purpose**: Compress responses to reduce bandwidth

```python
from starlette.middleware.gzip import GZipMiddleware

app.add_middleware(
    GZipMiddleware,
    minimum_size=1000,    # Only compress > 1KB
    compresslevel=6,      # Balance speed/compression (1-9)
)
```

**Benefits**:
- Reduces response size by 60-80%
- Configurable compression level
- Automatic content-type detection
- Only compresses responses above minimum size

**Compression Levels**:
- `1-3`: Fast compression, lower ratio
- `4-6`: Balanced (recommended)
- `7-9`: Best compression, slower

## Configuration

### Automatic Setup

```python
# app/main.py
from app.core.middleware import setup_middleware

settings = get_settings()
setup_middleware(app, settings)
```

### Development vs Production

**Development** (`DEBUG=True`):
- No HTTPS redirect
- Relaxed CORS origins
- Detailed logging
- No trusted host validation

**Production** (`DEBUG=False`):
- HTTPS redirect enabled
- Strict CORS origins
- Trusted host validation
- Security headers enforced
- HSTS enabled

## Optional Middleware

### Rate Limiting by IP

**Purpose**: Simple IP-based rate limiting (use Redis-based limiter for production)

```python
from app.core.middleware import RateLimitByIPMiddleware

app.add_middleware(
    RateLimitByIPMiddleware,
    calls=100,    # 100 requests
    period=60,    # per minute
)
```

**Note**: This is a simple in-memory implementation. For production with multiple workers, use `fastapi-limiter` with Redis.

**Response Format**:
```json
{
  "error": "rate_limit_exceeded",
  "message": "Too many requests. Please try again later.",
  "details": [
    {
      "type": "rate_limit_exceeded",
      "message": "Rate limit: 100 requests per 60 seconds",
      "field": null
    }
  ]
}
```

### CSRF Protection

**Purpose**: Validate CSRF tokens for state-changing requests

```python
from app.core.middleware import CSRFProtectionMiddleware

app.add_middleware(
    CSRFProtectionMiddleware,
    secret_key=settings.security.secret_key.get_secret_value(),
    exempt_paths=["/api/v1/auth/login", "/api/v1/auth/register"],
)
```

**Features**:
- Validates CSRF tokens for POST, PUT, PATCH, DELETE
- Exempts safe methods (GET, HEAD, OPTIONS, TRACE)
- Configurable exempt paths
- Automatic exemption for docs endpoints

**Client Usage**:
```bash
# Include CSRF token in header
curl -X POST https://api.example.com/api/v1/users \
  -H "X-CSRF-Token: your-csrf-token" \
  -H "Content-Type: application/json" \
  -d '{"name": "John"}'
```

## Security Headers Explained

### Content Security Policy (CSP)

```
Content-Security-Policy: default-src 'self'; script-src 'self' 'unsafe-inline';
```

**Directives**:
- `default-src 'self'` - Only load resources from same origin
- `script-src 'self' 'unsafe-inline'` - Scripts from same origin + inline
- `style-src 'self' 'unsafe-inline'` - Styles from same origin + inline
- `img-src 'self' data: https:` - Images from same origin, data URLs, HTTPS
- `frame-ancestors 'none'` - Prevent embedding in frames

**Customization**:
```python
# Modify in SecurityHeadersMiddleware
"Content-Security-Policy": (
    "default-src 'self'; "
    "script-src 'self' https://cdn.example.com; "
    "style-src 'self' https://fonts.googleapis.com; "
    "img-src 'self' data: https:; "
)
```

### HTTP Strict Transport Security (HSTS)

```
Strict-Transport-Security: max-age=31536000; includeSubDomains; preload
```

**Features**:
- `max-age=31536000` - 1 year duration
- `includeSubDomains` - Apply to all subdomains
- `preload` - Eligible for browser preload lists

**Browser Behavior**:
- Forces HTTPS for specified duration
- Prevents SSL stripping attacks
- Automatic HTTPS upgrade

### X-Frame-Options

```
X-Frame-Options: DENY
```

**Options**:
- `DENY` - Cannot be embedded in any frame
- `SAMEORIGIN` - Can be embedded in same-origin frames
- `ALLOW-FROM uri` - Can be embedded in specified URI (deprecated)

**Protection**: Prevents clickjacking attacks

### Permissions Policy

```
Permissions-Policy: geolocation=(), microphone=(), camera=()
```

**Features**:
- Restricts browser features
- Prevents unauthorized access to sensors
- Improves privacy and security

## Best Practices

### 1. Middleware Order

Always maintain this order for security:
1. Size limits first (prevent large payloads)
2. Host validation (prevent injection)
3. HTTPS redirect (secure transport)
4. CORS (handle preflight)
5. Security headers (protect responses)
6. Compression (optimize bandwidth)
7. Request ID (enable tracking)
8. Logging (capture everything)

### 2. Production Configuration

```python
# .env.production
DEBUG=False
BACKEND_CORS_ORIGINS=["https://app.example.com"]
DATABASE_PROVIDER=postgresql
```

### 3. Security Headers

- Always use HSTS in production
- Customize CSP for your needs
- Enable all OWASP headers
- Test with security scanners

### 4. Rate Limiting

- Use Redis-based limiter for production
- Set appropriate limits per endpoint
- Provide clear error messages
- Include Retry-After header

### 5. Logging

- Include request ID in all logs
- Log errors with full context
- Use structured logging
- Monitor log aggregation

### 6. CORS

- Never use `allow_origins=["*"]` in production
- Specify exact origins
- Limit allowed methods
- Expose only necessary headers

## Testing Middleware

### Test Security Headers

```python
def test_security_headers(client: TestClient):
    response = client.get("/")
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert response.headers["X-Frame-Options"] == "DENY"
    assert "Content-Security-Policy" in response.headers
```

### Test Request ID

```python
def test_request_id(client: TestClient):
    response = client.get("/")
    assert "X-Request-ID" in response.headers
    
    # Test custom request ID
    response = client.get("/", headers={"X-Request-ID": "custom-id"})
    assert response.headers["X-Request-ID"] == "custom-id"
```

### Test Rate Limiting

```python
def test_rate_limit(client: TestClient):
    # Make requests up to limit
    for _ in range(100):
        response = client.get("/")
        assert response.status_code == 200
    
    # Next request should be rate limited
    response = client.get("/")
    assert response.status_code == 429
    assert "Retry-After" in response.headers
```

## Monitoring

### Metrics to Track

1. **Request Duration**: Monitor slow endpoints
2. **Error Rate**: Track failed requests
3. **Rate Limit Hits**: Identify abuse
4. **Request Size**: Monitor payload sizes
5. **Response Size**: Track compression effectiveness

### Log Analysis

```python
# Find slow requests
grep "Request completed" app.log | awk '$NF > 1.0'

# Count errors by endpoint
grep "Request failed" app.log | awk '{print $5}' | sort | uniq -c

# Track rate limit violations
grep "rate_limit_exceeded" app.log | wc -l
```

## Troubleshooting

### CORS Issues

**Problem**: CORS errors in browser
**Solution**: 
- Check `BACKEND_CORS_ORIGINS` includes your frontend URL
- Verify protocol (http vs https)
- Check allowed methods and headers

### Rate Limiting

**Problem**: Legitimate users getting rate limited
**Solution**:
- Increase limits for authenticated users
- Use per-user rate limiting instead of IP
- Implement Redis-based limiter for accuracy

### Request Size

**Problem**: Large file uploads failing
**Solution**:
- Increase `max_size` in `RequestSizeLimitMiddleware`
- Use streaming for large files
- Implement chunked uploads

## References

- [FastAPI Middleware](https://fastapi.tiangolo.com/tutorial/middleware/)
- [Starlette Middleware](https://www.starlette.io/middleware/)
- [OWASP Security Headers](https://owasp.org/www-project-secure-headers/)
- [MDN CSP Guide](https://developer.mozilla.org/en-US/docs/Web/HTTP/CSP)
