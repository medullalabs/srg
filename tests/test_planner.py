"""Tests for Issue 6 — Acyclic planner."""
from __future__ import annotations

import pytest

from srg.models.edge import ReasoningEdge
from srg.models.graph import ReasoningGraph
from srg.models.node import NodeKind, ReasoningNode
from srg.runtime.planner import CycleError, compute_execution_order


def _make_node(node_id: str) -> ReasoningNode:
    return ReasoningNode(
        id=node_id,
        kind=NodeKind.DETERMINISTIC,
        inputs=[],
        outputs=[],
    )


class TestComputeExecutionOrder:
    def test_linear_graph(self) -> None:
        graph = ReasoningGraph(
            name="linear",
            nodes=[_make_node("a"), _make_node("b"), _make_node("c")],
            edges=[
                ReasoningEdge(from_node="a", to_node="b"),
                ReasoningEdge(from_node="b", to_node="c"),
            ],
        )
        order = compute_execution_order(graph)
        assert order == ["a", "b", "c"]

    def test_diamond_graph(self) -> None:
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
        order = compute_execution_order(graph)
        assert order[0] == "a"
        assert order[-1] == "d"
        assert order.index("b") < order.index("d")
        assert order.index("c") < order.index("d")

    def test_single_node(self) -> None:
        graph = ReasoningGraph(
            name="single",
            nodes=[_make_node("a")],
            edges=[],
        )
        order = compute_execution_order(graph)
        assert order == ["a"]

    def test_disconnected_nodes(self) -> None:
        graph = ReasoningGraph(
            name="disconnected",
            nodes=[_make_node("a"), _make_node("b"), _make_node("c")],
            edges=[],
        )
        order = compute_execution_order(graph)
        assert set(order) == {"a", "b", "c"}
        assert len(order) == 3

    def test_cycle_raises_error(self) -> None:
        graph = ReasoningGraph(
            name="cycle",
            nodes=[_make_node("a"), _make_node("b")],
            edges=[
                ReasoningEdge(from_node="a", to_node="b"),
                ReasoningEdge(from_node="b", to_node="a"),
            ],
        )
        with pytest.raises(CycleError, match="cycle"):
            compute_execution_order(graph)

    def test_self_loop_raises_error(self) -> None:
        graph = ReasoningGraph(
            name="self_loop",
            nodes=[_make_node("a")],
            edges=[ReasoningEdge(from_node="a", to_node="a")],
        )
        with pytest.raises(CycleError, match="cycle"):
            compute_execution_order(graph)

    def test_three_node_cycle(self) -> None:
        graph = ReasoningGraph(
            name="tri_cycle",
            nodes=[_make_node("a"), _make_node("b"), _make_node("c")],
            edges=[
                ReasoningEdge(from_node="a", to_node="b"),
                ReasoningEdge(from_node="b", to_node="c"),
                ReasoningEdge(from_node="c", to_node="a"),
            ],
        )
        with pytest.raises(CycleError):
            compute_execution_order(graph)

    def test_fan_out_graph(self) -> None:
        graph = ReasoningGraph(
            name="fan_out",
            nodes=[_make_node("a"), _make_node("b"), _make_node("c")],
            edges=[
                ReasoningEdge(from_node="a", to_node="b"),
                ReasoningEdge(from_node="a", to_node="c"),
            ],
        )
        order = compute_execution_order(graph)
        assert order[0] == "a"
        assert set(order[1:]) == {"b", "c"}

    def test_deterministic_ordering(self) -> None:
        """Same graph should always produce the same order."""
        graph = ReasoningGraph(
            name="stable",
            nodes=[_make_node("c"), _make_node("a"), _make_node("b")],
            edges=[
                ReasoningEdge(from_node="a", to_node="c"),
                ReasoningEdge(from_node="b", to_node="c"),
            ],
        )
        order1 = compute_execution_order(graph)
        order2 = compute_execution_order(graph)
        assert order1 == order2
