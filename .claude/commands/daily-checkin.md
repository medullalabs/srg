Perform a daily check-in on the SRG project by reviewing open GitHub issues and providing a prioritized status report.

## Instructions

### Step 1: Fetch Issues

**Primary method — GitHub MCP:**
First, use `ToolSearch` to fetch the `mcp__github__list_issues` tool (it is a deferred tool that must be loaded before use). Then call `mcp__github__list_issues` with `owner: "medullalabs"`, `repo: "semantic-reasoning-graph"`, `state: "OPEN"` to list all open issues.

**Fallback — gh CLI:**
If the MCP tools fail or are unavailable, fall back to the `gh` CLI:
```
gh issue list -R medullalabs/semantic-reasoning-graph --state open --limit 50 --json number,title,labels,milestone,assignees,createdAt,updatedAt
```

### Step 2: Analyze and Prioritize

Review all open issues and organize them by urgency:

1. **Blocked / Stale**: Issues that haven't been updated in 7+ days, or issues whose dependencies are unmet
2. **Ready to Work**: Issues whose dependencies are all closed/completed — these are actionable now
3. **In Progress**: Issues with assignees or recent activity
4. **Upcoming**: Issues whose dependencies are still open

For each issue, check its dependencies (listed in the issue body as `#N` references) against the current issue state to determine if it's unblocked.

### Step 3: Check Milestone Progress

For each milestone, report:
- Total issues
- Closed issues
- Open issues that are ready to work
- Blocking issues (open issues that other issues depend on)

### Step 4: Rubric Score

Read `docs/SRG_RUTHLESS_REVIEW_RUBRIC.md` and score the current state of the codebase against all 8 categories (0/1/2 each). For each category:

1. Check what evidence exists in the codebase (tests, examples, implementations)
2. Assign a score based on the rubric's pass/fail criteria
3. Note what would move the score up

Compare against the previous score if one exists in memory. Flag any regressions.

### Step 5: Output Report

Present the report in this format:

```
## SRG Daily Check-in — {date}

### Rubric Score: {total}/16 — {interpretation}
| Category | Score | Evidence | To Improve |
|----------|-------|----------|------------|

### Milestone Progress
| Milestone | Open | Closed | Ready | Blocked |
|-----------|------|--------|-------|---------|

### Ready to Work (prioritized)
Issues that can be picked up right now, ordered by dependency impact (issues that unblock the most other work first).

### Recently Updated
Issues with activity in the last 48 hours.

### Blocked / Needs Attention
Issues that are stale or have unresolved blockers.

### Recommended Focus
Top 3 issues to work on next, with reasoning based on:
- Rubric score impact (what moves the score toward 13+)
- Dependency chain impact (what unblocks the most downstream work)
- Milestone priority (earlier milestones first)
- Spec conformance (`docs/srg_spec_v0_3.md` and `docs/srg_conformance_v0_3.md`)
```
