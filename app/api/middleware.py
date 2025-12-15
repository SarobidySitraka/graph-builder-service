"""
Complete middleware implementations for request processing.
Includes logging, rate limiting, security headers, and monitoring.
"""
import time
import logging
import uuid
from typing import Callable, Dict
from collections import defaultdict

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from app.core.config import settings

logger = logging.getLogger(__name__)


# ============================================================================
# Request ID Middleware
# ============================================================================

class RequestIDMiddleware(BaseHTTPMiddleware):
    """
    Add unique request ID to each request.
    Useful for tracing requests through logs.
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Add request ID to request state and response headers."""
        # Get request ID from header or generate new one
        request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())

        # Store in request state for access in endpoints
        request.state.request_id = request_id

        # Process request
        response = await call_next(request)

        # Add to response headers
        response.headers["X-Request-ID"] = request_id

        return response


# ============================================================================
# Request Logging Middleware
# ============================================================================

class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Log all incoming requests and outgoing responses.
    Includes timing information and status codes.
    """

    def __init__(self, app: ASGIApp, log_bodies: bool = False):
        """
        Initialize logging middleware.

        Args:
            app: ASGI application
            log_bodies: Whether to log request/response bodies (security risk!)
        """
        super().__init__(app)
        self.log_bodies = log_bodies

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Log request and response details."""
        # Extract request info
        request_id = getattr(request.state, "request_id", "unknown")
        method = request.method
        url = str(request.url)
        client_ip = request.client.host if request.client else "unknown"
        user_agent = request.headers.get("user-agent", "unknown")

        # Start timing
        start_time = time.time()

        # Log incoming request
        logger.info(
            f"Request started",
            extra={
                "request_id": request_id,
                "method": method,
                "url": url,
                "client_ip": client_ip,
                "user_agent": user_agent,
            }
        )

        # Process request
        try:
            response = await call_next(request)
            status_code = response.status_code
            error = None
        except Exception as e:
            status_code = 500
            error = str(e)
            logger.exception(
                f"Request failed with exception",
                extra={
                    "request_id": request_id,
                    "error": error,
                }
            )
            raise
        finally:
            # Calculate duration
            duration = time.time() - start_time

            # Log response
            log_level = logging.ERROR if status_code >= 500 else logging.WARNING if status_code >= 400 else logging.INFO
            logger.log(
                log_level,
                f"Request completed",
                extra={
                    "request_id": request_id,
                    "method": method,
                    "url": url,
                    "status_code": status_code,
                    "duration_ms": round(duration * 1000, 2),
                    "error": error,
                }
            )

        # Add timing header
        response.headers["X-Process-Time"] = f"{duration:.4f}"

        return response


# ============================================================================
# Rate Limiting Middleware
# ============================================================================

class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Simple in-memory rate limiting.
    For production, use Redis-based rate limiting.
    """

    def __init__(
            self,
            app: ASGIApp,
            requests_per_minute: int = 60,
            burst: int = 10
    ):
        """
        Initialize rate limiting.

        Args:
            app: ASGI application
            requests_per_minute: Max requests per minute per IP
            burst: Max burst requests allowed
        """
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.burst = burst
        self.requests: Dict[str, list] = defaultdict(list)
        self.burst_requests: Dict[str, int] = defaultdict(int)

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Check rate limit and process request."""
        # Skip rate limiting for health checks
        if request.url.path in ["/health", "/api/v1/health"]:
            return await call_next(request)

        if not request.client:
            return await call_next(request)

        client_ip = request.client.host
        current_time = time.time()

        # Clean old requests (older than 60 seconds)
        self.requests[client_ip] = [
            t for t in self.requests[client_ip]
            if current_time - t < 60
        ]

        # Check burst limit
        if self.burst_requests[client_ip] >= self.burst:
            last_request_time = self.requests[client_ip][-1] if self.requests[client_ip] else 0
            if current_time - last_request_time < 1:  # Within 1 second
                logger.warning(
                    f"Burst rate limit exceeded",
                    extra={"client_ip": client_ip, "burst": self.burst}
                )
                from fastapi.responses import JSONResponse
                return JSONResponse(
                    status_code=429,
                    content={
                        "error": {
                            "type": "RateLimitExceeded",
                            "message": f"Burst limit exceeded. Maximum {self.burst} requests per second.",
                        }
                    },
                    headers={
                        "Retry-After": "1",
                        "X-RateLimit-Limit": str(self.requests_per_minute),
                        "X-RateLimit-Remaining": "0",
                    }
                )

        # Check rate limit
        if len(self.requests[client_ip]) >= self.requests_per_minute:
            logger.warning(
                f"Rate limit exceeded",
                extra={
                    "client_ip": client_ip,
                    "requests_per_minute": self.requests_per_minute
                }
            )
            from fastapi.responses import JSONResponse
            return JSONResponse(
                status_code=429,
                content={
                    "error": {
                        "type": "RateLimitExceeded",
                        "message": f"Rate limit exceeded. Maximum {self.requests_per_minute} requests per minute.",
                    }
                },
                headers={
                    "Retry-After": "60",
                    "X-RateLimit-Limit": str(self.requests_per_minute),
                    "X-RateLimit-Remaining": "0",
                }
            )

        # Add current request
        self.requests[client_ip].append(current_time)
        self.burst_requests[client_ip] += 1

        # Reset burst counter every second
        if not self.requests[client_ip] or current_time - self.requests[client_ip][0] >= 1:
            self.burst_requests[client_ip] = 1

        # Process request
        response = await call_next(request)

        # Add rate limit headers
        remaining = max(0, self.requests_per_minute - len(self.requests[client_ip]))
        response.headers["X-RateLimit-Limit"] = str(self.requests_per_minute)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Reset"] = str(int(current_time + 60))

        return response


