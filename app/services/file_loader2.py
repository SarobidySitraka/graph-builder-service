"""
File loading utilities for various file formats.
"""
import logging
from typing import Optional
from pathlib import Path
# import polars as pl
import pandas as pd

logger = logging.getLogger(__name__)


def load_csv(file_path: str | Path, **kwargs) -> pd.DataFrame: # type: ignore
    """Load CSV file as Polars DataFrame."""
    return pd.read_csv(file_path, **kwargs) # type: ignore


def load_excel(file_path: str | Path, sheet_name: Optional[str] = None, **kwargs) -> pd.DataFrame:
    """Load Excel file as Polars DataFrame."""
    # Read with pandas first, then convert to polars
    df_pandas = pd.read_excel(file_path, sheet_name=sheet_name, **kwargs)
    return df_pandas


def load_json(file_path: str | Path, **kwargs) -> pd.DataFrame:
    """Load JSON file as Polars DataFrame."""
    return pd.read_json(file_path, **kwargs)


def load_file(file_path: str | Path, file_extension: Optional[str] = None) -> pd.DataFrame:
    """
    Load a file based on its extension.
    
    Args:
        file_path: Path to the file
        file_extension: Optional file extension override
        
    Returns:
        Polars DataFrame
    """
    path = Path(file_path)
    ext = file_extension or path.suffix.lower()
    
    try:
        if ext in ['.csv', '.tsv', '.dsv', '.txt']:
            return load_csv(path)
        elif ext in ['.xlsx', '.xls']:
            return load_excel(path)
        elif ext == '.json':
            return load_json(path)
        else:
            raise ValueError(f"Unsupported file extension: {ext}")
    except Exception as e:
        logger.error(f"Error loading file {file_path}: {e}")
        raise


async def load_file_from_bytes(content: bytes, filename: str, **kwargs) -> pd.DataFrame:
    """
    Load file from bytes content.
    
    Args:
        content: File content as bytes
        filename: Original filename (used to determine format)
        **kwargs: Additional arguments for file readers
        
    Returns:
        Polars DataFrame
    """
    import io
    
    path = Path(filename)
    ext = path.suffix.lower()
    
    try:
        if ext in ['.csv', '.tsv', '.dsv', '.txt']:
            # Use StringIO for CSV
            try:
                content_str = content.decode('utf-8')
                return pd.read_csv(io.StringIO(content_str), sep=',', **kwargs)
            except:
                content_str = content.decode('latin1')
                return pd.read_csv(io.StringIO(content_str), sep=';')
        elif ext in ['.xlsx', '.xls']:
            # Use BytesIO for Excel
            return pd.read_excel(io.BytesIO(content), **kwargs)
        elif ext == '.json':
            # Use StringIO for JSON
            try:
                content_str = content.decode('utf-8')
                return pd.read_json(io.StringIO(content_str), **kwargs)
            except:
                content_str = content.decode('latin1')
                return pd.read_json(io.StringIO(content_str), **kwargs)
        else:
            raise ValueError(f"Unsupported file extension: {ext}")
    except Exception as e:
        logger.error(f"Error loading file from bytes {filename}: {e}")
        raise

