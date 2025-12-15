"""Health check endpoints."""
from fastapi import APIRouter, Depends
from app.core.config import settings
# from app.api.dependencies import SessionManagerDep
from app.api.dependencies import get_session_manager
from app.services.session_manager2 import SessionManager

router = APIRouter()

@router.get("")
async def health_check():
    """
    Quick health check.
    Returns service status.
    """
    return {
        "status": "healthy",
        "service": settings.app_name,
        "version": "0.1.0",
    }


@router.get("/detailed")
async def detailed_health_check(session_manager: SessionManager = Depends(get_session_manager)):
    """
    Detailed health check with component status.
    Checks all dependencies.
    """
    health_status = {
        "status": "healthy",
        "service": settings.app_name,
        "version": "0.1.0",
        "environment": settings.environment,
        "components": {}
    }

    # Check session manager
    try:
        sessions = session_manager.list_sessions()
        health_status["components"]["session_manager"] = {
            "status": "healthy",
            "active_sessions": len(sessions)
        }
    except Exception as e:
        health_status["components"]["session_manager"] = {
            "status": "unhealthy",
            "error": str(e)
        }
        health_status["status"] = "degraded"

    # Check Neo4j connection
    try:
        from app.services.neo4j.singleton import neo4j_driver
        driver = await neo4j_driver.get_driver()
        driver._driver.verify_connectivity()
        health_status["components"]["neo4j"] = {"status": "healthy"}
    except Exception as e:
        health_status["components"]["neo4j"] = {
            "status": "unhealthy",
            "error": str(e)
        }
        health_status["status"] = "degraded"

    return health_status
