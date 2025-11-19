"""Example demonstrating middleware usage in FastAPI application.

This example shows how to:
1. Use built-in middleware
2. Access request state
3. Create custom middleware
4. Test middleware behavior
"""

from typing import Callable

from fastapi import FastAPI, Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.config import get_settings
from app.core.middleware import setup_middleware


# ============================================================================
# Example 1: Basic Setup
# ============================================================================

def example_basic_setup():
    """Example of basic middleware setup."""
    app = FastAPI()
    settings = get_settings()
    
    # Setup all middleware with one function
    setup_middleware(app, settings)
    
    @app.get("/")
    async def root():
        return {"message": "Middleware configured"}
    
    return app


# ============================================================================
# Example 2: Accessing Request State
# ============================================================================

def example_request_state():
    """Example of accessing request state set by middleware."""
    app = FastAPI()
    setup_middleware(app, get_settings())
    
    @app.get("/info")
    async def get_info(request: Request):
        """Get request information from middleware."""
        return {
            "request_id": request.state.request_id,  # From RequestIDMiddleware
            "client_ip": request.client.host if request.client else "unknown",
            "user_agent": request.headers.get("User-Agent"),
        }
    
    return app


# ============================================================================
# Example 3: Custom Middleware
# ============================================================================

class TimingMiddleware(BaseHTTPMiddleware):
    """Custom middleware to measure request processing time."""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Add processing time to response headers.
        
        Args:
            request (Request): Incoming request
            call_next (Callable): Next middleware/endpoint
        
        Returns:
            Response: Response with X-Process-Time header
        """
        import time
        
        start_time = time.time()
        
        # Process request
        response = await call_next(request)
        
        # Calculate duration
        process_time = time.time() - start_time
        
        # Add to response headers
        response.headers["X-Process-Time"] = f"{process_time:.4f}"
        
        return response


def example_custom_middleware():
    """Example of adding custom middleware."""
    app = FastAPI()
    
    # Add custom middleware first
    app.add_middleware(TimingMiddleware)
    
    # Then setup standard middleware
    setup_middleware(app, get_settings())
    
    @app.get("/slow")
    async def slow_endpoint():
        """Endpoint that takes time to process."""
        import asyncio
        await asyncio.sleep(0.1)
        return {"message": "Done"}
    
    return app


# ============================================================================
# Example 4: Conditional Middleware
# ============================================================================

class DebugMiddleware(BaseHTTPMiddleware):
    """Middleware that only runs in debug mode."""
    
    def __init__(self, app, *, debug: bool = False):
        """Initialize debug middleware.
        
        Args:
            app: ASGI application
            debug (bool): Whether debug mode is enabled
        """
        super().__init__(app)
        self.debug = debug
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Add debug information if enabled.
        
        Args:
            request (Request): Incoming request
            call_next (Callable): Next middleware/endpoint
        
        Returns:
            Response: Response with optional debug headers
        """
        response = await call_next(request)
        
        if self.debug:
            response.headers["X-Debug"] = "enabled"
            response.headers["X-Request-Path"] = str(request.url.path)
        
        return response


def example_conditional_middleware():
    """Example of middleware that behaves differently based on config."""
    app = FastAPI()
    settings = get_settings()
    
    # Add debug middleware only in development
    app.add_middleware(DebugMiddleware, debug=settings.debug)
    
    # Setup standard middleware
    setup_middleware(app, settings)
    
    @app.get("/")
    async def root():
        return {"message": "Check response headers"}
    
    return app


# ============================================================================
# Example 5: Middleware with State
# ============================================================================

