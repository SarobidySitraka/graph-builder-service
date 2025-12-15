from pydantic import BaseModel, Field
from fastapi import File, UploadFile
from typing import Optional

class FileConfig(BaseModel):
    """Configuration for file loading."""
    file: UploadFile = File(..., description="File to be loaded")
    delimiter: Optional[str] = Field(default=None, description="Delimiter for CSV/TSV/DSV files")
    has_header: Optional[bool] = Field(default=True, description="Indicates if the file has a header row")
    infer_schema: Optional[bool] = Field(default=True, description="Whether to infer schema from data")