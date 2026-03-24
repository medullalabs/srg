"""Issue 15 — Comprehensive failure mode tests."""
from __future__ import annotations

from typing import Any


from srg.models.edge import ReasoningEdge
from srg.models.graph import ReasoningGraph
from srg.models.node import NodeKind, ReasoningNode, RetryPolicy
from srg.runtime.deterministic_registry import DeterministicRegistry
from srg.runtime.graph_runner import run_graph
from srg.runtime.graph_validator import validate_graph


# ---- Mock LLM providers -----------------------------------------------


class SchemaFailLLM:
    """Always returns output that fails schema validation."""

    def generate(
        self,
        prompt: str,
        output_schema: dict[str, Any] | None = None,
        timeout_ms: int | None = None,
    ) -> dict[str, Any]:
        return {"score": "not_a_number"}  # always wrong type


class ContractFailLLM:
    """Returns output that passes schema but fails contracts."""

    def generate(
        self,
        prompt: str,
        output_schema: dict[str, Any] | None = None,
        timeout_ms: int | None = None,
    ) -> dict[str, Any]:
        return {"score": -999}  # valid number, but fails >= 0 contract


# ---- Graph runner failure mode tests -----------------------------------


class TestAgenticSchemaExhaustsRetries:
    def test_schema_failure_exhausts_retries_graph_fails(self) -> None:
        graph = ReasoningGraph(
            name="schema_fail",
            nodes=[
                ReasoningNode(
                    id="agent",
                    kind=NodeKind.AGENTIC,
                    inputs=[],
                    outputs=["score"],
                    prompt_template="Give a score",
                    output_schema={
                        "type": "object",
                        "properties": {"score": {"type": "number"}},
                        "required": ["score"],
                    },
                    contracts=["score >= 0"],
                    retry_policy=RetryPolicy(
                        max_attempts=2, retry_on=["schema_failure"]
                    ),
                ),
            ],
            edges=[],
        )
        reg = DeterministicRegistry()
        result = run_graph(graph, reg, llm_provider=SchemaFailLLM())

        assert result.status == "failure"
        assert "agent" in (result.error or "")
        assert len(result.node_results) == 1
        assert result.node_results[0].status == "failure"

    def test_evidence_emitted_on_schema_exhaustion(self) -> None:
        graph = ReasoningGraph(
            name="schema_ev",
            nodes=[
                ReasoningNode(
                    id="agent",
                    kind=NodeKind.AGENTIC,
                    inputs=[],
                    outputs=["score"],
                    prompt_template="Give a score",
                    output_schema={
                        "type": "object",
                        "properties": {"score": {"type": "number"}},
                        "required": ["score"],
                    },
                    contracts=["score >= 0"],
                    retry_policy=RetryPolicy(
                        max_attempts=3, retry_on=["schema_failure"]
                    ),
                ),
            ],
            edges=[],
        )
        reg = DeterministicRegistry()
        result = run_graph(graph, reg, llm_provider=SchemaFailLLM())

        assert result.status == "failure"
        evidence = result.node_results[0].evidence
        assert len(evidence) == 3
        for ev in evidence:
            assert ev.status == "failure"
            assert ev.validation_outcome == "schema_failure"


class TestAgenticContractExhaustsRetries:
    def test_contract_failure_exhausts_retries_graph_fails(self) -> None:
        graph = ReasoningGraph(
            name="contract_fail",
            nodes=[
                ReasoningNode(
                    id="agent",
                    kind=NodeKind.AGENTIC,
                    inputs=[],
                    outputs=["score"],
                    prompt_template="Give a score",
                    output_schema={
                        "type": "object",
                        "properties": {"score": {"type": "number"}},
                        "required": ["score"],
                    },
                    contracts=["score >= 0"],
                    retry_policy=RetryPolicy(
                        max_attempts=2, retry_on=["contract_failure"]
                    ),
                ),
            ],
            edges=[],
        )
        reg = DeterministicRegistry()
        result = run_graph(graph, reg, llm_provider=ContractFailLLM())

        assert result.status == "failure"
        assert len(result.node_results) == 1
        assert result.node_results[0].status == "failure"

    def test_evidence_emitted_on_contract_exhaustion(self) -> None:
        graph = ReasoningGraph(
            name="contract_ev",
            nodes=[
                ReasoningNode(
                    id="agent",
                    kind=NodeKind.AGENTIC,
                    inputs=[],
                    outputs=["score"],
                    prompt_template="Give a score",
                    output_schema={
                        "type": "object",
                        "properties": {"score": {"type": "number"}},
                    },
                    contracts=["score >= 0"],
                    retry_policy=RetryPolicy(
                        max_attempts=2, retry_on=["contract_failure"]
                    ),
                ),
            ],
            edges=[],
        )
        reg = DeterministicRegistry()
        result = run_graph(graph, reg, llm_provider=ContractFailLLM())

        assert result.status == "failure"
        evidence = result.node_results[0].evidence
        assert len(evidence) == 2
        for ev in evidence:
            assert ev.status == "failure"
            assert ev.validation_outcome == "contract_failure"


