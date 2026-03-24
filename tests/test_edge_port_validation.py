"""Issue 15 — Tests for edge from_output/to_input validation."""
from __future__ import annotations

from srg.models.edge import ReasoningEdge
from srg.models.graph import ReasoningGraph
from srg.models.node import NodeKind, ReasoningNode
from srg.runtime.graph_validator import validate_graph


def _det_node(id: str, inputs: list[str] | None = None, outputs: list[str] | None = None) -> ReasoningNode:
    return ReasoningNode(id=id, kind=NodeKind.DETERMINISTIC, inputs=inputs or [], outputs=outputs or [], function_ref=f"{id}_fn")


def _graph(nodes: list[ReasoningNode], edges: list[ReasoningEdge]) -> ReasoningGraph:
    return ReasoningGraph(name="test", nodes=nodes, edges=edges)


class TestEdgePortValidation:
    def test_valid_from_output(self) -> None:
        g = _graph(
            [_det_node("a", outputs=["x", "y"]), _det_node("b", inputs=["x"])],
            [ReasoningEdge(from_node="a", to_node="b", from_output="x")],
        )
        result = validate_graph(g)
        assert result.valid

    def test_valid_to_input(self) -> None:
        g = _graph(
            [_det_node("a", outputs=["x"]), _det_node("b", inputs=["x", "y"])],
            [ReasoningEdge(from_node="a", to_node="b", to_input="x")],
        )
        result = validate_graph(g)
        assert result.valid

    def test_valid_both_ports(self) -> None:
        g = _graph(
            [_det_node("a", outputs=["out1"]), _det_node("b", inputs=["in1"])],
            [ReasoningEdge(from_node="a", to_node="b", from_output="out1", to_input="in1")],
        )
        result = validate_graph(g)
        assert result.valid

    def test_invalid_from_output(self) -> None:
        g = _graph(
            [_det_node("a", outputs=["x"]), _det_node("b")],
            [ReasoningEdge(from_node="a", to_node="b", from_output="nonexistent")],
        )
        result = validate_graph(g)
        assert not result.valid
        assert any("from_output 'nonexistent'" in e for e in result.errors)

    def test_invalid_to_input(self) -> None:
        g = _graph(
            [_det_node("a"), _det_node("b", inputs=["x"])],
            [ReasoningEdge(from_node="a", to_node="b", to_input="nonexistent")],
        )
        result = validate_graph(g)
        assert not result.valid
        assert any("to_input 'nonexistent'" in e for e in result.errors)

    def test_bare_edges_still_pass(self) -> None:
        g = _graph(
            [_det_node("a", outputs=["x"]), _det_node("b", inputs=["x"])],
            [ReasoningEdge(from_node="a", to_node="b")],
        )
        result = validate_graph(g)
        assert result.valid

    def test_error_identifies_edge(self) -> None:
        g = _graph(
            [_det_node("src", outputs=["a"]), _det_node("dst", inputs=["b"])],
            [ReasoningEdge(from_node="src", to_node="dst", from_output="wrong")],
        )
        result = validate_graph(g)
        assert not result.valid
        assert any("src->dst" in e for e in result.errors)

    def test_existing_example_graphs_still_valid(self) -> None:
        from pathlib import Path
        from srg.runtime.loader import load_graph

        examples = Path(__file__).resolve().parent.parent / "srg" / "examples"
        for yaml_file in examples.glob("*.yaml"):
            graph = load_graph(yaml_file)
            result = validate_graph(graph)
            assert result.valid, f"{yaml_file.name}: {result.errors}"
