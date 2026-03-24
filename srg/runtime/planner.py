from __future__ import annotations

from collections import defaultdict

from srg.models.graph import ReasoningGraph


class CycleError(Exception):
    """Raised when the graph contains a cycle."""


def compute_execution_order(graph: ReasoningGraph) -> list[str]:
    """Compute topological execution order from graph edges.

    Returns an ordered list of node IDs. Raises CycleError if the graph
    contains a cycle.
    """
    node_ids = {node.id for node in graph.nodes}

    in_degree: dict[str, int] = {nid: 0 for nid in node_ids}
    adjacency: dict[str, list[str]] = defaultdict(list)

    for edge in graph.edges:
        if edge.from_node in node_ids and edge.to_node in node_ids:
            adjacency[edge.from_node].append(edge.to_node)
            in_degree[edge.to_node] += 1

    queue: list[str] = sorted(
        nid for nid in node_ids if in_degree[nid] == 0
    )
    order: list[str] = []

    while queue:
        current = queue.pop(0)
        order.append(current)
        for neighbor in sorted(adjacency[current]):
            in_degree[neighbor] -= 1
            if in_degree[neighbor] == 0:
                queue.append(neighbor)

    if len(order) != len(node_ids):
        raise CycleError("Graph contains a cycle")

    return order
