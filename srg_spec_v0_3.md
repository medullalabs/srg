# SRG Semantic Reasoning Graph Specification — v0.3
## Strictly Scoped North-Star Specification for Semantic IR over Reasoning Structure

**Status:** Draft  
**Intended Audience:** human architects, agentic coding systems, library engineers, runtime engineers  
**Purpose:** restore the project to a true semantic IR focus by defining SRG as a narrowly scoped semantic reasoning graph model layered over a contract-enforced agentic execution kernel.

---

# Status of This Memo

This document specifies a v0.3 architecture and implementation contract for SRG. Distribution of this memo is unlimited.

This document uses the key words **MUST**, **MUST NOT**, **REQUIRED**, **SHALL**, **SHALL NOT**, **SHOULD**, **SHOULD NOT**, **RECOMMENDED**, **NOT RECOMMENDED**, **MAY**, and **OPTIONAL** as described in RFC 2119 and RFC 8174 when, and only when, they appear in all capitals.

---

# Abstract

SRG is a **semantic reasoning graph** representation for describing meaningful computation in a form that is:

- explicit,
- composable,
- inspectable,
- agent-modifiable,
- lowerable to execution,
- and constrained enough for present-day LLM use.

A conformant SRG implementation is NOT:

- a workflow engine,
- a reactive stream system,
- an adapter marketplace,
- a generalized orchestration framework,
- or a replacement for Python.

A conformant SRG implementation SHALL provide a standard mechanism for:

- representing reasoning units as typed nodes,
- representing semantic data dependencies as edges,
- attaching contracts and effects to nodes,
- composing deterministic and agentic reasoning steps,
- emitting execution evidence,
- enabling structural edits and semantic diffs,
- and lowering graphs into a narrow execution runtime built around validated agentic calls.

This document intentionally rejects infrastructure ownership and declarative I/O ambitions. SRG concerns **reasoning structure**, not infrastructure topology.

---

# 1. Introduction

Earlier attempts to generalize the system into orchestration or declarative pipeline semantics weakened the original semantic IR thesis. The value of SRG is not that it can describe all software systems. The value of SRG is that it can describe **reasoning-centric computation** in a way that both humans and current LLMs can consume effectively.

The core processing model established by this document is:

```text
SRG graph -> graph validation -> execution plan -> kernel execution -> evidence
```

The graph is the source of truth for reasoning structure. Infrastructure remains outside the graph.

---

# 2. Scope

## 2.1 In Scope

A conformant SRG implementation MUST support:

- semantic nodes representing reasoning units,
- edges representing semantic data dependencies,
- contracts on node outputs,
- declared effects,
- deterministic nodes,
- agentic nodes,
- graph validation,
- graph composition for small reasoning systems,
- evidence emission per node execution,
- lowering to a narrow runtime built on a contract-enforced agentic kernel.

## 2.2 Out of Scope

A conformant SRG implementation MUST NOT attempt to define or own:

- workflow orchestration,
- transport abstractions,
- external adapter ecosystems,
- database/query backends,
- event streaming semantics,
- distributed job scheduling,
- message bus control,
- secret management platforms,
- generalized microservice deployment,
- Kubernetes or infrastructure lifecycle,
- universal programming-language replacement.

## 2.3 Embedding Rule

SRG SHALL be embedded in a host language runtime. Python is REQUIRED for the first implementation target.

---

# 3. Design Objective

The objective of SRG is to provide a **semantic IR for reasoning structure** that is:

- more explicit than handwritten glue code,
- more modifiable by LLMs than raw Python,
- more portable than ad hoc helper functions,
- and more disciplined than free-form prompt chaining.

A conformant implementation MUST privilege:

- semantic clarity,
- current LLM consumability,
- graph-level editability,
- contract enforcement,
- evidence emission,
- and minimal vocabulary expansion.

---

# 4. Overarching Value Proposition

The value of SRG lies in the following:

1. **Reasoning structure as data**
2. **Composable semantic nodes**
3. **Contract-aware graph execution**
4. **Explicit deterministic vs agentic boundaries**
5. **Semantic diffs over computation structure**
6. **Portable, agent-editable reasoning artifacts**
7. **Layering over a reusable contract kernel**

