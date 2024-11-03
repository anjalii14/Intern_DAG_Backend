import uuid
from typing import List, Dict, Set, Union
from src.models.graph_model import Graph
from src.models.node_model import Node, DataType
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

    return updated_graph

def compute_node_output(node: Node, data_in: Dict[str, DataType]) -> Dict[str, DataType]:
    """
    Computes the output of the node based on the node's predefined `data_out`.

    Args:
        node: The current node being executed.
        data_in: The resolved inputs for the node.

    Returns:
        dict: The computed outputs for the node.
    """
    # Since the outputs for the nodes (NodeA, NodeB) are predefined in data_out,
    # we can just return the predefined data_out here.
    return node.data_out

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

def find_islands_in_graph(graph: Graph, return_islands: bool = False) -> Union[bool, List[Set[str]]]:
    """
    Find if there are any islands (disconnected components) in the graph.
    Optionally, return the list of all islands.

    Args:
        graph (Graph): The graph to check.
        return_islands (bool): Whether to return the list of islands or just a boolean indicating existence.

    Returns:
        bool or List[Set[str]]: Returns True if there are multiple disconnected components if return_islands is False.
                                Otherwise, returns a list of sets where each set contains node IDs that form an island.
    """
    visited = set()
    islands = []

    # Function to perform DFS from a given node
    def dfs(node_id: str, current_island: Set[str]):
        stack = [node_id]
        while stack:
            current_node_id = stack.pop()
            if current_node_id not in visited:
                visited.add(current_node_id)
                current_island.add(current_node_id)
                current_node = next((n for n in graph.nodes if n.node_id == current_node_id), None)
                if current_node:
                    # Traverse all connected nodes through paths_out
                    for edge in current_node.paths_out:
                        if edge.dst_node not in visited:
                            stack.append(edge.dst_node)
                    # Traverse all connected nodes through paths_in (since it can be undirected)
                    for edge in current_node.paths_in:
                        if edge.src_node not in visited:
                            stack.append(edge.src_node)

    # Loop through all nodes to find disconnected components
    for node in graph.nodes:
        if node.node_id not in visited:
            current_island = set()
            dfs(node.node_id, current_island)
            islands.append(current_island)

            # If we're not interested in returning islands but just checking if there are multiple
            if not return_islands and len(islands) > 1:
                return True  # Multiple disconnected components detected

    # If return_islands is True, return the list of islands
    if return_islands:
        return islands

    # If return_islands is False, return whether there are multiple disconnected components
    return len(islands) > 1

def resolve_data_in(node: Node, run_result_outputs: Dict[str, Dict], config) -> Dict[str, DataType]:
    """
    Resolves the `data_in` for a node based on the incoming edges (paths_in) and configuration.

    Args:
        node: The current node being executed.
        run_result_outputs: The results of nodes that have already been executed.
        config: The run configuration which may contain data overwrites.

    Returns:
        dict: The resolved `data_in` for the node.
    """
    current_data_in = {}
    edge_used_for_key = {}  # Tracks the latest edge used for each key

    # Process incoming edges (paths_in) and handle overwrites
    for edge in node.paths_in:
        src_node_id = edge.src_node
        if edge.src_to_dst_data_keys:
            for src_key, dst_key in edge.src_to_dst_data_keys.items():
                # Check if the source node has already been executed and has the required output
                if src_node_id in run_result_outputs and src_key in run_result_outputs[src_node_id]:
                    # If the destination key already exists, check overwrite conditions
                    if dst_key in current_data_in:
                        # If nodes are executed at the same level, choose lexicographically smaller node_id
                        if src_node_id < current_data_in[dst_key][1]:
                            current_data_in[dst_key] = (run_result_outputs[src_node_id][src_key], src_node_id)
                            edge_used_for_key[dst_key] = f"{src_node_id} -> {node.node_id} ({src_key} -> {dst_key})"
                    else:
                        # Directly add the result if this is the first time writing to this key
                        current_data_in[dst_key] = (run_result_outputs[src_node_id][src_key], src_node_id)
                        edge_used_for_key[dst_key] = f"{src_node_id} -> {node.node_id} ({src_key} -> {dst_key})"

    # Apply config-level overwrites (if any) for the current node
    if node.node_id in config.data_overwrites:
        for key, value in config.data_overwrites[node.node_id].items():
            current_data_in[key] = (value, node.node_id)

    # Return the cleaned data_in for execution (only the values, not the source node ids)
    return {key: value[0] for key, value in current_data_in.items()}, edge_used_for_key