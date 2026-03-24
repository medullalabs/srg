# SRG MVP Scaffold and Issue Breakdown
## Repo Skeleton + Suggested Issues for Agentic Coding

**Status:** Draft  
**Purpose:** Provide a practical scaffold and issue plan for building an MVP quickly without drifting back into orchestration or language overreach.

---

# 1. MVP Goal

Build an MVP that can:

1. load an SRG graph from YAML,
2. validate graph structure,
3. plan acyclic execution order,
4. execute deterministic nodes,
5. execute agentic nodes via the contract kernel,
6. emit per-node evidence,
7. return a graph execution result.

This is the MVP.
Anything beyond this is optional.

---

# 2. Repository Scaffold

```text
srg/
  pyproject.toml
  README.md

  srg/
    __init__.py

    schemas/
      graph.schema.json
      evidence.schema.json

    models/
      graph.py
      node.py
      edge.py
      evidence.py
      result.py

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
      loader.py

    utils/
      semantic_diff.py

    examples/
      validator_scorer.yaml
      repo_risk.yaml

    tests/
      test_loader.py
      test_graph_validator.py
      test_planner.py
      test_deterministic_registry.py
      test_graph_runner.py
      test_agentic_node.py
      test_semantic_diff.py
```

---

# 3. Suggested Milestones

## Milestone 1 — Core Models and Loader
Deliverable: graph can be loaded into validated models.

## Milestone 2 — Validation and Planning
Deliverable: graph structure can be validated and ordered.

## Milestone 3 — Kernel and Node Execution
Deliverable: deterministic and agentic nodes can run.

## Milestone 4 — Full Graph Runner
Deliverable: full graph execution with evidence.

## Milestone 5 — Semantic Diff and Examples
Deliverable: graph changes become inspectable.

---

# 4. Issue Breakdown

## Issue 1 — Create project skeleton
**Goal:** establish repo layout and package boundaries  
**Files:** `pyproject.toml`, package dirs, test dirs  
**Acceptance Criteria:**
- package installs locally
- test runner configured
- repo layout matches scaffold

---

## Issue 2 — Define core graph models
**Goal:** define `ReasoningGraph`, `ReasoningNode`, `ReasoningEdge`  
**Files:** `models/graph.py`, `models/node.py`, `models/edge.py`  
**Acceptance Criteria:**
- models exist
- node kinds restricted to `deterministic` and `agentic`
- duplicate/invalid field combinations can be validated at model level where practical

---

## Issue 3 — Define result and evidence models
**Goal:** define `NodeExecutionResult`, `GraphExecutionResult`, `EvidenceRecord`  
**Files:** `models/result.py`, `models/evidence.py`  
**Acceptance Criteria:**
- per-node result model exists
- graph-level result model exists
- evidence record has required fields

---

## Issue 4 — Implement YAML loader
**Goal:** load YAML graph into models  
**Files:** `runtime/loader.py`  
**Acceptance Criteria:**
- can load example graph
- invalid YAML or invalid shape fails clearly
- structured error surfaced

---

## Issue 5 — Implement graph validator
**Goal:** validate graph integrity  
**Files:** `runtime/graph_validator.py`  
**Acceptance Criteria:**
- duplicate ids rejected
- invalid edge references rejected
- agentic nodes without schema rejected
- agentic nodes without contracts rejected

---

## Issue 6 — Implement acyclic planner
**Goal:** compute topological execution order  
**Files:** `runtime/planner.py`  
**Acceptance Criteria:**
- valid DAG yields ordered node ids
- cycles fail by default
- planner output deterministic for same graph

---

## Issue 7 — Implement deterministic registry
**Goal:** bind deterministic node `function_ref` to Python callables  
**Files:** `runtime/deterministic_registry.py`  
**Acceptance Criteria:**
- registry supports registration and lookup
- missing callable fails cleanly
- deterministic node can execute simple example function

---

## Issue 8 — Implement kernel models
**Goal:** define kernel-side spec and result models for agentic execution  
**Files:** `kernel/validation.py`, `kernel/contracts.py`, `kernel/retry.py`  
**Acceptance Criteria:**
- output schema validator exists
- simple contract checker exists
- retry policy model exists

---

## Issue 9 — Implement `agentic_call`
**Goal:** provide the core contract-enforced execution primitive  
**Files:** `kernel/agentic_call.py`  
**Acceptance Criteria:**
- accepts spec + inputs
- validates output schema
- checks contracts
- retries on schema/contract failure
- emits evidence per attempt

