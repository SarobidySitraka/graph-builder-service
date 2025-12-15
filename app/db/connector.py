"""
Database connection utilities.
"""
import logging
from contextlib import asynccontextmanager
from sqlalchemy import create_engine, Engine
from sqlalchemy.pool import QueuePool

from app.models.db_config import DBConfigBase
from app.models.types import DBType

logger = logging.getLogger(__name__)


def _build_connection_url(db_config: DBConfigBase) -> str:
    """Build SQLAlchemy connection URL from configuration."""
    if db_config.db_type == DBType.MYSQL:
        return (
            f"mysql+pymysql://{db_config.user}:{db_config.password}"
            f"@{db_config.host}:{db_config.port}/{db_config.db}"
        )
    elif db_config.db_type in [DBType.POSTGRES, DBType.POSTGRESQL]:
        return (
            f"postgresql+psycopg2://{db_config.user}:{db_config.password}"
            f"@{db_config.host}:{db_config.port}/{db_config.db}"
        )
    elif db_config.db_type == DBType.ORACLE:
        return (
            f"oracle+cx_oracle://{db_config.user}:{db_config.password}"
            f"@{db_config.host}:{db_config.port}/?service_name={db_config.db}"
        )
    elif db_config.db_type == DBType.SQLITE:
        return f"sqlite:///{db_config.db}"
    else:
        raise ValueError(f"Unsupported database type: {db_config.db_type}")


async def connect_db(db_config: DBConfigBase) -> Engine:
    """
    Create and return a database connection engine.
    
    Args:
        db_config: Database configuration
        
    Returns:
        SQLAlchemy Engine instance
        
    Note:
        Returns a synchronous engine. For async operations, use async context manager.
    """
    try:
        connection_url = _build_connection_url(db_config)
        
        # Create engine with connection pooling
        engine = create_engine(
            connection_url,
            poolclass=QueuePool,
            pool_size=5,
            max_overflow=10,
            pool_pre_ping=True,  # Verify connections before using
            echo=False,
        )
        
        logger.info(f"Connected to {db_config.db_type} database: {db_config.db}")
        return engine
        
    except Exception as e:
        logger.error(f"Failed to connect to database: {e}")
        raise


@asynccontextmanager
async def get_db_connection(db_config: DBConfigBase):
    """
    Async context manager for database connections.
    
    Usage:
        async with get_db_connection(db_config) as conn:
            result = await conn.execute(query)
    """
    engine = await connect_db(db_config)
    try:
        with engine.connect() as connection:
            yield connection
    finally:
        engine.dispose()

