"""
Response data models for API responses.
"""
from typing import Hashable, List, Dict, Any, Optional
from pydantic import Field
from app.models.base import BaseSchema
from app.models.types import DBType

class TableData(BaseSchema):
    """Table metadata information."""
    table_name: str = Field(..., description="Table name")
    columns: List[str] = Field(..., description="Column names")
    total_rows: int = Field(..., ge=0, description="Total number of rows")
    total_columns: int = Field(..., ge=0, description="Total number of columns")
    preview: Optional[List[Dict[Hashable, Any]]] = Field(None, description="Sample rows preview")

class DataResponses(BaseSchema):
    """Response model for data ingestion."""
    message: str = Field(..., description="Status message")
    total_tables: int = Field(..., ge=0, description="Total number of tables")
    data_tables: Dict[str, TableData] = Field(default_factory=dict, description="Table metadata")
    db_type: Optional[DBType] = Field(None, description="Database type (if from database)")
    database: Optional[str] = Field(None, description="Database name (if from database)")