class TestMissingFunctionRef:
    def test_deterministic_node_no_function_ref_fails(self) -> None:
        graph = ReasoningGraph(
            name="no_ref",
            nodes=[
                ReasoningNode(
                    id="step",
                    kind=NodeKind.DETERMINISTIC,
                    inputs=["x"],
                    outputs=["y"],
                    # no function_ref
                ),
            ],
            edges=[],
        )
        reg = DeterministicRegistry()
        result = run_graph(graph, reg, inputs={"x": 1})
        assert result.status == "failure"
        assert "missing function_ref" in (result.error or "").lower()

    def test_deterministic_node_unregistered_function_ref_fails(self) -> None:
        graph = ReasoningGraph(
            name="bad_ref",
            nodes=[
                ReasoningNode(
                    id="step",
                    kind=NodeKind.DETERMINISTIC,
                    inputs=["x"],
                    outputs=["y"],
                    function_ref="does_not_exist",
                ),
            ],
            edges=[],
        )
        reg = DeterministicRegistry()
        result = run_graph(graph, reg, inputs={"x": 1})
        assert result.status == "failure"
        assert "not found in registry" in (result.error or "")


class TestMissingLLMProvider:
    def test_agentic_node_no_provider_fails(self) -> None:
        graph = ReasoningGraph(
            name="no_llm",
            nodes=[
                ReasoningNode(
                    id="agent",
                    kind=NodeKind.AGENTIC,
                    inputs=[],
                    outputs=["out"],
                    prompt_template="do something",
                    output_schema={"type": "object"},
                    contracts=["out is nonempty"],
                ),
            ],
            edges=[],
        )
        reg = DeterministicRegistry()
        result = run_graph(graph, reg)
        assert result.status == "failure"
        assert "LLM provider" in (result.error or "")


class TestEvidenceOnFailedAttempts:
    def test_failed_attempts_still_emit_evidence(self) -> None:
        """Even when the graph fails, every attempt should have evidence."""

        class AlternatingLLM:
            def __init__(self) -> None:
                self._count = 0

            def generate(
                self,
                prompt: str,
                output_schema: dict[str, Any] | None = None,
                timeout_ms: int | None = None,
            ) -> dict[str, Any]:
                self._count += 1
                # Always return bad schema
                return {"score": "bad_string"}

        graph = ReasoningGraph(
            name="ev_fail",
            nodes=[
                ReasoningNode(
                    id="agent",
                    kind=NodeKind.AGENTIC,
                    inputs=[],
                    outputs=["score"],
                    prompt_template="Give a score",
                    output_schema={
                        "type": "object",
                        "properties": {"score": {"type": "number"}},
                        "required": ["score"],
                    },
                    contracts=["score >= 0"],
                    retry_policy=RetryPolicy(
                        max_attempts=3, retry_on=["schema_failure"]
                    ),
                ),
            ],
            edges=[],
        )
        reg = DeterministicRegistry()
        result = run_graph(graph, reg, llm_provider=AlternatingLLM())

        assert result.status == "failure"
        evidence = result.node_results[0].evidence
        assert len(evidence) == 3
        for i, ev in enumerate(evidence):
            assert ev.attempt == i + 1
            assert ev.node_id == "agent"
            assert ev.graph_name == "ev_fail"


# ---- Graph validator failure mode tests --------------------------------


