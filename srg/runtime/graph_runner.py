"""Issue 10 — Full graph execution runner."""
from __future__ import annotations

import time
from datetime import datetime, timezone
from typing import Any

from srg.kernel.agentic_call import (
    AgenticCallSpec,
    LLMProvider,
    agentic_call,
)
from srg.models.evidence import EvidenceRecord
from srg.models.graph import ReasoningGraph
from srg.models.node import NodeKind, ReasoningNode, RetryPolicy
from srg.models.result import GraphExecutionResult, NodeExecutionResult
from srg.runtime.deterministic_registry import DeterministicRegistry
from srg.runtime.graph_validator import validate_graph
from srg.runtime.planner import compute_execution_order


class GraphRunnerError(Exception):
    """Raised when graph execution encounters an unrecoverable error."""


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _build_prompt(node: ReasoningNode, state: dict[str, Any]) -> str:
    """Build a prompt from the node's template with state values interpolated."""
    template = node.prompt_template or ""
    prompt = template
    for key, val in state.items():
        prompt = prompt.replace(f"{{{key}}}", str(val))
    return prompt


def run_graph(
    graph: ReasoningGraph,
    registry: DeterministicRegistry,
    llm_provider: LLMProvider | None = None,
    inputs: dict[str, Any] | None = None,
) -> GraphExecutionResult:
    """Execute a full reasoning graph.

    Flow
    ----
    1. Validate graph
    2. Compute execution order
    3. For each node: execute deterministic or agentic
    4. Collect per-node results
    5. Return ``GraphExecutionResult``
    """

    # --- 1. validate ---
    validation = validate_graph(graph)
    if not validation.valid:
        return GraphExecutionResult(
            graph_name=graph.name,
            status="failure",
            error=f"Graph validation failed: {'; '.join(validation.errors)}",
        )

    # --- 2. execution order ---
    try:
        order = compute_execution_order(graph)
    except Exception as exc:
        return GraphExecutionResult(
            graph_name=graph.name,
            status="failure",
            error=str(exc),
        )

    node_map: dict[str, ReasoningNode] = {n.id: n for n in graph.nodes}
    state: dict[str, Any] = dict(inputs) if inputs else {}
    node_results: list[NodeExecutionResult] = []

    # --- 3. execute each node ---
    for node_id in order:
        node = node_map[node_id]
        t0 = time.monotonic()

        if node.kind == NodeKind.DETERMINISTIC:
            result = _run_deterministic(node, state, registry, graph.name)
        else:
            if llm_provider is None:
                result = NodeExecutionResult(
                    node_id=node_id,
                    status="failure",
                    error="Agentic node requires an LLM provider",
                )
            else:
                result = _run_agentic(node, state, llm_provider, graph.name)

        duration_ms = (time.monotonic() - t0) * 1000.0
        result.duration_ms = round(duration_ms, 2)
        node_results.append(result)

        if result.status == "failure":
            return GraphExecutionResult(
                graph_name=graph.name,
                status="failure",
                node_results=node_results,
                outputs=state,
                error=f"Node '{node_id}' failed: {result.error}",
            )

        # merge outputs into state
        state.update(result.outputs)

    return GraphExecutionResult(
        graph_name=graph.name,
        status="success",
        node_results=node_results,
        outputs=state,
    )


def _run_deterministic(
    node: ReasoningNode,
    state: dict[str, Any],
    registry: DeterministicRegistry,
    graph_name: str,
) -> NodeExecutionResult:
    """Execute a deterministic node via the registry."""
    fn_name = node.function_ref
    if fn_name is None:
        return NodeExecutionResult(
            node_id=node.id,
            status="failure",
            error="Deterministic node missing function_ref",
        )

    if not registry.has(fn_name):
        return NodeExecutionResult(
            node_id=node.id,
            status="failure",
            error=f"Function '{fn_name}' not found in registry",
        )

    fn = registry.get(fn_name)
    try:
        outputs: dict[str, Any] = fn(state)
    except Exception as exc:
        return NodeExecutionResult(
            node_id=node.id,
            status="failure",
            error=f"Function raised: {exc}",
        )

    evidence = EvidenceRecord(
        graph_name=graph_name,
        node_id=node.id,
        attempt=1,
        status="success",
        timestamp=_now_iso(),
    )

    return NodeExecutionResult(
        node_id=node.id,
        status="success",
        outputs=outputs,
        evidence=[evidence],
    )


def _run_agentic(
    node: ReasoningNode,
    state: dict[str, Any],
    llm_provider: LLMProvider,
    graph_name: str,
) -> NodeExecutionResult:
    """Execute an agentic node via ``agentic_call``."""
    prompt = _build_prompt(node, state)

    spec = AgenticCallSpec(
        node_id=node.id,
        prompt=prompt,
        output_schema=node.output_schema or {},
        contracts=node.contracts,
        retry_policy=node.retry_policy or RetryPolicy(),
    )

    result = agentic_call(spec, llm_provider, graph_name=graph_name)

    if result.success:
        return NodeExecutionResult(
            node_id=node.id,
            status="success",
            outputs=result.outputs,
            evidence=result.evidence,
        )

    return NodeExecutionResult(
        node_id=node.id,
        status="failure",
        error=result.error,
        evidence=result.evidence,
    )
