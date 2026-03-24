# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Is

SRG (Semantic Reasoning Graph) is a **semantic IR for reasoning structure** — not a workflow engine, not an adapter marketplace, not an orchestration framework. It describes reasoning-centric computation as typed nodes connected by explicit data-flow edges, layered over a contract-enforced agentic execution kernel. The north-star spec is `srg_spec_v0_3.md`.

## Commands

```bash
pip install -e ".[dev]"       # Install with dev deps
pytest tests/ -v              # Run all tests
pytest tests/test_planner.py -v              # Run one test file
pytest tests/test_planner.py::test_name -v   # Run a single test
ruff check srg/ tests/        # Lint
mypy srg/                     # Type check (strict mode, pydantic plugin)
```

## Architecture (4 layers — never collapse these)

1. **Models** (`srg/models/`) — Pydantic v2 data models: `ReasoningNode`, `ReasoningEdge`, `ReasoningGraph`, `EvidenceRecord`, `NodeExecutionResult`, `GraphExecutionResult`. Two node kinds only: `DETERMINISTIC` and `AGENTIC`.

2. **Kernel** (`srg/kernel/`) — Execution primitives for agentic calls: `agentic_call()` orchestrates prompt→LLM→JSON parse→schema validation→contract check→retry→evidence. `LLMProvider` is a protocol with a single `generate(prompt, output_schema)` method. Contracts are string-based (`score in 0..100`, `field is nonempty`, `field exists`, comparisons).

3. **Runtime** (`srg/runtime/`) — Graph-level operations: `loader.py` (YAML→ReasoningGraph), `graph_validator.py` (structural checks + cycle detection via Kahn's algorithm), `planner.py` (topological sort), `graph_runner.py` (main orchestrator: validate→plan→execute→evidence), `deterministic_registry.py` (maps `function_ref` strings to callables), `evidence_aggregator.py`.

4. **Utils** (`srg/utils/`) — `semantic_diff.py` compares two `ReasoningGraph` instances structurally.

**Data flow:** YAML graph → `load_graph()` → `validate_graph()` → `compute_execution_order()` → `run_graph()` (executes deterministic nodes via registry, agentic nodes via kernel) → `GraphExecutionResult` with per-node evidence.

## Spec Conformance Rules

All code MUST conform to `srg_spec_v0_3.md` and pass `srg_conformance_v0_3.md`. Key invariants:

- **Agentic nodes MUST have `contracts` and `output_schema`.** The graph validator rejects violations.
- **All edges MUST be explicit.** No implicit dependency inference.
- **LLM outputs MUST be validated JSON.** Free-form text is rejected.
- **Every node execution MUST emit an `EvidenceRecord`**, including failed attempts.
- **Deterministic nodes use `function_ref`** resolved via `DeterministicRegistry`.
- **No inline transforms.** Computation in registered functions or LLM calls only.

## Scope Guards (enforced by `tests/test_scope_guard.py`)

These will fail CI if violated:

- No modules named `adapter`, `workflow`, `scheduler`, `stream`, or `transport` in `srg/`
- `NodeKind` must only have `DETERMINISTIC` and `AGENTIC`
- `ReasoningNode` must not have `transform` or `adapter` fields

Do NOT add features that drift toward orchestration, reactive streams, adapter ecosystems, or infrastructure concerns. If in doubt, re-read Section 2 (Scope) of `srg_spec_v0_3.md`.

## GitHub Tool Preference

When interacting with GitHub (issues, PRs, repos, etc.), prefer tools in this order:

1. **GitHub MCP tools** (`mcp__github__*`) — use `ToolSearch` to fetch deferred tools first
2. **gh CLI** (`gh issue list`, `gh pr create`, etc.)
3. **gh API** (`gh api repos/...`) — only as a last resort

## Schema References

- `srg/schemas/graph.schema.json` — JSON Schema for graph declarations
- `srg/schemas/evidence.schema.json` — JSON Schema for evidence records
- `srg_schema_v0_1.md` — Canonical schema specification for the MVP
