"""Issue 5 — Tests for graph-level evidence summary in GraphExecutionResult."""
from __future__ import annotations

from pathlib import Path
from typing import Any

from srg.runtime.deterministic_registry import DeterministicRegistry
from srg.runtime.graph_runner import run_graph
from srg.runtime.loader import load_graph

from srg.examples.subnet_scorer_functions import (
    aggregate_scores,
    extract_features,
    score_economic_sustainability,
    score_mechanism_design,
    score_network_effects,
)

EXAMPLE_PATH = Path(__file__).resolve().parent.parent / "srg" / "examples"

SAMPLE_DATA: dict[str, Any] = {
    "subnet_data": {
        "validator_stakes": [100, 200, 150],
        "participation_ratio": 0.80,
        "consensus_agreement": 0.90,
        "network_size": 100,
        "validator_count": 20,
        "coldkey_concentration": 0.10,
        "emission": 0.50,
        "github_stars": 50,
        "commit_count_90d": 100,
        "contributor_count": 5,
        "has_ci": True,
        "has_tests": True,
        "real_emission": 0.50,
        "distribution_fairness": 0.60,
        "price_stability": 0.70,
        "pool_liquidity": 10000.0,
        "subnet_description": "Test subnet",
        "unique_mechanisms": ["test-mechanism"],
    }
}


class MockLLM:
    def generate(self, prompt: str, output_schema: dict | None = None, timeout_ms: int | None = None) -> dict:
        if "team" in prompt.lower():
            return {"team_quality_score": 60.0, "team_quality_reasoning": "OK team."}
        return {"technical_innovation_score": 50.0, "technical_innovation_reasoning": "Average."}


def _build_registry() -> DeterministicRegistry:
    reg = DeterministicRegistry()
    reg.register("extract_features")(extract_features)
    reg.register("score_mechanism_design")(score_mechanism_design)
    reg.register("score_network_effects")(score_network_effects)
    reg.register("score_economic_sustainability")(score_economic_sustainability)
    reg.register("aggregate_scores")(aggregate_scores)
    return reg


class TestEvidenceSummary:
    def test_summary_present_on_success(self) -> None:
        graph = load_graph(EXAMPLE_PATH / "subnet_scorer.yaml")
        result = run_graph(graph, _build_registry(), llm_provider=MockLLM(), inputs=SAMPLE_DATA)

        assert result.status == "success"
        assert result.evidence_summary is not None

    def test_summary_fields(self) -> None:
        graph = load_graph(EXAMPLE_PATH / "subnet_scorer.yaml")
        result = run_graph(graph, _build_registry(), llm_provider=MockLLM(), inputs=SAMPLE_DATA)

        s = result.evidence_summary
        assert s is not None
        assert s["total_nodes"] == 7
        assert s["passed"] == 7
        assert s["failed"] == 0
        assert s["total_attempts"] >= 7
        assert s["total_duration_ms"] >= 0

    def test_summary_on_failure(self) -> None:
        graph = load_graph(EXAMPLE_PATH / "subnet_scorer.yaml")
        # No LLM provider → agentic nodes will fail
        result = run_graph(graph, _build_registry(), inputs=SAMPLE_DATA)

        assert result.status == "failure"
        assert result.evidence_summary is not None
        assert result.evidence_summary["failed"] >= 1

    def test_summary_simple_graph(self) -> None:
        graph = load_graph(EXAMPLE_PATH / "repo_risk.yaml")
        reg = DeterministicRegistry()

        @reg.register("gather_metrics")
        def gather_metrics(state: dict) -> dict:
            return {"metrics": {"files": 10}}

        @reg.register("format_report")
        def format_report(state: dict) -> dict:
            return {"report": f"Risk: {state['risk_level']}"}

        class MockRiskLLM:
            def generate(self, prompt: str, output_schema: dict | None = None, timeout_ms: int | None = None) -> dict:
                return {"risk_level": "low", "risk_factors": ["none"]}

        result = run_graph(graph, reg, llm_provider=MockRiskLLM(), inputs={"repo_path": "/tmp"})

        assert result.status == "success"
        s = result.evidence_summary
        assert s is not None
        assert s["total_nodes"] == 3
        assert s["passed"] == 3
        assert s["failed"] == 0

    def test_no_evidence_records_in_summary(self) -> None:
        """evidence_records should NOT be in the summary (they're in node_results)."""
        graph = load_graph(EXAMPLE_PATH / "subnet_scorer.yaml")
        result = run_graph(graph, _build_registry(), llm_provider=MockLLM(), inputs=SAMPLE_DATA)

        assert "evidence_records" not in result.evidence_summary