SRG does NOT claim that every computation should be a graph. It claims only that reasoning-centric, agent-modifiable systems benefit from an explicit semantic representation.

---

# 5. Relationship to the Agentic Contract Kernel

SRG is layered over the narrower contract kernel.

The kernel provides:

- `agentic_call`,
- output validation,
- contract checking,
- retry,
- evidence emission.

SRG provides:

- node semantics,
- graph composition,
- reasoning structure,
- graph validation,
- graph execution order,
- semantic diffs and editability.

The kernel is the execution primitive. SRG is the semantic structure above it.

---

# 6. Architectural Model

A conformant SRG implementation MUST separate the system into three layers:

1. **Graph Declaration Layer**
2. **Graph Validation and Planning Layer**
3. **Kernel Execution Layer**

## 6.1 Graph Declaration Layer

The declaration layer defines:

- nodes,
- edges,
- contracts,
- effects,
- graph metadata.

## 6.2 Graph Validation and Planning Layer

The planning layer validates graph shape, contract completeness, edge integrity, and execution order.

## 6.3 Kernel Execution Layer

The execution layer runs deterministic nodes directly and agentic nodes via the contract-enforced kernel.

---

# 7. Core Primitive

The core primitive of SRG is the **Reasoning Node**.

A conformant implementation MUST support two primary node kinds:

- `deterministic`
- `agentic`

All graph semantics SHALL be expressed through these node kinds and explicit edges.

---

# 8. Serialization and Representation

## 8.1 Required Representations

A conformant implementation MUST support at least:

- Python model/API usage
- YAML or JSON serializable graph declaration

## 8.2 Surface Syntax Restriction

A custom DSL MAY be added later. It MUST NOT be required for the first conformant implementation.

## 8.3 Priority Rule

The Python model/API and the structured serialized graph are REQUIRED.
Custom syntax is OPTIONAL.

---

# 9. Object Model

A conformant SRG implementation MUST define or provide equivalent models for:

- `ReasoningGraph`
- `ReasoningNode`
- `ReasoningEdge`
- `NodeContract`
- `NodeEffect`
- `GraphMetadata`
- `ExecutionPlan`
- `NodeExecutionResult`
- `GraphExecutionResult`
- `EvidenceRecord`

It SHOULD reuse kernel models where appropriate, including:

- `AgenticCallSpec`
- `AgenticResult`
- `ValidationFailure`

---

# 10. ReasoningGraph Requirements

## 10.1 Required Fields

A `ReasoningGraph` MUST include:

- `name`
- `nodes`
- `edges`

It SHOULD include:

- `metadata`
- `version`
- `description`
- `tags`

## 10.2 Graph Integrity

A conformant implementation MUST reject graphs with:

- missing node references,
- duplicate node identifiers,
- invalid edge targets,
- cycles unless cycles are explicitly and narrowly supported.

Cycles are NOT REQUIRED in v0.3 and are NOT RECOMMENDED.

---

# 11. ReasoningNode Requirements

## 11.1 Required Fields

Each `ReasoningNode` MUST include:

- `id`
- `kind`
- `inputs`
- `outputs`

It SHOULD include:

- `contracts`
- `effects`
- `description`
- `metadata`

## 11.2 Supported Node Kinds

A conformant implementation MUST support:

- `deterministic`
- `agentic`

Additional node kinds are NOT RECOMMENDED in v0.3.

## 11.3 Node Meaning

A node MUST represent a unit of **reasoning-relevant computation**, not infrastructure configuration.

---

# 12. ReasoningEdge Requirements

## 12.1 Required Fields

Each `ReasoningEdge` MUST include:

- `from_node`
- `to_node`

It SHOULD include:

- `from_output`
- `to_input`
- `kind`

## 12.2 Edge Semantics

Edges SHALL represent semantic data dependency, not transport or deployment linkage.

The default edge kind is `data_flow`.

---

# 13. Deterministic Node Semantics

## 13.1 Purpose

Deterministic nodes provide bounded, inspectable computation local to the graph.

## 13.2 Allowed Uses

Deterministic nodes are RECOMMENDED for:

- feature extraction,
- normalization,
- arithmetic scoring,
- output formatting,
- evidence formatting,
- light transformations around agentic reasoning.

## 13.3 Prohibited Drift

