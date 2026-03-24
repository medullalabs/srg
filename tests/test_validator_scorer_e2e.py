"""Issue 12 — End-to-end test for the validator_scorer example."""
from __future__ import annotations

from pathlib import Path
from typing import Any

from srg.runtime.deterministic_registry import DeterministicRegistry
from srg.runtime.graph_runner import run_graph
from srg.runtime.loader import load_graph


# ---- Mock LLM ---------------------------------------------------------


class MockScorerLLM:
    """Returns a fixed score/explanation matching the validator_scorer schema."""

    def generate(
        self,
        prompt: str,
        output_schema: dict[str, Any] | None = None,
        timeout_ms: int | None = None,
    ) -> dict[str, Any]:
        return {"score": 75.0, "explanation": "Data quality is acceptable."}


# ---- Tests -------------------------------------------------------------

EXAMPLE_PATH = Path(__file__).resolve().parent.parent / "srg" / "examples" / "validator_scorer.yaml"


class TestValidatorScorerEndToEnd:
    def test_load_graph(self) -> None:
        graph = load_graph(EXAMPLE_PATH)
        assert graph.name == "validator_scorer"
        assert len(graph.nodes) == 2
        assert len(graph.edges) == 1

    def test_full_run(self) -> None:
        graph = load_graph(EXAMPLE_PATH)

        registry = DeterministicRegistry()

        @registry.register("validate_input_fn")
        def validate_input_fn(state: dict[str, Any]) -> dict[str, Any]:
            raw = state.get("raw_data", "")
            return {"validated_data": str(raw).strip()}

        llm = MockScorerLLM()
        result = run_graph(
            graph,
            registry,
            llm_provider=llm,
            inputs={"raw_data": "  sample input data  "},
        )

        assert result.status == "success"
        assert result.outputs["score"] == 75.0
        assert result.outputs["explanation"] == "Data quality is acceptable."

    def test_evidence_emitted(self) -> None:
        graph = load_graph(EXAMPLE_PATH)

        registry = DeterministicRegistry()

        @registry.register("validate_input_fn")
        def validate_input_fn(state: dict[str, Any]) -> dict[str, Any]:
            return {"validated_data": state.get("raw_data", "")}

        llm = MockScorerLLM()
        result = run_graph(
            graph,
            registry,
            llm_provider=llm,
            inputs={"raw_data": "test"},
        )

        assert result.status == "success"
        assert len(result.node_results) == 2

        # Deterministic node should have evidence
        det_result = result.node_results[0]
        assert det_result.node_id == "validate_input"
        assert len(det_result.evidence) == 1
        assert det_result.evidence[0].status == "success"

        # Agentic node should have evidence
        agent_result = result.node_results[1]
        assert agent_result.node_id == "score_data"
        assert len(agent_result.evidence) >= 1
        assert agent_result.evidence[0].status == "success"
        assert agent_result.evidence[0].graph_name == "validator_scorer"

    def test_node_results_have_duration(self) -> None:
        graph = load_graph(EXAMPLE_PATH)

        registry = DeterministicRegistry()

        @registry.register("validate_input_fn")
        def validate_input_fn(state: dict[str, Any]) -> dict[str, Any]:
            return {"validated_data": state.get("raw_data", "")}

        llm = MockScorerLLM()
        result = run_graph(
            graph, registry, llm_provider=llm, inputs={"raw_data": "x"}
        )

        for nr in result.node_results:
            assert nr.duration_ms is not None
            assert nr.duration_ms >= 0

    def test_outputs_flow_through_state(self) -> None:
        """validated_data from node 1 should be available in node 2's prompt."""
        graph = load_graph(EXAMPLE_PATH)

        registry = DeterministicRegistry()

        @registry.register("validate_input_fn")
        def validate_input_fn(state: dict[str, Any]) -> dict[str, Any]:
            return {"validated_data": "CLEANED:" + str(state.get("raw_data", ""))}

        prompts_seen: list[str] = []

        class CaptureLLM:
            def generate(
                self,
                prompt: str,
                output_schema: dict[str, Any] | None = None,
                timeout_ms: int | None = None,
            ) -> dict[str, Any]:
                prompts_seen.append(prompt)
                return {"score": 90.0, "explanation": "Excellent"}

        result = run_graph(
            graph,
            registry,
            llm_provider=CaptureLLM(),
            inputs={"raw_data": "hello"},
        )

        assert result.status == "success"
        assert len(prompts_seen) == 1
        assert "CLEANED:hello" in prompts_seen[0]
