# graph_run_routes.py

from fastapi import APIRouter, HTTPException
from typing import Dict, Any, List, Optional
from src.controllers.graph_controller import (
    run_graph, get_run_outputs, get_leaf_outputs,
    level_wise_traversal, topological_sort
)
from src.models.graph_run_config import GraphRunConfig

# Create the APIRouter instance for the execution and run operations
router = APIRouter()

@router.post("/graph/{graph_id}/run", response_model=Dict[str, Any])
async def run_graph_route(graph_id: str, config: GraphRunConfig):
    """
    Run the graph using the provided GraphRunConfig.
    
    Args:
        graph_id (str): The ID of the graph to run.
        config (GraphRunConfig): The configuration for running the graph.
    
    Returns:
        dict: Contains the run ID of the run.
    
    Raises:
        HTTPException: If the graph is not found or configuration is invalid.
    """
    try:
        run_id = await run_graph(graph_id, config)
        return {"run_id": run_id}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/graph/{graph_id}/run/{run_id}/outputs", response_model=Dict[str, Any])
async def get_run_outputs_route(graph_id: str, run_id: str):
    """
    Get the outputs of a specific graph run.
    
    Args:
        graph_id (str): The ID of the graph.
        run_id (str): The run ID.
    
    Returns:
        dict: Outputs of the graph run.
    
    Raises:
        HTTPException: If the run is not found.
    """
    try:
        outputs = await get_run_outputs(graph_id, run_id)
        return outputs
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/graph/{graph_id}/run/{run_id}/leaf-outputs", response_model=Dict[str, Any])
async def get_leaf_outputs_route(graph_id: str, run_id: str):
    """
    Get the outputs of leaf nodes for a specific run.
    
    Args:
        graph_id (str): The ID of the graph.
        run_id (str): The run ID.
    
    Returns:
        dict: Outputs of the leaf nodes.
    
    Raises:
        HTTPException: If the run is not found.
    """
    try:
        leaf_outputs = await get_leaf_outputs(graph_id, run_id)
        return leaf_outputs
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/api/graph/{graph_id}/level-wise", response_model=List[List[str]])
async def level_wise_traversal_route(graph_id: str, config: GraphRunConfig):
    """
    Perform a level-wise traversal of the graph based on the GraphRunConfig.
    
    Args:
        graph_id (str): The ID of the graph.
        config (GraphRunConfig): The configuration for running the graph.
    
    Returns:
        dict: Level-wise traversal of nodes.
    
    Raises:
        HTTPException: If the graph is not found or configuration is invalid.
    """
    try:
        traversal = await level_wise_traversal(graph_id, config)
        return traversal
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/graph/{graph_id}/toposort", response_model=List[str])
async def topological_sort_route(graph_id: str, config: GraphRunConfig):
    """
    Return a topological sort of the graph.
    
    Args:
        graph_id (str): The ID of the graph.
    
    Returns:
        list: List of nodes in topological order.
    
    Raises:
        HTTPException: If the graph cannot be topologically sorted.
    """
    try:
        topological_order = await topological_sort(graph_id, config)
        return topological_order
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/graph/{graph_id}/run/{run_id}/leaf-nodes", response_model=List[str])
async def get_leaf_nodes_route(graph_id: str, run_id: str):
    """
    Get the list of all leaf nodes for a given graph run.

    Args:
        graph_id (str): The ID of the graph.
        run_id (str): The run ID.

    Returns:
        list: List of leaf nodes for the graph run.

    Raises:
        HTTPException: If the graph run is not found.
    """
    try:
        leaf_nodes = await get_leaf_outputs(graph_id, run_id)
        return leaf_nodes
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


## TO-DO efficiently calculating and validating graph run config

# @router.get("/graph/{graph_id}/islands", response_model=List[List[str]])
# async def get_graph_islands_route(
#     graph_id: str, 
#     config: Optional[GraphRunConfig] = None, 
#     run_id: Optional[str] = None
# ):
#     """
#     Get a list of all islands (i.e., connected components) for the graph.

#     Args:
#         graph_id (str): The ID of the graph.
#         config (Optional[GraphRunConfig]): The configuration for running the graph.
#         run_id (Optional[str]): The run ID to analyze.

#     Returns:
#         list: List of connected components (islands).

#     Raises:
#         HTTPException: If the graph is not found or if both config and run_id are provided.
#     """
#     if (config and run_id) or (not config and not run_id):
#         raise HTTPException(status_code=400, detail="Provide either 'GraphRunConfig' or 'run_id', but not both.")

#     try:
#         islands = await calculate_islands(graph_id, config=config, run_id=run_id)
#         return islands
#     except ValueError as e:
#         raise HTTPException(status_code=400, detail=str(e))