Deterministic nodes MUST NOT be used as a backdoor for turning SRG into a general-purpose programming language in v0.3.

---

# 14. Agentic Node Semantics

## 14.1 Purpose

Agentic nodes encapsulate LLM-driven reasoning steps with explicit contracts.

## 14.2 Required Fields

Each `agentic` node MUST declare or derive:

- prompt template or prompt strategy,
- output schema,
- contracts,
- retry policy or default retry policy.

## 14.3 Validation Requirement

Agentic node outputs MUST be validated against output schema and contracts before they are considered successful.

## 14.4 Free-Form Output Restriction

Free-form unvalidated text MUST NOT be treated as a successful final output unless explicitly modeled as schema and still contract-checked.

---

# 15. Contracts

## 15.1 Required Support

A conformant implementation MUST support contracts on node outputs.

## 15.2 Minimum Contract Classes

The implementation MUST support at least:

- range constraints,
- required field presence,
- nonempty field constraints,
- simple cross-field constraints where practical.

## 15.3 Failure Semantics

Contract violations MUST produce a validation failure artifact and SHALL fail node execution unless retry succeeds.

---

# 16. Effects

## 16.1 Explicit Effects

A conformant implementation MUST support explicit effect declaration.

## 16.2 Effect Purpose

Effects exist to mark capability boundaries such as:

- reads external context,
- emits evidence,
- writes summary,
- invokes model.

## 16.3 Restriction

Effects MUST remain declarative and MUST NOT expand into an infrastructure adapter vocabulary.

---

# 17. Graph Validation

## 17.1 Required Validation Passes

A conformant implementation MUST validate at least:

- graph integrity,
- node uniqueness,
- edge validity,
- node input/output consistency,
- contract presence for agentic nodes,
- output schema presence for agentic nodes.

## 17.2 Validation Output

Validation MUST produce structured failures, not only free-form text.

---

# 18. Planning and Execution Order

## 18.1 Required Planning Behavior

The implementation MUST compute a valid execution order for acyclic graphs.

## 18.2 Planning Scope

Planning in v0.3 SHALL be limited to dependency ordering and simple execution readiness.

Planning MUST NOT introduce workflow-engine semantics such as distributed scheduling, queue orchestration, or temporal triggers.

---

# 19. Execution Model

## 19.1 Deterministic Execution

Deterministic nodes SHALL execute via host-language callables or equivalent runtime bindings.

## 19.2 Agentic Execution

Agentic nodes SHALL execute via the contract-enforced kernel.

## 19.3 Node Result

Each node execution MUST yield a structured result containing:

- status,
- outputs or failure,
- evidence,
- timing metadata if available.

## 19.4 Graph Result

A graph run MUST yield a structured graph execution result containing:

- overall status,
- per-node results,
- final outputs,
- graph-level evidence summary.

---

# 20. Evidence Requirements

## 20.1 Required Evidence Support

A conformant implementation MUST emit evidence for each node execution attempt.

## 20.2 Minimum Evidence Fields

Each evidence record MUST include:

- graph name,
- node id,
- attempt number,
- status,
- timestamp,
- validation outcome.

It SHOULD include:

- duration,
- prompt hash,
- input hash,
- output hash,
- retry reason,
- contract summary.

## 20.3 Evidence Stability

Evidence SHOULD be stable enough to support diffing, audit, and debugging.

---

# 21. LLM Compatibility Requirements

## 21.1 Vocabulary Discipline

A conformant implementation MUST minimize novel vocabulary.

## 21.2 Familiarity Rule

The graph declaration form SHOULD use concepts current LLMs already understand:

- node
- edge
- input
- output
- schema
- contract
- effect
- retry
- evidence

## 21.3 Avoidance Rule

Implementations MUST NOT require the LLM to learn a large custom operational vocabulary for infrastructure, adapters, or orchestration.

---

# 22. Conformance Requirements for Agentic Coding

## 22.1 Source of Truth

The SRG schemas and models SHALL be the source of truth. Helper code MUST conform to them.

## 22.2 Required Implementation Order

Agentic coding systems SHOULD proceed in this order:

1. define graph models,
2. define kernel models if not already present,
3. implement graph validation,
4. implement deterministic node bindings,
5. implement agentic node lowering to kernel,
6. implement execution ordering,
7. implement graph runner,
8. implement evidence aggregation,
9. implement examples,
10. implement semantic diff helpers.

