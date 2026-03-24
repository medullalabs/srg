"""Tests for Issue 2 & 3 — Core graph models, result, and evidence models."""
from __future__ import annotations

import json

import pytest
from pydantic import ValidationError

from srg.models.node import NodeKind, ReasoningNode, RetryPolicy
from srg.models.edge import ReasoningEdge
from srg.models.graph import ReasoningGraph
from srg.models.evidence import EvidenceRecord
from srg.models.result import GraphExecutionResult, NodeExecutionResult


# --- ReasoningNode ---


class TestReasoningNode:
    def test_create_deterministic_node(self) -> None:
        node = ReasoningNode(
            id="step_one",
            kind=NodeKind.DETERMINISTIC,
            inputs=["x"],
            outputs=["y"],
            function_ref="my_func",
        )
        assert node.id == "step_one"
        assert node.kind == NodeKind.DETERMINISTIC
        assert node.inputs == ["x"]
        assert node.outputs == ["y"]
        assert node.function_ref == "my_func"
        assert node.contracts == []
        assert node.effects == []
        assert node.metadata == {}

    def test_create_agentic_node(self) -> None:
        node = ReasoningNode(
            id="step_two",
            kind=NodeKind.AGENTIC,
            inputs=["data"],
            outputs=["result"],
            prompt_template="Analyze {data}",
            output_schema={"type": "object"},
            contracts=["result is nonempty"],
        )
        assert node.kind == NodeKind.AGENTIC
        assert node.prompt_template == "Analyze {data}"
        assert node.output_schema == {"type": "object"}
        assert node.contracts == ["result is nonempty"]

    def test_node_with_retry_policy(self) -> None:
        policy = RetryPolicy(max_attempts=3, retry_on=["schema_failure"])
        node = ReasoningNode(
            id="retryable",
            kind=NodeKind.AGENTIC,
            inputs=["in"],
            outputs=["out"],
            output_schema={"type": "object"},
            contracts=["out is nonempty"],
            retry_policy=policy,
        )
        assert node.retry_policy is not None
        assert node.retry_policy.max_attempts == 3
        assert node.retry_policy.retry_on == ["schema_failure"]

    def test_retry_policy_defaults(self) -> None:
        policy = RetryPolicy()
        assert policy.max_attempts == 2
        assert policy.retry_on == ["schema_failure", "contract_failure"]

    def test_node_missing_required_fields(self) -> None:
        with pytest.raises(ValidationError):
            ReasoningNode(id="bad")  # type: ignore[call-arg]

    def test_invalid_kind(self) -> None:
        with pytest.raises(ValidationError):
            ReasoningNode(
                id="bad",
                kind="unknown",  # type: ignore[arg-type]
                inputs=[],
                outputs=[],
            )

    def test_node_serialization_roundtrip(self) -> None:
        node = ReasoningNode(
            id="test",
            kind=NodeKind.DETERMINISTIC,
            inputs=["a"],
            outputs=["b"],
            description="A test node",
            metadata={"key": "value"},
        )
        data = json.loads(node.model_dump_json())
        restored = ReasoningNode.model_validate(data)
        assert restored == node

    def test_node_with_metadata(self) -> None:
        node = ReasoningNode(
            id="meta",
            kind=NodeKind.DETERMINISTIC,
            inputs=[],
            outputs=[],
            metadata={"author": "test", "version": 1},
        )
        assert node.metadata["author"] == "test"

    def test_node_with_effects(self) -> None:
        node = ReasoningNode(
            id="effectful",
            kind=NodeKind.DETERMINISTIC,
            inputs=[],
            outputs=[],
            effects=["read_db", "write_file"],
        )
        assert node.effects == ["read_db", "write_file"]


# --- ReasoningEdge ---


class TestReasoningEdge:
    def test_create_edge(self) -> None:
        edge = ReasoningEdge(from_node="a", to_node="b")
        assert edge.from_node == "a"
        assert edge.to_node == "b"
        assert edge.kind == "data_flow"
        assert edge.from_output is None
        assert edge.to_input is None

    def test_edge_with_ports(self) -> None:
        edge = ReasoningEdge(
            from_node="a",
            to_node="b",
            from_output="result",
            to_input="data",
        )
        assert edge.from_output == "result"
        assert edge.to_input == "data"

    def test_edge_custom_kind(self) -> None:
        edge = ReasoningEdge(from_node="a", to_node="b", kind="control_flow")
        assert edge.kind == "control_flow"

    def test_edge_serialization_roundtrip(self) -> None:
        edge = ReasoningEdge(
            from_node="x", to_node="y", from_output="out", to_input="in"
        )
        data = json.loads(edge.model_dump_json())
        restored = ReasoningEdge.model_validate(data)
        assert restored == edge


