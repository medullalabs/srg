from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class NodeKind(str, Enum):
    DETERMINISTIC = "deterministic"
    AGENTIC = "agentic"


class RetryPolicy(BaseModel):
    max_attempts: int = 2
    retry_on: list[str] = Field(
        default_factory=lambda: ["schema_failure", "contract_failure"]
    )


class ReasoningNode(BaseModel):
    id: str
    kind: NodeKind
    inputs: list[str]
    outputs: list[str]
    description: str | None = None
    function_ref: str | None = None  # deterministic only
    prompt_template: str | None = None  # agentic only
    output_schema: dict[str, Any] | None = None  # required for agentic
    contracts: list[str] = Field(default_factory=list)
    effects: list[str] = Field(default_factory=list)
    retry_policy: RetryPolicy | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
