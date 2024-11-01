import uuid
from typing import List, Dict
from src.models.graph_model import Graph
from src.models.node_model import Node
from fastapi import HTTPException
from src.database import db

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

    # Validate that enable_list and disable_list are mutually exclusive
    if set(config.enable_list) & set(config.disable_list):
        raise ValueError("Nodes cannot be in both enable_list and disable_list. Ensure there is no overlap.")

    # Ensure all nodes are covered by either enable_list or disable_list
    all_node_ids = {node.node_id for node in graph.nodes}
    specified_nodes = set(config.enable_list) | set(config.disable_list)
    if all_node_ids != specified_nodes:
        raise ValueError("All nodes must be specified in either enable_list or disable_list.")

    # Get the set of nodes to disable
    nodes_to_disable = set(config.disable_list)

    # Enable or disable nodes based on configuration
    # Filter out nodes that are in the disable list
    if nodes_to_disable:
        updated_graph.nodes = [node for node in updated_graph.nodes if node.node_id not in nodes_to_disable]

    # Remove references to disabled nodes from paths_in and paths_out of the remaining nodes
    for node in updated_graph.nodes:
        node.paths_in = [edge for edge in node.paths_in if edge.src_node not in nodes_to_disable]
        node.paths_out = [edge for edge in node.paths_out if edge.dst_node not in nodes_to_disable]

    # Overwrite data_in for nodes based on provided configuration
    for node_id, data_overwrite in config.data_overwrites.items():
        node = get_node_by_id(updated_graph, node_id)
        if node:
            node.data_in.update(data_overwrite)

    return updated_graph

def compute_node_output(node: Node, previous_outputs: dict) -> dict:
    """
    Compute the output for a node based on its inputs and previous node outputs.

    Parameters:
        node (Node): The node to compute output for.
        previous_outputs (dict): Dictionary of outputs from previously executed nodes.

    Returns:
        dict: The output of the node.
    """
    # Example logic: Simply copy data_in to data_out, or apply some operation if needed
    node_output = node.data_in.copy()

    # For each input, check if it depends on a previous node's output
    for edge in node.paths_in:
        if edge.src_node in previous_outputs:
            for src_key, dst_key in edge.src_to_dst_data_keys.items():
                if src_key in previous_outputs[edge.src_node]:
                    node_output[dst_key] = previous_outputs[edge.src_node][src_key]

    return node_output


def get_level_wise_traversal(graph: Graph) -> List[List[str]]:
    """
    Perform a level-wise traversal of the graph.

    Parameters:
        graph (Graph): The graph to traverse.

    Returns:
        List[List[str]]: A list where each dictionary represents a level,
                                    with the key being the level number as a string
                                    and the value being a list of node IDs at that level.
    """
    levels = {}
    queue = []

    # Adding root nodes to the queue
    for node in graph.nodes:
        if len(node.paths_in) == 0:
            queue.append(node.node_id)
            levels[node.node_id] = 0

    level_result = {}

    while queue:
        node_id = queue.pop(0)
        current_level = levels[node_id]

        # Add node to the corresponding level in level_result
        if current_level not in level_result:
            level_result[current_level] = []
        level_result[current_level].append(node_id)

        # Process child nodes
        node = get_node_by_id(graph, node_id)
        for edge in node.paths_out:
            dst_node = edge.dst_node
            if dst_node not in levels:
                queue.append(dst_node)
                levels[dst_node] = current_level + 1

    # Convert level_result from a dictionary to a list of lists
    level_order = [level_result[level] for level in sorted(level_result.keys())]

    return level_order
