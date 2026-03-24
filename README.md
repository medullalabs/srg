# SRG -- Semantic Reasoning Graph

SRG is a **structural safety net for reasoning-centric systems**. It describes computation as typed nodes connected by explicit data-flow edges, with contract-enforced agentic execution and automatic evidence trails. Two node kinds: **deterministic** (pure Python functions) and **agentic** (LLM calls with JSON schema validation, contract checking, and automatic retry).

SRG's value is not making edits easier -- a capable LLM can edit Python equally well. The value is making edits **safer**: structural validation catches bugs (duplicate nodes, invalid edges, cycles, missing schemas) that Python silently accepts. Contracts prevent silent reasoning degradation. Evidence provides automatic, structured debugging without custom logging.

## What SRG gives you over plain Python

- **Contracts as infrastructure.** Declarative (`score in 0..100`), auto-enforced with retry, required on all agentic nodes. Not optional `if/raise` scattered across function bodies.
- **Structural validation.** `validate_graph()` catches duplicate nodes, invalid edges, cycles, and missing schemas before execution. Python lets these through as silent bugs or runtime exceptions.
- **Automatic evidence.** Every node execution emits an `EvidenceRecord` with timestamps, input/output hashes, attempt counts, and duration. No instrumentation needed.
- **Separation of policy from computation.** Graph topology, weights, contracts, and node types live in YAML. Computation lives in Python. Non-coders can review the reasoning structure.
- **Semantic diff.** `semantic_diff(old, new)` detects "node added", "contract changed", "edge rewired" -- structured changes, not line-level noise.
- **Composition.** `compose_graphs(a, b, connecting_edges)` merges graphs with validation.

## What SRG is NOT

- **Not more compact than Python.** SRG is ~1.7x larger (YAML + Python vs Python alone).
- **Not a productivity multiplier.** Adding a scoring factor takes more total lines in SRG.
- **Not a workflow engine.** No task queues, no scheduling, no DAG orchestration.
- **Not an adapter marketplace.** No plugin system, no connectors, no transports.
- **Not a reactive stream system.** No event streams, no pub/sub, no backpressure.
- **Not a replacement for Python.** SRG graphs describe reasoning structure; Python does the work.

## When to use SRG

Systems where **the cost of a silent reasoning bug exceeds the cost of framework overhead**:
- Scoring, decision, and assessment pipelines with LLM components
- Systems that will be iteratively modified (contracts catch regressions)
- Teams where non-coders need to review reasoning structure
- Systems that need audit trails without custom logging

## Quick example

```yaml
name: subnet_scorer
nodes:
  - id: extract_features
    kind: deterministic
    inputs: [subnet_data]
    outputs: [mechanism_features, network_features, team_features]
    function_ref: extract_features

  - id: score_team_quality
    kind: agentic
    inputs: [team_features]
    outputs: [team_quality_score, team_quality_reasoning]
    prompt_template: |
      Assess team quality from GitHub metrics: {team_features}
      Return JSON with team_quality_score (0-100) and team_quality_reasoning.
    output_schema:
      type: object
      required: [team_quality_score, team_quality_reasoning]
      properties:
        team_quality_score: { type: number, minimum: 0, maximum: 100 }
        team_quality_reasoning: { type: string }
    contracts:
      - team_quality_score in 0..100
      - team_quality_reasoning is nonempty
    retry_policy:
      max_attempts: 2
      retry_on: [schema_failure, contract_failure]

  - id: aggregate_scores
    kind: deterministic
    inputs: [mechanism_score, network_score, team_quality_score]
    outputs: [overall_score]
    function_ref: aggregate_scores

edges:
  - from_node: extract_features
    to_node: score_team_quality
  - from_node: score_team_quality
    to_node: aggregate_scores
```

```python
from srg.runtime.loader import load_graph
from srg.runtime.graph_runner import run_graph
from srg.runtime.deterministic_registry import DeterministicRegistry
from srg.kernel.agentic_call import OllamaProvider

graph = load_graph("srg/examples/subnet_scorer.yaml")

registry = DeterministicRegistry()

@registry.register("extract_features")
def extract_features(state):
    data = state["subnet_data"]
    return {"mechanism_features": ..., "network_features": ..., "team_features": ...}

@registry.register("aggregate_scores")
def aggregate_scores(state):
    return {"overall_score": state["team_quality_score"] * 0.15 + ...}

result = run_graph(
    graph, registry,
    llm_provider=OllamaProvider(model="qwen2.5:7b"),
    inputs={"subnet_data": {...}},
)

print(result.status)                    # "success"
print(result.outputs["overall_score"])  # 78.09
print(result.evidence_summary)          # {total_nodes: 7, passed: 7, ...}
```

## CLI

```bash
srg validate graph.yaml           # Validate structure + show execution order
srg run graph.yaml --provider ollama --model qwen2.5:7b --input '{"key": "val"}'
srg diff old.yaml new.yaml        # Semantic diff between two graphs
```

## Running tests

```bash
pip install -e ".[dev]"
pytest tests/ -v          # 281 tests
ruff check srg/ tests/    # Lint
mypy srg/                 # Type check (strict)
```

## Benchmarks

```bash
python benchmarks/token_benchmark.py          # SRG vs Python token efficiency
python benchmarks/llm_editing_experiment.py   # LLM editing: SRG vs Python (5 tasks)
python benchmarks/evidence_debugging_demo.py  # Evidence vs logging (3 scenarios)
```

## Specification

See `docs/srg_spec_v0_3.md` for the full specification, `docs/srg_conformance_v0_3.md` for the conformance checklist, and `docs/SRG_RUTHLESS_REVIEW_RUBRIC.md` for the evaluation rubric.
