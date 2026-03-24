from __future__ import annotations

from pydantic import BaseModel


class ReasoningEdge(BaseModel):
    from_node: str
    to_node: str
    from_output: str | None = None
    to_input: str | None = None
    kind: str = "data_flow"
