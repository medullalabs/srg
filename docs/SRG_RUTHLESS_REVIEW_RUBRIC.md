# SRG Ruthless Review Rubric
## Determining Whether SRG Is a Real Semantic IR or Just Python in Disguise

**Status:** Draft  
**Purpose:** Provide a strict, outcome-oriented rubric to evaluate whether SRG delivers real value as a semantic reasoning graph system.

---

# 1. The Core Question

> Would a serious engineer choose SRG over plain Python for reasoning-centric systems?

If the answer is not clearly **yes** on multiple dimensions, SRG is not yet justified.

---

# 2. Scoring Model

Each category is scored:

- **0 = No advantage**
- **1 = Plausible but unproven**
- **2 = Clearly demonstrated**

**Total possible score: 16**

## Interpretation

- **13–16:** Real semantic IR advantage  
- **9–12:** Promising but not yet undeniable  
- **5–8:** Mostly a convenience wrapper  
- **0–4:** Abstraction without clear value  

---

# 3. Evaluation Categories

## 3.1 Structural Editability

**Question:** Is changing reasoning structure easier in SRG than Python?

### Test Cases
- Add a node
- Remove a node
- Rewire dependencies
- Swap deterministic → agentic
- Change scoring composition

### Pass Criteria (Score 2)
- Changes are localized and obvious
- Minimal breakage risk
- Graph remains readable

### Fail Criteria (Score 0)
- Same change is equally easy or easier in Python

---

## 3.2 Semantic Diff Superiority

**Question:** Can SRG show *meaningful* changes better than text diff?

### Required Capabilities
- Node added/removed
- Contract changed
- Edge rewired
- Node type changed (deterministic → agentic)

### Pass Criteria (Score 2)
- Diff clearly communicates semantic changes

### Fail Criteria (Score 0)
- Git diff on Python is equally or more useful

---

## 3.3 Agent Editability (LLM Advantage)

**Question:** Can LLMs modify SRG more reliably than Python?

### Measure
- Prompt length required
- Number of correction cycles
- Structural breakage rate

### Pass Criteria (Score 2)
- LLM edits are stable and require fewer iterations

### Fail Criteria (Score 0)
- Same fragility as Python editing

---

## 3.4 Contract Discipline

**Question:** Does SRG enforce contracts as a standard pattern?

### Required Behavior
- Schema validation
- Contract enforcement
- Retry handling
- Evidence emission

### Pass Criteria (Score 2)
- Contracts are first-class and consistently enforced

### Fail Criteria (Score 0)
- Contracts feel optional or ad hoc

---

## 3.5 Composability of Reasoning Units

**Question:** Can reasoning graphs be composed cleanly?

### Test Cases
- Combine two graphs
- Reuse a node across graphs
- Extend a graph without rewriting it

### Pass Criteria (Score 2)
- Composition is explicit and safe

### Fail Criteria (Score 0)
- Composition requires manual plumbing

---

## 3.6 Evidence Usefulness

**Question:** Does evidence materially improve debugging and analysis?

### Required Insights
- Which node failed
- Why it failed (schema vs contract)
- Retry behavior
- Differences between runs

### Pass Criteria (Score 2)
- Evidence provides actionable insight

### Fail Criteria (Score 0)
- Equivalent to logs

---

## 3.7 Narrowness Discipline

**Question:** Does SRG stay within its defined scope?

### Must NOT Include
- Workflow orchestration
- Adapter ecosystems
- Reactive/event systems
- Infrastructure abstractions

### Pass Criteria (Score 2)
- New features reinforce semantic reasoning only

### Fail Criteria (Score 0)
- Drift toward platform or infrastructure concerns

---

## 3.8 Use-Case Undeniability

**Question:** Is there at least one domain where SRG is clearly superior?

### Target Example
- Validator scoring
- Risk analysis
- Decision systems

### Pass Criteria (Score 2)
- SRG is obviously better than Python for this use case

### Fail Criteria (Score 0)
- Example is nice but not compelling

---

# 4. Required Demonstrations

To validate SRG, the following SHOULD be demonstrated:

## 4.1 Python vs SRG Comparison

Same system implemented in:
- Python
- SRG

Compare:
- modification effort
- clarity
- diff quality

---

## 4.2 LLM Editing Benchmark

Give identical tasks:
- modify Python system
- modify SRG graph

Measure:
- prompt size
- iterations
- correctness

---

## 4.3 Semantic Diff Demo

Show:
- graph v1
- graph v2

Output:
- structured semantic diff

---

# 5. Failure Conditions

SRG should be reconsidered if:

- It does not outperform Python in structural edits
- Semantic diff is not meaningfully better
- LLM editing is not improved
- Contracts are not consistently enforced
- The system drifts into orchestration or infrastructure

---

# 6. Final Statement

SRG is justified only if it proves:

> Reasoning structure is a better authoring and modification surface than Python for a meaningful class of systems.

If this is not demonstrated, SRG should collapse back into a simpler library around agentic execution primitives.

---

# 7. Guidance for Maintainers

When evaluating changes:

- Ask: does this strengthen semantic reasoning?
- Reject: anything that introduces infrastructure concerns
- Prefer: simplicity over flexibility
- Protect: graph as the source of truth

---

# 8. Closing Note

This rubric is intentionally strict.

It exists to prevent SRG from becoming:
- a workflow engine,
- a platform,
- or a diluted abstraction.

It enforces the only claim that matters:

> SRG must make reasoning systems meaningfully better to build, modify, and understand.

---
