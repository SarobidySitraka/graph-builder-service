"""Custom exceptions for the application."""
from typing import Any, Dict, Optional


class GraphBuilderException(Exception):
    """Base exception for all application errors."""

    def __init__(
            self,
            message: str,
            status_code: int = 500,
            details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)


class DatabaseConnectionError(GraphBuilderException):
    """Raised when database connection fails."""

    def __init__(self, message: str = "Database connection failed", details: Optional[Dict[str, Any]] = None):
        super().__init__(message, status_code=503, details=details)


class Neo4jConnectionError(GraphBuilderException):
    """Raised when Neo4j connection fails."""

    def __init__(self, message: str = "Neo4j connection failed", details: Optional[Dict[str, Any]] = None):
        super().__init__(message, status_code=503, details=details)


class SessionNotFoundError(GraphBuilderException):
    """Raised when session is not found."""

    def __init__(self, session_id: str):
        super().__init__(
            message=f"Session not found: {session_id}",
            status_code=404,
            details={"session_id": session_id}
        )


class SessionExpiredError(GraphBuilderException):
    """Raised when session has expired."""

    def __init__(self, session_id: str):
        super().__init__(
            message=f"Session expired: {session_id}",
            status_code=410,
            details={"session_id": session_id}
        )


class InvalidFileFormatError(GraphBuilderException):
    """Raised when file format is invalid."""

    def __init__(self, filename: str, expected_formats: list):
        super().__init__(
            message=f"Invalid file format for {filename}. Expected: {', '.join(expected_formats)}",
            status_code=400,
            details={"filename": filename, "expected_formats": expected_formats}
        )


class FileTooLargeError(GraphBuilderException):
    """Raised when uploaded file is too large."""

    def __init__(self, filename: str, size: int, max_size: int):
        super().__init__(
            message=f"File {filename} is too large ({size} bytes). Maximum size: {max_size} bytes",
            status_code=413,
            details={"filename": filename, "size": size, "max_size": max_size}
        )


class GraphConfigurationError(GraphBuilderException):
    """Raised when graph configuration is invalid."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, status_code=400, details=details)


class DataIngestionError(GraphBuilderException):
    """Raised when data ingestion fails."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, status_code=500, details=details)


class GraphCreationError(GraphBuilderException):
    """Raised when graph creation fails."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, status_code=500, details=details)