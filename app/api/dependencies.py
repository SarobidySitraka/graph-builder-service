"""
FastAPI dependencies for dependency injection.
All heavy imports and initializations happen here once at startup.
"""
from functools import lru_cache
from typing import Annotated
from fastapi import Depends, Header, HTTPException, status

from app.core.config import settings
from app.services.session_manager2 import SessionManager


# ============================================================================
# Service Dependencies (Singletons)
# ============================================================================

@lru_cache()
def get_session_manager() -> SessionManager:
    """
    Get SessionManager singleton instance.
    Uses lru_cache to ensure only one instance is created.
    """
    return SessionManager(
        cache_dir=settings.cache_dir,
        session_timeout=settings.session_timeout
    )


# Dependency injection aliases
SessionManagerDep = Annotated[SessionManager, Depends(get_session_manager)]

# ============================================================================
# Authentication Dependencies
# ============================================================================

async def verify_api_key(
    x_api_key: str = Header(..., alias=settings.api_key_name)
) -> str:
    """
    Verify API key from request header.
    Raise 401 if invalid.
    """
    if x_api_key != settings.api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key"
        )
    return x_api_key


# Optional: Use this dependency to protect endpoints
ApiKeyDep = Annotated[str, Depends(verify_api_key)]


# ============================================================================
# Common Query Parameters
# ============================================================================

class PaginationParams:
    """Common pagination parameters."""

    def __init__(
            self,
            skip: int = 0,
            limit: int = 100,
    ):
        self.skip = skip
        self.limit = min(limit, 1000)  # Max 1000 items


PaginationDep = Annotated[PaginationParams, Depends()]