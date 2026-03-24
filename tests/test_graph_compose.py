"""Issue 12 — Tests for graph composition utility."""
from __future__ import annotations

import pytest

from srg.models.edge import ReasoningEdge
from srg.models.graph import ReasoningGraph
from srg.models.node import NodeKind, ReasoningNode
from srg.utils.graph_compose import ComposeError, compose_graphs


def _det_node(id: str, inputs: list[str] | None = None, outputs: list[str] | None = None) -> ReasoningNode:
    return ReasoningNode(
        id=id,
        kind=NodeKind.DETERMINISTIC,
        inputs=inputs or [],
        outputs=outputs or [],
        function_ref=f"{id}_fn",
    )


def _agentic_node(id: str) -> ReasoningNode:
    return ReasoningNode(
        id=id,
        kind=NodeKind.AGENTIC,
        inputs=["data"],
        outputs=["result"],
        output_schema={"type": "object", "properties": {"result": {"type": "string"}}, "required": ["result"]},
        contracts=["result is nonempty"],
    )


def _graph(name: str, nodes: list[ReasoningNode], edges: list[ReasoningEdge] | None = None, **kwargs) -> ReasoningGraph:
    return ReasoningGraph(name=name, nodes=nodes, edges=edges or [], **kwargs)


class TestComposeGraphs:
    def test_simple_compose(self) -> None:
        a = _graph("a", [_det_node("n1", outputs=["x"])], [])
        b = _graph("b", [_det_node("n2", inputs=["x"])], [])
        connecting = [ReasoningEdge(from_node="n1", to_node="n2")]

        composed = compose_graphs(a, b, connecting_edges=connecting)

        assert composed.name == "a+b"
        assert len(composed.nodes) == 2
        assert len(composed.edges) == 1
        assert {n.id for n in composed.nodes} == {"n1", "n2"}

    def test_compose_without_connecting_edges(self) -> None:
        a = _graph("a", [_det_node("n1")])
        b = _graph("b", [_det_node("n2")])

        composed = compose_graphs(a, b)

        assert len(composed.nodes) == 2
        assert len(composed.edges) == 0

    def test_compose_preserves_internal_edges(self) -> None:
        a = _graph(
            "a",
            [_det_node("a1"), _det_node("a2")],
            [ReasoningEdge(from_node="a1", to_node="a2")],
        )
        b = _graph(
            "b",
            [_det_node("b1"), _det_node("b2")],
            [ReasoningEdge(from_node="b1", to_node="b2")],
        )
        connecting = [ReasoningEdge(from_node="a2", to_node="b1")]

        composed = compose_graphs(a, b, connecting_edges=connecting)

        assert len(composed.nodes) == 4
        assert len(composed.edges) == 3

    def test_duplicate_node_ids_rejected(self) -> None:
        a = _graph("a", [_det_node("shared_id")])
        b = _graph("b", [_det_node("shared_id")])

        with pytest.raises(ComposeError, match="Duplicate node IDs.*shared_id"):
            compose_graphs(a, b)

    def test_connecting_edge_unknown_from_node(self) -> None:
        a = _graph("a", [_det_node("n1")])
        b = _graph("b", [_det_node("n2")])
        bad_edge = [ReasoningEdge(from_node="ghost", to_node="n2")]

        with pytest.raises(ComposeError, match="unknown node.*ghost"):
            compose_graphs(a, b, connecting_edges=bad_edge)

    def test_connecting_edge_unknown_to_node(self) -> None:
        a = _graph("a", [_det_node("n1")])
        b = _graph("b", [_det_node("n2")])
        bad_edge = [ReasoningEdge(from_node="n1", to_node="ghost")]

        with pytest.raises(ComposeError, match="unknown node.*ghost"):
            compose_graphs(a, b, connecting_edges=bad_edge)

    def test_cycle_introduction_rejected(self) -> None:
        a = _graph(
            "a",
            [_det_node("a1"), _det_node("a2")],
            [ReasoningEdge(from_node="a1", to_node="a2")],
        )
        b = _graph("b", [_det_node("b1")])
        # Create cycle: a1 → a2 → b1 → a1
        connecting = [
            ReasoningEdge(from_node="a2", to_node="b1"),
            ReasoningEdge(from_node="b1", to_node="a1"),
        ]

        with pytest.raises(ComposeError, match="cycle"):
            compose_graphs(a, b, connecting_edges=connecting)

    def test_custom_name(self) -> None:
        a = _graph("a", [_det_node("n1")])
        b = _graph("b", [_det_node("n2")])

        composed = compose_graphs(a, b, name="custom_name")

        assert composed.name == "custom_name"

    def test_custom_description(self) -> None:
        a = _graph("a", [_det_node("n1")])
        b = _graph("b", [_det_node("n2")])

        composed = compose_graphs(a, b, description="A composed graph")

        assert composed.description == "A composed graph"

    def test_metadata_merge(self) -> None:
        a = _graph("a", [_det_node("n1")], metadata={"source": "a", "shared": 1})
        b = _graph("b", [_det_node("n2")], metadata={"source": "b", "shared": 2})

        composed = compose_graphs(a, b)

        # b overrides on conflict
        assert composed.metadata["source"] == "b"
        assert composed.metadata["shared"] == 2

    def test_metadata_explicit_override(self) -> None:
        a = _graph("a", [_det_node("n1")], metadata={"x": 1})
        b = _graph("b", [_det_node("n2")], metadata={"y": 2})

        composed = compose_graphs(a, b, metadata={"custom": True})

        assert composed.metadata == {"custom": True}

    def test_compose_with_agentic_nodes(self) -> None:
        a = _graph("a", [_det_node("prep", outputs=["data"])])
        b = _graph("b", [_agentic_node("assess")])
        connecting = [ReasoningEdge(from_node="prep", to_node="assess")]

        composed = compose_graphs(a, b, connecting_edges=connecting)

        assert len(composed.nodes) == 2
        kinds = {n.id: n.kind for n in composed.nodes}
        assert kinds["prep"] == NodeKind.DETERMINISTIC
        assert kinds["assess"] == NodeKind.AGENTIC

    def test_compose_real_graphs(self) -> None:
        """Compose two loaded example-style graphs."""
        scorer_a = _graph(
            "scorer_a",
            [_det_node("extract_a", outputs=["features_a"]),
             _det_node("score_a", inputs=["features_a"], outputs=["score_a"])],
            [ReasoningEdge(from_node="extract_a", to_node="score_a")],
        )
        scorer_b = _graph(
            "scorer_b",
            [_det_node("extract_b", outputs=["features_b"]),
             _det_node("score_b", inputs=["features_b"], outputs=["score_b"])],
            [ReasoningEdge(from_node="extract_b", to_node="score_b")],
        )
        # Add aggregation
        agg = _graph(
            "agg",
            [_det_node("aggregate", inputs=["score_a", "score_b"], outputs=["final"])],
        )

        # Compose scorers first
        combined = compose_graphs(scorer_a, scorer_b, name="combined_scorers")
        # Then add aggregation
        final = compose_graphs(
            combined, agg,
            connecting_edges=[
                ReasoningEdge(from_node="score_a", to_node="aggregate"),
                ReasoningEdge(from_node="score_b", to_node="aggregate"),
            ],
            name="full_pipeline",
        )

        assert final.name == "full_pipeline"
        assert len(final.nodes) == 5
        assert len(final.edges) == 4
