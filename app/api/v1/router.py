"""
Main API v1 router.
Aggregates all endpoint routers and provides API-wide configuration.
"""
from fastapi import APIRouter
from app.api.v1.endpoints import (
    files,
    databases,
    sessions,
    graph_builder,
    neo4j,
    health,
)

# Create main API router
api_router = APIRouter()

# ============================================================================
# Health Endpoints (No authentication required)
# ============================================================================
api_router.include_router(
    health.router,
    prefix="/health",
    tags=["Health"],
    responses={
        200: {"description": "Service is healthy"},
        503: {"description": "Service is unhealthy"}
    }
)

# ============================================================================
# File Management Endpoints
# ============================================================================
api_router.include_router(
    files.router,
    prefix="/files",
    tags=["Files"],
    responses={
        400: {"description": "Invalid file or format"},
        413: {"description": "File too large"},
        500: {"description": "Internal server error"}
    }
)

# ============================================================================
# Database Connection Endpoints
# ============================================================================
api_router.include_router(
    databases.router,
    prefix="/databases",
    tags=["Databases"],
    responses={
        400: {"description": "Invalid database configuration"},
        503: {"description": "Database connection failed"},
        500: {"description": "Internal server error"}
    }
)

# ============================================================================
# Session Management Endpoints
# ============================================================================
api_router.include_router(
    sessions.router,
    prefix="/sessions",
    tags=["Sessions"],
    responses={
        404: {"description": "Session not found"},
        410: {"description": "Session expired"},
        500: {"description": "Internal server error"}
    }
)

# ============================================================================
# Graph Builder Endpoints
# ============================================================================
api_router.include_router(
    graph_builder.router,
    prefix="/graph_builder",
    tags=["Graph Builder"],
    responses={
        400: {"description": "Invalid graph configuration"},
        404: {"description": "Session not found"},
        500: {"description": "Graph creation failed"}
    }
)

# ============================================================================
# Neo4j Database Endpoints
# ============================================================================
api_router.include_router(
    neo4j.router,
    prefix="/neo4j",
    tags=["Neo4j"],
    responses={
        503: {"description": "Neo4j connection failed"},
        500: {"description": "Internal server error"}
    }
)


# ============================================================================
# API Root Endpoint
# ============================================================================
@api_router.get(
    "",
    tags=["Root"],
    summary="API Information",
    description="Get information about the API and available endpoints"
)
async def api_root():
    """
    Get API v1 information.

    Returns:
        API metadata and available endpoint groups
    """
    return {
        "version": "v1",
        "description": "Graph Builder Service API",
        "endpoints": {
            "health": {
                "path": "/api/v1/health",
                "description": "Health check endpoints"
            },
            "files": {
                "path": "/api/v1/files",
                "description": "File upload and management"
            },
            "databases": {
                "path": "/api/v1/databases",
                "description": "Database connections and data import"
            },
            "sessions": {
                "path": "/api/v1/sessions",
                "description": "Data session management"
            },
            "graph_builder": {
                "path": "/api/v1/graph_builder",
                "description": "Neo4j graph creation"
            },
            "neo4j": {
                "path": "/api/v1/neo4j",
                "description": "Neo4j database inspection"
            }
        },
        "documentation": {
            "swagger": "/docs",
            "redoc": "/redoc",
            "openapi": "/openapi.json"
        }
    }