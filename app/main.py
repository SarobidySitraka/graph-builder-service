"""
Graph Builder Service - Main Application
FastAPI application for building Neo4j knowledge graphs from multiple data sources.
"""
import time
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.config import settings
from app.core.logging import setup_logging
from app.api.v1.router import api_router

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Manage application lifecycle.
    Handles startup and shutdown events.
    """
    # Startup
    logger.info("Starting %s...", settings.app_name)
    logger.info("Environment: %s", settings.environment)
    logger.info("Debug mode: %s", settings.debug)

    # Initialize dependencies
    from app.api.dependencies import get_session_manager
    from app.services.neo4j.singleton import neo4j_driver

    app.state.session_manager = get_session_manager()
    logger.info("Session manager initialized")

    # Optional: Initialize Neo4j connection pool
    if not settings.debug:
        try:
            await neo4j_driver.get_driver()
            logger.info("Neo4j driver initialized")
        except Exception as e:
            logger.warning("Neo4j driver initialization failed: %s", e)

    logger.info("%s started successfully on %s:%s", settings.app_name, settings.host, settings.port)

    yield

    # Shutdown
    logger.info("Shutting down %s...", settings.app_name)

    # Cleanup Neo4j connections
    try:
        await neo4j_driver.close()
        logger.info("Neo4j connections closed")
    except Exception as e:
        logger.error("Error closing Neo4j connections: %s", e)

    logger.info("Shutdown complete")


# Create FastAPI application
app = FastAPI(
    title=settings.app_name,
    description="High-performance service for building Neo4j knowledge graphs from multiple data sources",
    version="0.1.0",
    debug=settings.debug,
    lifespan=lifespan,
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None,
    openapi_url="/openapi.json" if settings.debug else None,
)

# ============================================================================
# Middleware Configuration
# ============================================================================

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=settings.cors_allow_credentials,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# GZip Compression
app.add_middleware(GZipMiddleware, minimum_size=1000)

# Request timing middleware
@app.middleware("http")
async def add_process_time_header(request: Request, call_next): # pyright: ignore[reportMissingParameterType, reportUnknownParameterType]
    """Add processing time to response headers."""
    start_time = time.time()
    response = await call_next(request) # pyright: ignore[reportUnknownVariableType]
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(f"{process_time:.4f}") # pyright: ignore[reportUnknownMemberType]
    return response # pyright: ignore[reportUnknownVariableType]


# Request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next): # type: ignore
    """Log all incoming requests."""
    logger.info("%s %s", request.method, request.url.path)
    response = await call_next(request) # type: ignore
    logger.info("%s %s - Status: %s", request.method, request.url.path, response.status_code) # type: ignore
    return response # type: ignore


# ============================================================================
# Exception Handlers
# ============================================================================

@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(_request: Request, exc: StarletteHTTPException):
    """Handle HTTP exceptions."""
    logger.error("HTTP error: %s - %s", exc.status_code, exc.detail)
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "type": "HTTPException",
                "message": exc.detail,
                "status_code": exc.status_code,
            }
        },
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(_request: Request, exc: RequestValidationError):
    """Handle validation errors."""
    logger.error("Validation error: %s", exc.errors())
    return JSONResponse(
        status_code=422,
        content={
            "error": {
                "type": "ValidationError",
                "message": "Request validation failed",
                "details": exc.errors(),
            }
        },
    )


@app.exception_handler(Exception)
async def general_exception_handler(_request: Request, exc: Exception):
    """Handle all other exceptions."""
    logger.exception("Unhandled exception: %s", exc)
    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "type": "InternalServerError",
                "message": "An internal server error occurred",
                "details": str(exc) if settings.debug else None,
            }
        },
    )


# ============================================================================
# Routes
# ============================================================================

# Health check endpoint (always available)
@app.get("/health", tags=["health"])
async def health_check():
    """
    Health check endpoint.
    Returns the service status and version.
    """
    return {
        "status": "healthy",
        "service": settings.app_name,
        "version": "0.1.0",
        "environment": settings.environment,
    }


# Root endpoint
@app.get("/", tags=["root"])
async def root(): # type: ignore
    """
    Root endpoint.
    Returns API information and available endpoints.
    """
    return {
        "message": f"Welcome to {settings.app_name}",
        "version": "0.1.0",
        "environment": settings.environment,
        "documentation": "/docs" if settings.debug else "Contact admin for API docs",
        "health": "/health",
        "api": {
            "v1": "/api/v1"
        }
    } # type: ignore


# Include API router
app.include_router(api_router, prefix=f"/api/{settings.api_version}")

# ============================================================================
# Application Entry Point
# ============================================================================

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.reload,
        workers=1 if settings.reload else settings.workers,
        log_level=str(settings.log_level).lower(),
        access_log=True,
    )
