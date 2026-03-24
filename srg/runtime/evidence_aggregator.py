"""Issue 11 — Evidence aggregation across node execution results."""
from __future__ import annotations

from typing import Any

from srg.models.evidence import EvidenceRecord
from srg.models.result import NodeExecutionResult


def aggregate_evidence(
    node_results: list[NodeExecutionResult],
) -> dict[str, Any]:
    """Aggregate evidence from a list of node execution results.

    Returns
    -------
    dict with keys:
        total_nodes, passed, failed, total_attempts, evidence_records
    """
    total_nodes = len(node_results)
    passed = sum(1 for r in node_results if r.status == "success")
    failed = sum(1 for r in node_results if r.status == "failure")

    all_evidence: list[EvidenceRecord] = []
    total_attempts = 0

    for nr in node_results:
        all_evidence.extend(nr.evidence)
        if nr.evidence:
            total_attempts += len(nr.evidence)
        else:
            # deterministic nodes with no evidence still count as 1 attempt
            total_attempts += 1

    total_duration_ms = round(
        sum(nr.duration_ms for nr in node_results if nr.duration_ms is not None),
        2,
    )

    return {
        "total_nodes": total_nodes,
        "passed": passed,
        "failed": failed,
        "total_attempts": total_attempts,
        "total_duration_ms": total_duration_ms,
        "evidence_records": all_evidence,
    }
