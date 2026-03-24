"""Issue 12 — Graph composition utility.

Merges two ReasoningGraph instances into a combined graph with
optional connecting edges. Validates the result.
"""
from __future__ import annotations

from typing import Any

from srg.models.edge import ReasoningEdge
from srg.models.graph import ReasoningGraph
from srg.runtime.graph_validator import validate_graph


class ComposeError(Exception):
    """Raised when graph composition fails."""


def compose_graphs(
    graph_a: ReasoningGraph,
    graph_b: ReasoningGraph,
    connecting_edges: list[ReasoningEdge] | None = None,
    name: str | None = None,
    description: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> ReasoningGraph:
    """Merge two ReasoningGraphs into a combined graph.

    Parameters
    ----------
    graph_a, graph_b:
        The graphs to compose.
    connecting_edges:
        Optional edges linking nodes across the two graphs.
    name:
        Name for the composed graph. Defaults to ``"{a.name}+{b.name}"``.
    description:
        Description for the composed graph.
    metadata:
        Metadata for the composed graph. If None, merges both graphs'
        metadata (graph_b overrides on key conflict).

    Raises
    ------
    ComposeError
        If node IDs collide, connecting edges reference unknown nodes,
        or the composed graph fails validation (e.g., introduces a cycle).
    """
    # Check for duplicate node IDs across graphs
    ids_a = {n.id for n in graph_a.nodes}
    ids_b = {n.id for n in graph_b.nodes}
    overlap = ids_a & ids_b
    if overlap:
        raise ComposeError(
            f"Duplicate node IDs across graphs: {sorted(overlap)}"
        )

    all_ids = ids_a | ids_b

    # Validate connecting edges reference real nodes
    for edge in connecting_edges or []:
        if edge.from_node not in all_ids:
            raise ComposeError(
                f"Connecting edge references unknown node: {edge.from_node}"
            )
        if edge.to_node not in all_ids:
            raise ComposeError(
                f"Connecting edge references unknown node: {edge.to_node}"
            )

    # Build composed graph
    composed_name = name or f"{graph_a.name}+{graph_b.name}"
    composed_metadata: dict[str, Any] = {}
    if metadata is not None:
        composed_metadata = metadata
    else:
        composed_metadata = {**graph_a.metadata, **graph_b.metadata}

    composed = ReasoningGraph(
        name=composed_name,
        nodes=list(graph_a.nodes) + list(graph_b.nodes),
        edges=list(graph_a.edges) + list(graph_b.edges) + list(connecting_edges or []),
        description=description,
        metadata=composed_metadata,
    )

    # Validate the result
    result = validate_graph(composed)
    if not result.valid:
        raise ComposeError(
            f"Composed graph failed validation: {'; '.join(result.errors)}"
        )

    return composed
