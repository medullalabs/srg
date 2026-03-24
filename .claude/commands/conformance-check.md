Run a full SRG conformance check against the spec, conformance checklist, and ruthless review rubric.

## Instructions

### Step 1: Run Tests

Run the full test suite to establish a baseline:
```bash
.venv/bin/pytest tests/ -v
.venv/bin/ruff check srg/ tests/
.venv/bin/mypy srg/
```

### Step 2: Spec Conformance (`docs/srg_conformance_v0_3.md`)

Read `docs/srg_conformance_v0_3.md` and evaluate each section against the current codebase. For each requirement:

1. Read the relevant source code to verify the requirement is met
2. Check if tests exist that enforce the requirement
3. Score as **PASS**, **FAIL**, or **PARTIAL**

Group results by section:
- Product Boundary (2.1-2.2)
- Scope Control (3.1-3.3)
- Core Models (4.1-4.2)
- Graph Integrity (5.1-5.3)
- Node Semantics (6.1-6.3)
- Agentic Nodes (7.1-7.3)
- Deterministic Nodes (8.1)
- Planning and Execution (9.1-9.2)
- Evidence (10.1-10.2)
- Semantic IR Value (11.1-11.2)
- LLM Compatibility (12.1-12.2)
- Agentic Coding Discipline (13.1-13.2)

Calculate: total MUST requirements passed, total SHOULD requirements passed, overall conformance verdict per Section 14.

### Step 3: Ruthless Review Rubric (`docs/SRG_RUTHLESS_REVIEW_RUBRIC.md`)

Read `docs/SRG_RUTHLESS_REVIEW_RUBRIC.md` and score all 8 categories (0/1/2 each):

1. **Structural Editability** — Check example graphs, test cases for add/remove/rewire operations
2. **Semantic Diff Superiority** — Check `semantic_diff()` implementation and test coverage
3. **Agent Editability** — Check if LLM editing benchmarks exist (Issue #2)
4. **Contract Discipline** — Check contract enforcement in kernel, validator, and e2e tests
5. **Composability** — Check if `compose_graphs()` exists and is tested
6. **Evidence Usefulness** — Check evidence records, aggregator, and whether debugging scenarios are demonstrated
7. **Narrowness Discipline** — Check scope guards, module names, NodeKind values
8. **Use-Case Undeniability** — Check real-world examples and Python-vs-SRG comparisons

For each category, cite specific files and test results as evidence.

### Step 4: Output Report

```
## SRG Conformance Report — {date}

### Test Results
- pytest: {passed}/{total}
- ruff: {status}
- mypy: {status}

### Spec Conformance (`docs/srg_conformance_v0_3.md`)
| Section | Requirement | Status | Evidence |
|---------|-------------|--------|----------|

**MUST requirements:** {passed}/{total}
**SHOULD requirements:** {passed}/{total}
**Verdict:** {CONFORMANT / NON-CONFORMANT} per Section 14

### Ruthless Review Rubric (`docs/SRG_RUTHLESS_REVIEW_RUBRIC.md`)
| # | Category | Score | Evidence | To Improve |
|---|----------|-------|----------|------------|

**Total: {score}/16 — {interpretation}**

### Gap Analysis
Ordered list of the highest-impact gaps between current state and full conformance/rubric score, with the specific issue or work needed to close each gap.

### Recommended Next Steps
Top 3 actions to improve conformance and rubric score, referencing specific GitHub issues where applicable.
```
