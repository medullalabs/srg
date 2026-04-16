# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.0] - 2026-04-16

Initial public release.

### Added

- Pydantic v2 data models: `ReasoningNode`, `ReasoningEdge`, `ReasoningGraph`, `EvidenceRecord`, `NodeExecutionResult`, `GraphExecutionResult`.
- Two node kinds: `DETERMINISTIC` and `AGENTIC` (scope-guarded — no other kinds permitted).
- Agentic execution kernel (`srg.kernel.agentic_call`): prompt → LLM → JSON parse → schema validation → contract check → retry → evidence emission.
- String-based contracts: `score in 0..100`, `field is nonempty`, `field exists`, comparisons.
- Graph runtime: YAML loader, structural validator (duplicate IDs, invalid edges, missing schemas/contracts on agentic nodes, cycle detection via Kahn's algorithm), topological planner, graph runner.
- `DeterministicRegistry` mapping `function_ref` strings to Python callables.
- Evidence aggregator + summary for post-run analysis and debugging.
- `semantic_diff` — structural graph comparison detecting added/removed nodes, rewired edges, changed contracts, kind switches.
- `compose_graphs` — explicit, validated composition of multiple reasoning graphs.
- `srg` CLI: `validate`, `run`, `diff` subcommands.
- Example graphs: `validator_scorer.yaml`, `repo_risk.yaml`, `subnet_scorer.yaml`.
- JSON schemas for graph and evidence records (bundled in the wheel).
- Scope-guard test suite preventing drift toward workflow, orchestration, adapter, or infrastructure abstractions.

[Unreleased]: https://github.com/medullalabs/semantic-reasoning-graph/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/medullalabs/semantic-reasoning-graph/releases/tag/v0.1.0
