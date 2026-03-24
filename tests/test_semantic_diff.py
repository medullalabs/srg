"""Issue 14 — Tests for the semantic diff utility."""
from __future__ import annotations

from srg.models.edge import ReasoningEdge
from srg.models.graph import ReasoningGraph
from srg.models.node import NodeKind, ReasoningNode
from srg.utils.semantic_diff import semantic_diff


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


class TestSemanticDiffNodes:
    def test_identical_graphs_produce_empty_diff(self) -> None:
        graph = ReasoningGraph(
            name="g",
            nodes=[_make_node("a"), _make_node("b")],
            edges=[ReasoningEdge(from_node="a", to_node="b")],
        )
        diff = semantic_diff(graph, graph)
        assert diff.added_nodes == []
        assert diff.removed_nodes == []
        assert diff.modified_nodes == []
        assert diff.added_edges == []
        assert diff.removed_edges == []
        assert diff.metadata_changes == {}

    def test_added_node(self) -> None:
        old = ReasoningGraph(
            name="g",
            nodes=[_make_node("a")],
            edges=[],
        )
        new = ReasoningGraph(
            name="g",
            nodes=[_make_node("a"), _make_node("b")],
            edges=[],
        )
        diff = semantic_diff(old, new)
        assert diff.added_nodes == ["b"]
        assert diff.removed_nodes == []

    def test_removed_node(self) -> None:
        old = ReasoningGraph(
            name="g",
            nodes=[_make_node("a"), _make_node("b")],
            edges=[],
        )
        new = ReasoningGraph(
            name="g",
            nodes=[_make_node("a")],
            edges=[],
        )
        diff = semantic_diff(old, new)
        assert diff.removed_nodes == ["b"]
        assert diff.added_nodes == []

    def test_modified_node_kind(self) -> None:
        old = ReasoningGraph(
            name="g",
            nodes=[_make_node("a", kind=NodeKind.DETERMINISTIC)],
            edges=[],
        )
        new = ReasoningGraph(
            name="g",
            nodes=[
                _make_node(
                    "a",
                    kind=NodeKind.AGENTIC,
                    output_schema={"type": "object"},
                    contracts=["x is nonempty"],
                )
            ],
            edges=[],
        )
        diff = semantic_diff(old, new)
        assert len(diff.modified_nodes) == 1
        assert diff.modified_nodes[0].node_id == "a"
        assert "kind" in diff.modified_nodes[0].changes

    def test_modified_node_contracts(self) -> None:
        old = ReasoningGraph(
            name="g",
            nodes=[_make_node("a", contracts=["x >= 0"])],
            edges=[],
        )
        new = ReasoningGraph(
            name="g",
            nodes=[_make_node("a", contracts=["x >= 0", "x <= 100"])],
            edges=[],
        )
        diff = semantic_diff(old, new)
        assert len(diff.modified_nodes) == 1
        assert "contracts" in diff.modified_nodes[0].changes
        old_val, new_val = diff.modified_nodes[0].changes["contracts"]
        assert old_val == ["x >= 0"]
        assert new_val == ["x >= 0", "x <= 100"]

    def test_modified_node_output_schema(self) -> None:
        old = ReasoningGraph(
            name="g",
            nodes=[_make_node("a", output_schema={"type": "object"})],
            edges=[],
        )
        new = ReasoningGraph(
            name="g",
            nodes=[
                _make_node(
                    "a",
                    output_schema={
                        "type": "object",
                        "properties": {"x": {"type": "number"}},
                    },
                )
            ],
            edges=[],
        )
        diff = semantic_diff(old, new)
        assert len(diff.modified_nodes) == 1
        assert "output_schema" in diff.modified_nodes[0].changes

    def test_modified_node_inputs_outputs(self) -> None:
        old = ReasoningGraph(
            name="g",
            nodes=[_make_node("a", inputs=["x"], outputs=["y"])],
            edges=[],
        )
        new = ReasoningGraph(
            name="g",
            nodes=[_make_node("a", inputs=["x", "z"], outputs=["y", "w"])],
            edges=[],
        )
        diff = semantic_diff(old, new)
        assert len(diff.modified_nodes) == 1
        assert "inputs" in diff.modified_nodes[0].changes
        assert "outputs" in diff.modified_nodes[0].changes

    def test_modified_node_function_ref(self) -> None:
        old = ReasoningGraph(
            name="g",
            nodes=[_make_node("a", function_ref="old_fn")],
            edges=[],
        )
        new = ReasoningGraph(
            name="g",
            nodes=[_make_node("a", function_ref="new_fn")],
            edges=[],
        )
        diff = semantic_diff(old, new)
        assert len(diff.modified_nodes) == 1
        assert "function_ref" in diff.modified_nodes[0].changes
        assert diff.modified_nodes[0].changes["function_ref"] == ("old_fn", "new_fn")

    def test_modified_node_prompt_template(self) -> None:
        old = ReasoningGraph(
            name="g",
            nodes=[_make_node("a", prompt_template="old prompt")],
            edges=[],
        )
        new = ReasoningGraph(
            name="g",
            nodes=[_make_node("a", prompt_template="new prompt")],
            edges=[],
        )
        diff = semantic_diff(old, new)
        assert len(diff.modified_nodes) == 1
        assert "prompt_template" in diff.modified_nodes[0].changes


