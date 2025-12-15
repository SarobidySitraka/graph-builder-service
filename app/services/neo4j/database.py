"""
Neo4j database operations for graph creation.
"""
"""
Optimized Neo4j database operations for ultra-fast graph creation.
Single-pass batch processing with minimal overhead.
"""
import time
import logging
from typing import List, Dict, Any, cast, LiteralString
from neo4j import AsyncGraphDatabase, AsyncDriver

# from app.core.config import settings
from app.core.exceptions import Neo4jConnectionError, GraphCreationError

logger = logging.getLogger(__name__)


async def _create_batch(session, batch: List[Dict[str, Any]]):
    """
    Create nodes and relationships in single query.

    This is the core optimization: instead of 3 queries per config,
    we do 1 query for the entire batch.
    """
    if not batch:
        return

    # Prepare batch data
    configs_data = []
    for cfg in batch:
        configs_data.append({
            "source_label": cfg["source"]["label"],
            "source_props": cfg["source"]["properties"],
            "target_label": cfg["target"]["label"],
            "target_props": cfg["target"]["properties"],
            "rel_label": cfg["rels"]["label"],
            "rel_props": cfg["rels"].get("properties", {})
        })

    # Single optimized query for entire batch
    # Uses UNWIND to process all configs at once
    query = """
    UNWIND $configs AS cfg
    CALL apoc.merge.node(
        [cfg.source_label], 
        cfg.source_props
    ) YIELD node AS source
    CALL apoc.merge.node(
        [cfg.target_label], 
        cfg.target_props
    ) YIELD node AS target
    CALL apoc.merge.relationship(
        source,
        cfg.rel_label,
        {},
        cfg.rel_props,
        target,
        {}
    ) YIELD rel
    RETURN count(rel) AS created
    """

    try:
        result = await session.run(query, configs=configs_data)
        await result.consume()
    except Exception as e:
        logger.error(f"Batch creation error: {e}")
        raise


class Neo4jGraphCreation:
    """
    Ultra-optimized Neo4j graph creation service.

    Features:
    - Single-pass creation (nodes + relationships in one query)
    - Batch processing for performance
    - Minimal memory overhead
    - Fast UNWIND + MERGE operations
    """

    def __init__(
            self,
            uri: str,
            user: str,
            password: str,
            database: str = "neo4j",
            batch_size: int = 1000
    ):
        """
        Initialize Neo4j connection.

        Args:
            uri: Neo4j connection URI
            user: Username
            password: Password
            database: Database name
            batch_size: Records per batch
        """
        self.uri = uri
        self.user = user
        self.password = password
        self.database = database
        self.batch_size = batch_size
        self._driver: AsyncDriver = AsyncGraphDatabase.driver(
            self.uri,
            auth=(self.user, self.password),
            max_connection_lifetime=3600,
            max_connection_pool_size=50,
            connection_timeout=30
        )
        logger.info(f"Neo4j service initialized: {uri}, batch_size={batch_size}")

    async def _get_driver(self) -> AsyncDriver:
        """Get async driver."""
        return self._driver

    async def close(self):
        """Close driver connection."""
        if self._driver:
            await self._driver.close()
            self._driver = None
            logger.info("Neo4j driver closed")

    async def create_graph_data(
            self,
            graph_config_list: List[Dict[str, Any]],
            batch_size: int = None
    ) -> Dict[str, Any]:
        """
        Create complete graph (nodes + relationships) in one pass.

        Ultra-optimized: Uses UNWIND + MERGE in single query per batch.
        No separate node/relationship creation = 3x faster.

        Args:
            graph_config_list: List of graph configurations
            batch_size: Override default batch size

        Returns:
            Simple statistics dict

        Example config:
            {
                "source": {
                    "label": "Person",
                    "properties": {"id": "1", "name": "John"}
                },
                "target": {
                    "label": "Company",
                    "properties": {"id": "10", "name": "Acme"}
                },
                "rels": {
                    "label": "WORKS_AT",
                    "properties": {"since": "2020"}
                }
            }
        """
        start_time = time.time()
        total_configs = len(graph_config_list)

        if total_configs == 0:
            raise GraphCreationError("Empty graph configuration list")

        # Use provided batch_size or default
        batch_size = batch_size or self.batch_size

        # Split into batches
        batches = [
            graph_config_list[i:i + batch_size]
            for i in range(0, total_configs, batch_size)
        ]

        logger.info(f"Creating graph: {total_configs} configs in {len(batches)} batches")

        try:
            driver = await self._get_driver()
            async with driver.session(database=self.database) as session:
                for batch_idx, batch in enumerate(batches, 1):
                    try:
                        await _create_batch(session, batch)
                        logger.info(f"Batch {batch_idx}/{len(batches)} processed ({len(batch)} configs)")
                    except Exception as e:
                        logger.error(f"Batch {batch_idx} failed: {e}")
                        raise GraphCreationError(
                            message=f"Failed to process batch {batch_idx}",
                            details={"error": str(e), "batch_size": len(batch)}
                        )

            elapsed = round(time.time() - start_time, 2)

            logger.info(f"Graph creation completed in {elapsed}s")

            return {
                "configs_processed": total_configs,
                "batches": len(batches),
                "elapsed_time_sec": elapsed
            }

        except Neo4jConnectionError:
            raise
        except Exception as e:
            logger.exception(f"Graph creation failed: {e}")
            raise GraphCreationError(
                message="Failed to create graph",
                details={"error": str(e), "configs": total_configs}
            )

    async def execute_query(self, query: str, parameters: Dict = None):
        """
        Execute custom Cypher query.

        Args:
            query: Cypher query string
            parameters: Query parameters

        Returns:
            Query results as list of dicts
        """
        driver = await self._get_driver()

        try:
            async with driver.session(database=self.database) as session:
                query = cast(LiteralString, query)
                result = await session.run(query, parameters or {})
                records = await result.data()
                return records
        except Exception as e:
            logger.error(f"Query execution failed: {e}")
            raise Neo4jConnectionError(
                message="Failed to execute query",
                details={"error": str(e)}
            )

    async def clear_database(self):
        """
        Clear all data from database.
        Use with caution!
        """
        logger.warning("Clearing database - all data will be deleted!")

        try:
            await self.execute_query("MATCH (n) DETACH DELETE n")
            logger.info("Database cleared")
        except Exception as e:
            logger.error(f"Failed to clear database: {e}")
            raise

    async def get_statistics(self) -> Dict[str, Any]:
        """
        Get database statistics.

        Returns:
            Node and relationship counts
        """
        try:
            # Count nodes
            nodes_result = await self.execute_query("MATCH (n) RETURN count(n) AS count")
            total_nodes = nodes_result[0]["count"] if nodes_result else 0

            # Count relationships
            rels_result = await self.execute_query("MATCH ()-[r]->() RETURN count(r) AS count")
            total_rels = rels_result[0]["count"] if rels_result else 0

            return {
                "total_nodes": total_nodes,
                "total_relationships": total_rels
            }
        except Exception as e:
            logger.error(f"Failed to get statistics: {e}")
            return {
                "total_nodes": 0,
                "total_relationships": 0,
                "error": str(e)
            }

