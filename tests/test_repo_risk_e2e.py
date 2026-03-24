"""Issue 13 — End-to-end test for the repo_risk example."""
from __future__ import annotations

from pathlib import Path
from typing import Any

from srg.runtime.deterministic_registry import DeterministicRegistry
from srg.runtime.graph_runner import run_graph
from srg.runtime.loader import load_graph


# ---- Mock LLM ---------------------------------------------------------


class MockRiskLLM:
    """Returns a fixed risk assessment matching the repo_risk schema."""

    def generate(
        self,
        prompt: str,
        output_schema: dict[str, Any] | None = None,
        timeout_ms: int | None = None,
    ) -> dict[str, Any]:
        return {
            "risk_level": "medium",
            "risk_factors": [
                "No test coverage for 30% of modules",
                "3 dependencies with known CVEs",
            ],
        }


# ---- Tests -------------------------------------------------------------

EXAMPLE_PATH = Path(__file__).resolve().parent.parent / "srg" / "examples" / "repo_risk.yaml"


class TestRepoRiskEndToEnd:
    def test_load_graph(self) -> None:
        graph = load_graph(EXAMPLE_PATH)
        assert graph.name == "repo_risk"
        assert len(graph.nodes) == 3
        assert len(graph.edges) == 2

    def test_full_run(self) -> None:
        graph = load_graph(EXAMPLE_PATH)

        registry = DeterministicRegistry()

        @registry.register("gather_metrics")
        def gather_metrics(state: dict[str, Any]) -> dict[str, Any]:
            return {
                "metrics": {
                    "files": 120,
                    "test_coverage": 0.70,
                    "open_issues": 15,
                    "dependencies_with_cves": 3,
                }
            }

        @registry.register("format_report")
        def format_report(state: dict[str, Any]) -> dict[str, Any]:
            risk_level = state["risk_level"]
            risk_factors = state["risk_factors"]
            lines = [f"Risk Level: {risk_level}", "Risk Factors:"]
            for factor in risk_factors:
                lines.append(f"  - {factor}")
            return {"report": "\n".join(lines)}

        llm = MockRiskLLM()
        result = run_graph(
            graph,
            registry,
            llm_provider=llm,
            inputs={"repo_path": "/tmp/fake_repo"},
        )

        assert result.status == "success"
        assert result.outputs["risk_level"] == "medium"
        assert len(result.outputs["risk_factors"]) == 2
        assert "Risk Level: medium" in result.outputs["report"]

    def test_evidence_emitted_for_all_nodes(self) -> None:
        graph = load_graph(EXAMPLE_PATH)

        registry = DeterministicRegistry()

        @registry.register("gather_metrics")
        def gather_metrics(state: dict[str, Any]) -> dict[str, Any]:
            return {"metrics": {"files": 10}}

        @registry.register("format_report")
        def format_report(state: dict[str, Any]) -> dict[str, Any]:
            return {"report": f"Risk: {state['risk_level']}"}

        llm = MockRiskLLM()
        result = run_graph(
            graph, registry, llm_provider=llm, inputs={"repo_path": "/tmp/r"}
        )

        assert result.status == "success"
        assert len(result.node_results) == 3

        # Each node should have at least one evidence record
        for nr in result.node_results:
            assert len(nr.evidence) >= 1
            assert nr.duration_ms is not None

    def test_three_node_pipeline_ordering(self) -> None:
        graph = load_graph(EXAMPLE_PATH)

        registry = DeterministicRegistry()

        @registry.register("gather_metrics")
        def gather_metrics(state: dict[str, Any]) -> dict[str, Any]:
            return {"metrics": {"x": 1}}

        @registry.register("format_report")
        def format_report(state: dict[str, Any]) -> dict[str, Any]:
            return {"report": "done"}

        llm = MockRiskLLM()
        result = run_graph(
            graph, registry, llm_provider=llm, inputs={"repo_path": "/tmp/r"}
        )

        assert result.status == "success"
        node_ids = [nr.node_id for nr in result.node_results]
        assert node_ids == ["gather_metrics", "assess_risk", "format_report"]
