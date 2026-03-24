"""Issue 1 — End-to-end test for the subnet_scorer example.

Validates the 7-node fan-out/fan-in graph that models the
subnet-scorer-worker's 5-factor scoring algorithm.
"""
from __future__ import annotations

import copy
from pathlib import Path
from typing import Any

from srg.models.edge import ReasoningEdge
from srg.models.node import NodeKind, ReasoningNode
from srg.runtime.deterministic_registry import DeterministicRegistry
from srg.runtime.graph_runner import run_graph
from srg.runtime.loader import load_graph
from srg.utils.semantic_diff import semantic_diff

from srg.examples.subnet_scorer_functions import (
    aggregate_scores,
    extract_features,
    score_economic_sustainability,
    score_mechanism_design,
    score_network_effects,
)

# ---- Constants -----------------------------------------------------------

EXAMPLE_PATH = (
    Path(__file__).resolve().parent.parent / "srg" / "examples" / "subnet_scorer.yaml"
)

SAMPLE_SUBNET_DATA: dict[str, Any] = {
    "validator_stakes": [100, 200, 150, 300, 250],
    "participation_ratio": 0.85,
    "consensus_agreement": 0.92,
    "network_size": 500,
    "validator_count": 50,
    "coldkey_concentration": 0.15,
    "emission": 0.75,
    "github_stars": 120,
    "commit_count_90d": 340,
    "contributor_count": 12,
    "has_ci": True,
    "has_tests": True,
    "real_emission": 0.65,
    "distribution_fairness": 0.70,
    "price_stability": 0.80,
    "pool_liquidity": 50000.0,
    "subnet_description": "Decentralized AI inference network",
    "unique_mechanisms": ["proof-of-inference", "adaptive-difficulty"],
}


# ---- Mock LLM ------------------------------------------------------------


class MockSubnetScorerLLM:
    """Returns canned responses for the two agentic scoring nodes."""

    def generate(
        self,
        prompt: str,
        output_schema: dict[str, Any] | None = None,
        timeout_ms: int | None = None,
    ) -> dict[str, Any]:
        if "team" in prompt.lower():
            return {
                "team_quality_score": 72.0,
                "team_quality_reasoning": (
                    "Active development with 340 commits in 90 days, "
                    "12 contributors, CI and tests present."
                ),
            }
        return {
            "technical_innovation_score": 65.0,
            "technical_innovation_reasoning": (
                "Novel proof-of-inference mechanism with adaptive "
                "difficulty, moderate documentation."
            ),
        }


class MockContractViolatingLLM:
    """Returns an out-of-range score on first call, valid on second."""

    def __init__(self) -> None:
        self._call_count = 0

    def generate(
        self,
        prompt: str,
        output_schema: dict[str, Any] | None = None,
        timeout_ms: int | None = None,
    ) -> dict[str, Any]:
        self._call_count += 1
        if "team" in prompt.lower():
            if self._call_count <= 1:
                return {
                    "team_quality_score": 150.0,
                    "team_quality_reasoning": "Excellent team.",
                }
            return {
                "team_quality_score": 72.0,
                "team_quality_reasoning": "Active development.",
            }
        return {
            "technical_innovation_score": 65.0,
            "technical_innovation_reasoning": "Novel mechanisms.",
        }


class CaptureLLM:
    """Captures prompts sent to the LLM for inspection."""

    def __init__(self) -> None:
        self.prompts: list[str] = []

    def generate(
        self,
        prompt: str,
        output_schema: dict[str, Any] | None = None,
        timeout_ms: int | None = None,
    ) -> dict[str, Any]:
        self.prompts.append(prompt)
        if "team" in prompt.lower():
            return {
                "team_quality_score": 72.0,
                "team_quality_reasoning": "Good team.",
            }
        return {
            "technical_innovation_score": 65.0,
            "technical_innovation_reasoning": "Novel approach.",
        }


# ---- Helpers -------------------------------------------------------------


def _build_registry() -> DeterministicRegistry:
    """Register all 5 deterministic functions."""
    registry = DeterministicRegistry()
    registry.register("extract_features")(extract_features)
    registry.register("score_mechanism_design")(score_mechanism_design)
    registry.register("score_network_effects")(score_network_effects)
    registry.register("score_economic_sustainability")(score_economic_sustainability)
    registry.register("aggregate_scores")(aggregate_scores)
    return registry


# ---- Tests ---------------------------------------------------------------


