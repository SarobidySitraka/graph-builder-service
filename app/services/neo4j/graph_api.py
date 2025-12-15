"""
Graph API service for processing graph configurations.
"""
# import logging
# logger = logging.getLogger(__name__)

# async def create_graph_api(
#     graph_config_list: List[GraphConfig],
#     data_dico: Dict[str, pl.DataFrame]
# ) -> List[Dict[str, Any]]:
#     """
#     Process graph configurations and prepare them for Neo4j graph creation.
    
#     Args:
#         graph_config_list: List of graph configurations
#         data_dico: Dictionary of dataframes keyed by table name
        
#     Returns:
#         List of processed graph configurations ready for Neo4j
        
#     Raises:
#         ValueError: If required tables or columns are missing
#     """
#     processed_configs = []
    
#     for config in graph_config_list:
#         try:
#             # Determine source and target dataframes
#             # Prefer explicit table names on the config if present; otherwise try source.table_name/target.table_name,
#             # and finally fall back to the first table in data_dico (if any).
#             if data_dico:
#                 if hasattr(config, "source_table") and getattr(config, "source_table"):
#                     source_table = config.source_table
#                 elif hasattr(config, "source") and hasattr(config.source, "table_name") and getattr(config.source, "table_name"):
#                     source_table = config.source.table_name
#                 else:
#                     source_table = list(data_dico.keys())[0]

#                 if hasattr(config, "target_table") and getattr(config, "target_table"):
#                     target_table = config.target_table
#                 elif hasattr(config, "target") and hasattr(config.target, "table_name") and getattr(config.target, "table_name"):
#                     target_table = config.target.table_name
#                 else:
#                     target_table = source_table
#             else:
#                 source_table = None
#                 target_table = None
            
#             if source_table not in data_dico:
#                 raise ValueError(f"Source table '{source_table}' not found in data")
#             if target_table not in data_dico:
#                 raise ValueError(f"Target table '{target_table}' not found in data")
            
#             source_df = data_dico[source_table]
#             target_df = data_dico[target_table]
            
#             # Validate that required properties exist in dataframes
#             missing_source_props = [p for p in config.source.properties if p not in source_df.columns]
#             if missing_source_props:
#                 raise ValueError(f"Missing source properties: {missing_source_props}")
            
#             missing_target_props = [p for p in config.target.properties if p not in target_df.columns]
#             if missing_target_props:
#                 raise ValueError(f"Missing target properties: {missing_target_props}")
            
#             # Prepare graph configuration
#             graph_api_config = { # type: ignore
#                 "source": {
#                     "label": config.source.label,
#                     "properties": config.source.properties,
#                     "dataframe": source_df,
#                     "table_name": source_table,
#                     "key": config.source_key or config.source.properties[0] if config.source.properties else None
#                 },
#                 "target": {
#                     "label": config.target.label,
#                     "properties": config.target.properties,
#                     "dataframe": target_df,
#                     "table_name": target_table,
#                     "key": config.target_key or config.target.properties[0] if config.target.properties else None
#                 },
#                 "relationship": {
#                     "label": config.rels.label,
#                     "properties": config.rels.properties
#                 }
#             }
            
#             processed_configs.append(graph_api_config) # type: ignore
#             logger.info(f"Processed graph config: {config.source.label} -[{config.rels.label}]-> {config.target.label}")
            
#         except Exception as e:
#             logger.error(f"Error processing graph config: {e}")
#             raise
    
#     return processed_configs # type: ignore

# ==================================

# import polars as pl
import pandas as pd
from pydantic import Field
from typing import List, Dict, Any
import hashlib
from app.models.graph_config import GraphConfig
from .ingest import create_data_frame_from_props_block

def graph_element_props(
    data:pd.DataFrame,
    label: str,
    props:list[str]
) -> List[Dict[str, Any]]:
    try:
        from app.utils.data_manip import check_cols_exist_in_db
        graph_props, _ = check_cols_exist_in_db(data=data, cols=props) # type: ignore
        graph_element_df = data[graph_props]
        graph_props_list = graph_element_df.to_dict(orient="records")

        graph_elements = []
        for props in graph_props_list: # type: ignore
            raw_key = f"{label}:{sorted(props.items())}" # type: ignore
            props["id"] = hashlib.sha1(raw_key.encode()).hexdigest() # type: ignore

            dico = { # type: ignore
                "label": label,
                "properties": props
            }
            graph_elements.append(dico) # type: ignore
        return graph_elements # type: ignore
    except Exception as e:
        raise ValueError(e)

def source_to_target_rels( # type: ignore
    data: pd.DataFrame = Field(..., description="Data Frame that contains all the needed information"),
    graph_config: GraphConfig = Field(..., description="Graph configs that contains all the necessaries graph element configs")
) -> List[Dict[str, dict]]: # type: ignore
    source_props_list = graph_element_props(data=data, label=graph_config.source.label, props=graph_config.source.properties)
    target_props_list = graph_element_props(data=data, label=graph_config.target.label, props=graph_config.target.properties)
    rels_props_list = graph_element_props(data=data, label=graph_config.rels.label, props=graph_config.rels.properties)

    source_to_target_list = []
    for source, target, rels in zip(source_props_list, target_props_list, rels_props_list):
        graph_props_bloc = {
            "source": source,
            "target": target,
            "rels": rels
        }
        source_to_target_list.append(graph_props_bloc) # type: ignore

    return source_to_target_list # type: ignore

async def create_graph_api(graph_config_list: List[GraphConfig], data_dico: Dict[str, pd.DataFrame]) -> list: # type: ignore
    full_graph_elements = []
    if len(data_dico) > 1:
        for graph_config_bloc in graph_config_list:
            data = create_data_frame_from_props_block(data_dico=data_dico, props_block=graph_config_bloc) # type: ignore
            source_to_target_rel = source_to_target_rels(data=data, graph_config=graph_config_bloc) # type: ignore
            full_graph_elements.extend(source_to_target_rel) # type: ignore
        pass
    else:
        data = list(data_dico.values())[0]
        for graph_config_bloc in graph_config_list:
            source_to_target_rel = source_to_target_rels(data=data, graph_config=graph_config_bloc) # type: ignore
            full_graph_elements.extend(source_to_target_rel) # type: ignore
    return full_graph_elements # type: ignore