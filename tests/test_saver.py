"""Issue 13 — Tests for YAML round-trip (save_graph)."""
from __future__ import annotations

import copy
from pathlib import Path

from srg.models.edge import ReasoningEdge
from srg.models.node import NodeKind, ReasoningNode
from srg.models.graph import ReasoningGraph
from srg.runtime.loader import load_graph
from srg.runtime.saver import save_graph, save_graph_to_string

EXAMPLES = Path(__file__).resolve().parent.parent / "srg" / "examples"


class TestSaveGraphToString:
    def test_produces_valid_yaml(self) -> None:
        graph = load_graph(EXAMPLES / "repo_risk.yaml")
        yaml_str = save_graph_to_string(graph)
        assert "name:" in yaml_str
        assert "nodes:" in yaml_str
        assert "edges:" in yaml_str

    def test_omits_none_fields(self) -> None:
        graph = ReasoningGraph(
            name="minimal",
            nodes=[ReasoningNode(
                id="n1", kind=NodeKind.DETERMINISTIC,
                inputs=[], outputs=[], function_ref="fn",
            )],
            edges=[],
        )
        yaml_str = save_graph_to_string(graph)
        assert "prompt_template" not in yaml_str
        assert "output_schema" not in yaml_str
        assert "retry_policy" not in yaml_str

    def test_omits_empty_optional_lists(self) -> None:
        graph = ReasoningGraph(
            name="minimal",
            nodes=[ReasoningNode(
                id="n1", kind=NodeKind.DETERMINISTIC,
                inputs=[], outputs=[], function_ref="fn",
            )],
            edges=[],
        )
        yaml_str = save_graph_to_string(graph)
        assert "contracts:" not in yaml_str
        assert "effects:" not in yaml_str
        assert "metadata:" not in yaml_str

    def test_omits_default_edge_kind(self) -> None:
        graph = ReasoningGraph(
            name="test",
            nodes=[
                ReasoningNode(id="a", kind=NodeKind.DETERMINISTIC, inputs=[], outputs=[], function_ref="a_fn"),
                ReasoningNode(id="b", kind=NodeKind.DETERMINISTIC, inputs=[], outputs=[], function_ref="b_fn"),
            ],
            edges=[ReasoningEdge(from_node="a", to_node="b")],
        )
        yaml_str = save_graph_to_string(graph)
        assert "kind: data_flow" not in yaml_str


class TestRoundTrip:
    def test_repo_risk_round_trip(self, tmp_path) -> None:
        original = load_graph(EXAMPLES / "repo_risk.yaml")
        save_graph(original, tmp_path / "out.yaml")
        reloaded = load_graph(tmp_path / "out.yaml")

        assert reloaded.name == original.name
        assert len(reloaded.nodes) == len(original.nodes)
        assert len(reloaded.edges) == len(original.edges)
        for orig_node, reload_node in zip(original.nodes, reloaded.nodes):
            assert orig_node.id == reload_node.id
            assert orig_node.kind == reload_node.kind
            assert orig_node.inputs == reload_node.inputs
            assert orig_node.outputs == reload_node.outputs
            assert orig_node.contracts == reload_node.contracts

    def test_validator_scorer_round_trip(self, tmp_path) -> None:
        original = load_graph(EXAMPLES / "validator_scorer.yaml")
        save_graph(original, tmp_path / "out.yaml")
        reloaded = load_graph(tmp_path / "out.yaml")

        assert reloaded.name == original.name
        assert len(reloaded.nodes) == len(original.nodes)
        assert len(reloaded.edges) == len(original.edges)

    def test_subnet_scorer_round_trip(self, tmp_path) -> None:
        original = load_graph(EXAMPLES / "subnet_scorer.yaml")
        save_graph(original, tmp_path / "out.yaml")
        reloaded = load_graph(tmp_path / "out.yaml")

        assert reloaded.name == original.name
        assert len(reloaded.nodes) == len(original.nodes)
        assert len(reloaded.edges) == len(original.edges)

        # Check agentic nodes preserved
        for orig, new in zip(original.nodes, reloaded.nodes):
            assert orig.id == new.id
            assert orig.kind == new.kind
            assert orig.output_schema == new.output_schema
            assert orig.contracts == new.contracts
            if orig.retry_policy:
                assert new.retry_policy is not None
                assert orig.retry_policy.max_attempts == new.retry_policy.max_attempts

    def test_round_trip_after_add_node(self, tmp_path) -> None:
        graph = load_graph(EXAMPLES / "repo_risk.yaml")
        modified = copy.deepcopy(graph)
        modified.nodes.append(ReasoningNode(
            id="extra_step",
            kind=NodeKind.DETERMINISTIC,
            inputs=["report"],
            outputs=["summary"],
            function_ref="summarize",
        ))
        modified.edges.append(ReasoningEdge(from_node="format_report", to_node="extra_step"))

        save_graph(modified, tmp_path / "modified.yaml")
        reloaded = load_graph(tmp_path / "modified.yaml")

        assert len(reloaded.nodes) == 4
        assert len(reloaded.edges) == 3
        assert reloaded.nodes[-1].id == "extra_step"

    def test_round_trip_after_change_contract(self, tmp_path) -> None:
        graph = load_graph(EXAMPLES / "subnet_scorer.yaml")
        modified = copy.deepcopy(graph)

        team_node = next(n for n in modified.nodes if n.id == "score_team_quality")
        team_node.contracts.append("team_quality_score >= 10")

        save_graph(modified, tmp_path / "tightened.yaml")
        reloaded = load_graph(tmp_path / "tightened.yaml")

        reloaded_team = next(n for n in reloaded.nodes if n.id == "score_team_quality")
        assert "team_quality_score >= 10" in reloaded_team.contracts
