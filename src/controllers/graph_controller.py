# graph_controller.py

from typing import List, Dict, Set
from bson import ObjectId
from src.models.graph_model import Graph
from src.models.graph_run_config import GraphRunConfig
from src.utils.graph_validations import validate_graph_structure
from src.utils.graph_run_validations import validate_graph_config
from src.utils.helpers import generate_run_id, get_node_by_id, get_topological_order, is_leaf_node, apply_run_config, compute_node_output, get_level_wise_traversal, find_islands_in_graph
from src.database import db


async def create_graph(graph: Graph):
    """
    Create a new graph in the database after validating its structure.

    Args:
        graph (Graph): The graph object to be created.

    Returns:
        dict: The graph dictionary with the inserted ID.

    Raises:
        ValueError: If the graph already exists or validation fails.
    """
    validate_graph_structure(graph)
    graph_dict = graph.dict(by_alias=True, exclude={"id"})

    existing_graph = await db["graphs"].find_one(graph_dict)
    if existing_graph:
        existing_graph["_id"] = str(existing_graph["_id"])
        print("Graph already exists")
        return existing_graph

    result = await db["graphs"].insert_one(graph_dict)
    graph_dict["_id"] = str(result.inserted_id)

    return graph_dict


async def get_graph(graph_id: str):
    """
    Retrieve a graph by its ID.

    Args:
        graph_id (str): The ID of the graph to retrieve.

    Returns:
        Graph: The retrieved graph object.

    Raises:
        ValueError: If the graph is not found.
    """
    graph = await db["graphs"].find_one({"_id": ObjectId(graph_id)})
    if graph is None:
        raise ValueError("Graph not found")

    graph["_id"] = str(graph["_id"])
    return Graph(**graph)

async def get_all_graphs():
    """
    Retrieve all graphs from the database.

    Returns:
        List[dict]: A list of all graph dictionaries with their IDs as strings.
    """
    graphs = []
    async for graph in db["graphs"].find():
        graph["_id"] = str(graph["_id"])  # Convert ObjectId to string
        graphs.append(graph)
    return graphs

async def update_graph(graph_id: str, updated_graph: Graph):
    """
    Update an existing graph.

    Args:
        graph_id (str): The ID of the graph to update.
        updated_graph (Graph): The updated graph object.

    Returns:
        Graph: The updated graph object.

    Raises:
        ValueError: If the graph is not found or validation fails.
    """
    validate_graph_structure(updated_graph)
    updated_graph_dict = updated_graph.dict(by_alias=True, exclude={"id"})

    update_result = await db["graphs"].replace_one({"_id": ObjectId(graph_id)}, updated_graph_dict)
    if update_result.matched_count == 0:
        raise ValueError("Graph not found")

    return await get_graph(graph_id)


async def delete_graph(graph_id: str):
    """
    Delete a graph by its ID.

    Args:
        graph_id (str): The ID of the graph to delete.

    Returns:
        bool: True if the graph is successfully deleted, otherwise raises an error.

    Raises:
        ValueError: If the graph is not found.
    """
    delete_result = await db["graphs"].delete_one({"_id": ObjectId(graph_id)})
    if delete_result.deleted_count == 0:
        raise ValueError("Graph not found")
    return True

async def run_graph(graph_id: str, config: GraphRunConfig):
    """
    Run the graph using the provided GraphRunConfig.

    Args:
        graph_id (str): The ID of the graph to run.
        config (GraphRunConfig): The configuration for running the graph.

    Returns:
        dict: The run result outputs, the generated run ID, and the configured graph.

    Raises:
        HTTPException: If the graph is not found, configuration is invalid, or if there are other errors.
    """
    try:
        # Check if a similar run configuration already exists
        existing_run = await db["graph_runs"].find_one({"graph_id": graph_id, "config": config.dict()})
        if existing_run:
            return {
                "message": "Run with the same configuration already exists",
                "run_id": existing_run["run_id"],
                "outputs": existing_run["outputs"],
                "configured_graph": existing_run.get("configured_graph")  # Include configured_graph if available
            }

        # Retrieve the graph and validate the configuration
        graph = await get_graph(graph_id)
        validate_graph_config(graph, config)
        
        # Apply the run configuration and validate
        configured_graph = apply_run_config(graph, config)
        # Generate topological order for nodes
        print(configured_graph.nodes)
        sorted_node_ids = get_topological_order(configured_graph)
        node_lookup = {node.node_id: node for node in configured_graph.nodes}

        # Generate unique run ID
        run_id = generate_run_id()
        run_result_outputs = {}

        # Execute nodes in topological order
        for node_id in sorted_node_ids:
            node = node_lookup[node_id]
            node_output = compute_node_output(node, run_result_outputs)
            run_result_outputs[node_id] = node_output

        # Prepare final run result for MongoDB
        run_result = {
            "run_id": run_id,
            "graph_id": graph_id,
            "config": config.dict(),
            "outputs": run_result_outputs,
            "configured_graph": configured_graph.dict()
        }

        # Insert result into MongoDB
        await db["graph_runs"].insert_one(run_result)

        # Return the run ID, outputs, and configured graph for visualization
        return {
            "run_id": run_id,
            "outputs": run_result_outputs,
            "configured_graph": configured_graph.dict()
        }

    except ValueError as ve:
        # Raise HTTP 400 error with a detailed message for validation issues
        raise HTTPException(status_code=400, detail=f"Validation Error: {str(ve)}")

    except Exception as e:
        # Handle unexpected errors with a 500 error code and return the error message
        raise HTTPException(status_code=500, detail=f"{str(e)}")


