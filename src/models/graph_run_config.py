from typing import List, Dict, Union
from pydantic import BaseModel, Field

DataType = Union[int, float, str, bool, list, dict]  

class GraphRunConfig(BaseModel):
    """
    Represents the configuration for running a graph, including root inputs, data overwrites, and enabled nodes.
    """
    root_inputs: Dict[str, Dict[str, DataType]] = Field(default_factory=dict)  
    data_overwrites: Dict[str, Dict[str, DataType]] = Field(default_factory=dict)  
    enable_list: List[str] = Field(default_factory=list)  
    disable_list: List[str] = Field(default_factory=list)  

    class Config:
        """
        Pydantic configuration for the GraphRunConfig model.
        """
        allow_population_by_field_name = True
