from __future__ import annotations

from pydantic import BaseModel


class EvidenceRecord(BaseModel):
    graph_name: str
    node_id: str
    attempt: int
    status: str  # "success" | "failure"
    timestamp: str
    validation_outcome: str | None = None
    duration_ms: float | None = None
    prompt_hash: str | None = None
    input_hash: str | None = None
    output_hash: str | None = None
    retry_reason: str | None = None
    contract_summary: str | None = None
