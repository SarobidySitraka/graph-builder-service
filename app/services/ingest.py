"""
Data ingestion service for loading data from files and databases.
"""
import logging
from typing import Dict, List, Optional, Any, Hashable, cast
from pathlib import Path
# import polars as pl
import pandas as pd
from fastapi import UploadFile

from app.models.db_config import DBConfig
from app.models.response_data import TableData
from app.services.file_loader import load_file # type: ignore
from app.services.db_loader import (
    load_table_from_db,
    execute_query,
    list_tables
)
from app.db.connector import connect_db

logger = logging.getLogger(__name__)

async def create_data_frame(
    files: Optional[List[UploadFile]] = None,
    db_config: Optional[DBConfig] = None
) -> tuple[Dict[str, TableData], Dict[str, pd.DataFrame]]:
    """
    Create dataframes and table metadata from files or database.
    
    Args:
        files: Optional list of uploaded files
        db_config: Optional database configuration
        
    Returns:
        Tuple of (table_data_dict, dataframes_dict)
        
    Raises:
        ValueError: If neither files nor db_config is provided
    """
    if files:
        return await _create_data_frame_from_files(files)
    elif db_config:
        return await _create_data_frame_from_db(db_config)
    else:
        raise ValueError("Either 'files' or 'db_config' must be provided")


async def _create_data_frame_from_files(
    files: List[UploadFile]
) -> tuple[Dict[str, TableData], Dict[str, pd.DataFrame]]:
    """Create dataframes from uploaded files."""
    table_data: Dict[str, TableData] = {}
    dataframes: Dict[str, pd.DataFrame] = {}
    
    for file in files:
        try:
            # Read file content
            content = await file.read()
            filename = file.filename or "unknown"
            
            # Generate table name from filename (without extension)
            table_name = Path(filename).stem
            
            logger.info(f"Loading file: {filename}")
            
            # Load as DataFrame
            df = await load_file(content, filename)
            
            # Store dataframe
            dataframes[table_name] = df
            
            # Create table metadata
            columns = df.columns.to_list()
            total_rows = len(df)
            total_columns = len(columns)
            
            # Create preview (first 5 rows as dict)
            preview = cast(List[Dict[Hashable, Any]], df.head(5).to_dict(orient="records")) if total_rows > 0 else None
            
            table_data[table_name] = TableData(
                table_name=table_name,
                columns=columns,
                total_rows=total_rows,
                total_columns=total_columns,
                preview=preview
            )
            
            logger.info(f"Loaded {filename}: {total_rows} rows, {total_columns} columns")
            
        except Exception as e:
            logger.error(f"Error processing file {file.filename}: {e}")
            raise
    
    return table_data, dataframes


async def _create_data_frame_from_db(
    db_config: DBConfig
) -> tuple[Dict[str, TableData], Dict[str, pd.DataFrame]]:
    """Create dataframes from database."""
    table_data: Dict[str, TableData] = {}
    dataframes: Dict[str, pd.DataFrame] = {}
    
    try:
        # Connect to database
        engine = await connect_db(db_config)
        
        # If query is provided, execute it
        if db_config.query:
            logger.info("Executing custom query")
            df = await execute_query(engine, db_config.query)
            
            table_name = db_config.table_name or "query_result"
            dataframes[table_name] = df
            
            columns = df.columns.to_list()
            total_rows = len(df)
            total_columns = len(columns)
            preview = cast(List[Dict[Hashable, Any]], df.head(5).to_dicts()) if total_rows > 0 else None
            
            table_data[table_name] = TableData(
                table_name=table_name,
                columns=columns,
                total_rows=total_rows,
                total_columns=total_columns,
                preview=preview
            )
            
        # If table_name is provided, load that table
        elif db_config.table_name:
            logger.info(f"Loading table: {db_config.table_name}")
            df = await load_table_from_db(
                engine,
                db_config.table_name,
                limit=db_config.limit,
                db_type=db_config.db_type
            )
            
            table_name = db_config.table_name
            dataframes[table_name] = df
            
            columns = df.columns
            total_rows = len(df)
            total_columns = len(columns)
            preview = cast(List[Dict[Hashable, Any]], df.head(5).to_dicts()) if total_rows > 0 else None
            
            table_data[table_name] = TableData(
                table_name=table_name,
                columns=columns,
                total_rows=total_rows,
                total_columns=total_columns,
                preview=preview
            )
            
        # Otherwise, load all tables
        else:
            logger.info("Loading all tables from database")
            tables = await list_tables(engine)
            
            for table_name in tables:
                try:
                    df = await load_table_from_db(
                        engine,
                        table_name,
                        limit=db_config.limit,
                        db_type=db_config.db_type
                    )
                    
                    dataframes[table_name] = df
                    
                    columns = df.columns
                    total_rows = len(df)
                    total_columns = len(columns)
                    preview = cast(List[Dict[Hashable, Any]], df.head(5).to_dicts()) if total_rows > 0 else None
                    
                    table_data[table_name] = TableData(
                        table_name=table_name,
                        columns=columns,
                        total_rows=total_rows,
                        total_columns=total_columns,
                        preview=preview
                    )
                    
                    logger.info(f"Loaded table {table_name}: {total_rows} rows")
                    
                except Exception as e:
                    logger.warning(f"Failed to load table {table_name}: {e}")
                    continue
        
        engine.dispose()
        
    except Exception as e:
        logger.error(f"Error loading from database: {e}")
        raise
    
    return table_data, dataframes

