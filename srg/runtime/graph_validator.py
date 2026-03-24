from __future__ import annotations

from collections import defaultdict

from pydantic import BaseModel, Field

from srg.models.graph import ReasoningGraph
from srg.models.node import NodeKind


class ValidationResult(BaseModel):
    valid: bool
    errors: list[str] = Field(default_factory=list)


def validate_graph(graph: ReasoningGraph) -> ValidationResult:
    """Validate a ReasoningGraph and return structured results."""
    errors: list[str] = []

    # Check for duplicate node IDs
    seen_ids: set[str] = set()
    for node in graph.nodes:
        if node.id in seen_ids:
            errors.append(f"Duplicate node ID: {node.id}")
        seen_ids.add(node.id)

    # Check edges reference existing nodes and valid ports
    node_ids = {node.id for node in graph.nodes}
    node_map = {node.id: node for node in graph.nodes}
    for edge in graph.edges:
        if edge.from_node not in node_ids:
            errors.append(
                f"Edge references non-existent node: {edge.from_node}"
            )
        if edge.to_node not in node_ids:
            errors.append(
                f"Edge references non-existent node: {edge.to_node}"
            )

        # Validate from_output against source node's outputs
        if edge.from_output and edge.from_node in node_map:
            source = node_map[edge.from_node]
            if source.outputs and edge.from_output not in source.outputs:
                errors.append(
                    f"Edge {edge.from_node}->{edge.to_node}: "
                    f"from_output '{edge.from_output}' not in "
                    f"{edge.from_node}'s outputs {source.outputs}"
                )

        # Validate to_input against target node's inputs
        if edge.to_input and edge.to_node in node_map:
            target = node_map[edge.to_node]
            if target.inputs and edge.to_input not in target.inputs:
                errors.append(
                    f"Edge {edge.from_node}->{edge.to_node}: "
                    f"to_input '{edge.to_input}' not in "
                    f"{edge.to_node}'s inputs {target.inputs}"
                )

    # Check agentic nodes have output_schema
    for node in graph.nodes:
        if node.kind == NodeKind.AGENTIC:
            if node.output_schema is None:
                errors.append(
                    f"Agentic node '{node.id}' missing output_schema"
                )
            if not node.contracts:
                errors.append(
                    f"Agentic node '{node.id}' missing contracts"
                )

    # Check for cycles using topological sort (Kahn's algorithm)
    in_degree: dict[str, int] = defaultdict(int)
    adjacency: dict[str, list[str]] = defaultdict(list)

    for nid in node_ids:
        in_degree[nid] = 0

    for edge in graph.edges:
        if edge.from_node in node_ids and edge.to_node in node_ids:
            adjacency[edge.from_node].append(edge.to_node)
            in_degree[edge.to_node] += 1

    queue: list[str] = [nid for nid in node_ids if in_degree[nid] == 0]
    visited_count = 0

    while queue:
        current = queue.pop(0)
        visited_count += 1
        for neighbor in adjacency[current]:
            in_degree[neighbor] -= 1
            if in_degree[neighbor] == 0:
                queue.append(neighbor)

    if visited_count != len(node_ids):
        errors.append("Graph contains a cycle")

    return ValidationResult(valid=len(errors) == 0, errors=errors)
