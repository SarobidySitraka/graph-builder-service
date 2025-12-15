"""Neo4j driver singleton for connection management."""
import logging
from typing import Optional
from neo4j import AsyncGraphDatabase, AsyncDriver

from app.core.config import settings
from app.core.exceptions import Neo4jConnectionError

logger = logging.getLogger(__name__)


class Neo4jDriverSingleton:
    """
    Singleton pattern for Neo4j driver management.

    Ensures only one driver instance is created and reused
    across the application lifecycle.
    """

    _instance: Optional['Neo4jDriverSingleton'] = None
    _driver: Optional[AsyncDriver] = None
    _initialized: bool = False

    def __new__(cls):
        """Ensure only one instance exists."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    async def get_driver(self) -> 'Neo4jDriverSingleton':
        """
        Get or create the Neo4j driver.

        Returns:
            Neo4jDriverSingleton instance with initialized driver

        Raises:
            Neo4jConnectionError: If driver initialization fails
        """
        if not self._initialized:
            await self._initialize_driver()
        return self

    async def _initialize_driver(self):
        """Initialize the Neo4j async driver."""
        if self._initialized:
            return

        try:
            logger.info(f"Initializing Neo4j driver: {settings.neo4j_uri}")

            self._driver = AsyncGraphDatabase.driver( # type: ignore
                settings.neo4j_uri,
                auth=(settings.neo4j_username, settings.neo4j_password),
                database=settings.neo4j_database,
                max_connection_lifetime=settings.neo4j_max_connection_lifetime,
                max_connection_pool_size=settings.neo4j_max_connection_pool_size,
                connection_timeout=settings.neo4j_connection_timeout,
            )

            # Verify connectivity
            await self._driver.verify_connectivity() # type: ignore

            self._initialized = True
            logger.info("Neo4j driver initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize Neo4j driver: {e}")
            self._initialized = False
            self._driver = None
            raise Neo4jConnectionError(
                message="Failed to initialize Neo4j driver",
                details={"error": str(e), "uri": settings.neo4j_uri}
            )

    async def close(self):
        """Close the Neo4j driver and cleanup resources."""
        if self._driver:
            try:
                logger.info("Closing Neo4j driver...")
                await self._driver.close()
                logger.info("Neo4j driver closed")
            except Exception as e:
                logger.error(f"Error closing Neo4j driver: {e}")
            finally:
                self._driver = None
                self._initialized = False

    def is_initialized(self) -> bool:
        """Check if driver is initialized."""
        return self._initialized

    async def verify_connection(self) -> bool:
        """
        Verify Neo4j connection is active.

        Returns:
            True if connection is active, False otherwise
        """
        if not self._initialized or not self._driver:
            return False

        try:
            await self._driver.verify_connectivity() # type: ignore
            return True
        except Exception as e:
            logger.warning(f"Neo4j connection verification failed: {e}")
            return False

    async def execute_query(self, query: str, parameters: dict = None): # type: ignore
        """
        Execute a Cypher query.

        Args:
            query: Cypher query string
            parameters: Query parameters

        Returns:
            Query result
        """
        if not self._initialized:
            await self._initialize_driver()

        async with self._driver.session() as session: # type: ignore
            result = await session.run(query, parameters or {}) # type: ignore
            return await result.data()

    def __repr__(self) -> str:
        """String representation."""
        status = "initialized" if self._initialized else "not initialized"
        return f"<Neo4jDriverSingleton {status} at {settings.neo4j_uri}>"


# Global singleton instance
neo4j_driver = Neo4jDriverSingleton()