"""
Type definitions and enums.
"""
from enum import Enum


class DBType(str, Enum):
    """Supported database types."""
    MYSQL = "mysql"
    POSTGRES = "postgres"
    POSTGRESQL = "postgresql"
    ORACLE = "oracle"
    SQLITE = "sqlite"


class SourceType(str, Enum):
    """Data source types."""
    FILE = "file"
    DATABASE = "database"

