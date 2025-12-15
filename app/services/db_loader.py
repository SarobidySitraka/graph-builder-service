"""
Database loading utilities.
"""
import logging
from typing import List, Optional
# import polars as pl
import pandas as pd
from sqlalchemy import text, inspect
from sqlalchemy.engine import Engine
from app.models.types import DBType

logger = logging.getLogger(__name__)

async def load_table_from_db(
    engine: Engine,
    table_name: str,
    limit: Optional[int] = None,
    db_type: Optional[DBType] = None
) -> pd.DataFrame:
    """
    Load a table from database as Polars DataFrame.
    
    Args:
        engine: SQLAlchemy engine
        table_name: Name of the table to load
        limit: Optional limit on number of rows
        db_type: Database type (for SQL dialect differences)
        
    Returns:
        Polars DataFrame
    """
    try:
        # Build query
        if limit:
            if db_type == DBType.ORACLE:
                query = text(f"SELECT * FROM {table_name} WHERE ROWNUM <= {limit}")
            elif db_type == DBType.POSTGRES or db_type == DBType.POSTGRESQL:
                query = text(f"SELECT * FROM {table_name} LIMIT {limit}")
            else:
                query = text(f"SELECT * FROM {table_name} LIMIT {limit}")
        else:
            query = text(f"SELECT * FROM {table_name}")
        
        # Execute query and convert to pandas first, then polars
        with engine.connect() as conn:
            result = conn.execute(query)
            # Convert to pandas DataFrame
            df_pandas = result.fetchall()
            columns = result.keys()
            
            # Convert to Polars DataFrame
            if df_pandas:
                df_dict = {col: [row[i] for row in df_pandas] for i, col in enumerate(columns)}
                return pd.DataFrame(df_dict)
            else:
                # Empty result
                return pd.DataFrame({col: [] for col in columns})
                
    except Exception as e:
        logger.error(f"Error loading table {table_name}: {e}")
        raise


async def execute_query(engine: Engine, query: str) -> pd.DataFrame:
    """
    Execute a custom SQL query and return as Polars DataFrame.
    
    Args:
        engine: SQLAlchemy engine
        query: SQL query string
        
    Returns:
        Polars DataFrame
    """
    try:
        with engine.connect() as conn:
            result = conn.execute(text(query))
            columns = result.keys()
            rows = result.fetchall()
            
            if rows:
                df_dict = {col: [row[i] for row in rows] for i, col in enumerate(columns)}
                return pd.DataFrame(df_dict)
            else:
                return pd.DataFrame({col: [] for col in columns})
                
    except Exception as e:
        logger.error(f"Error executing query: {e}")
        raise


async def list_tables(engine: Engine) -> List[str]:
    """
    List all tables in the database.
    
    Args:
        engine: SQLAlchemy engine
    Returns:
        List of table names
    """
    try:
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        return tables
    except Exception as e:
        logger.error(f"Error listing tables: {e}")
        raise


async def get_table_columns(engine: Engine, table_name: str) -> List[str]:
    """
    Get column names for a table.
    
    Args:
        engine: SQLAlchemy engine
        table_name: Name of the table
        
    Returns:
        List of column names
    """
    try:
        inspector = inspect(engine)
        columns = [col['name'] for col in inspector.get_columns(table_name)]
        return columns
    except Exception as e:
        logger.error(f"Error getting columns for {table_name}: {e}")
        raise

