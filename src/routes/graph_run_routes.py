# graph_run_routes.py

from fastapi import APIRouter, HTTPException
from typing import Dict, Any, List, Optional, Set
from src.controllers.graph_controller import (
    run_graph, get_run_outputs, get_node_output_for_run,
    level_wise_traversal, topological_sort, get_islands_for_graph, get_graph_runs, get_leaf_outputs_for_run
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
        dict: Contains the run ID, outputs, and configured graph of the run.
    
    Raises:
        HTTPException: If the graph is not found or configuration is invalid.
    """
    try:
        # Capture the entire response from run_graph, including run_id, outputs, and configured graph
        run_result = await run_graph(graph_id, config)
        
        # Return the complete run result
        return run_result

    except ValueError as e:
        # Return a 400 status with the error message for validation issues
        raise HTTPException(status_code=400, detail=str(e))

    except Exception as e:
        # Catch any unexpected exceptions and return a 500 error
        raise HTTPException(status_code=500, detail=f"{str(e)}")


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


@router.get("/graph/run/{run_id}/leaf-outputs", response_model=Dict[str, Any])
async def get_leaf_outputs_route(run_id: str):
    """
    Get the outputs of leaf nodes for a specific run.
    
    Args:
        run_id (str): The run ID.
    
    Returns:
        dict: Outputs of the leaf nodes.
    
    Raises:
        HTTPException: If the run is not found.
    """
    try:
        leaf_outputs = await get_leaf_outputs_for_run(run_id)
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

@router.get("/node-output", response_model=list)
async def get_node_output(run_id: str, node_id: str):
    """
    Get the data output for a given graph run and node id.

    Args:
        node_id (str): The ID of the node.
        run_id (str): The run ID.

    Returns:
        list: Data In and data out respectively.

    Raises:
        HTTPException: If the graph run or node id is not found.
    """
    return await get_node_output_for_run(run_id, node_id)

@router.post("/api/graph/{graph_id}/islands")
async def get_islands_route(graph_id: str, config: GraphRunConfig) -> List[Set[str]]:
    """
    API endpoint to get islands in a graph after applying a GraphRunConfig.

    Args:
        graph_id (str): The ID of the graph.
        config (GraphRunConfig): The configuration for running the graph.

    Returns:
        List[Set[str]]: A list of sets where each set contains node IDs that form an island.

    Raises:
        HTTPException: If the graph is not found or other errors occur.
    """
    try:
        islands = await get_islands_for_graph(graph_id, config=config)
        return islands
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))