#
# # =============================================================
# import logging
# from typing import List, Dict, Any, Optional, LiteralString, cast
# from neo4j import AsyncGraphDatabase, AsyncDriver
# import polars as pl
#
# logger = logging.getLogger(__name__)
#
# class Neo4jGraphCreation:
#     """
#     Class for creating graphs in Neo4j from dataframes and configurations.
#     """
#
#     def __init__(self, uri: str, user: str, password: str, database: str = "neo4j"):
#         """
#         Initialize Neo4j graph creation client.
#
#         Args:
#             uri: Neo4j connection URI
#             user: Neo4j username
#             password: Neo4j password
#             database: Neo4j database name
#         """
#         self.uri = uri
#         self.user = user
#         self.password = password
#         self.database = database
#         self._driver: Optional[AsyncDriver] = None
#
#     async def _get_driver(self) -> AsyncDriver:
#         """Get or create Neo4j driver."""
#         if self._driver is None:
#             self._driver = AsyncGraphDatabase.driver( # type: ignore
#                 self.uri,
#                 auth=(self.user, self.password)
#             )
#         return self._driver
#
#     async def create_graph_data(
#         self,
#         graph_config_list: List[Dict[str, Any]],
#         batch_size: int = 1000
#     ) -> Dict[str, Any]:
#         """
#         Create graph data in Neo4j from graph configurations.
#
#         Args:
#             graph_config_list: List of processed graph configurations
#             batch_size: Number of records to process per batch
#
#         Returns:
#             Dictionary with creation statistics
#         """
#         driver = await self._get_driver()
#         stats = { # type: ignore
#             "nodes_created": 0,
#             "relationships_created": 0,
#             "errors": []
#         }
#
#         async with driver.session(database=self.database) as session: # type: ignore
#             for config in graph_config_list:
#                 try:
#                     # Extract configuration
#                     source_config = config["source"]
#                     target_config = config["target"]
#                     rel_config = config["relationship"]
#
#                     source_df: pl.DataFrame = source_config["dataframe"]
#                     target_df: pl.DataFrame = target_config["dataframe"]
#
#                     # Create source nodes
#                     source_stats = await self._create_nodes( # type: ignore
#                         session,
#                         source_config["label"],
#                         source_df,
#                         source_config["properties"],
#                         source_config.get("key"),
#                         batch_size
#                     )
#                     stats["nodes_created"] += source_stats["created"]
#
#                     # Create target nodes
#                     target_stats = await self._create_nodes( # type: ignore
#                         session,
#                         target_config["label"],
#                         target_df,
#                         target_config["properties"],
#                         target_config.get("key"),
#                         batch_size
#                     )
#                     stats["nodes_created"] += target_stats["created"]
#
#                     # Create relationships
#                     # For simplicity, we'll create relationships based on matching keys
#                     # This assumes source and target share a common key
#                     rel_stats = await self._create_relationships( # type: ignore
#                         session,
#                         source_config["label"],
#                         target_config["label"],
#                         rel_config["label"],
#                         source_df,
#                         target_df,
#                         source_config.get("key"),
#                         target_config.get("key"),
#                         rel_config.get("properties", []),
#                         batch_size
#                     )
#                     stats["relationships_created"] += rel_stats["created"]
#
#                 except Exception as e:
#                     logger.error(f"Error creating graph data: {e}")
#                     stats["errors"].append(str(e)) # type: ignore
#
#         return stats # type: ignore
#
#     async def _create_nodes(
#         self,
#         session, # type: ignore
#         label: str,
#         df: pl.DataFrame,
#         properties: List[str],
#         key_property: Optional[str] = None,
#         batch_size: int = 1000
#     ) -> Dict[str, int]:
#         """Create nodes in Neo4j from dataframe."""
#         created = 0
#         key_prop = key_property or (properties[0] if properties else None)
#
#         # Process in batches
#         for i in range(0, len(df), batch_size):
#             batch = df.slice(i, batch_size)
#
#             # Create nodes using UNWIND for batch insertion
#             # Prepare batch data
#             batch_data = []
#             for row in batch.iter_rows(named=True):
#                 node_data = {prop: row[prop] for prop in properties if prop in row}
#                 batch_data.append(node_data) # type: ignore
#
#             if not batch_data:
#                 continue
#
#             # Build query with parameterized properties
#             if key_prop:
#                 query = f"""
#                 UNWIND $batch AS row
#                 MERGE (n:{label} {{{key_prop}: row.{key_prop}}})
#                 SET n += row
#                 RETURN count(n) as created
#                 """
#             else:
#                 # If no key property, create nodes without MERGE
#                 query = f"""
#                 UNWIND $batch AS row
#                 CREATE (n:{label})
#                 SET n += row
#                 RETURN count(n) as created
#                 """
#
#             result = await session.run(cast(LiteralString, query), batch=batch_data) # type: ignore
#             record = await result.single() # type: ignore
#             created += record["created"] if record else len(batch) # type: ignore
#
#         return {"created": created}
#
#     async def _create_relationships(
#         self,
#         session, # type: ignore
#         source_label: str,
#         target_label: str,
#         rel_label: str,
#         source_df: pl.DataFrame,
#         target_df: pl.DataFrame,
#         source_key: Optional[str] = None,
#         target_key: Optional[str] = None,
#         rel_properties: List[str] = [],
#         batch_size: int = 1000
#     ) -> Dict[str, int]:
#         """Create relationships in Neo4j."""
#         created = 0
#
#         # Simple implementation: create relationships based on matching rows
#         # This assumes source and target dataframes have matching keys
#         if source_key and target_key:
#             # Use MERGE to create relationships
#             query = f"""
#             UNWIND $batch AS row
#             MATCH (source:{source_label} {{{source_key}: row.source_key}})
#             MATCH (target:{target_label} {{{target_key}: row.target_key}})
#             MERGE (source)-[r:{rel_label}]->(target)
#             SET r += row.rel_props
#             RETURN count(r) as created
#             """
#
#             # Process in batches
#             for i in range(0, len(source_df), batch_size):
#                 batch = source_df.slice(i, batch_size)
#
#                 batch_data = []
#                 for row in batch.iter_rows(named=True):
#                     batch_data.append({ # type: ignore
#                         "source_key": row[source_key],
#                         "target_key": row.get(target_key, row[source_key]),  # Fallback
#                         "rel_props": {prop: row[prop] for prop in rel_properties if prop in row}
#                     })
#
#                 result = await session.run(cast(LiteralString, query), batch=batch_data) # type: ignore
#                 record = await result.single() # type: ignore
#                 created += record["created"] if record else 0 # type: ignore
#
#         return {"created": created}
#
#     async def execute_query(self, query: str) -> Any:
#         """
#         Execute a Cypher query.
#
#         Args:
#             query: Cypher query string
#
#         Returns:
#             Query result
#         """
#         driver = await self._get_driver()
#         async with driver.session(database=self.database) as session: # type: ignore
#             result = await session.run(cast(LiteralString, query))
#             records = []
#             async for record in result:
#                 records.append(record.data()) # type: ignore
#             return records # type: ignore
#
#     async def close(self):
#         """Close the Neo4j driver connection."""
#         if self._driver:
#             await self._driver.close()
#             self._driver = None
#
