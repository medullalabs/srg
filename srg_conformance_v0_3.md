# SRG v0.3 Conformance & Alignment Checklist
## Strict Validation Companion for the Semantic Reasoning Graph Specification

**Status:** Draft  
**Purpose:** Provide a strict checklist for validating whether an implementation remains aligned with the narrowed SRG semantic IR specification.

---

# 1. Usage

This checklist is intended for:

- human reviewers,
- LLM coding agents,
- pull request review,
- CI gatekeeping.

Each item contains:

- **Requirement**
- **Validation Question**
- **Pass Criteria**

An implementation is considered aligned only if it preserves the strict semantic-IR scope defined in the v0.3 specification.

---

# 2. Product Boundary

## 2.1 Semantic IR Identity

**Requirement:** The implementation MUST behave as a semantic reasoning graph system layered over a kernel.

**Validation Question:**
- Is the implementation centered on nodes, edges, contracts, and graph execution rather than orchestration?

**Pass Criteria:**
- Graph models and graph runner are architectural centerpieces

---

## 2.2 No False Framing

**Requirement:** The implementation MUST NOT present itself as a workflow engine, adapter platform, or infrastructure system.

**Validation Question:**
- Do docs and code stay within semantic reasoning graph framing?

**Pass Criteria:**
- No infrastructure or orchestration claims are required for core operation

---

# 3. Scope Control

## 3.1 No Orchestration Drift

**Requirement:** The implementation MUST NOT own orchestration concerns.

**Validation Question:**
- Are scheduling, transport, queueing, and job-control features absent from core?

**Pass Criteria:**
- Core modules do not include workflow, scheduler, queue, or transport abstractions

---

## 3.2 No Adapter Drift

**Requirement:** The implementation MUST NOT introduce an adapter ecosystem.

**Validation Question:**
- Are database, bus, storage, and service adapters excluded from core?

**Pass Criteria:**
- No adapter registry or adapter plugin system exists in core

---

## 3.3 No Reactive Drift

**Requirement:** The implementation MUST NOT become a reactive or event-stream framework.

**Validation Question:**
- Are subscriptions, stream operators, and event graphs absent?

**Pass Criteria:**
- No Rx-style abstractions exist in core

---

# 4. Core Models

## 4.1 Required Graph Models

**Requirement:** Required SRG models MUST exist.

**Validation Question:**
- Are the following models present or equivalent: ReasoningGraph, ReasoningNode, ReasoningEdge, NodeExecutionResult, GraphExecutionResult, EvidenceRecord?

**Pass Criteria:**
- All required models exist and are imported from a clear source of truth

---

## 4.2 Kernel Reuse

**Requirement:** Agentic execution SHOULD reuse kernel primitives.

**Validation Question:**
- Do agentic nodes lower to a kernel-style agentic call instead of inventing a separate execution mechanism?

**Pass Criteria:**
- Yes

---

# 5. Graph Integrity

## 5.1 Node Identity

**Requirement:** Node ids MUST be unique.

**Validation Question:**
- Does validation reject duplicate ids?

**Pass Criteria:**
- Yes

---

## 5.2 Edge Integrity

**Requirement:** Edges MUST reference valid nodes.

**Validation Question:**
- Are invalid references rejected?

**Pass Criteria:**
- Yes

---

## 5.3 Cycle Policy

**Requirement:** Cycles MUST be rejected unless explicitly and narrowly supported.

**Validation Question:**
- Are cycles rejected by default?

**Pass Criteria:**
- Yes

---

# 6. Node Semantics

## 6.1 Required Fields

**Requirement:** Nodes MUST declare id, kind, inputs, and outputs.

**Validation Question:**
- Can a node exist without these fields?

**Pass Criteria:**
- No

---

## 6.2 Kind Restriction

**Requirement:** Core node kinds MUST remain narrow.

**Validation Question:**
- Are node kinds limited to deterministic and agentic in core?

**Pass Criteria:**
- Yes, or additional kinds are clearly non-core and justified

---

## 6.3 Meaning Restriction

**Requirement:** Nodes MUST represent reasoning-relevant computation.

**Validation Question:**
- Do nodes avoid encoding infrastructure concerns?

**Pass Criteria:**
- Yes

---

# 7. Agentic Nodes

## 7.1 Output Schema Requirement

**Requirement:** Agentic nodes MUST declare output schema.

**Validation Question:**
- Can an agentic node execute without output schema?

