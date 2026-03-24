# Contributing to SRG

## Spec Alignment Rules

All contributions to SRG MUST conform to the v0.3 specification (`srg_spec_v0_3.md`). The following rules are non-negotiable:

### What SRG is

- A semantic reasoning graph representation.
- Explicit, composable, inspectable, agent-modifiable.
- Two node kinds only: `deterministic` and `agentic`.
- Contract-enforced agentic execution with evidence trails.

### What SRG is NOT

Do not add features that turn SRG into any of the following:

- A workflow engine
- A reactive stream system
- An adapter marketplace
- A generalized orchestration framework
- A replacement for Python

### Scope guardrails

The following are enforced by automated tests (`tests/test_scope_guard.py`) and will cause CI to fail:

- No module named `adapter`, `workflow`, `scheduler`, `stream`, or `transport` may exist in `srg/`.
- `NodeKind` MUST only have `DETERMINISTIC` and `AGENTIC` values.
- `ReasoningNode` MUST NOT have `transform` or `adapter` fields.

### Required invariants

- **Agentic nodes MUST have contracts and output_schema.** The graph validator rejects graphs that violate this.
- **All edges MUST be explicit.** No implicit dependency inference.
- **LLM outputs MUST be JSON.** Free-form text is rejected.
- **Every node execution MUST emit evidence.** EvidenceRecord is not optional.
- **Deterministic nodes use function_ref.** They look up callables from a DeterministicRegistry.
- **No inline transforms.** Computation happens in registered functions or LLM calls, not in the graph representation itself.

### Code standards

- All code must pass `mypy --strict`.
- All code must pass `ruff check`.
- All tests must pass (`pytest tests/ -v`).
- New features require tests.

### Architecture layers

Never collapse these:

1. **Models** (`srg/models/`) -- Pydantic data models for nodes, edges, graphs, evidence, results.
2. **Kernel** (`srg/kernel/`) -- Execution primitives: agentic_call, contracts, validation, retry.
3. **Runtime** (`srg/runtime/`) -- Graph-level operations: loader, validator, planner, runner, registry, evidence aggregator.
4. **Utils** (`srg/utils/`) -- Utilities like semantic_diff that operate on model instances.
