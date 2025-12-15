"""
Database configuration models.
"""
from typing import Optional
from pydantic import Field

from app.models.base import BaseSchema
from app.models.types import DBType


class DBConfigBase(BaseSchema):
    """Base database configuration for connection testing."""
    db_type: DBType = Field(..., description="Database type")
    host: str = Field(..., description="Database host")
    port: int = Field(..., ge=1, le=65535, description="Database port")
    db: str = Field(..., description="Database name")
    user: str = Field(..., description="Database username")
    password: str = Field(..., description="Database password")


class DBConfig(DBConfigBase):
    """Complete database configuration with optional query."""
    query: Optional[str] = Field(None, description="Optional SQL query to execute")
    table_name: Optional[str] = Field(None, description="Optional table name to load")
    limit: Optional[int] = Field(None, ge=1, description="Optional limit on rows to load")
    pool_size: Optional[int] = Field(5, ge=1, description="Database connection pool size")
    max_overflow: Optional[int] = Field(10, ge=0, description="Maximum overflow size for connection pool")
    connect_timeout: Optional[int] = Field(10, ge=1, description="Connection timeout in seconds")

