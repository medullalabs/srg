"""Issue 13 — Save a ReasoningGraph back to YAML."""
from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from srg.models.graph import ReasoningGraph


def _clean_node(node_dict: dict[str, Any]) -> dict[str, Any]:
    """Remove None/empty optional fields for clean YAML output."""
    cleaned: dict[str, Any] = {}
    # Preserve key order matching the canonical schema
    key_order = [
        "id", "kind", "inputs", "outputs", "description",
        "function_ref", "prompt_template", "output_schema",
        "contracts", "effects", "retry_policy", "metadata",
    ]
    for key in key_order:
        if key not in node_dict:
            continue
        val = node_dict[key]
        # Skip None values
        if val is None:
            continue
        # Skip empty lists/dicts for optional fields
        if key in ("contracts", "effects", "metadata") and not val:
            continue
        cleaned[key] = val
    return cleaned


def _clean_edge(edge_dict: dict[str, Any]) -> dict[str, Any]:
    """Remove None/default optional fields for clean YAML output."""
    cleaned: dict[str, Any] = {}
    for key in ("from_node", "to_node", "from_output", "to_input", "kind"):
        if key not in edge_dict:
            continue
        val = edge_dict[key]
        if val is None:
            continue
        if key == "kind" and val == "data_flow":
            continue
        cleaned[key] = val
    return cleaned


def save_graph_to_string(graph: ReasoningGraph) -> str:
    """Serialize a ReasoningGraph to a YAML string."""
    data: dict[str, Any] = {"name": graph.name}

    if graph.description:
        data["description"] = graph.description
    if graph.version:
        data["version"] = graph.version
    if graph.metadata:
        data["metadata"] = graph.metadata

    data["nodes"] = [
        _clean_node(node.model_dump(mode="json")) for node in graph.nodes
    ]
    data["edges"] = [
        _clean_edge(edge.model_dump(mode="json")) for edge in graph.edges
    ]

    return yaml.dump(
        data,
        default_flow_style=False,
        sort_keys=False,
        allow_unicode=True,
    )


def save_graph(graph: ReasoningGraph, path: str | Path) -> None:
    """Serialize a ReasoningGraph to a YAML file."""
    Path(path).write_text(save_graph_to_string(graph), encoding="utf-8")