# --- ReasoningGraph ---


class TestReasoningGraph:
    def test_create_graph(self) -> None:
        graph = ReasoningGraph(
            name="test_graph",
            nodes=[
                ReasoningNode(
                    id="n1",
                    kind=NodeKind.DETERMINISTIC,
                    inputs=["x"],
                    outputs=["y"],
                ),
            ],
            edges=[],
        )
        assert graph.name == "test_graph"
        assert len(graph.nodes) == 1
        assert graph.description is None
        assert graph.version is None
        assert graph.metadata == {}

    def test_graph_with_edges(self) -> None:
        graph = ReasoningGraph(
            name="pipeline",
            nodes=[
                ReasoningNode(
                    id="a",
                    kind=NodeKind.DETERMINISTIC,
                    inputs=["x"],
                    outputs=["y"],
                ),
                ReasoningNode(
                    id="b",
                    kind=NodeKind.DETERMINISTIC,
                    inputs=["y"],
                    outputs=["z"],
                ),
            ],
            edges=[ReasoningEdge(from_node="a", to_node="b")],
        )
        assert len(graph.edges) == 1
        assert graph.edges[0].from_node == "a"

    def test_graph_serialization_roundtrip(self) -> None:
        graph = ReasoningGraph(
            name="roundtrip",
            description="Test roundtrip",
            version="1.0",
            nodes=[
                ReasoningNode(
                    id="n1",
                    kind=NodeKind.DETERMINISTIC,
                    inputs=[],
                    outputs=[],
                ),
            ],
            edges=[],
            metadata={"tag": "test"},
        )
        data = json.loads(graph.model_dump_json())
        restored = ReasoningGraph.model_validate(data)
        assert restored == graph


# --- EvidenceRecord ---


class TestEvidenceRecord:
    def test_create_evidence(self) -> None:
        ev = EvidenceRecord(
            graph_name="my_graph",
            node_id="node_1",
            attempt=1,
            status="success",
            timestamp="2024-01-01T00:00:00Z",
        )
        assert ev.graph_name == "my_graph"
        assert ev.status == "success"
        assert ev.validation_outcome is None
        assert ev.duration_ms is None

    def test_evidence_with_all_fields(self) -> None:
        ev = EvidenceRecord(
            graph_name="g",
            node_id="n",
            attempt=2,
            status="failure",
            timestamp="2024-01-01T00:00:00Z",
            validation_outcome="schema_mismatch",
            duration_ms=123.4,
            prompt_hash="abc123",
            input_hash="def456",
            output_hash="ghi789",
            retry_reason="schema_failure",
            contract_summary="score out of range",
        )
        assert ev.attempt == 2
        assert ev.retry_reason == "schema_failure"

    def test_evidence_serialization_roundtrip(self) -> None:
        ev = EvidenceRecord(
            graph_name="g",
            node_id="n",
            attempt=1,
            status="success",
            timestamp="2024-01-01T00:00:00Z",
            duration_ms=50.0,
        )
        data = json.loads(ev.model_dump_json())
        restored = EvidenceRecord.model_validate(data)
        assert restored == ev


# --- NodeExecutionResult & GraphExecutionResult ---


class TestResults:
    def test_node_execution_result(self) -> None:
        result = NodeExecutionResult(
            node_id="n1",
            status="success",
            outputs={"y": 42},
            duration_ms=10.0,
        )
        assert result.node_id == "n1"
        assert result.outputs["y"] == 42
        assert result.evidence == []
        assert result.error is None

    def test_node_execution_result_failure(self) -> None:
        result = NodeExecutionResult(
            node_id="n1",
            status="failure",
            error="contract violation",
        )
        assert result.status == "failure"
        assert result.error == "contract violation"

    def test_graph_execution_result(self) -> None:
        node_result = NodeExecutionResult(
            node_id="n1", status="success", outputs={"y": 1}
        )
        result = GraphExecutionResult(
            graph_name="my_graph",
            status="success",
            outputs={"y": 1},
            node_results=[node_result],
        )
        assert result.graph_name == "my_graph"
        assert len(result.node_results) == 1
        assert result.error is None

    def test_graph_execution_result_failure(self) -> None:
        result = GraphExecutionResult(
            graph_name="g",
            status="failure",
            error="cycle detected",
        )
        assert result.status == "failure"

    def test_result_serialization_roundtrip(self) -> None:
        result = GraphExecutionResult(
            graph_name="g",
            status="success",
            outputs={"out": "value"},
            node_results=[
                NodeExecutionResult(
                    node_id="n1",
                    status="success",
                    outputs={"out": "value"},
                ),
            ],
        )
        data = json.loads(result.model_dump_json())
        restored = GraphExecutionResult.model_validate(data)
        assert restored == result
