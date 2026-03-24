"""Issue #2 — Tests for the token efficiency benchmark.

Ensures the benchmark inputs exist and the Python equivalent produces
identical scoring results to the SRG graph.
"""
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

import sys

BENCH_DIR = Path(__file__).resolve().parent.parent / "benchmarks"
sys.path.insert(0, str(BENCH_DIR))
import python_equivalent as py_equiv  # noqa: E402


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


class MockLLM:
    def generate(self, prompt: str, output_schema: dict | None = None, timeout_ms: int | None = None) -> dict:
        if "team" in prompt.lower():
            return {"team_quality_score": 72.0, "team_quality_reasoning": "Good team."}
        return {"technical_innovation_score": 65.0, "technical_innovation_reasoning": "Novel."}


def mock_llm_call(prompt: str) -> dict[str, Any]:
    if "team" in prompt.lower():
        return {"team_quality_score": 72.0, "team_quality_reasoning": "Good team."}
    return {"technical_innovation_score": 65.0, "technical_innovation_reasoning": "Novel."}


class TestBenchmarkFiles:
    def test_srg_yaml_exists(self) -> None:
        assert (BENCH_DIR.parent / "srg" / "examples" / "subnet_scorer.yaml").exists()

    def test_srg_functions_exist(self) -> None:
        assert (BENCH_DIR.parent / "srg" / "examples" / "subnet_scorer_functions.py").exists()

    def test_python_equivalent_exists(self) -> None:
        assert (BENCH_DIR / "python_equivalent.py").exists()

    def test_benchmark_script_exists(self) -> None:
        assert (BENCH_DIR / "token_benchmark.py").exists()


class TestDeterministicParity:
    """Verify the Python equivalent produces identical deterministic scores."""

    def test_mechanism_design_parity(self) -> None:
        # SRG path: extract features then score
        state = {"subnet_data": SAMPLE_SUBNET_DATA}
        features = extract_features(state)
        state.update(features)
        srg_result = score_mechanism_design(state)

        # Python path
        py_score = py_equiv.score_mechanism_design(SAMPLE_SUBNET_DATA)

        assert srg_result["mechanism_design_score"] == py_score

    def test_network_effects_parity(self) -> None:
        state = {"subnet_data": SAMPLE_SUBNET_DATA}
        features = extract_features(state)
        state.update(features)
        srg_result = score_network_effects(state)

        py_score = py_equiv.score_network_effects(SAMPLE_SUBNET_DATA)

        assert srg_result["network_effects_score"] == py_score

    def test_economic_sustainability_parity(self) -> None:
        state = {"subnet_data": SAMPLE_SUBNET_DATA}
        features = extract_features(state)
        state.update(features)
        srg_result = score_economic_sustainability(state)

        py_score = py_equiv.score_economic_sustainability(SAMPLE_SUBNET_DATA)

        assert srg_result["economic_sustainability_score"] == py_score

    def test_overall_score_parity(self) -> None:
        """Full pipeline: SRG graph vs Python equivalent produce same overall score."""
        # SRG path
        graph = load_graph(BENCH_DIR.parent / "srg" / "examples" / "subnet_scorer.yaml")
        registry = DeterministicRegistry()
        registry.register("extract_features")(extract_features)
        registry.register("score_mechanism_design")(score_mechanism_design)
        registry.register("score_network_effects")(score_network_effects)
        registry.register("score_economic_sustainability")(score_economic_sustainability)
        registry.register("aggregate_scores")(aggregate_scores)

        srg_result = run_graph(
            graph, registry, llm_provider=MockLLM(),
            inputs={"subnet_data": SAMPLE_SUBNET_DATA},
        )

        # Python path
        py_result = py_equiv.score_subnet(SAMPLE_SUBNET_DATA, mock_llm_call)

        assert srg_result.status == "success"
        assert srg_result.outputs["overall_score"] == py_result.overall_score
        assert srg_result.outputs["score_breakdown"] == py_result.score_breakdown
