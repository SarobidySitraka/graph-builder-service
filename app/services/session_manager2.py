import time
import pickle
from typing import Dict, Any, Optional
from pathlib import Path
# import polars as pl
import pandas as pd
from app.models.response_data import TableData

class SessionManager:
    """Manages data sessions for caching loaded dataframes and metadata."""

    def __init__(self, cache_dir: str = "cache_dir", session_timeout: int = 3600):
        self.cache_dir = Path(cache_dir)
        self.session_timeout = session_timeout  # 1 hour default
        self._initialized = False

        # In-memory session metadata for fast access
        self._sessions: Dict[str, Dict[str, Any]] = {}

    def _ensure_initialized(self):
        """Lazy initialization of cache directory."""
        if not self._initialized:
            try:
                self.cache_dir.mkdir(exist_ok=True, parents=True)
                self._initialized = True
            except Exception as e:
                raise RuntimeError(f"Failed to initialize cache directory: {e}")

    def _get_session_path(self, session_id: str) -> Path:
        """Get the file path for a session."""
        return self.cache_dir / f"session_{session_id}.pkl"

    def _load_session_metadata(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Load session metadata from disk."""
        self._ensure_initialized()

        session_path = self._get_session_path(session_id)
        if not session_path.exists():
            return None

        try:
            with open(session_path, 'rb') as f:
                session_data = pickle.load(f)

            # Check if session has expired
            if time.time() - session_data.get('created_at', 0) > self.session_timeout:
                self.delete_session(session_id)
                return None

            return session_data
        except Exception as e:
            print(f"Error loading session {session_id}: {e}")
            return None

    def _save_session_metadata(self, session_id: str, session_data: Dict[str, Any]):
        """Save session metadata to disk."""
        self._ensure_initialized()

        session_path = self._get_session_path(session_id)
        try:
            with open(session_path, 'wb') as f:
                pickle.dump(session_data, f)
        except Exception as e:
            raise RuntimeError(f"Failed to save session data: {e}")

    def create_session(
            self,
            session_id: str,
            dataframes: Dict[str, pd.DataFrame],
            table_data: Dict[str, TableData],
            source_type: str = "file"  # "file" or "database"
    ) -> str:
        """Create a new session with dataframes and metadata."""
        self._ensure_initialized()

        session_data = { # type: ignore
            'session_id': session_id,
            'created_at': time.time(),
            'source_type': source_type,
            'table_data': table_data,
            'dataframe_count': len(dataframes),
            'total_rows': sum(len(df) for df in dataframes.values()),
            'dataframes': dataframes  # Store the actual dataframes
        }

        self._save_session_metadata(session_id, session_data) # type: ignore
        self._sessions[session_id] = session_data

        return session_id

    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session data by ID."""
        # Check in-memory cache first
        if session_id in self._sessions:
            session_data = self._sessions[session_id]
            # Check if still valid
            if time.time() - session_data.get('created_at', 0) <= self.session_timeout:
                return session_data
            else:
                # Expired, remove from memory
                del self._sessions[session_id]

        # Load from disk
        session_data = self._load_session_metadata(session_id)
        if session_data:
            self._sessions[session_id] = session_data
        return session_data

    def get_dataframes(self, session_id: str) -> Optional[Dict[str, pd.DataFrame]]:
        """Get dataframes for a session."""
        session = self.get_session(session_id)
        return session.get('dataframes') if session else None

    def get_table_data(self, session_id: str) -> Optional[Dict[str, TableData]]:
        """Get table metadata for a session."""
        session = self.get_session(session_id)
        return session.get('table_data') if session else None

    def get_session_info(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session information without the full dataframes."""
        session = self.get_session(session_id)
        if not session:
            return None

        # Return metadata without the actual dataframes
        info = session.copy()
        info.pop('dataframes', None)
        return info

    def delete_session(self, session_id: str) -> bool:
        """Delete a session and its data."""
        try:
            # Remove from memory
            self._sessions.pop(session_id, None)

            # Remove from disk
            session_path = self._get_session_path(session_id)
            if session_path.exists():
                session_path.unlink()

            return True
        except Exception as e:
            print(f"Error deleting session {session_id}: {e}")
            return False

    def list_sessions(self) -> Dict[str, Dict[str, Any]]:
        """List all active sessions."""
        self._ensure_initialized()

        active_sessions = {}
        current_time = time.time()

        # Check in-memory sessions
        for session_id, session_data in list(self._sessions.items()):
            if current_time - session_data.get('created_at', 0) <= self.session_timeout:
                active_sessions[session_id] = self.get_session_info(session_id)
            else:
                # Remove expired sessions
                del self._sessions[session_id]

        # Check disk for sessions not in memory
        if self.cache_dir.exists():
            for session_file in self.cache_dir.glob("session_*.pkl"):
                session_id = session_file.stem.replace("session_", "")
                if session_id not in active_sessions:
                    session_info = self.get_session_info(session_id)
                    if session_info:
                        active_sessions[session_id] = session_info

        return active_sessions # type: ignore

    def cleanup_expired_sessions(self) -> int:
        """Clean up expired sessions and return count of removed sessions."""
        self._ensure_initialized()

        current_time = time.time()
        removed_count = 0

        # Clean memory cache
        for session_id in list(self._sessions.keys()):
            session_data = self._sessions[session_id]
            if current_time - session_data.get('created_at', 0) > self.session_timeout:
                del self._sessions[session_id]
                removed_count += 1

        # Clean disk cache
        if self.cache_dir.exists():
            for session_file in self.cache_dir.glob("session_*.pkl"):
                try:
                    with open(session_file, 'rb') as f:
                        session_data = pickle.load(f)

                    if current_time - session_data.get('created_at', 0) > self.session_timeout:
                        session_file.unlink()
                        removed_count += 1
                except Exception as e:
                    # If we can't read the file, assume it's corrupted and delete it
                    try:
                        session_file.unlink()
                        removed_count += 1
                    except:
                        pass
                    print(f"Error cleaning session file {session_file}: {e}")

        return removed_count


# Global session manager instance - lazy initialization
session_manager = SessionManager()