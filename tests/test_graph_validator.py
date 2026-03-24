"""Tests for Issue 5 — Graph validator."""
from __future__ import annotations

from srg.models.edge import ReasoningEdge
from srg.models.graph import ReasoningGraph
from srg.models.node import NodeKind, ReasoningNode
from srg.runtime.graph_validator import validate_graph


def _make_node(
    node_id: str,
    kind: NodeKind = NodeKind.DETERMINISTIC,
    **kwargs: object,
) -> ReasoningNode:
    defaults: dict[str, object] = {
        "id": node_id,
        "kind": kind,
        "inputs": [],
        "outputs": [],
    }
    defaults.update(kwargs)
    return ReasoningNode.model_validate(defaults)


class TestValidateGraph:
    def test_valid_linear_graph(self) -> None:
        graph = ReasoningGraph(
            name="linear",
            nodes=[
                _make_node("a", inputs=["x"], outputs=["y"]),
                _make_node("b", inputs=["y"], outputs=["z"]),
            ],
            edges=[ReasoningEdge(from_node="a", to_node="b")],
        )
        result = validate_graph(graph)
        assert result.valid
        assert result.errors == []

    def test_valid_agentic_node(self) -> None:
        graph = ReasoningGraph(
            name="agentic",
            nodes=[
                _make_node(
                    "a",
                    kind=NodeKind.AGENTIC,
                    inputs=["x"],
                    outputs=["y"],
                    output_schema={"type": "object"},
                    contracts=["y is nonempty"],
                ),
            ],
            edges=[],
        )
        result = validate_graph(graph)
        assert result.valid

    def test_duplicate_node_ids(self) -> None:
        graph = ReasoningGraph(
            name="dup",
            nodes=[
                _make_node("a"),
                _make_node("a"),
            ],
            edges=[],
        )
        result = validate_graph(graph)
        assert not result.valid
        assert any("Duplicate node ID" in e for e in result.errors)

    def test_edge_references_nonexistent_from_node(self) -> None:
        graph = ReasoningGraph(
            name="bad_edge",
            nodes=[_make_node("a")],
            edges=[ReasoningEdge(from_node="nonexistent", to_node="a")],
        )
        result = validate_graph(graph)
        assert not result.valid
        assert any("non-existent node: nonexistent" in e for e in result.errors)

    def test_edge_references_nonexistent_to_node(self) -> None:
        graph = ReasoningGraph(
            name="bad_edge",
            nodes=[_make_node("a")],
            edges=[ReasoningEdge(from_node="a", to_node="nonexistent")],
        )
        result = validate_graph(graph)
        assert not result.valid
        assert any("non-existent node: nonexistent" in e for e in result.errors)

    def test_agentic_node_missing_output_schema(self) -> None:
        graph = ReasoningGraph(
            name="no_schema",
            nodes=[
                _make_node(
                    "a",
                    kind=NodeKind.AGENTIC,
                    contracts=["x is nonempty"],
                ),
            ],
            edges=[],
        )
        result = validate_graph(graph)
        assert not result.valid
        assert any("missing output_schema" in e for e in result.errors)

    def test_agentic_node_missing_contracts(self) -> None:
        graph = ReasoningGraph(
            name="no_contracts",
            nodes=[
                _make_node(
                    "a",
                    kind=NodeKind.AGENTIC,
                    output_schema={"type": "object"},
                ),
            ],
            edges=[],
        )
        result = validate_graph(graph)
        assert not result.valid
        assert any("missing contracts" in e for e in result.errors)

    def test_agentic_node_missing_both(self) -> None:
        graph = ReasoningGraph(
            name="no_both",
            nodes=[
                _make_node("a", kind=NodeKind.AGENTIC),
            ],
            edges=[],
        )
        result = validate_graph(graph)
        assert not result.valid
        assert len(result.errors) == 2

    def test_cycle_detected(self) -> None:
        graph = ReasoningGraph(
            name="cycle",
            nodes=[
                _make_node("a"),
                _make_node("b"),
            ],
            edges=[
                ReasoningEdge(from_node="a", to_node="b"),
                ReasoningEdge(from_node="b", to_node="a"),
            ],
        )
        result = validate_graph(graph)
        assert not result.valid
        assert any("cycle" in e.lower() for e in result.errors)

    def test_self_loop_detected(self) -> None:
        graph = ReasoningGraph(
            name="self_loop",
            nodes=[_make_node("a")],
            edges=[ReasoningEdge(from_node="a", to_node="a")],
        )
        result = validate_graph(graph)
        assert not result.valid
        assert any("cycle" in e.lower() for e in result.errors)

    def test_diamond_graph_valid(self) -> None:
        graph = ReasoningGraph(
            name="diamond",
            nodes=[
                _make_node("a"),
                _make_node("b"),
                _make_node("c"),
                _make_node("d"),
            ],
            edges=[
                ReasoningEdge(from_node="a", to_node="b"),
                ReasoningEdge(from_node="a", to_node="c"),
                ReasoningEdge(from_node="b", to_node="d"),
                ReasoningEdge(from_node="c", to_node="d"),
            ],
        )
        result = validate_graph(graph)
        assert result.valid

    def test_empty_graph_valid(self) -> None:
        graph = ReasoningGraph(
            name="empty",
            nodes=[_make_node("a")],
            edges=[],
        )
        result = validate_graph(graph)
        assert result.valid

    def test_multiple_errors_reported(self) -> None:
        graph = ReasoningGraph(
            name="multi_error",
            nodes=[
                _make_node("a"),
                _make_node("a"),  # duplicate
                _make_node("b", kind=NodeKind.AGENTIC),  # missing schema+contracts
            ],
            edges=[
                ReasoningEdge(from_node="a", to_node="ghost"),  # bad ref
            ],
        )
        result = validate_graph(graph)
        assert not result.valid
        assert len(result.errors) >= 3