class RequestCounterMiddleware(BaseHTTPMiddleware):
    """Middleware that counts requests per endpoint."""
    
    def __init__(self, app):
        """Initialize request counter middleware.
        
        Args:
            app: ASGI application
        """
        super().__init__(app)
        self.request_counts: dict[str, int] = {}
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Count requests per endpoint.
        
        Args:
            request (Request): Incoming request
            call_next (Callable): Next middleware/endpoint
        
        Returns:
            Response: Response with request count header
        """
        path = request.url.path
        
        # Increment counter
        self.request_counts[path] = self.request_counts.get(path, 0) + 1
        
        # Process request
        response = await call_next(request)
        
        # Add count to response
        response.headers["X-Request-Count"] = str(self.request_counts[path])
        
        return response


def example_stateful_middleware():
    """Example of middleware that maintains state."""
    app = FastAPI()
    
    # Add counter middleware
    counter_middleware = RequestCounterMiddleware(app)
    app.add_middleware(RequestCounterMiddleware)
    
    # Setup standard middleware
    setup_middleware(app, get_settings())
    
    @app.get("/")
    async def root():
        return {"message": "Check X-Request-Count header"}
    
    @app.get("/stats")
    async def stats():
        """Get request statistics."""
        return {
            "request_counts": counter_middleware.request_counts,
        }
    
    return app


# ============================================================================
# Example 6: Error Handling in Middleware
# ============================================================================

class ErrorHandlingMiddleware(BaseHTTPMiddleware):
    """Middleware that handles errors gracefully."""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Handle errors in middleware.
        
        Args:
            request (Request): Incoming request
            call_next (Callable): Next middleware/endpoint
        
        Returns:
            Response: Response or error response
        """
        try:
            response = await call_next(request)
            return response
        except Exception as e:
            # Log error
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Middleware error: {str(e)}")
            
            # Return error response
            from fastapi.responses import JSONResponse
            return JSONResponse(
                status_code=500,
                content={
                    "error": "internal_error",
                    "message": "An error occurred processing your request",
                },
            )


def example_error_handling():
    """Example of error handling in middleware."""
    app = FastAPI()
    
    # Add error handling middleware
    app.add_middleware(ErrorHandlingMiddleware)
    
    # Setup standard middleware
    setup_middleware(app, get_settings())
    
    @app.get("/error")
    async def error_endpoint():
        """Endpoint that raises an error."""
        raise ValueError("Something went wrong")
    
    return app


# ============================================================================
# Example 7: Testing Middleware
# ============================================================================

def test_middleware():
    """Example of testing middleware behavior."""
    from fastapi.testclient import TestClient
    
    app = example_basic_setup()
    client = TestClient(app)
    
    # Test request ID
    response = client.get("/")
    assert "X-Request-ID" in response.headers
    print(f"✓ Request ID: {response.headers['X-Request-ID']}")
    
    # Test security headers
    assert response.headers["X-Frame-Options"] == "DENY"
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    print("✓ Security headers present")
    
    # Test custom request ID
    response = client.get("/", headers={"X-Request-ID": "custom-123"})
    assert response.headers["X-Request-ID"] == "custom-123"
    print("✓ Custom request ID preserved")
    
    # Test CORS
    response = client.options(
        "/",
        headers={"Origin": "http://localhost:3000"},
    )
    print(f"✓ CORS headers: {response.headers.get('Access-Control-Allow-Origin')}")


# ============================================================================
# Example 8: Middleware Order
# ============================================================================

class FirstMiddleware(BaseHTTPMiddleware):
    """First middleware in chain."""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Add marker to request state.
        
        Args:
            request (Request): Incoming request
            call_next (Callable): Next middleware/endpoint
        
        Returns:
            Response: Response with execution order
        """
        request.state.execution_order = ["first"]
        response = await call_next(request)
        response.headers["X-First"] = "executed"
        return response


class SecondMiddleware(BaseHTTPMiddleware):
    """Second middleware in chain."""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Add marker to request state.
        
        Args:
            request (Request): Incoming request
            call_next (Callable): Next middleware/endpoint
        
        Returns:
            Response: Response with execution order
        """
        request.state.execution_order.append("second")
        response = await call_next(request)
        response.headers["X-Second"] = "executed"
        return response


def example_middleware_order():
    """Example demonstrating middleware execution order."""
    app = FastAPI()
    
    # Add middleware (reverse order of execution)
    app.add_middleware(SecondMiddleware)  # Executes second
    app.add_middleware(FirstMiddleware)   # Executes first
    
    @app.get("/")
    async def root(request: Request):
        return {
            "execution_order": request.state.execution_order,
            "message": "Check response headers for X-First and X-Second",
        }
    
    return app


# ============================================================================
# Main
# ============================================================================

if __name__ == "__main__":
    print("Middleware Examples")
    print("=" * 50)
    
    # Run tests
    print("\nTesting middleware...")
    test_middleware()
    
    print("\n✓ All examples completed successfully")
