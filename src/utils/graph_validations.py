from src.models.graph_model import Graph
from src.utils.helpers import get_topological_order, find_islands_in_graph
from typing import Dict

def validate_graph_structure(graph: Graph):
    """
    Validate the structure of a graph.
    - Check for cycles.
    - Check for isolated nodes (islands).
    - Validate data type compatibility.
    - Ensure there are no duplicate edges.
    - Ensure edges have correct parity (mirrored paths).
    - Confirm data consistency.
    - Ensure nodes referenced in paths exist.
    """
    node_lookup = {node.node_id: node for node in graph.nodes}
    
    validate_no_cycles(graph)
    validate_no_islands(graph)
    validate_data_type_compatibility(graph, node_lookup)
    validate_unique_edges(graph, node_lookup)
    validate_edge_parity(graph, node_lookup)
    validate_data_consistency(graph, node_lookup)
    validate_node_existence(graph, node_lookup)

def validate_no_cycles(graph: Graph):
    """
    Validate that there are no cycles in the graph.
    - This function uses topological sorting to detect cycles.
    """
    try:
        get_topological_order(graph)
    except ValueError as e:
        raise ValueError(f"Graph validation failed as it contains cycle: {str(e)}")

def validate_no_islands(graph: Graph):
    """
    Validate if the graph contains any islands.
    Raises an error if the graph contains disconnected components.

    Args:
        graph (Graph): The graph to validate.

    Raises:
        ValueError: If the graph contains islands.
    """
    has_islands = find_islands_in_graph(graph, return_islands=False)
    if has_islands:
        raise ValueError("Graph validation failed: The graph contains isolated nodes or disconnected components.")

def validate_data_type_compatibility(graph: Graph, node_lookup: Dict[str, Graph]):
    """
    Validate the data types compatibility across edges between nodes.
    Ensures that the data types being passed between nodes are compatible.
    """
    for node in graph.nodes:
        for edge in node.paths_out:
            src_node = node_lookup.get(edge.src_node)
            dst_node = node_lookup.get(edge.dst_node)
            if not src_node or not dst_node:
                raise ValueError(f"Invalid edge from {edge.src_node} to {edge.dst_node}")

            for src_key, dst_key in edge.src_to_dst_data_keys.items():
                if src_key not in src_node.data_out:
                    raise ValueError(f"Data key '{src_key}' not found in data_out of node {src_node.node_id}")
                
                if dst_key not in dst_node.data_in:
                    raise ValueError(f"Data key '{dst_key}' not found in data_in of node {dst_node.node_id}")

                if type(src_node.data_out[src_key]) != type(dst_node.data_in[dst_key]):
                    raise ValueError(
                        f"Data type mismatch for key '{src_key}' from node {src_node.node_id} to '{dst_key}' "
                        f"of node {dst_node.node_id}: {type(src_node.data_out[src_key])} vs {type(dst_node.data_in[dst_key])}"
                    )

def validate_unique_edges(graph: Graph, node_lookup: Dict[str, Graph]):
    """
    Validate that there are no duplicate edges between nodes.
    """
    seen_edges = set()
    for node in graph.nodes:
        for edge in node.paths_out:
            edge_signature = (edge.src_node, edge.dst_node, frozenset(edge.src_to_dst_data_keys.items()) if edge.src_to_dst_data_keys else frozenset())
            if edge_signature in seen_edges:
                raise ValueError(f"Duplicate edge detected between {edge.src_node} and {edge.dst_node} with the same key mapping.")
            seen_edges.add(edge_signature)

def validate_edge_parity(graph: Graph, node_lookup: Dict[str, Graph]):
    """
    Validate that edges are properly represented in both source and destination nodes.
    """
    for node in graph.nodes:
        for edge in node.paths_out:
            dst_node = node_lookup.get(edge.dst_node)
            if not dst_node:
                raise ValueError(f"Invalid edge: {edge.src_node} -> {edge.dst_node}")

            if edge not in dst_node.paths_in:
                raise ValueError(f"Edge from {edge.src_node} to {edge.dst_node} is missing in destination node's paths_in.")

        for edge in node.paths_in:
            src_node = node_lookup.get(edge.src_node)
            if not src_node:
                raise ValueError(f"Invalid edge: {edge.src_node} -> {edge.dst_node}")

            if edge not in src_node.paths_out:
                raise ValueError(f"Edge from {edge.src_node} to {edge.dst_node} is missing in source node's paths_out.")

def validate_data_consistency(graph: Graph, node_lookup: Dict[str, Graph]):
    """
    Validate data consistency across connected nodes.
    """
    for node in graph.nodes:
        for edge in node.paths_out:
            src_node = node_lookup.get(edge.src_node)
            dst_node = node_lookup.get(edge.dst_node)

            if not src_node or not dst_node:
                raise ValueError(f"Edge references nonexistent node: {edge.src_node} or {edge.dst_node}")

            for src_key, dst_key in edge.src_to_dst_data_keys.items():
                if src_key not in src_node.data_out:
                    raise ValueError(f"Data key '{src_key}' missing in data_out of node {src_node.node_id}")
                
                if dst_key not in dst_node.data_in:
                    raise ValueError(f"Data key '{dst_key}' missing in data_in of node {dst_node.node_id}")


def validate_node_existence(graph: Graph, node_lookup: Dict[str, Graph]):
    """
    Validate that every node referenced in paths exists within the graph.
    """
    node_ids = set(node_lookup.keys())
    for node in graph.nodes:
        for edge in node.paths_out + node.paths_in:
            if edge.src_node not in node_ids or edge.dst_node not in node_ids:
                raise ValueError(f"Path references nonexistent node: {edge.src_node} or {edge.dst_node}")
