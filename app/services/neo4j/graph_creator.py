"""
Graph creation utilities for Neo4j.
"""
import logging
from typing import List, Dict, Any
import polars as pl

from app.models.graph_config import GraphConfig
from .graph_api import create_graph_api # type: ignore

logger = logging.getLogger(__name__)

async def build_graph_from_config(
    graph_configs: List[GraphConfig],
    dataframes: Dict[str, pl.DataFrame]
) -> List[Dict[str, Any]]:
    """
    Build graph structure from configurations and dataframes.
    
    This is a convenience wrapper around create_graph_api.
    
    Args:
        graph_configs: List of graph configurations
        dataframes: Dictionary of dataframes
        
    Returns:
        List of processed graph configurations
    """
    return await create_graph_api(graph_configs, dataframes) # type: ignore

