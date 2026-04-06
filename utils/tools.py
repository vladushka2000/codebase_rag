from langgraph.constants import END


def get_max_path_depth(graph, start_node="__start__", depth=0, visited=None):
    """
    Calculate maximum path depth in the graph
    :param graph: CompiledStateGraph object
    :param start_node: starting node name
    :param depth: current depth
    :param visited: set of visited nodes
    :return: maximum depth
    """

    if visited is None:
        visited = set()

    if start_node in visited:
        return depth

    visited.add(start_node)
    graph_state = graph.get_graph()
    outgoing_edges = []

    for edge in graph_state.edges:
        if edge.source == start_node:
            outgoing_edges.append(edge.target)

    if not outgoing_edges:
        return depth

    max_depth = depth

    for next_node in outgoing_edges:
        if next_node == END:
            max_depth = max(max_depth, depth + 1)
        else:
            max_depth = max(max_depth, get_max_path_depth(graph, next_node, depth + 1, visited.copy()))

    return max_depth
