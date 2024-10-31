from typing import List, Optional
from pydantic import BaseModel, Field, model_validator
from bson import ObjectId
from .node_model import Node

class Graph(BaseModel):
    """
    Represents a graph structure comprising nodes and edges.
    """
    id: Optional[str] = Field(None, alias="_id")
    nodes: List[Node]  # List of Node objects

    @model_validator(mode="before")
    @classmethod
    def validate_unique_node_ids(cls, values):
        """
        Ensures that each node within the graph has a unique ID.
        """
        nodes = values.get('nodes', [])
        
        # Extract node_ids from dictionary or from Node instances
        node_ids = [node['node_id'] if isinstance(node, dict) else node.node_id for node in nodes]
        
        if len(node_ids) != len(set(node_ids)):
            raise ValueError("Node IDs must be unique within the graph.")
        
        return values

    class Config:
        json_encoders = {
            ObjectId: lambda obj_id: str(obj_id)
        }
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
