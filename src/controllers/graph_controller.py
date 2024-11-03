# graph_controller.py

from typing import List, Dict, Set
from bson import ObjectId
from src.models.graph_model import Graph
from src.models.graph_run_config import GraphRunConfig
from src.utils.graph_validations import validate_graph_structure
from src.utils.graph_run_validations import validate_graph_config
from src.utils.helpers import generate_run_id, get_node_by_id, get_topological_order, is_leaf_node, apply_run_config, compute_node_output, get_level_wise_traversal, find_islands_in_graph, resolve_data_in
from src.database import db
from fastapi import HTTPException

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
    Run the graph using the provided GraphRunConfig, save the results and leaf outputs in the database,
    and check if a similar run exists before executing the graph.

    Args:
        graph_id (str): The ID of the graph to run.
        config (GraphRunConfig): The configuration for running the graph.

    Returns:
        dict: The run result outputs, the list of executed node IDs, updated data_in for each node, 
        leaf node outputs, and the latest edge used for each data_in key, stored as per the node model structure.

    Raises:
        HTTPException: If the graph is not found, configuration is invalid, or if there are other errors.
    """
    try:
        # Check if a similar run configuration already exists
        existing_run = await db["graph_runs"].find_one({"graph_id": graph_id, "config": config.dict()})
        if existing_run:
            # If run already exists, print the run details and return the outputs
            print(f"Run with the same configuration already exists: {existing_run['run_id']}")
            return {
                "run_id": existing_run["run_id"],
                "executed_nodes": existing_run["executed_nodes"],
                "updated_data_in": existing_run["updated_data_in"],
                "edges_used": existing_run["edges_used"],
                "run_result_outputs": existing_run["outputs"],
                "leaf_outputs": existing_run.get("leaf_outputs", {})
            }

        # Retrieve the graph and validate the configuration
        graph = await get_graph(graph_id)
        validate_graph_config(graph, config)

        # Apply the run configuration to the graph
        configured_graph = apply_run_config(graph, config)

        # Generate topological order for nodes
        sorted_node_ids = get_topological_order(configured_graph)
        print(sorted_node_ids)

        node_lookup = {node.node_id: node for node in configured_graph.nodes}

        # Generate unique run ID
        run_id = generate_run_id()
        run_result_outputs = {}
        updated_data_in = {}  # To track updated data_in for each node
        edge_tracking = {}  # To track which edge contributed to each data_in key
        leaf_outputs = {}  # To track outputs for leaf nodes

        # Execute nodes in topological order
        executed_node_ids = []  # List to track executed nodes
        for node_id in sorted_node_ids:
            node = node_lookup[node_id]

            # Skip nodes that are disabled
            if hasattr(node, 'enabled') and not node.enabled:
                continue

            # Debug: Print the current node being executed
            print(f"Executing node: {node_id}")

            # Resolve data_in for the current node and track the edges used
            current_data_in, edges_for_node = resolve_data_in(node, run_result_outputs, config)
            print(current_data_in)

            # Update the node's data_in with the resolved values
            node.data_in = current_data_in

            # Store the updated data_in and edges for this node
            updated_data_in[node_id] = current_data_in
            edge_tracking[node_id] = edges_for_node

            # Compute node output with resolved data_in
            node_output = compute_node_output(node, current_data_in)
            run_result_outputs[node_id] = node_output

            # Update the node's data_out with the computed output
            node.data_out = node_output

            # Check if the node is a leaf node (no paths_out)
            if not node.paths_out:
                leaf_outputs[node_id] = node_output

            # Add the executed node ID to the list
            executed_node_ids.append(node_id)

            # Debug: Print the output after executing each node
            print(f"Node {node_id} executed. Outputs: {run_result_outputs[node_id]}")

        # Save the run result into the database, including leaf outputs
        run_result = {
            "run_id": run_id,
            "graph_id": graph_id,
            "config": config.dict(),
            "executed_nodes": executed_node_ids,
            "updated_data_in": updated_data_in,
            "edges_used": edge_tracking,
            "outputs": run_result_outputs,
            "leaf_outputs": leaf_outputs  # Add leaf outputs to the saved result
        }
        await db["graph_runs"].insert_one(run_result)

        # Return the run ID, executed node IDs, updated data_in for each node, edge tracking, run outputs, and leaf outputs
        return {
            "run_id": run_id,
            "executed_nodes": executed_node_ids,
            "updated_data_in": updated_data_in,
            "edges_used": edge_tracking,
            "run_result_outputs": run_result_outputs,
            "leaf_outputs": leaf_outputs
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="An error occurred while running the graph: " + str(e))
      
async def get_run_outputs(graph_id: str, run_id: str):
    """
    Get the outputs, data_in, data_out, and edges used of a specific graph run.

    Args:
        graph_id (str): The ID of the graph.
        run_id (str): The run ID.

    Returns:
        dict: Outputs of the graph run, including data_in, data_out, and edges used.

    Raises:
        ValueError: If the run is not found.
    """
    # Fetch the run from the database
    run = await db["graph_runs"].find_one({"graph_id": graph_id, "run_id": run_id})
    
    # Check if the run exists
    if not run:
        raise ValueError("Run not found")
    
    # Return the data_in, data_out, edges_used, and outputs from the run
    return {
        "outputs": run.get("outputs", {}),
        "data_in": run.get("updated_data_in", {}),
        "data_out": {node_id: node_output for node_id, node_output in run.get("outputs", {}).items()},
        "edges_used": run.get("edges_used", {})
    }
async def get_node_output_for_run(run_id: str, node_id: str):
    """
    Get the data_in and data_out for a specific node in the graph run.

    Args:
        run_id (str): The run ID.
        node_id (str): The node ID.

    Returns:
        list: A list containing the data_in and data_out for the specified node.
    """
    # Fetch the run result from the database
    run = await db["graph_runs"].find_one(
        {"run_id": run_id},
        {"updated_data_in": 1, "outputs": 1}  # Fetch only the fields needed for node outputs
    )

    # Check if the run exists
    if not run:
        raise ValueError(f"Run with ID {run_id} not found.")

    # Fetch data_in and data_out for the specific node
    data_in = run.get("updated_data_in", {}).get(node_id)
    data_out = run.get("outputs", {}).get(node_id)

    # Raise an error if the node is not found in the run
    if data_in is None or data_out is None:
        raise ValueError(f"Node {node_id} not found in the run.")

    # Wrap the result in a list
    return [{
        "node_id": node_id,
        "data_in": data_in,
        "data_out": data_out
    }]

async def get_leaf_outputs_for_run(run_id: str):
    """
    Retrieve the outputs for all leaf nodes in the graph run from the database.

    Args:
        run_id (str): The run ID.

    Returns:
        dict: Outputs of all leaf nodes.

    Raises:
        ValueError: If the run is not found or there are no leaf outputs.
    """
    # Fetch the run data from the database
    run = await db["graph_runs"].find_one(
        {"run_id": run_id},
        {"leaf_outputs": 1}  # Fetch only the leaf_outputs field
    )
    
    # Check if the run exists
    if not run:
        raise ValueError(f"Run with ID {run_id} not found.")
    
    # Get the leaf outputs
    leaf_outputs = run.get("leaf_outputs", {})
    
    # Check if there are leaf outputs available
    if not leaf_outputs:
        raise ValueError(f"No leaf outputs found for run {run_id}.")
    
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
