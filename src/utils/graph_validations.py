from src.models.graph_model import Graph
from src.utils.helpers import get_topological_order

def validate_graph_structure(graph: Graph):
    """
    Validate the structure of a graph.
    - Check for cycles.
    - Validate data type compatibility.
    - Ensure there are no isolated nodes (using topological sort result).
    - Validate edge uniqueness and parity.
    """
    validate_no_cycles_and_islands(graph)  # Combine cycle check and isolated nodes check
    validate_data_type_compatibility(graph)  # Validate data type compatibility across edges
    validate_unique_edges(graph)  # Ensure no duplicate edges exist
    validate_edge_parity(graph)  # Ensure edge parity between source and destination nodes

def validate_no_cycles_and_islands(graph: Graph):
    """
    Validate that there are no cycles in the graph and that all nodes are connected.
    - This function also checks for isolated nodes as part of the topological sort.
    """
    try:
        get_topological_order(graph)
    except ValueError as e:
        raise ValueError(f"Graph validation failed: {str(e)}")

def validate_data_type_compatibility(graph: Graph):
    """
    Validate the data types compatibility across edges between nodes.
    Ensures that the data types being passed between nodes are compatible.

    Args:
        graph (Graph): The graph containing nodes and their connections.

    Raises:
        ValueError: If data types are incompatible between nodes.
    """
    for node in graph.nodes:
        for edge in node.paths_out:
            # Retrieve source and destination nodes based on edge information
            src_node = next((n for n in graph.nodes if n.node_id == edge.src_node), None)
            dst_node = next((n for n in graph.nodes if n.node_id == edge.dst_node), None)

            # Ensure both source and destination nodes exist
            if not src_node or not dst_node:
                raise ValueError(f"Invalid edge from {edge.src_node} to {edge.dst_node}")

            # Validate data type compatibility between source and destination nodes
            for src_key, dst_key in edge.src_to_dst_data_keys.items():
                if src_key not in src_node.data_out:
                    raise ValueError(f"Data key '{src_key}' not found in data_out of node {src_node.node_id}")
                
                if dst_key not in dst_node.data_in:
                    raise ValueError(f"Data key '{dst_key}' not found in data_in of node {dst_node.node_id}")

                # Ensure that the data types of the source and destination keys are compatible
                if type(src_node.data_out[src_key]) != type(dst_node.data_in[dst_key]):
                    raise ValueError(
                        f"Data type mismatch for key '{src_key}' from node {src_node.node_id} to '{dst_key}' "
                        f"of node {dst_node.node_id}: {type(src_node.data_out[src_key])} vs {type(dst_node.data_in[dst_key])}"
                    )

def validate_unique_edges(graph: Graph):
    """
    Validate that there are no duplicate edges between nodes.
    A node should have only one edge from the same source to the same destination with the same key mapping.
    """
    seen_edges = set()
    for node in graph.nodes:
        for edge in node.paths_out:
            edge_signature = (edge.src_node, edge.dst_node, frozenset(edge.src_to_dst_data_keys.items()) if edge.src_to_dst_data_keys else frozenset())
            if edge_signature in seen_edges:
                raise ValueError(f"Duplicate edge detected between {edge.src_node} and {edge.dst_node} with the same key mapping.")
            seen_edges.add(edge_signature)

def validate_edge_parity(graph: Graph):
    """
    Validate that edges are properly represented in both source and destination nodes.
    - Ensure that both src and dst nodes acknowledge the edge.
    """
    for node in graph.nodes:
        for edge in node.paths_out:
            dst_node = next((n for n in graph.nodes if n.node_id == edge.dst_node), None)

            if not dst_node:
                raise ValueError(f"Invalid edge: {edge.src_node} -> {edge.dst_node}")

            # Check if the edge is present in the destination node's paths_in
            if edge not in dst_node.paths_in:
                raise ValueError(f"Edge from {edge.src_node} to {edge.dst_node} is missing in destination node's paths_in.")

        for edge in node.paths_in:
            src_node = next((n for n in graph.nodes if n.node_id == edge.src_node), None)

            if not src_node:
                raise ValueError(f"Invalid edge: {edge.src_node} -> {edge.dst_node}")

            # Check if the edge is present in the source node's paths_out
            if edge not in src_node.paths_out:
                raise ValueError(f"Edge from {edge.src_node} to {edge.dst_node} is missing in source node's paths_out.")