async def get_configured_graph(graph_id: str, run_id: str):
    """
    Retrieve a configured graph by graph ID and run ID.

    Args:
        graph_id (str): The ID of the graph.
        run_id (str): The unique run ID of the graph execution.

    Returns:
        The configured graph object with run_id and graph_id.

    Raises:
        ValueError: If the configured graph is not found or if the run_id is invalid.
    """
    try:
        # Convert run_id to ObjectId and handle invalid format
        run_object_id = ObjectId(run_id)
    except:
        raise ValueError(f"Invalid run_id format: {run_id}")

    # Fetch the graph run record from MongoDB using the graph_id and run_id
    graph_run = await db["graph_runs"].find_one({"_id": run_object_id, "graph_id": graph_id})
    
    # If no such record exists, raise an exception
    if graph_run is None:
        raise ValueError("Configured graph run not found")

    # Prepare the response directly as a dictionary
    response = {
        "run_id": str(graph_run["_id"]),
        "graph_id": graph_run["graph_id"],
        "configured_graph": graph_run["configured_graph"]
    }
    
    return response

async def get_run_outputs(graph_id: str, run_id: str):
    """
    Get the outputs of a specific graph run.

    Args:
        graph_id (str): The ID of the graph.
        run_id (str): The run ID.

    Returns:
        dict: Outputs of the graph run.

    Raises:
        ValueError: If the run is not found.
    """
    run = await db["graph_runs"].find_one({"graph_id": graph_id, "run_id": run_id})
    if not run:
        raise ValueError("Run not found")
    return run["outputs"]


async def get_leaf_outputs(graph_id: str, run_id: str):
    """
    Get the outputs of the leaf nodes for a specific run.

    Args:
        graph_id (str): The ID of the graph.
        run_id (str): The run ID.

    Returns:
        dict: Outputs of the leaf nodes.

    Raises:
        ValueError: If the run is not found.
    """
    run = await db["graph_runs"].find_one({"graph_id": graph_id, "run_id": run_id})
    if not run:
        raise ValueError("Run not found")

    graph = await get_graph(graph_id)
    leaf_node_ids = [node.node_id for node in graph.nodes if is_leaf_node(node)]
    leaf_outputs = {node_id: run["outputs"].get(node_id) for node_id in leaf_node_ids}
    print(leaf_outputs)
    return leaf_outputs

async def level_wise_traversal(graph_id: str, config: GraphRunConfig) -> List[List[str]]:
    """
    Perform a level-wise traversal of the graph based on the GraphRunConfig.

    Args:
        graph_id (str): The ID of the graph.
        config (GraphRunConfig): The configuration for running the graph.

    Returns:
        List[List[str]]: A list of lists where each inner list contains node IDs at the corresponding level.
    """
    # Retrieve the graph
    graph = await get_graph(graph_id)

    # Apply the run configuration
    configured_graph = apply_run_config(graph, config)

    return get_level_wise_traversal(configured_graph)

async def topological_sort(graph_id: str, config):
    """
    Return a topological sort of the graph with the applied configuration.

    Args:
        graph_id (str): The ID of the graph.
        config (GraphRunConfig): The configuration for running the graph.

    Returns:
        list: List of nodes in topological order.

    Raises:
        ValueError: If the graph cannot be topologically sorted.
    """
    # Retrieve the graph using the given graph ID
    graph = await get_graph(graph_id)

    # Apply the provided configuration to the graph
    configured_graph = apply_run_config(graph, config)

    # Attempt to get the topological order of the configured graph
    try:
        return get_topological_order(configured_graph)
    except ValueError as e:
        raise ValueError("Cannot perform topological sort: " + str(e))
    
async def get_islands_for_graph(graph_id: str, config: GraphRunConfig) -> List[Set[str]]:
    """
    Find and return all islands in the graph after applying GraphRunConfig.

    Args:
        graph_id (str): The ID of the graph.
        config (GraphRunConfig): The configuration for running the graph.

    Returns:
        List[Set[str]]: A list of sets where each set contains node IDs that form an island.

    Raises:
        ValueError: If the graph is not found.
    """
    # Retrieve the graph using the given graph ID
    graph = await get_graph(graph_id)
    if not graph:
        raise ValueError(f"Graph with ID {graph_id} not found.")

    # Apply the provided configuration to the graph
    configured_graph = apply_run_config(graph, config)

    # Find all islands in the configured graph
    islands = find_islands_in_graph(configured_graph, return_islands=True)

    return islands

from fastapi import HTTPException

async def get_graph_runs(graph_id: str) -> List[Dict]:
    """
    Retrieve all runs associated with a specific graph ID.

    Args:
        graph_id (str): The ID of the graph to fetch runs for.

    Returns:
        List[Dict]: A list of all runs associated with the graph, with their IDs and timestamps.

    Raises:
        HTTPException: If any database operation fails.
    """
    try:
        runs = await db["graph_runs"].find({"graph_id": graph_id}).to_list(length=None)
        
        # Convert each run to include `created_at` as a string or default to an empty string if None
        return [
            {
                "run_id": str(run["_id"]),
                "created_at": run.get("created_at", "").isoformat() if run.get("created_at") else ""
            }
            for run in runs
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching runs: {str(e)}")
