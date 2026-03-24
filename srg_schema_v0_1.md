# SRG Schema v0.1
## Minimal Semantic Reasoning Graph Schema for MVP

**Status:** Draft  
**Purpose:** Define the minimum schema required to implement an MVP of Semantic Reasoning Graphs.

---

# 1. Design Constraints

The MVP schema MUST support:

- deterministic nodes
- agentic nodes
- explicit edges
- output schema for agentic nodes
- contracts
- optional effects
- graph metadata

The MVP schema MUST NOT support:

- infrastructure adapters
- reactive/event semantics
- transport layers
- scheduling metadata beyond dependency order
- generalized plugin ecosystems

---

# 2. Canonical Shape

```yaml
graph:
  name: string
  description: string?
  version: string?
  metadata: object?
  nodes: [ReasoningNode]
  edges: [ReasoningEdge]
```

---

# 3. ReasoningNode

## 3.1 Canonical Shape

```yaml
- id: string
  kind: deterministic | agentic
  description: string?
  inputs: [string]
  outputs: [string]
  function_ref: string?              # deterministic only
  prompt_template: string?           # agentic only
  output_schema: object?             # agentic only
  contracts: [string]?
  effects: [string]?
  retry_policy: object?
  metadata: object?
```

## 3.2 Field Rules

### `id`
- REQUIRED
- MUST be unique within graph

### `kind`
- REQUIRED
- MUST be one of:
  - `deterministic`
  - `agentic`

### `inputs`
- REQUIRED
- list of symbolic input names consumed by the node

### `outputs`
- REQUIRED
- list of symbolic output names produced by the node

### `function_ref`
- OPTIONAL
- SHOULD be present for deterministic nodes
- MUST NOT be required for agentic nodes

### `prompt_template`
- OPTIONAL
- SHOULD be present for agentic nodes
- MUST NOT be required for deterministic nodes

### `output_schema`
- REQUIRED for agentic nodes
- MUST be absent or ignored for deterministic nodes unless explicitly used for validation

### `contracts`
- REQUIRED for agentic nodes
- OPTIONAL for deterministic nodes

### `effects`
- OPTIONAL
- examples:
  - `invoke_model`
  - `emit_evidence`
  - `read_context`

### `retry_policy`
- OPTIONAL
- if absent, default policy MAY be inherited from runtime

---

# 4. ReasoningEdge

## 4.1 Canonical Shape

```yaml
- from_node: string
  to_node: string
  from_output: string?
  to_input: string?
  kind: data_flow?
```

## 4.2 Field Rules

### `from_node`
- REQUIRED
- MUST reference existing node id

### `to_node`
- REQUIRED
- MUST reference existing node id

### `from_output`
- OPTIONAL
- if present, SHOULD match an output declared by `from_node`

### `to_input`
- OPTIONAL
- if present, SHOULD match an input declared by `to_node`

### `kind`
- OPTIONAL
- default value: `data_flow`

---

# 5. Retry Policy

## 5.1 Canonical Shape

```yaml
retry_policy:
  max_attempts: integer
  retry_on: [schema_failure, contract_failure]
```

## 5.2 MVP Support

The MVP SHOULD support only:
- `schema_failure`
- `contract_failure`

---

# 6. Output Schema

The MVP SHOULD use JSON-Schema-like structure for agentic node outputs.

## 6.1 Example

```yaml
output_schema:
  type: object
  required: [score, rationale]
  properties:
    score:
      type: integer
    rationale:
      type: string
```

---

# 7. Contracts

The MVP MAY use string-based contracts for simplicity.

## 7.1 Supported Contract Forms

The MVP SHOULD support at least:
- `field in a..b`
- `field is nonempty`
- `field exists`

## 7.2 Example

```yaml
contracts:
  - score in 0..100
  - rationale is nonempty
```

---

# 8. Minimal Graph Example

```yaml
graph:
  name: validator_scorer
  description: minimal scoring graph
  version: "0.1"
  nodes:
    - id: extract_features
      kind: deterministic
      inputs: [repo_data, metrics]
      outputs: [features]
      function_ref: extract_features

    - id: assess_team
      kind: agentic
      inputs: [features]
      outputs: [team_score, rationale]
      prompt_template: |
        Assess the team quality based on the provided features.
        Return a score and rationale.
      output_schema:
        type: object
        required: [team_score, rationale]
        properties:
          team_score:
            type: integer
          rationale:
            type: string
      contracts:
        - team_score in 0..100
        - rationale is nonempty
      effects:
        - invoke_model
        - emit_evidence
      retry_policy:
        max_attempts: 2
        retry_on: [schema_failure, contract_failure]

    - id: final_score
      kind: deterministic
      inputs: [team_score]
      outputs: [score]
      function_ref: identity_score

  edges:
    - from_node: extract_features
      to_node: assess_team
      from_output: features
      to_input: features

    - from_node: assess_team
      to_node: final_score
      from_output: team_score
      to_input: team_score
```

---

# 9. Validation Rules

The MVP validator MUST reject:

- duplicate node ids
- missing node references in edges
- cycles by default
- agentic node missing output schema
- agentic node missing contracts
- edges referencing unknown outputs or inputs when specified

---

# 10. MVP Runtime Mapping

- `deterministic` node -> Python callable by `function_ref`
- `agentic` node -> kernel `agentic_call(...)`
- graph execution -> topological order
- node evidence -> emitted after each node execution attempt
- graph result -> collected per-node results + final outputs

---

# 11. Final Guidance

This schema is intentionally small.

Its purpose is not to describe every system.
Its purpose is to get an MVP back onto the semantic IR track quickly and safely.

---