class TestCycleDetectionComplex:
    def test_three_node_cycle(self) -> None:
        graph = ReasoningGraph(
            name="tri_cycle",
            nodes=[
                ReasoningNode(
                    id="a", kind=NodeKind.DETERMINISTIC, inputs=[], outputs=[]
                ),
                ReasoningNode(
                    id="b", kind=NodeKind.DETERMINISTIC, inputs=[], outputs=[]
                ),
                ReasoningNode(
                    id="c", kind=NodeKind.DETERMINISTIC, inputs=[], outputs=[]
                ),
            ],
            edges=[
                ReasoningEdge(from_node="a", to_node="b"),
                ReasoningEdge(from_node="b", to_node="c"),
                ReasoningEdge(from_node="c", to_node="a"),
            ],
        )
        result = validate_graph(graph)
        assert not result.valid
        assert any("cycle" in e.lower() for e in result.errors)

    def test_cycle_in_larger_graph(self) -> None:
        """Cycle among b->c->d->b, with a leading into b."""
        graph = ReasoningGraph(
            name="partial_cycle",
            nodes=[
                ReasoningNode(
                    id="a", kind=NodeKind.DETERMINISTIC, inputs=[], outputs=[]
                ),
                ReasoningNode(
                    id="b", kind=NodeKind.DETERMINISTIC, inputs=[], outputs=[]
                ),
                ReasoningNode(
                    id="c", kind=NodeKind.DETERMINISTIC, inputs=[], outputs=[]
                ),
                ReasoningNode(
                    id="d", kind=NodeKind.DETERMINISTIC, inputs=[], outputs=[]
                ),
            ],
            edges=[
                ReasoningEdge(from_node="a", to_node="b"),
                ReasoningEdge(from_node="b", to_node="c"),
                ReasoningEdge(from_node="c", to_node="d"),
                ReasoningEdge(from_node="d", to_node="b"),
            ],
        )
        result = validate_graph(graph)
        assert not result.valid
        assert any("cycle" in e.lower() for e in result.errors)


class TestMultipleValidationErrors:
    def test_multiple_errors_reported(self) -> None:
        """Graph with duplicate ID, missing output_schema, bad edge ref."""
        graph = ReasoningGraph(
            name="multi_err",
            nodes=[
                ReasoningNode(
                    id="x", kind=NodeKind.DETERMINISTIC, inputs=[], outputs=[]
                ),
                ReasoningNode(
                    id="x", kind=NodeKind.DETERMINISTIC, inputs=[], outputs=[]
                ),
                ReasoningNode(
                    id="y",
                    kind=NodeKind.AGENTIC,
                    inputs=[],
                    outputs=["out"],
                    # missing output_schema and contracts
                ),
            ],
            edges=[
                ReasoningEdge(from_node="x", to_node="ghost"),
            ],
        )
        result = validate_graph(graph)
        assert not result.valid
        # Should report at least: duplicate ID, missing output_schema,
        # missing contracts, non-existent edge target
        assert len(result.errors) >= 4

    def test_all_error_types_at_once(self) -> None:
        graph = ReasoningGraph(
            name="everything_wrong",
            nodes=[
                ReasoningNode(
                    id="a", kind=NodeKind.DETERMINISTIC, inputs=[], outputs=[]
                ),
                ReasoningNode(
                    id="a", kind=NodeKind.DETERMINISTIC, inputs=[], outputs=[]
                ),
                ReasoningNode(
                    id="b",
                    kind=NodeKind.AGENTIC,
                    inputs=[],
                    outputs=[],
                    # no output_schema, no contracts
                ),
            ],
            edges=[
                ReasoningEdge(from_node="phantom", to_node="a"),
                ReasoningEdge(from_node="a", to_node="phantom2"),
            ],
        )
        result = validate_graph(graph)
        assert not result.valid
        error_text = " ".join(result.errors).lower()
        assert "duplicate" in error_text
        assert "output_schema" in error_text
        assert "contracts" in error_text
        assert "non-existent" in error_text


class TestEdgePortValidation:
    def test_edge_with_nonexistent_from_node(self) -> None:
        graph = ReasoningGraph(
            name="bad_from",
            nodes=[
                ReasoningNode(
                    id="a", kind=NodeKind.DETERMINISTIC, inputs=["x"], outputs=["y"]
                ),
            ],
            edges=[
                ReasoningEdge(
                    from_node="nonexistent",
                    to_node="a",
                    from_output="result",
                    to_input="x",
                ),
            ],
        )
        result = validate_graph(graph)
        assert not result.valid
        assert any("non-existent" in e.lower() for e in result.errors)

    def test_edge_with_nonexistent_to_node(self) -> None:
        graph = ReasoningGraph(
            name="bad_to",
            nodes=[
                ReasoningNode(
                    id="a", kind=NodeKind.DETERMINISTIC, inputs=["x"], outputs=["y"]
                ),
            ],
            edges=[
                ReasoningEdge(
                    from_node="a",
                    to_node="nonexistent",
                    from_output="y",
                    to_input="z",
                ),
            ],
        )
        result = validate_graph(graph)
        assert not result.valid
        assert any("non-existent" in e.lower() for e in result.errors)
