from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from srg.models.evidence import EvidenceRecord


class NodeExecutionResult(BaseModel):
    node_id: str
    status: str  # "success" | "failure"
    outputs: dict[str, Any] = Field(default_factory=dict)
    error: str | None = None
    evidence: list[EvidenceRecord] = Field(default_factory=list)
    duration_ms: float | None = None


class GraphExecutionResult(BaseModel):
    graph_name: str
    status: str  # "success" | "failure"
    outputs: dict[str, Any] = Field(default_factory=dict)
    node_results: list[NodeExecutionResult] = Field(default_factory=list)
    error: str | None = None
    evidence_summary: dict[str, Any] | None = None
