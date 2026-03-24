# SRG -- Semantic Reasoning Graph

SRG is a narrowly scoped semantic reasoning graph library for describing meaningful computation as typed nodes connected by explicit data-flow edges. It supports two node kinds -- **deterministic** (pure Python functions) and **agentic** (contract-enforced LLM calls with structured JSON output, schema validation, and automatic retry). Every execution emits evidence records for auditability. SRG concerns **reasoning structure**, not infrastructure topology.

## What SRG is NOT

- **Not a workflow engine.** No task queues, no scheduling, no DAG orchestration.
- **Not an adapter marketplace.** No plugin system, no connectors, no transports.
- **Not a reactive stream system.** No event streams, no pub/sub, no backpressure.
- **Not a generalized orchestration framework.** No service mesh, no deployment.
- **Not a replacement for Python.** SRG graphs describe reasoning steps; Python does the work.

## Quick example -- a graph in YAML

```yaml
name: validator_scorer
description: Validate and score input data.

nodes:
  - id: validate_input
    kind: deterministic
    inputs: [raw_data]
    outputs: [validated_data]
    function_ref: validate_input_fn

  - id: score_data
    kind: agentic
    inputs: [validated_data]
    outputs: [score, explanation]
    prompt_template: |
      Score this data: {validated_data}
    output_schema:
      type: object
      properties:
        score: { type: number, minimum: 0, maximum: 100 }
        explanation: { type: string }
      required: [score, explanation]
    contracts:
      - score >= 0
      - score <= 100
      - explanation is nonempty
    retry_policy:
      max_attempts: 2
      retry_on: [schema_failure, contract_failure]

edges:
  - from_node: validate_input
    to_node: score_data
```

## Python API

```python
from srg import (
    load_graph,
    run_graph,
    DeterministicRegistry,
    OllamaProvider,
)

# Load graph from YAML
graph = load_graph("examples/validator_scorer.yaml")

# Register deterministic functions
registry = DeterministicRegistry()

@registry.register("validate_input_fn")
def validate_input_fn(state):
    return {"validated_data": state["raw_data"].strip()}

# Run with an LLM provider
result = run_graph(
    graph,
    registry,
    llm_provider=OllamaProvider(model="llama3"),
    inputs={"raw_data": "  sample data  "},
)

print(result.status)       # "success"
print(result.outputs)      # {"validated_data": ..., "score": 85, "explanation": "..."}
```

## Running tests

```bash
# Install in dev mode
pip install -e ".[dev]"

# Run the test suite
pytest tests/ -v

# Lint and type check
ruff check srg/ tests/
mypy srg/
```

## Specification

See `srg_spec_v0_3.md` for the full specification and `srg_conformance_v0_3.md` for the conformance checklist.
