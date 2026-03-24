"""Tests for Issue 11 — Evidence aggregation."""
from __future__ import annotations

from srg.models.evidence import EvidenceRecord
from srg.models.result import NodeExecutionResult
from srg.runtime.evidence_aggregator import aggregate_evidence


def _make_evidence(
    node_id: str = "n",
    attempt: int = 1,
    status: str = "success",
) -> EvidenceRecord:
    return EvidenceRecord(
        graph_name="test",
        node_id=node_id,
        attempt=attempt,
        status=status,
        timestamp="2024-01-01T00:00:00Z",
    )


class TestAggregateEvidence:
    def test_all_success(self) -> None:
        results = [
            NodeExecutionResult(
                node_id="a",
                status="success",
                outputs={"x": 1},
                evidence=[_make_evidence("a")],
            ),
            NodeExecutionResult(
                node_id="b",
                status="success",
                outputs={"y": 2},
                evidence=[_make_evidence("b")],
            ),
        ]
        agg = aggregate_evidence(results)
        assert agg["total_nodes"] == 2
        assert agg["passed"] == 2
        assert agg["failed"] == 0
        assert agg["total_attempts"] == 2
        assert len(agg["evidence_records"]) == 2

    def test_mixed_success_failure(self) -> None:
        results = [
            NodeExecutionResult(
                node_id="a",
                status="success",
                outputs={"x": 1},
                evidence=[_make_evidence("a")],
            ),
            NodeExecutionResult(
                node_id="b",
                status="failure",
                error="contract violation",
                evidence=[
                    _make_evidence("b", attempt=1, status="failure"),
                    _make_evidence("b", attempt=2, status="failure"),
                ],
            ),
        ]
        agg = aggregate_evidence(results)
        assert agg["total_nodes"] == 2
        assert agg["passed"] == 1
        assert agg["failed"] == 1
        assert agg["total_attempts"] == 3
        assert len(agg["evidence_records"]) == 3

    def test_empty_results(self) -> None:
        agg = aggregate_evidence([])
        assert agg["total_nodes"] == 0
        assert agg["passed"] == 0
        assert agg["failed"] == 0
        assert agg["total_attempts"] == 0
        assert agg["evidence_records"] == []

    def test_node_without_evidence(self) -> None:
        """Deterministic nodes may have no evidence records."""
        results = [
            NodeExecutionResult(
                node_id="a",
                status="success",
                outputs={"x": 1},
                # no evidence
            ),
        ]
        agg = aggregate_evidence(results)
        assert agg["total_nodes"] == 1
        assert agg["passed"] == 1
        assert agg["total_attempts"] == 1  # counted as 1 even without evidence

    def test_multiple_retries(self) -> None:
        results = [
            NodeExecutionResult(
                node_id="a",
                status="success",
                outputs={"x": 1},
                evidence=[
                    _make_evidence("a", attempt=1, status="failure"),
                    _make_evidence("a", attempt=2, status="failure"),
                    _make_evidence("a", attempt=3, status="success"),
                ],
            ),
        ]
        agg = aggregate_evidence(results)
        assert agg["total_nodes"] == 1
        assert agg["passed"] == 1
        assert agg["total_attempts"] == 3

    def test_evidence_records_are_flattened(self) -> None:
        results = [
            NodeExecutionResult(
                node_id="a",
                status="success",
                outputs={},
                evidence=[_make_evidence("a", 1), _make_evidence("a", 2)],
            ),
            NodeExecutionResult(
                node_id="b",
                status="success",
                outputs={},
                evidence=[_make_evidence("b", 1)],
            ),
        ]
        agg = aggregate_evidence(results)
        records = agg["evidence_records"]
        assert len(records) == 3
        node_ids = [r.node_id for r in records]
        assert node_ids == ["a", "a", "b"]
