from typing import Dict, Optional, List, Union
from pydantic import BaseModel, Field
from .edge_model import Edge

DataType = Union[int, float, str, bool, list, dict]  # Nested lists and dicts of primitive types allowed

class Node(BaseModel):
    """
    Represents a node within a graph, including its inputs, outputs, and associated edges.
    """
    node_id: str 
    data_in: Dict[str, DataType] = Field(default_factory=dict)
    data_out: Dict[str, DataType] = Field(default_factory=dict)
    paths_in: List[Edge] = Field(default_factory=list)  # List of incoming edges
    paths_out: List[Edge] = Field(default_factory=list)  # List of outgoing edges

    class Config:
        allow_population_by_field_name = True
