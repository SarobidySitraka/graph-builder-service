# import polars as pl
import pandas as pd
from typing import List, Dict
from app.models.graph_config import GraphConfig

def find_data_frame(data_dico: Dict[str, pd.DataFrame], props: List[str]):
    """Find the first dataframe that contains all the required properties."""
    from app.utils.data_manip import check_cols_exist_in_db
    for df_name, df in data_dico.items():
        try:
            exist_cols, _ = check_cols_exist_in_db(data=df, cols=props)
            return df_name, df[exist_cols]
        except ValueError:
            # This dataframe doesn't have all required columns, continue to next
            continue
    raise ValueError(f"No dataframe found containing all required properties: {props}")

def create_data_frame_from_props_block(data_dico: Dict[str, pd.DataFrame], props_block: GraphConfig): # type: ignore
    """
    Args:
        data_dico: set of df name and df values
        props_block: has SOURCE, TARGET AND RELS as attributes
    Task:
        create Data frame for each props of GraphConfig attributes
        source_df = data[props_block.source.properties]
        target_df = data[props_block.target.properties]
        rels_df = data[props_block.rels.properties]
    Returns:
        DataFrame -> data frame that combines the source_df, target_df and rels_df
    """
    _, source_df = find_data_frame(data_dico=data_dico, props=props_block.source.properties)
    _, target_df = find_data_frame(data_dico=data_dico, props=props_block.target.properties)
    _, rels_df = find_data_frame(data_dico=data_dico, props=props_block.rels.properties)

    st_intersection = set(source_df.columns) & set(target_df.columns)
    st_df_lazy = source_df.join(target_df, on=list(st_intersection), how="right")
    str_intersection = set(st_df_lazy.columns) & set(rels_df.columns)
    str_df_lazy = st_df_lazy.join(rels_df, on=list(str_intersection), how="right")
    str_df = str_df_lazy.collect() # type: ignore
    return str_df # type: ignore