## 22.3 Prohibited Early Work

Agentic coding systems MUST NOT begin with:

- custom DSL parser,
- orchestration features,
- adapter plugins,
- reactive/event semantics,
- microservice deployment abstractions,
- generalized compiler pipeline ambitions.

---

# 23. Strong Agentic Hints

## 23.1 First Milestone

The first milestone MUST include:

- `ReasoningGraph`
- `ReasoningNode`
- `ReasoningEdge`
- graph validator
- acyclic execution planner
- deterministic node execution
- agentic node lowering to kernel
- one working graph example
- per-node evidence emission

## 23.2 Second Milestone

The second milestone SHOULD include:

- graph-level result model
- semantic diff utility
- graph composition helper
- YAML round-trip support
- tests for node failure and graph failure

## 23.3 Third Milestone

The third milestone MAY include:

- small reusable node catalog
- graph linting rules
- simple graph visualization export

## 23.4 Anti-Patterns

Agentic coding systems SHOULD avoid:

- building workflow semantics,
- building adapters,
- building scheduler abstractions,
- embedding too much Python inside graph declarations,
- pretending edges model infrastructure,
- using graphs for non-reasoning concerns.

---

# 24. Suggested Repository Layout

```text
srg/
  schemas/
    graph.schema.json
    node.schema.json
    edge.schema.json
    evidence.schema.json
  models/
    graph.py
    node.py
    edge.py
    result.py
    evidence.py
  kernel/
    agentic_call.py
    contracts.py
    retry.py
    validation.py
  runtime/
    graph_validator.py
    planner.py
    deterministic_registry.py
    graph_runner.py
    evidence_aggregator.py
  utils/
    semantic_diff.py
    graph_compose.py
  examples/
    validator_scorer.yaml
    repo_risk.yaml
  tests/
    test_graph_validator.py
    test_planner.py
    test_graph_runner.py
    test_semantic_diff.py
```

---

# 25. Example Minimal Graph

```yaml
graph:
  name: validator_scorer
  nodes:
    - id: extract_features
      kind: deterministic
      inputs:
        - repo_data
        - metrics
      outputs:
        - features

    - id: assess_team
      kind: agentic
      inputs:
        - features
      outputs:
        - team_score
        - rationale
      output_schema:
        type: object
        required: [team_score, rationale]
        properties:
          team_score: {type: integer}
          rationale: {type: string}
      contracts:
        - team_score in 0..100
        - rationale is nonempty

    - id: final_score
      kind: deterministic
      inputs:
        - team_score
      outputs:
        - score

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

# 26. Evaluation Criteria

A conformant v0.3 implementation SHOULD be evaluated by whether:

- graphs are readable by humans,
- graphs are editable by LLMs without large custom prompting overhead,
- deterministic and agentic nodes compose cleanly,
- graph validation catches structural errors,
- graph execution is predictable,
- per-node evidence exists,
- graph structure can be semantically diffed,
- use cases such as scoring and decision systems become easier to modify than equivalent raw Python.

---

# 27. Security and Safety Considerations

## 27.1 Blind Trust Prohibition

Agentic node output MUST NOT be trusted without validation.

## 27.2 Graph Drift Risk

The main design risk is drift back into infrastructure or orchestration description. Such drift SHOULD be treated as a design failure.

## 27.3 Sensitive Data

Implementations SHOULD support hashing or redaction policies for sensitive prompts and inputs.

---

# 28. IANA Considerations

This document has no IANA actions.

---

# 29. References

## 29.1 Normative References

- RFC 2119, “Key words for use in RFCs to Indicate Requirement Levels”
- RFC 8174, “Ambiguity of Uppercase vs Lowercase in RFC 2119 Key Words”

---

# 30. Final Directive

SRG v0.3 SHALL be treated as a **semantic IR for reasoning structure**.

It is NOT a workflow engine.
It is NOT a reactive system.
It is NOT an adapter framework.
It is NOT infrastructure description.

Its purpose is to make one class of thing explicit, composable, and agent-editable:

> **reasoning-centric computation with contracts, semantic structure, and evidence**

Everything else is subordinate to that purpose.

---