---

## Issue 10 — Implement graph runner
**Goal:** execute full graph in planner order  
**Files:** `runtime/graph_runner.py`  
**Acceptance Criteria:**
- deterministic nodes run
- agentic nodes lower to kernel `agentic_call`
- outputs flow between nodes
- graph result returned with per-node results

---

## Issue 11 — Implement evidence aggregation
**Goal:** aggregate node evidence into graph summary  
**Files:** `runtime/evidence_aggregator.py`  
**Acceptance Criteria:**
- node evidence collected
- graph summary emitted
- failures preserved

---

## Issue 12 — Add `validator_scorer` example
**Goal:** provide one realistic use case in your domain  
**Files:** `examples/validator_scorer.yaml`  
**Acceptance Criteria:**
- graph includes deterministic + agentic nodes
- graph can run end to end with mocked model backend

---

## Issue 13 — Add `repo_risk` example
**Goal:** show portability beyond validator scoring  
**Files:** `examples/repo_risk.yaml`  
**Acceptance Criteria:**
- graph is small and readable
- example demonstrates decision/risk style reasoning

---

## Issue 14 — Add semantic diff utility
**Goal:** compare graph structure meaningfully  
**Files:** `utils/semantic_diff.py`  
**Acceptance Criteria:**
- added/removed nodes detected
- changed contracts detected
- changed edges detected
- output more meaningful than raw text diff

---

## Issue 15 — Add tests for graph failure modes
**Goal:** pin down strict scope and behavior  
**Files:** `tests/test_graph_validator.py`, `tests/test_graph_runner.py`  
**Acceptance Criteria:**
- invalid graph cases covered
- cycle rejection covered
- agentic schema failure covered
- contract failure retry covered

---

## Issue 16 — Add scope guard tests
**Goal:** keep repo from drifting back into orchestration  
**Files:** `tests/` or lint policy docs  
**Acceptance Criteria:**
- no `adapter` core package
- no `workflow` or `scheduler` core package
- no stream/reactive abstractions in core
- tests or checks enforce narrow scope

---

# 5. Strong Agentic Coding Instructions

These instructions are intended to be copied into prompts.

## Instruction Block

- Preserve strict SRG scope.
- Do not add orchestration, adapters, streaming, or infrastructure concerns.
- Keep node kinds limited to deterministic and agentic.
- Reuse `agentic_call` for all agentic execution.
- Prefer clear Python and Pydantic-style models.
- Keep each PR or issue vertically small.
- Do not invent a DSL.
- Do not over-abstract.
- Graphs describe reasoning structure only.

---

# 6. Suggested Implementation Order

1. Issue 1 — project skeleton  
2. Issue 2 — core graph models  
3. Issue 3 — result/evidence models  
4. Issue 4 — YAML loader  
5. Issue 5 — graph validator  
6. Issue 6 — planner  
7. Issue 7 — deterministic registry  
8. Issue 8 — kernel validation/contracts/retry  
9. Issue 9 — `agentic_call`  
10. Issue 10 — graph runner  
11. Issue 11 — evidence aggregation  
12. Issue 12 — validator example  
13. Issue 15 — failure mode tests  
14. Issue 14 — semantic diff  
15. Issue 13 — repo risk example  
16. Issue 16 — scope guard checks

---

# 7. MVP Definition of Done

The MVP is done when:

- a YAML graph loads successfully,
- invalid graphs fail validation,
- a valid graph produces deterministic execution order,
- deterministic and agentic nodes both run,
- agentic nodes use schema + contracts + retry,
- per-node evidence exists,
- graph-level result exists,
- at least one real example works,
- semantic diff can compare two graph versions,
- no orchestration or adapter drift has entered the core.

---

# 8. Recommended First Demo

**Demo name:** `validator_scorer`

**Why:** It is directly in your world and proves the “reasoning structure as IR” thesis.

**Suggested node chain:**
1. `extract_features` — deterministic  
2. `assess_team_quality` — agentic  
3. `assess_innovation` — agentic  
4. `combine_scores` — deterministic  
5. `summarize_evidence` — deterministic or agentic

This is enough to show:
- composition
- contracts
- evidence
- semantic diff potential
- LLM editability

---

# 9. Final Guidance

The fastest path back on track is:

- keep the kernel narrow,
- keep the graph semantic,
- keep the examples real,
- keep the issue slices small,
- and refuse all temptations to turn SRG into infrastructure.

If this scaffold is followed, you can get to a meaningful MVP quickly without circling the drain again.

---