**Pass Criteria:**
- No

---

## 7.2 Contract Requirement

**Requirement:** Agentic nodes MUST declare contracts.

**Validation Question:**
- Can an agentic node execute without contracts?

**Pass Criteria:**
- No, unless explicitly using a deliberate empty-contract path for testing only

---

## 7.3 Validation Requirement

**Requirement:** Agentic node outputs MUST be validated.

**Validation Question:**
- Are schema and contract checks enforced before success?

**Pass Criteria:**
- Yes

---

# 8. Deterministic Nodes

## 8.1 Helper Scope

**Requirement:** Deterministic nodes MUST remain bounded.

**Validation Question:**
- Are deterministic nodes used for local reasoning support rather than broad general programming?

**Pass Criteria:**
- Yes

---

# 9. Planning and Execution

## 9.1 Acyclic Planning

**Requirement:** Core planning MUST support acyclic graph execution order.

**Validation Question:**
- Does planner produce a valid topological order?

**Pass Criteria:**
- Yes

---

## 9.2 Limited Planning Scope

**Requirement:** Planning MUST NOT become workflow orchestration.

**Validation Question:**
- Does planner limit itself to dependency order and readiness?

**Pass Criteria:**
- Yes

---

# 10. Evidence

## 10.1 Per-Node Evidence

**Requirement:** Evidence MUST be emitted per node execution attempt.

**Validation Question:**
- Does each node attempt produce evidence?

**Pass Criteria:**
- Yes, including failed attempts

---

## 10.2 Graph Summary

**Requirement:** Graph runs SHOULD emit a summary.

**Validation Question:**
- Is there a graph-level result or summary?

**Pass Criteria:**
- Yes

---

# 11. Semantic IR Value

## 11.1 Agent Editability

**Requirement:** The representation SHOULD be LLM-editable.

**Validation Question:**
- Can an LLM plausibly add a node, tighten a contract, or rewire an edge with small localized edits?

**Pass Criteria:**
- Yes

---

## 11.2 Semantic Diff

**Requirement:** The implementation SHOULD support semantic diffing or a path toward it.

**Validation Question:**
- Can graph structure be compared meaningfully beyond raw text diff?

**Pass Criteria:**
- Yes, directly or via a clear utility path

---

# 12. LLM Compatibility

## 12.1 Vocabulary Control

**Requirement:** Novel vocabulary MUST remain small.

**Validation Question:**
- Is the declaration dominated by familiar concepts like nodes, edges, inputs, outputs, schema, contracts, effects, and evidence?

**Pass Criteria:**
- Yes

---

## 12.2 Locality

**Requirement:** Transformations SHOULD be local and inspectable.

**Validation Question:**
- Are validation, planning, execution, and evidence separately testable?

**Pass Criteria:**
- Yes

---

# 13. Agentic Coding Discipline

## 13.1 Correct Build Order

**Requirement:** The implementation SHOULD be built graph-first, not platform-first.

**Validation Question:**
- Was the work done in this order: graph models, validation, planner, deterministic execution, agentic lowering, runner, evidence, semantic diff?

**Pass Criteria:**
- Architecture reflects this order

---

## 13.2 Anti-Pattern Avoidance

**Requirement:** The implementation MUST avoid prohibited drift.

**Validation Question:**
- Does the repo avoid orchestration features, adapters, reactive semantics, custom DSL-first work, or infrastructure abstractions?

**Pass Criteria:**
- Yes

---

# 14. Final Conformance Verdict

## Pass Criteria

An implementation is **SRG v0.3 conformant** only if:

- All MUST requirements pass
- ≥ 85% of SHOULD requirements pass
- No scope-drift violations exist in core modules
- The graph system is usable directly from Python and/or YAML without requiring a custom language layer

---

# 15. Suggested CI Checks

- validate required graph models exist
- validate duplicate node ids fail
- validate invalid edges fail
- validate cycles fail by default
- validate agentic nodes require schema and contracts
- validate planner returns topological order
- validate per-node evidence exists
- validate prohibited core modules do not exist (adapter, workflow, scheduler, stream)

---

# 16. Closing Note

This checklist is intentionally narrow.

Its purpose is to ensure that SRG remains a real semantic reasoning graph system rather than drifting back into a general pipeline or platform description language.

If this checklist is followed, the implementation will remain aligned with the claim SRG actually needs to win:

> **reasoning structure as a composable, inspectable, agent-editable semantic IR**

---
