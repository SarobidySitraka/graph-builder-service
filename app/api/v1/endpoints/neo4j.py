"""
Neo4j database inspection and management endpoints.
"""
import logging
from fastapi import APIRouter, HTTPException, status

from app.core.config import settings
from app.services.neo4j.singleton import neo4j_driver

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/status")
async def get_neo4j_status():
    """
    Get Neo4j connection status.
    
    Returns:
        Connection status and database information
    """
    try:
        driver = await neo4j_driver.get_driver()
        
        if not driver.is_initialized():
            return {
                "status": "disconnected",
                "message": "Neo4j driver not initialized"
            }
        
        # Verify connectivity
        is_connected = await driver.verify_connection()
        
        return {
            "status": "connected" if is_connected else "disconnected",
            "uri": settings.neo4j_uri,
            "database": settings.neo4j_database,
            "connected": is_connected
        }
        
    except Exception as e:
        logger.error(f"Error checking Neo4j status: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Neo4j connection error: {str(e)}"
        )


@router.get("/stats")
async def get_neo4j_stats():
    """
    Get Neo4j database statistics.
    
    Returns:
        Database statistics including node and relationship counts
    """
    try:
        driver = await neo4j_driver.get_driver()
        
        if not driver.is_initialized():
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Neo4j driver not initialized"
            )
        
        async_driver = driver._driver
        async with async_driver.session(database=settings.neo4j_database) as session:
            # Get node statistics
            node_query = """
            MATCH (n)
            RETURN labels(n) as labels, count(n) as count
            ORDER BY count DESC
            """
            
            # Get relationship statistics
            rel_query = """
            MATCH ()-[r]->()
            RETURN type(r) as type, count(r) as count
            ORDER BY count DESC
            """
            
            # Get total counts
            total_query = """
            MATCH (n)
            WITH count(n) as node_count
            MATCH ()-[r]->()
            WITH node_count, count(r) as rel_count
            RETURN node_count, rel_count
            """
            
            result = await session.run(total_query)
            record = await result.single()
            
            node_result = await session.run(node_query)
            node_records = []
            async for r in node_result:
                node_records.append(r.data())
            
            rel_result = await session.run(rel_query)
            rel_records = []
            async for r in rel_result:
                rel_records.append(r.data())
            
            return {
                "total_nodes": record["node_count"] if record else 0,
                "total_relationships": record["rel_count"] if record else 0,
                "node_labels": [
                    {"label": r["labels"][0] if r["labels"] else "Unknown", "count": r["count"]}
                    for r in node_records
                ],
                "relationship_types": [
                    {"type": r["type"], "count": r["count"]}
                    for r in rel_records
                ]
            }
            
    except Exception as e:
        logger.error(f"Error getting Neo4j stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get Neo4j statistics: {str(e)}"
        )


@router.post("/query")
async def execute_cypher_query(query: str):
    """
    Execute a custom Cypher query.
    
    Args:
        query: Cypher query string
        
    Returns:
        Query results
    """
    try:
        driver = await neo4j_driver.get_driver()
        
        if not driver.is_initialized():
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Neo4j driver not initialized"
            )
        
        async_driver = driver._driver
        async with async_driver.session(database=settings.neo4j_database) as session:
            result = await session.run(query)
            records = []
            async for r in result:
                records.append(r.data())
            
            return {
                "success": True,
                "results": records,
                "count": len(records)
            }
            
    except Exception as e:
        logger.error(f"Error executing Cypher query: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Query execution failed: {str(e)}"
        )

