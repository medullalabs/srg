"""SRG — Semantic Reasoning Graph."""

from importlib.metadata import PackageNotFoundError, version as _pkg_version

try:
    __version__ = _pkg_version("semantic-reasoning-graph")
except PackageNotFoundError:
    __version__ = "0.0.0+unknown"

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