class TestSubnetScorerEndToEnd:
    def test_load_graph(self) -> None:
        graph = load_graph(EXAMPLE_PATH)
        assert graph.name == "subnet_scorer"
        assert len(graph.nodes) == 7
        assert len(graph.edges) == 10

    def test_full_run(self) -> None:
        graph = load_graph(EXAMPLE_PATH)
        registry = _build_registry()
        llm = MockSubnetScorerLLM()

        result = run_graph(
            graph, registry, llm_provider=llm, inputs={"subnet_data": SAMPLE_SUBNET_DATA}
        )

        assert result.status == "success"
        assert 0 <= result.outputs["overall_score"] <= 100
        breakdown = result.outputs["score_breakdown"]
        assert len(breakdown) == 5
        for key in (
            "mechanism_design_score",
            "network_effects_score",
            "team_quality_score",
            "economic_sustainability_score",
            "technical_innovation_score",
        ):
            assert key in breakdown
            assert 0 <= breakdown[key] <= 100

    def test_evidence_for_all_nodes(self) -> None:
        graph = load_graph(EXAMPLE_PATH)
        registry = _build_registry()
        llm = MockSubnetScorerLLM()

        result = run_graph(
            graph, registry, llm_provider=llm, inputs={"subnet_data": SAMPLE_SUBNET_DATA}
        )

        assert result.status == "success"
        assert len(result.node_results) == 7
        for nr in result.node_results:
            assert len(nr.evidence) >= 1
            assert nr.duration_ms is not None

    def test_fan_out_fan_in_ordering(self) -> None:
        graph = load_graph(EXAMPLE_PATH)
        registry = _build_registry()
        llm = MockSubnetScorerLLM()

        result = run_graph(
            graph, registry, llm_provider=llm, inputs={"subnet_data": SAMPLE_SUBNET_DATA}
        )

        assert result.status == "success"
        node_ids = [nr.node_id for nr in result.node_results]
        assert node_ids[0] == "extract_features"
        assert node_ids[-1] == "aggregate_scores"
        middle = set(node_ids[1:-1])
        assert middle == {
            "score_mechanism_design",
            "score_network_effects",
            "score_team_quality",
            "score_economic_sustainability",
            "score_technical_innovation",
        }

    def test_agentic_contracts_enforced(self) -> None:
        graph = load_graph(EXAMPLE_PATH)
        registry = _build_registry()
        llm = MockContractViolatingLLM()

        result = run_graph(
            graph, registry, llm_provider=llm, inputs={"subnet_data": SAMPLE_SUBNET_DATA}
        )

        # Should still succeed because retry_policy allows a second attempt
        assert result.status == "success"

        # Find the team_quality node result
        team_nr = next(
            nr for nr in result.node_results if nr.node_id == "score_team_quality"
        )
        # Should have 2 evidence records: failed first attempt + successful retry
        assert len(team_nr.evidence) == 2
        assert team_nr.evidence[0].status == "failure"
        assert team_nr.evidence[1].status == "success"

    def test_semantic_diff_add_factor(self) -> None:
        original = load_graph(EXAMPLE_PATH)
        modified = copy.deepcopy(original)

        # Add a 6th scoring node
        new_node = ReasoningNode(
            id="score_community_engagement",
            kind=NodeKind.DETERMINISTIC,
            inputs=["network_features"],
            outputs=["community_engagement_score"],
            function_ref="score_community_engagement",
        )
        modified.nodes.append(new_node)
        modified.edges.append(
            ReasoningEdge(
                from_node="extract_features",
                to_node="score_community_engagement",
            )
        )
        modified.edges.append(
            ReasoningEdge(
                from_node="score_community_engagement",
                to_node="aggregate_scores",
            )
        )

        diff = semantic_diff(original, modified)
        assert "score_community_engagement" in diff.added_nodes
        assert ("extract_features", "score_community_engagement") in diff.added_edges
        assert ("score_community_engagement", "aggregate_scores") in diff.added_edges

    def test_semantic_diff_change_weights(self) -> None:
        original = load_graph(EXAMPLE_PATH)
        modified = copy.deepcopy(original)

        # Change aggregate_scores metadata weights
        agg_node = next(n for n in modified.nodes if n.id == "aggregate_scores")
        agg_node.metadata = {
            "weights": {
                "mechanism_design": 0.25,
                "network_effects": 0.25,
                "team_quality": 0.15,
                "economic_sustainability": 0.20,
                "technical_innovation": 0.15,
            }
        }

        diff = semantic_diff(original, modified)
        modified_ids = [nd.node_id for nd in diff.modified_nodes]
        assert "aggregate_scores" in modified_ids
        agg_diff = next(
            nd for nd in diff.modified_nodes if nd.node_id == "aggregate_scores"
        )
        assert "metadata" in agg_diff.changes

    def test_data_flows_through_state(self) -> None:
        graph = load_graph(EXAMPLE_PATH)
        registry = _build_registry()
        llm = CaptureLLM()

        result = run_graph(
            graph, registry, llm_provider=llm, inputs={"subnet_data": SAMPLE_SUBNET_DATA}
        )

        assert result.status == "success"
        assert len(llm.prompts) == 2

        # The team quality prompt should contain extracted team features
        team_prompt = next(p for p in llm.prompts if "team" in p.lower())
        assert "github_stars" in team_prompt
        assert "120" in team_prompt

        # The innovation prompt should contain extracted innovation features
        innovation_prompt = next(p for p in llm.prompts if "innovation" in p.lower())
        assert "proof-of-inference" in innovation_prompt
