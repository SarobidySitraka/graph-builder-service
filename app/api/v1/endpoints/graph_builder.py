"""Routes pour la construction de graphes Neo4j."""
from typing import List
from fastapi import APIRouter, HTTPException, Body, Depends

from app.core.config import settings
from app.api.dependencies import get_session_manager
from app.services.session_manager2 import SessionManager
from app.services.neo4j.graph_api import create_graph_api
from app.services.neo4j.database import Neo4jGraphCreation
from app.models.graph_config import GraphConfig

router = APIRouter()

@router.post("/create_graph_data/{session_id}")
async def create_graph_data(
        session_id: str,
        graph_config_list: List[GraphConfig] = Body(...),
        limit: int | None = None,
        session_manager: SessionManager = Depends(get_session_manager),
):
    """Create graph data in Neo4j from session data."""
    try:
        session_info = session_manager.get_session_info(session_id)
        if not session_info:
            raise HTTPException(status_code=404, detail="Session not found or expired")

        dataframes = session_manager.get_dataframes(session_id)
        if not dataframes:
            raise HTTPException(status_code=404, detail="No data found for this session")

        if not graph_config_list or len(graph_config_list) == 0:
            raise HTTPException(status_code=400, detail="Graph configuration list is empty")

        graph_api = await create_graph_api(
            graph_config_list=graph_config_list,
            data_dico=dataframes
        )

        graph_builder = Neo4jGraphCreation(
            uri=settings.neo4j_uri,
            user=settings.neo4j_username,
            password=settings.neo4j_password,
            database=settings.neo4j_database
        )

        # Apply limit if specified
        graph_api_to_process = graph_api[:limit] if limit else graph_api

        result = await graph_builder.create_graph_data(
            graph_config_list=graph_api_to_process,
            batch_size=1000
        )
        await graph_builder.close()

        return {"success": True, "response": result}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create graph data: {str(e)}")


@router.post("/validate_graph_config")
async def validate_graph_config(graph_config: List[GraphConfig] = Body(...)):
    """Validate graph configuration."""
    try:
        if not graph_config or len(graph_config) == 0:
            return {"success": False, "error": "Graph configuration list is empty"}

        validation_errors: list[str] = []
        for i, config in enumerate(graph_config):
            if not config.source or not config.source.label:
                validation_errors.append(f"Config {i}: Missing source label")
            if not config.target or not config.target.label:
                validation_errors.append(f"Config {i}: Missing target label")
            if not config.rels or not config.rels.label:
                validation_errors.append(f"Config {i}: Missing relationship label")

        if validation_errors:
            return {"success": False, "errors": validation_errors}

        return {"success": True, "message": f"Validated {len(graph_config)} graph configurations"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Validation failed: {str(e)}")


@router.post("/check_neo4j_db")
async def check_neo4j_db():
    """Check Neo4j database statistics."""
    try:
        query_str = """
            MATCH (n)
            WITH COUNT(n) as nodes, labels(n) as label_list
            WITH nodes, COLLECT(DISTINCT label_list[0]) as labels
            MATCH ()-[r]->()
            WITH nodes, labels, COUNT(r) as relationships, type(r) as rel_type
            WITH nodes, labels, relationships, COLLECT(DISTINCT rel_type) as relationship_types
            RETURN {
                nodes: nodes,
                relationships: relationships,
                node_labels: labels,
                relationship_types: relationship_types,
                node_label_count: size(labels),
                relationship_type_count: size(relationship_types)
            } as stats
        """

        graph_builder = Neo4jGraphCreation(
            uri=settings.neo4j_uri,
            user=settings.neo4j_username,
            password=settings.neo4j_password,
            database=settings.neo4j_database
        )

        graph_stats = await graph_builder.execute_query(query=query_str)
        await graph_builder.close()
        return {"success": True, "stats": graph_stats}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Neo4j connection error: {str(e)}")