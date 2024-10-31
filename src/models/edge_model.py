from typing import Dict
from pydantic import BaseModel

class Edge(BaseModel):
    """
    Represents an edge in the graph, defining the connection from a source node to a destination node,
    with optional data mapping between the source and destination nodes.
    """
    src_node: str  # ID of the source node
    dst_node: str  # ID of the destination node
    src_to_dst_data_keys: Dict[str, str] = {}  # Maps data_out keys of src node to data_in keys of dst node

    @classmethod
    def validate_unique_keys(cls, data_keys):
        if data_keys and len(data_keys) != len(set(data_keys.values())):
            raise ValueError("Edge must have unique key mappings between source and destination.")
        return data_keys

    class Config:
        allow_population_by_field_name = True
