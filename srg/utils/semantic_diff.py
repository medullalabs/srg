"""Issue 14 — Semantic diff utility for comparing ReasoningGraph instances."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from srg.models.graph import ReasoningGraph


@dataclass
class NodeDiff:
    """Describes changes to a single node between two graph versions."""

    node_id: str
    changes: dict[str, tuple[Any, Any]] = field(default_factory=dict)


@dataclass
class GraphDiff:
    """Structured difference between two ReasoningGraph instances."""

    added_nodes: list[str] = field(default_factory=list)
    removed_nodes: list[str] = field(default_factory=list)
    modified_nodes: list[NodeDiff] = field(default_factory=list)
    added_edges: list[tuple[str, str]] = field(default_factory=list)
    removed_edges: list[tuple[str, str]] = field(default_factory=list)
    metadata_changes: dict[str, tuple[Any, Any]] = field(default_factory=dict)


# Fields compared when diffing nodes
_NODE_DIFF_FIELDS = (
    "kind",
    "inputs",
    "outputs",
    "function_ref",
    "prompt_template",
    "output_schema",
    "contracts",
    "effects",
    "description",
    "retry_policy",
    "metadata",
)


def _normalize(value: Any) -> Any:
    """Normalize a value for comparison purposes."""
    if hasattr(value, "model_dump"):
        return value.model_dump()
    return value


def semantic_diff(old: ReasoningGraph, new: ReasoningGraph) -> GraphDiff:
    """Compare two ReasoningGraph instances and return structured differences.

    Detects:
    - Added / removed nodes
    - Changed node fields (kind, inputs, outputs, contracts, output_schema,
      function_ref, prompt_template, effects, description, retry_policy, metadata)
    - Added / removed edges
    - Changed graph-level metadata (name, description, version, metadata)
    """
    diff = GraphDiff()

    # --- node diffs ---
    old_nodes = {n.id: n for n in old.nodes}
    new_nodes = {n.id: n for n in new.nodes}

    old_ids = set(old_nodes.keys())
    new_ids = set(new_nodes.keys())

    diff.added_nodes = sorted(new_ids - old_ids)
    diff.removed_nodes = sorted(old_ids - new_ids)

    for node_id in sorted(old_ids & new_ids):
        old_node = old_nodes[node_id]
        new_node = new_nodes[node_id]
        changes: dict[str, tuple[Any, Any]] = {}

        for fld in _NODE_DIFF_FIELDS:
            old_val = _normalize(getattr(old_node, fld))
            new_val = _normalize(getattr(new_node, fld))
            if old_val != new_val:
                changes[fld] = (old_val, new_val)

        if changes:
            diff.modified_nodes.append(NodeDiff(node_id=node_id, changes=changes))

    # --- edge diffs ---
    old_edge_keys = {(e.from_node, e.to_node) for e in old.edges}
    new_edge_keys = {(e.from_node, e.to_node) for e in new.edges}

    diff.added_edges = sorted(new_edge_keys - old_edge_keys)
    diff.removed_edges = sorted(old_edge_keys - new_edge_keys)

    # --- metadata diffs ---
    for attr in ("name", "description", "version"):
        old_val = getattr(old, attr)
        new_val = getattr(new, attr)
        if old_val != new_val:
            diff.metadata_changes[attr] = (old_val, new_val)

    if old.metadata != new.metadata:
        diff.metadata_changes["metadata"] = (old.metadata, new.metadata)

    return diff
