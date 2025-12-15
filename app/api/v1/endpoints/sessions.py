"""Routes pour la gestion des sessions."""
from fastapi import APIRouter, HTTPException, Depends
from app.api.dependencies import get_session_manager
from app.services.session_manager2 import SessionManager

router = APIRouter()

@router.get("/list")
async def list_sessions(session_manager: SessionManager = Depends(get_session_manager)):
    """List all active sessions."""
    try:
        sessions = session_manager.list_sessions()
        return {
            "sessions": sessions,
            "total_sessions": len(sessions)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list sessions: {str(e)}")

@router.get("/{session_id}")
async def get_session_info(
    session_id: str,
    session_manager: SessionManager = Depends(get_session_manager)
):
    """Get information about a specific session."""
    try:
        session_info = session_manager.get_session_info(session_id)
        if not session_info:
            raise HTTPException(status_code=404, detail="Session not found or expired")
        return {"session": session_info}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get session info: {str(e)}")

@router.delete("/{session_id}")
async def delete_session(
    session_id: str,
    session_manager: SessionManager = Depends(get_session_manager)
):
    """Delete a specific session."""
    try:
        success = session_manager.delete_session(session_id)
        if not success:
            raise HTTPException(status_code=404, detail="Session not found")
        return {"message": "Session deleted successfully", "success": True}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete session: {str(e)}")

@router.post("/cleanup")
async def cleanup_expired_sessions(session_manager: SessionManager = Depends(get_session_manager)):
    """Clean up expired sessions."""
    try:
        removed_count = session_manager.cleanup_expired_sessions()
        return {
            "message": f"Cleaned up {removed_count} expired sessions",
            "removed_count": removed_count,
            "success": True
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to cleanup sessions: {str(e)}")