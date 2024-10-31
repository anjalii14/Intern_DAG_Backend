import uuid
from typing import List, Dict
from src.models.graph_model import Graph
from src.models.node_model import Node

def generate_run_id() -> str:
    """
    Generate a unique run ID for graph executions.
    """
    return str(uuid.uuid4())

def get_node_by_id(graph: Graph, node_id: str) -> Node:
    """
    Retrieve a node by its ID from the graph.

    Parameters:
        graph (Graph): The graph to search.
        node_id (str): The ID of the node to find.

    Returns:
        Node: The node with the specified ID.
    """
    return next((n for n in graph.nodes if n.node_id == node_id), None)

def get_topological_order(graph: Graph) -> List[str]:
    """
    Return a topological ordering of the nodes in the graph.

    Parameters:
        graph (Graph): The graph to perform the topological sort on.

    Returns:
        List[str]: A list of node IDs in topological order.

    Raises:
        ValueError: If the graph contains a cycle or disconnected nodes.
    """
    # Kahn's algorithm for topological sorting
    in_degree = {node.node_id: 0 for node in graph.nodes}

    # Calculate in-degrees for each node
    for node in graph.nodes:
        for edge in node.paths_out:
            in_degree[edge.dst_node] += 1

    # Queue of nodes with no incoming edges
    queue = [node_id for node_id, degree in in_degree.items() if degree == 0]
    topological_order = []

    while queue:
        node_id = queue.pop(0)
        topological_order.append(node_id)
        node = get_node_by_id(graph, node_id)

        for edge in node.paths_out:
            dst_node = edge.dst_node
            in_degree[dst_node] -= 1
            if in_degree[dst_node] == 0:
                queue.append(dst_node)

    if len(topological_order) != len(graph.nodes):
        raise ValueError("Graph validation failed: Contains cycle")

    return topological_order

def is_leaf_node(node: Node) -> bool:
    """
    Check if a given node is a leaf node (i.e., has no outgoing edges).

    Parameters:
        node (Node): The node to check.

    Returns:
        bool: True if the node is a leaf, False otherwise.
    """
    return len(node.paths_out) == 0

def apply_run_config(graph: Graph, config) -> Graph:
    """
    Apply the given GraphRunConfig to the graph.

    Parameters:
        graph (Graph): The original graph to be modified.
        config (GraphRunConfig): The configuration for the run.

    Returns:
        Graph: The updated graph after applying enable/disable and data overwrites.
    """
    updated_graph = graph.copy(deep=True)

    # Enable or disable nodes based on configuration
    if config.enable_list:
        updated_graph.nodes = [node for node in updated_graph.nodes if node.node_id in config.enable_list]
    elif config.disable_list:
        updated_graph.nodes = [node for node in updated_graph.nodes if node.node_id not in config.disable_list]

    # Overwrite data_in for nodes based on provided configuration
    for node_id, data_overwrite in config.data_overwrites.items():
        node = get_node_by_id(updated_graph, node_id)
        if node:
            node.data_in.update(data_overwrite)

    return updated_graph

from typing import Dict
from bson import ObjectId
from fastapi import HTTPException

async def get_node_output(run_id: str, node_id: str) -> Dict:
    """
    Retrieve the output data for a specific node in a graph run.

    Args:
        run_id (str): The ID of the run.
        node_id (str): The ID of the node whose output is requested.

    Returns:
        dict: The output data for the specified node.

    Raises:
        HTTPException: If the run or node output is not found.
    """
    # Query the graph run results from the database
    run_result = await db["graph_runs"].find_one({"run_id": run_id})
    if not run_result:
        raise HTTPException(status_code=404, detail="Run not found")

    # Retrieve the output data for the specific node
    node_output = run_result.get("outputs", {}).get(node_id)
    if node_output is None:
        raise HTTPException(status_code=404, detail="Node output not found for given run ID")

    return node_output

def level_wise_traversal(graph: Graph) -> Dict[int, List[str]]:
    """
    Perform a level-wise traversal of the graph.

    Parameters:
        graph (Graph): The graph to traverse.

    Returns:
        Dict[int, List[str]]: A dictionary where the keys are level numbers and the values are lists of node IDs at that level.
    """
    levels = {}
    queue = []

    # Adding root nodes to the queue
    for node in graph.nodes:
        if len(node.paths_in) == 0:
            queue.append((node.node_id, 0))

    while queue:
        node_id, level = queue.pop(0)
        if level not in levels:
            levels[level] = []
        levels[level].append(node_id)
        node = get_node_by_id(graph, node_id)

        for edge in node.paths_out:
            dst_node = edge.dst_node
            queue.append((dst_node, level + 1))

    return levels
