from typing import List, Dict, Union
from pydantic import BaseModel, model_validator, Field

DataType = Union[int, float, str, bool, list, dict]  

class GraphRunConfig(BaseModel):
    """
    Represents the configuration for running a graph, including root inputs, data overwrites, and enabled nodes.
    """
    root_inputs: Dict[str, Dict[str, DataType]] = Field(default_factory=dict)  
    data_overwrites: Dict[str, Dict[str, DataType]] = Field(default_factory=dict)  
    enable_list: List[str] = Field(default_factory=list)  
    disable_list: List[str] = Field(default_factory=list)  

    @model_validator(mode="before")
    @classmethod
    def validate_enable_disable_lists(cls, values):
        """
        Validates that enable_list and disable_list are mutually exclusive
        and that they do not contain overlapping node IDs.
        
        Args:
            values (dict): The dictionary of all provided fields for the model.

        Returns:
            dict: The validated values to be used for model instantiation.

        Raises:
            ValueError: If there are any overlapping node IDs between enable_list and disable_list.
        """
        enable_list = values.get('enable_list', [])
        disable_list = values.get('disable_list', [])

        # Ensure enable_list and disable_list do not overlap
        if set(enable_list) & set(disable_list):
            raise ValueError("Nodes cannot be in both enable_list and disable_list. Ensure there is no overlap.")

        return values

    class Config:
        """
        Pydantic configuration for the GraphRunConfig model.
        """
        allow_population_by_field_name = True
