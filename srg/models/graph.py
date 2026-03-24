from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from srg.models.node import ReasoningNode
from srg.models.edge import ReasoningEdge


class ReasoningGraph(BaseModel):
    name: str
    nodes: list[ReasoningNode]
    edges: list[ReasoningEdge]
    description: str | None = None
    version: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
