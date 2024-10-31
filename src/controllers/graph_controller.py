# graph_controller.py

from typing import List
from bson import ObjectId
from src.models.graph_model import Graph
from src.models.graph_run_config import GraphRunConfig
from src.utils.graph_validations import validate_graph_structure
from src.utils.helpers import generate_run_id, get_node_by_id, get_topological_order, is_leaf_node, apply_run_config, get_node_output, level_wise_traversal
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
        dict: The run result outputs along with the generated run ID.

    Raises:
        ValueError: If the graph is not found or configuration is invalid.
    """
    graph = await get_graph(graph_id)

    # Apply the run configuration
    configured_graph = apply_run_config(graph, config)

    # Topological sort to ensure proper execution order
    topological_order = get_topological_order(configured_graph)

    # Ensure all nodes are covered by the topological order (no disconnected nodes)
    if len(topological_order) != len(configured_graph.nodes):
        raise ValueError("The graph contains disconnected nodes (islands).")

# Execute the graph and store results
    run_result_outputs = {}
    for node_id in topological_order:
        node_output = await get_node_output(configured_graph, node_id, run_result_outputs)
        run_result_outputs[node_id] = node_output

    # Generate a run ID for this run
    run_id = generate_run_id()

    # Save the run result
    run_result = {
        "run_id": run_id,
        "graph_id": graph_id,
        "outputs": run_result_outputs
    }
    await db["graph_runs"].insert_one(run_result)

    return {"run_id": run_id, "outputs": run_result_outputs}


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

    return leaf_outputs


async def level_wise_traversal(graph_id: str, config: GraphRunConfig):
    """
    Perform a level-wise traversal of the graph based on the GraphRunConfig.

    Args:
        graph_id (str): The ID of the graph.
        config (GraphRunConfig): The configuration for running the graph.

    Returns:
        dict: Level-wise traversal of nodes.
    """
    graph = await get_graph(graph_id)
    configured_graph = apply_run_config(graph, config)

    return level_wise_traversal(configured_graph)


async def topological_sort(graph_id: str):
    """
    Return a topological sort of the graph.

    Args:
        graph_id (str): The ID of the graph.

    Returns:
        list: List of nodes in topological order.

    Raises:
        ValueError: If the graph cannot be topologically sorted.
    """
    graph = await get_graph(graph_id)
    try:
        return get_topological_order(graph)
    except ValueError as e:
        raise ValueError("Cannot perform topological sort: " + str(e))
