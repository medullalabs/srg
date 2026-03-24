"""SRG — Semantic Reasoning Graph."""

__version__ = "0.1.0"

from srg.models.graph import ReasoningGraph
from srg.models.node import ReasoningNode, NodeKind
from srg.models.edge import ReasoningEdge
from srg.models.result import GraphExecutionResult, NodeExecutionResult
from srg.runtime.graph_runner import run_graph
from srg.runtime.loader import load_graph
from srg.runtime.deterministic_registry import DeterministicRegistry
from srg.kernel.agentic_call import (
    agentic_call,
    AgenticCallSpec,
    LLMProvider,
    OllamaProvider,
)

__all__ = [
    "ReasoningGraph",
    "ReasoningNode",
    "NodeKind",
    "ReasoningEdge",
    "GraphExecutionResult",
    "NodeExecutionResult",
    "run_graph",
    "load_graph",
    "DeterministicRegistry",
    "agentic_call",
    "AgenticCallSpec",
    "LLMProvider",
    "OllamaProvider",
]
