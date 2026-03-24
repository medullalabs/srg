"""Tests for Issue 10 — Graph runner."""
from __future__ import annotations

from typing import Any


from srg.models.edge import ReasoningEdge
from srg.models.graph import ReasoningGraph
from srg.models.node import NodeKind, ReasoningNode
from srg.runtime.deterministic_registry import DeterministicRegistry
from srg.runtime.graph_runner import run_graph


# ---- Mock LLM ---------------------------------------------------------


class MockLLM:
    """Simple mock LLM that returns a fixed response."""

    def __init__(self, response: dict[str, Any]) -> None:
        self._response = response

    def generate(
        self,
        prompt: str,
        output_schema: dict[str, Any] | None = None,
        timeout_ms: int | None = None,
    ) -> dict[str, Any]:
        return self._response


class SequenceLLM:
    """Mock LLM that returns responses in sequence."""

    def __init__(self, responses: list[dict[str, Any]]) -> None:
        self._responses = list(responses)
        self._idx = 0

    def generate(
        self,
        prompt: str,
        output_schema: dict[str, Any] | None = None,
        timeout_ms: int | None = None,
    ) -> dict[str, Any]:
        resp = self._responses[min(self._idx, len(self._responses) - 1)]
        self._idx += 1
        return resp


# ---- Helpers -----------------------------------------------------------


def _make_registry() -> DeterministicRegistry:
    reg = DeterministicRegistry()

    @reg.register("validate_input_fn")
    def validate_input(state: dict[str, Any]) -> dict[str, Any]:
        return {"validated_data": state.get("raw_data", "")}

    @reg.register("double_fn")
    def double(state: dict[str, Any]) -> dict[str, Any]:
        return {"result": state["x"] * 2}

    @reg.register("add_one_fn")
    def add_one(state: dict[str, Any]) -> dict[str, Any]:
        return {"y": state["x"] + 1}

    @reg.register("square_fn")
    def square(state: dict[str, Any]) -> dict[str, Any]:
        return {"z": state["y"] ** 2}

    return reg


# ---- Tests: deterministic only ----------------------------------------


class TestDeterministicGraph:
    def test_single_node(self) -> None:
        graph = ReasoningGraph(
            name="single",
            nodes=[
                ReasoningNode(
                    id="double",
                    kind=NodeKind.DETERMINISTIC,
                    inputs=["x"],
                    outputs=["result"],
                    function_ref="double_fn",
                ),
            ],
            edges=[],
        )
        reg = _make_registry()
        result = run_graph(graph, reg, inputs={"x": 5})
        assert result.status == "success"
        assert result.outputs["result"] == 10
        assert len(result.node_results) == 1

    def test_linear_pipeline(self) -> None:
        graph = ReasoningGraph(
            name="pipeline",
            nodes=[
                ReasoningNode(
                    id="add",
                    kind=NodeKind.DETERMINISTIC,
                    inputs=["x"],
                    outputs=["y"],
                    function_ref="add_one_fn",
                ),
                ReasoningNode(
                    id="sq",
                    kind=NodeKind.DETERMINISTIC,
                    inputs=["y"],
                    outputs=["z"],
                    function_ref="square_fn",
                ),
            ],
            edges=[ReasoningEdge(from_node="add", to_node="sq")],
        )
        reg = _make_registry()
        result = run_graph(graph, reg, inputs={"x": 3})
        assert result.status == "success"
        assert result.outputs["y"] == 4
        assert result.outputs["z"] == 16

    def test_missing_function_ref(self) -> None:
        graph = ReasoningGraph(
            name="no_ref",
            nodes=[
                ReasoningNode(
                    id="n",
                    kind=NodeKind.DETERMINISTIC,
                    inputs=["x"],
                    outputs=["y"],
                    # no function_ref
                ),
            ],
            edges=[],
        )
        reg = _make_registry()
        result = run_graph(graph, reg, inputs={"x": 1})
        assert result.status == "failure"
        assert "missing function_ref" in (result.error or "")

    def test_unregistered_function(self) -> None:
        graph = ReasoningGraph(
            name="unregistered",
            nodes=[
                ReasoningNode(
                    id="n",
                    kind=NodeKind.DETERMINISTIC,
                    inputs=["x"],
                    outputs=["y"],
                    function_ref="nonexistent_fn",
                ),
            ],
            edges=[],
        )
        reg = _make_registry()
        result = run_graph(graph, reg, inputs={"x": 1})
        assert result.status == "failure"
        assert "not found in registry" in (result.error or "")

    def test_function_raises_exception(self) -> None:
        reg = DeterministicRegistry()

        @reg.register("bad_fn")
        def bad_fn(state: dict[str, Any]) -> dict[str, Any]:
            raise ValueError("kaboom")

        graph = ReasoningGraph(
            name="exploding",
            nodes=[
                ReasoningNode(
                    id="n",
                    kind=NodeKind.DETERMINISTIC,
                    inputs=[],
                    outputs=["y"],
                    function_ref="bad_fn",
                ),
            ],
            edges=[],
        )
        result = run_graph(graph, reg)
        assert result.status == "failure"
        assert "kaboom" in (result.error or "")


class TestInvalidGraph:
    def test_invalid_graph_returns_failure(self) -> None:
        graph = ReasoningGraph(
            name="dup",
            nodes=[
                ReasoningNode(
                    id="a",
                    kind=NodeKind.DETERMINISTIC,
                    inputs=[],
                    outputs=[],
                ),
                ReasoningNode(
                    id="a",  # duplicate
                    kind=NodeKind.DETERMINISTIC,
                    inputs=[],
                    outputs=[],
                ),
            ],
            edges=[],
        )
        reg = _make_registry()
        result = run_graph(graph, reg)
        assert result.status == "failure"
        assert "validation failed" in (result.error or "").lower()