class TestSemanticDiffEdges:
    def test_added_edge(self) -> None:
        old = ReasoningGraph(
            name="g",
            nodes=[_make_node("a"), _make_node("b")],
            edges=[],
        )
        new = ReasoningGraph(
            name="g",
            nodes=[_make_node("a"), _make_node("b")],
            edges=[ReasoningEdge(from_node="a", to_node="b")],
        )
        diff = semantic_diff(old, new)
        assert diff.added_edges == [("a", "b")]
        assert diff.removed_edges == []

    def test_removed_edge(self) -> None:
        old = ReasoningGraph(
            name="g",
            nodes=[_make_node("a"), _make_node("b")],
            edges=[ReasoningEdge(from_node="a", to_node="b")],
        )
        new = ReasoningGraph(
            name="g",
            nodes=[_make_node("a"), _make_node("b")],
            edges=[],
        )
        diff = semantic_diff(old, new)
        assert diff.removed_edges == [("a", "b")]
        assert diff.added_edges == []

    def test_changed_edges(self) -> None:
        old = ReasoningGraph(
            name="g",
            nodes=[_make_node("a"), _make_node("b"), _make_node("c")],
            edges=[ReasoningEdge(from_node="a", to_node="b")],
        )
        new = ReasoningGraph(
            name="g",
            nodes=[_make_node("a"), _make_node("b"), _make_node("c")],
            edges=[ReasoningEdge(from_node="a", to_node="c")],
        )
        diff = semantic_diff(old, new)
        assert diff.added_edges == [("a", "c")]
        assert diff.removed_edges == [("a", "b")]


class TestSemanticDiffMetadata:
    def test_name_change(self) -> None:
        old = ReasoningGraph(name="old_name", nodes=[_make_node("a")], edges=[])
        new = ReasoningGraph(name="new_name", nodes=[_make_node("a")], edges=[])
        diff = semantic_diff(old, new)
        assert diff.metadata_changes["name"] == ("old_name", "new_name")

    def test_description_change(self) -> None:
        old = ReasoningGraph(
            name="g",
            description="old desc",
            nodes=[_make_node("a")],
            edges=[],
        )
        new = ReasoningGraph(
            name="g",
            description="new desc",
            nodes=[_make_node("a")],
            edges=[],
        )
        diff = semantic_diff(old, new)
        assert diff.metadata_changes["description"] == ("old desc", "new desc")

    def test_version_change(self) -> None:
        old = ReasoningGraph(
            name="g", version="0.1", nodes=[_make_node("a")], edges=[]
        )
        new = ReasoningGraph(
            name="g", version="0.2", nodes=[_make_node("a")], edges=[]
        )
        diff = semantic_diff(old, new)
        assert diff.metadata_changes["version"] == ("0.1", "0.2")

    def test_metadata_dict_change(self) -> None:
        old = ReasoningGraph(
            name="g",
            nodes=[_make_node("a")],
            edges=[],
            metadata={"key": "old"},
        )
        new = ReasoningGraph(
            name="g",
            nodes=[_make_node("a")],
            edges=[],
            metadata={"key": "new"},
        )
        diff = semantic_diff(old, new)
        assert "metadata" in diff.metadata_changes
        assert diff.metadata_changes["metadata"] == ({"key": "old"}, {"key": "new"})


class TestSemanticDiffComplex:
    def test_multiple_changes_at_once(self) -> None:
        old = ReasoningGraph(
            name="g",
            version="0.1",
            nodes=[
                _make_node("a", inputs=["x"]),
                _make_node("b"),
            ],
            edges=[ReasoningEdge(from_node="a", to_node="b")],
        )
        new = ReasoningGraph(
            name="g",
            version="0.2",
            nodes=[
                _make_node("a", inputs=["x", "y"]),
                _make_node("c"),
            ],
            edges=[ReasoningEdge(from_node="a", to_node="c")],
        )
        diff = semantic_diff(old, new)
        assert diff.added_nodes == ["c"]
        assert diff.removed_nodes == ["b"]
        assert len(diff.modified_nodes) == 1
        assert diff.modified_nodes[0].node_id == "a"
        assert diff.added_edges == [("a", "c")]
        assert diff.removed_edges == [("a", "b")]
        assert diff.metadata_changes["version"] == ("0.1", "0.2")
