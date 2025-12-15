"""
Graph configuration models for Neo4j graph creation.
"""
from pydantic import BaseModel, Field
from fastapi import Body

class GraphElement(BaseModel):
    """Base model for graph elements (nodes and relationships).

    Attributes:
        label (str): Label of the graph element.
        properties (list | dict): Properties of the graph element.
    """
    label: str = Field(..., description="Label of the graph element")
    properties: list[str] = Field(..., description="Properties of the graph element")

class GraphConfig(BaseModel):
    """Configuration for the graph API.

    Attributes:
        source (dict): Source node configuration.
        target (dict): Target node configuration.
        rels (dict): Relationship configuration.
    """
    source: GraphElement = Body(..., description="Source node configuration")
    target: GraphElement = Body(..., description="Target node configuration")
    rels: GraphElement = Body(..., description="Relationship configuration")
    class Config:
        """Pydantic configuration."""
        json_schema_extra = { # type: ignore
            "source_to_target": {
                "source": {
                    "label": "OFFICE",
                    "properties": ["CUSTOMS_OFFICE", "..."]
                },
                "target": {
                    "label": "CAD",
                    "properties": ["CAD", "..."]
                },
                "rels": {
                    "label": "REPORTS_TO",
                    "properties": ["ARTICLE_NAME", "..."]
                }
            }
        }