# ---- Tests: mixed graph with mock LLM ---------------------------------


class TestMixedGraph:
    def test_deterministic_then_agentic(self) -> None:
        graph = ReasoningGraph(
            name="mixed",
            nodes=[
                ReasoningNode(
                    id="validate",
                    kind=NodeKind.DETERMINISTIC,
                    inputs=["raw_data"],
                    outputs=["validated_data"],
                    function_ref="validate_input_fn",
                ),
                ReasoningNode(
                    id="score",
                    kind=NodeKind.AGENTIC,
                    inputs=["validated_data"],
                    outputs=["score", "explanation"],
                    prompt_template="Score: {validated_data}",
                    output_schema={
                        "type": "object",
                        "properties": {
                            "score": {"type": "number"},
                            "explanation": {"type": "string"},
                        },
                        "required": ["score", "explanation"],
                    },
                    contracts=[
                        "score >= 0",
                        "score <= 100",
                        "explanation is nonempty",
                    ],
                ),
            ],
            edges=[ReasoningEdge(from_node="validate", to_node="score")],
        )
        reg = _make_registry()
        llm = MockLLM({"score": 85, "explanation": "Looks good"})
        result = run_graph(graph, reg, llm_provider=llm, inputs={"raw_data": "test"})
        assert result.status == "success"
        assert result.outputs["score"] == 85
        assert result.outputs["explanation"] == "Looks good"
        assert len(result.node_results) == 2

    def test_agentic_without_provider_fails(self) -> None:
        graph = ReasoningGraph(
            name="no_llm",
            nodes=[
                ReasoningNode(
                    id="agent",
                    kind=NodeKind.AGENTIC,
                    inputs=[],
                    outputs=["out"],
                    output_schema={"type": "object"},
                    contracts=["out is nonempty"],
                ),
            ],
            edges=[],
        )
        reg = _make_registry()
        result = run_graph(graph, reg)
        assert result.status == "failure"
        assert "LLM provider" in (result.error or "")


class TestFailurePropagation:
    def test_first_node_failure_stops_execution(self) -> None:
        reg = DeterministicRegistry()

        @reg.register("fail_fn")
        def fail_fn(state: dict[str, Any]) -> dict[str, Any]:
            raise RuntimeError("fail")

        @reg.register("ok_fn")
        def ok_fn(state: dict[str, Any]) -> dict[str, Any]:
            return {"y": 1}

        graph = ReasoningGraph(
            name="fail_first",
            nodes=[
                ReasoningNode(
                    id="a",
                    kind=NodeKind.DETERMINISTIC,
                    inputs=[],
                    outputs=["x"],
                    function_ref="fail_fn",
                ),
                ReasoningNode(
                    id="b",
                    kind=NodeKind.DETERMINISTIC,
                    inputs=["x"],
                    outputs=["y"],
                    function_ref="ok_fn",
                ),
            ],
            edges=[ReasoningEdge(from_node="a", to_node="b")],
        )
        result = run_graph(graph, reg)
        assert result.status == "failure"
        # Only node "a" should have executed
        assert len(result.node_results) == 1
        assert result.node_results[0].node_id == "a"


class TestGraphRunnerEvidence:
    def test_deterministic_node_emits_evidence(self) -> None:
        graph = ReasoningGraph(
            name="ev_test",
            nodes=[
                ReasoningNode(
                    id="n",
                    kind=NodeKind.DETERMINISTIC,
                    inputs=["x"],
                    outputs=["result"],
                    function_ref="double_fn",
                ),
            ],
            edges=[],
        )
        reg = _make_registry()
        result = run_graph(graph, reg, inputs={"x": 5})
        assert len(result.node_results[0].evidence) == 1
        ev = result.node_results[0].evidence[0]
        assert ev.graph_name == "ev_test"
        assert ev.node_id == "n"
        assert ev.attempt == 1

    def test_agentic_node_emits_evidence(self) -> None:
        graph = ReasoningGraph(
            name="ev_agentic",
            nodes=[
                ReasoningNode(
                    id="agent",
                    kind=NodeKind.AGENTIC,
                    inputs=[],
                    outputs=["val"],
                    prompt_template="Give a value",
                    output_schema={
                        "type": "object",
                        "properties": {"val": {"type": "string"}},
                        "required": ["val"],
                    },
                    contracts=["val is nonempty"],
                ),
            ],
            edges=[],
        )
        reg = DeterministicRegistry()
        llm = MockLLM({"val": "hello"})
        result = run_graph(graph, reg, llm_provider=llm)
        assert result.status == "success"
        assert len(result.node_results[0].evidence) >= 1
        ev = result.node_results[0].evidence[0]
        assert ev.graph_name == "ev_agentic"

    def test_node_results_have_duration(self) -> None:
        graph = ReasoningGraph(
            name="dur",
            nodes=[
                ReasoningNode(
                    id="n",
                    kind=NodeKind.DETERMINISTIC,
                    inputs=[],
                    outputs=["x"],
                    function_ref="double_fn",
                ),
            ],
            edges=[],
        )
        reg = _make_registry()
        result = run_graph(graph, reg, inputs={"x": 1})
        assert result.node_results[0].duration_ms is not None
        assert result.node_results[0].duration_ms >= 0