# ============================================================================
# Security Headers Middleware
# ============================================================================

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Add security headers to all responses.
    Helps protect against common web vulnerabilities.
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Add security headers to response."""
        response = await call_next(request)

        # Security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        # Content Security Policy (adjust as needed)
        if not settings.is_development:
            response.headers["Content-Security-Policy"] = "default-src 'self'"

        # Strict Transport Security (HTTPS only)
        if not settings.is_development:
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"

        return response


# ============================================================================
# CORS Middleware (Alternative to FastAPI's built-in)
# ============================================================================

class CustomCORSMiddleware(BaseHTTPMiddleware):
    """
    Custom CORS middleware with additional features.
    Use this for fine-grained control over CORS behavior.
    """

    def __init__(
            self,
            app: ASGIApp,
            allow_origins: list = None,
            allow_credentials: bool = True,
            allow_methods: list = None,
            allow_headers: list = None,
            max_age: int = 600
    ):
        super().__init__(app)
        self.allow_origins = allow_origins or ["*"]
        self.allow_credentials = allow_credentials
        self.allow_methods = allow_methods or ["*"]
        self.allow_headers = allow_headers or ["*"]
        self.max_age = max_age

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Handle CORS preflight and add CORS headers."""
        origin = request.headers.get("origin")

        # Handle preflight request
        if request.method == "OPTIONS":
            response = Response(status_code=200)
        else:
            response = await call_next(request)

        # Add CORS headers
        if origin and ("*" in self.allow_origins or origin in self.allow_origins):
            response.headers["Access-Control-Allow-Origin"] = origin

            if self.allow_credentials:
                response.headers["Access-Control-Allow-Credentials"] = "true"

            if request.method == "OPTIONS":
                response.headers["Access-Control-Allow-Methods"] = ", ".join(self.allow_methods)
                response.headers["Access-Control-Allow-Headers"] = ", ".join(self.allow_headers)
                response.headers["Access-Control-Max-Age"] = str(self.max_age)

        return response


# ============================================================================
# Error Handling Middleware
# ============================================================================

class ErrorHandlingMiddleware(BaseHTTPMiddleware):
    """
    Catch and handle unexpected errors gracefully.
    Prevents sensitive error details from leaking.
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Catch and handle errors."""
        try:
            return await call_next(request)
        except Exception as e:
            request_id = getattr(request.state, "request_id", "unknown")

            logger.exception(
                f"Unhandled exception in middleware",
                extra={
                    "request_id": request_id,
                    "error": str(e),
                    "path": request.url.path,
                }
            )

            from fastapi.responses import JSONResponse

            # Don't leak error details in production
            error_detail = str(e) if settings.is_development else "An internal server error occurred"

            return JSONResponse(
                status_code=500,
                content={
                    "error": {
                        "type": "InternalServerError",
                        "message": error_detail,
                        "request_id": request_id,
                    }
                }
            )


# ============================================================================
# Cache Control Middleware
# ============================================================================

class CacheControlMiddleware(BaseHTTPMiddleware):
    """
    Add cache control headers to responses.
    Helps with API response caching.
    """

    def __init__(
            self,
            app: ASGIApp,
            default_max_age: int = 0,
            cache_static: bool = True
    ):
        super().__init__(app)
        self.default_max_age = default_max_age
        self.cache_static = cache_static

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Add cache control headers."""
        response = await call_next(request)

        # Don't cache by default (for API responses)
        if "Cache-Control" not in response.headers:
            response.headers["Cache-Control"] = f"max-age={self.default_max_age}, must-revalidate"

        # Cache static files longer
        if self.cache_static and request.url.path.startswith("/static"):
            response.headers["Cache-Control"] = "public, max-age=31536000, immutable"

        return response