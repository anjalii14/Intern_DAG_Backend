from src.models.graph_model import Graph

def validate_graph_config(graph: Graph, config):
    """
    Validate the graph configuration based on the provided config for the run.
    
    Args:
        graph (Graph): The graph to validate against.
        config (GraphRunConfig): The configuration object containing run-specific settings.

    Raises:
        ValueError: If the config contains invalid data, such as nonexistent nodes, invalid keys, or data type mismatches.
    """
    # Identify all nodes, root nodes (no incoming edges), and non-root nodes (with incoming edges)
    node_ids = {node.node_id for node in graph.nodes}
    root_nodes = {node.node_id for node in graph.nodes if not node.paths_in}  # Nodes without incoming edges
    non_root_nodes = {node.node_id for node in graph.nodes if node.paths_in}  # Nodes with incoming edges

    # Validate root_inputs
    for node_id, data in config.root_inputs.items():
        if node_id not in root_nodes:
            raise ValueError(f"Node '{node_id}' in root_inputs must be a root node (without incoming edges).")
        
        # Ensure all required data_in keys are present in root_inputs for this node
        root_node = next(node for node in graph.nodes if node.node_id == node_id)
        missing_keys = set(root_node.data_in.keys()) - set(data.keys())
        if missing_keys:
            raise ValueError(f"Root node '{node_id}' is missing required data_in keys: {missing_keys}")
        
        # Validate data types of root_inputs
        for key, value in data.items():
            expected_type = type(root_node.data_in[key])
            if not isinstance(value, expected_type):
                raise ValueError(
                    f"Data type mismatch in root_inputs for node '{node_id}': "
                    f"expected '{key}' to be of type '{expected_type.__name__}', but got '{type(value).__name__}'."
                )

    # Validate data_overwrites
    for node_id, overwrite_data in config.data_overwrites.items():
        if node_id not in non_root_nodes:
            raise ValueError(f"Node '{node_id}' in data_overwrites must be a non-root node (with incoming edges).")
        
        # Check if overwrite keys match the node’s data_in structure
        node = next(node for node in graph.nodes if node.node_id == node_id)
        invalid_keys = set(overwrite_data.keys()) - set(node.data_in.keys())
        if invalid_keys:
            raise ValueError(f"Data overwrites for node '{node_id}' contain invalid keys: {invalid_keys}")
        
        # Validate data types of data_overwrites
        for key, value in overwrite_data.items():
            expected_type = type(node.data_in[key])
            if not isinstance(value, expected_type):
                raise ValueError(
                    f"Data type mismatch in data_overwrites for node '{node_id}': "
                    f"expected '{key}' to be of type '{expected_type.__name__}', but got '{type(value).__name__}'."
                )

    # Validate enable_list and disable_list
    if config.enable_list and config.disable_list:
        overlapping_nodes = set(config.enable_list).intersection(config.disable_list)
        if overlapping_nodes:
            raise ValueError(f"Nodes cannot appear in both enable and disable lists. Conflicting nodes: {overlapping_nodes}")

    # Check that each node in the graph is in either enable_list or disable_list
    all_listed_nodes = set(config.enable_list or []).union(config.disable_list or [])
    missing_nodes = node_ids - all_listed_nodes
    if missing_nodes:
        raise ValueError(f"Every node must be in either enable or disable list. Missing nodes: {missing_nodes}")

    # Check that all nodes in enable_list or disable_list exist in the graph
    invalid_nodes = [node for node in (config.enable_list or config.disable_list) if node not in node_ids]
    if invalid_nodes:
        raise ValueError(f"Invalid nodes in enable/disable list: {invalid_nodes}")

    print("Graph config validation passed.")