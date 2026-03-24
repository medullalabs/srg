"""Issue 3 — Minimal CLI for SRG: validate, run, diff."""
from __future__ import annotations

import argparse
import importlib
import json
import sys
from pathlib import Path
from typing import Any

from srg.runtime.graph_validator import validate_graph
from srg.runtime.loader import load_graph
from srg.runtime.planner import compute_execution_order
from srg.utils.semantic_diff import semantic_diff


def cmd_validate(args: argparse.Namespace) -> int:
    """Load and validate a graph YAML file."""
    try:
        graph = load_graph(Path(args.graph))
    except Exception as exc:
        print(f"Load error: {exc}", file=sys.stderr)
        return 1

    result = validate_graph(graph)
    if result.valid:
        order = compute_execution_order(graph)
        print(f"Valid: {graph.name} ({len(graph.nodes)} nodes, {len(graph.edges)} edges)")
        print(f"Execution order: {' -> '.join(order)}")
        return 0

    print(f"Invalid: {len(result.errors)} error(s)", file=sys.stderr)
    for err in result.errors:
        print(f"  - {err}", file=sys.stderr)
    return 1


def cmd_run(args: argparse.Namespace) -> int:
    """Load, validate, and execute a graph."""
    from srg.runtime.deterministic_registry import DeterministicRegistry
    from srg.runtime.graph_runner import run_graph

    try:
        graph = load_graph(Path(args.graph))
    except Exception as exc:
        print(f"Load error: {exc}", file=sys.stderr)
        return 1

    # Build registry from module
    registry = DeterministicRegistry()
    if args.registry:
        try:
            mod = importlib.import_module(args.registry)
        except ImportError as exc:
            print(f"Registry import error: {exc}", file=sys.stderr)
            return 1
        # Auto-register functions decorated with @registry.register or
        # any callable with a _srg_register_name attribute.
        # Fallback: register all public functions.
        for name in dir(mod):
            if name.startswith("_"):
                continue
            obj = getattr(mod, name)
            if callable(obj):
                registry.register(name)(obj)

    # Parse inputs
    inputs: dict[str, Any] = {}
    if args.input:
        try:
            inputs = json.loads(args.input)
        except json.JSONDecodeError as exc:
            print(f"Input JSON error: {exc}", file=sys.stderr)
            return 1

    # LLM provider
    llm = None
    if args.provider:
        llm = _load_provider(args.provider, args.model)
        if llm is None:
            return 1

    result = run_graph(graph, registry, llm_provider=llm, inputs=inputs)

    if result.status == "success":
        print(json.dumps({
            "status": "success",
            "overall_output": {k: v for k, v in result.outputs.items()
                               if not k.endswith("_features")},
            "nodes_executed": len(result.node_results),
        }, indent=2, default=str))
        return 0

    print(f"Execution failed: {result.error}", file=sys.stderr)
    if result.node_results:
        for nr in result.node_results:
            status_mark = "ok" if nr.status == "success" else "FAIL"
            print(f"  [{status_mark}] {nr.node_id}", file=sys.stderr)
    return 1


def _load_provider(provider: str, model: str | None) -> Any | None:
    """Load an LLM provider by name."""
    if provider == "ollama":
        from srg.kernel.agentic_call import OllamaProvider
        return OllamaProvider(model=model or "llama3")
    print(f"Unknown provider: {provider}", file=sys.stderr)
    return None


def cmd_diff(args: argparse.Namespace) -> int:
    """Semantic diff between two graph YAML files."""
    try:
        old = load_graph(Path(args.old_graph))
        new = load_graph(Path(args.new_graph))
    except Exception as exc:
        print(f"Load error: {exc}", file=sys.stderr)
        return 1

    diff = semantic_diff(old, new)

    has_changes = (
        diff.added_nodes or diff.removed_nodes or diff.modified_nodes
        or diff.added_edges or diff.removed_edges or diff.metadata_changes
    )

    if not has_changes:
        print("No differences.")
        return 0

    if diff.metadata_changes:
        for key, (old_val, new_val) in diff.metadata_changes.items():
            print(f"  {key}: {old_val!r} -> {new_val!r}")

    if diff.added_nodes:
        for nid in diff.added_nodes:
            print(f"  + node {nid}")

    if diff.removed_nodes:
        for nid in diff.removed_nodes:
            print(f"  - node {nid}")

    if diff.modified_nodes:
        for nd in diff.modified_nodes:
            print(f"  ~ node {nd.node_id}:")
            for field, (old_val, new_val) in nd.changes.items():
                print(f"      {field}: {old_val!r} -> {new_val!r}")

    if diff.added_edges:
        for from_n, to_n in diff.added_edges:
            print(f"  + edge {from_n} -> {to_n}")

    if diff.removed_edges:
        for from_n, to_n in diff.removed_edges:
            print(f"  - edge {from_n} -> {to_n}")

    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="srg",
        description="Semantic Reasoning Graph CLI",
    )
    sub = parser.add_subparsers(dest="command")

    # srg validate
    p_validate = sub.add_parser("validate", help="Validate a graph YAML file")
    p_validate.add_argument("graph", help="Path to graph YAML file")

    # srg run
    p_run = sub.add_parser("run", help="Execute a graph")
    p_run.add_argument("graph", help="Path to graph YAML file")
    p_run.add_argument("--registry", help="Python module with deterministic functions")
    p_run.add_argument("--input", help="JSON string of input values")
    p_run.add_argument("--provider", help="LLM provider (ollama)")
    p_run.add_argument("--model", help="Model name for the LLM provider")

    # srg diff
    p_diff = sub.add_parser("diff", help="Semantic diff between two graphs")
    p_diff.add_argument("old_graph", help="Path to old graph YAML file")
    p_diff.add_argument("new_graph", help="Path to new graph YAML file")

    args = parser.parse_args(argv)

    if args.command is None:
        parser.print_help()
        return 1

    if args.command == "validate":
        return cmd_validate(args)
    elif args.command == "run":
        return cmd_run(args)
    elif args.command == "diff":
        return cmd_diff(args)

    return 1


if __name__ == "__main__":
    sys.exit(main())
