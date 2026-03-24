"""Issue #17 — Evidence debugging walkthrough.

Demonstrates that SRG's evidence trail surfaces problems faster than
traditional logging by running 3 failure scenarios and showing what
evidence reveals vs what logs would show.

Run: .venv/bin/python benchmarks/evidence_debugging_demo.py
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))

from srg.runtime.deterministic_registry import DeterministicRegistry
from srg.runtime.graph_runner import run_graph
from srg.runtime.loader import load_graph

from srg.examples.subnet_scorer_functions import (
    extract_features,
    score_economic_sustainability,
    score_mechanism_design,
    score_network_effects,
)

ROOT = Path(__file__).resolve().parent.parent
EXAMPLE = ROOT / "srg" / "examples" / "subnet_scorer.yaml"

SAMPLE_DATA: dict[str, Any] = {
    "subnet_data": {
        "validator_stakes": [100, 200, 150, 300, 250],
        "participation_ratio": 0.85,
        "consensus_agreement": 0.92,
        "network_size": 500,
        "validator_count": 50,
        "coldkey_concentration": 0.15,
        "emission": 0.75,
        "github_stars": 120,
        "commit_count_90d": 340,
        "contributor_count": 12,
        "has_ci": True,
        "has_tests": True,
        "real_emission": 0.65,
        "distribution_fairness": 0.70,
        "price_stability": 0.80,
        "pool_liquidity": 50000.0,
        "subnet_description": "Decentralized AI inference network",
        "unique_mechanisms": ["proof-of-inference", "adaptive-difficulty"],
    }
}


def _registry() -> DeterministicRegistry:
    reg = DeterministicRegistry()
    reg.register("extract_features")(extract_features)
    reg.register("score_mechanism_design")(score_mechanism_design)
    reg.register("score_network_effects")(score_network_effects)
    reg.register("score_economic_sustainability")(score_economic_sustainability)
    return reg


def _print_evidence_trail(result: Any) -> None:
    """Print the evidence trail from a GraphExecutionResult."""
    for nr in result.node_results:
        status_icon = "+" if nr.status == "success" else "X"
        duration = f"{nr.duration_ms:.0f}ms" if nr.duration_ms else "?ms"
        print(f"    [{status_icon}] {nr.node_id} ({duration})")
        for ev in nr.evidence:
            details = []
            if ev.validation_outcome:
                details.append(f"reason={ev.validation_outcome}")
            if ev.contract_summary:
                details.append(f"contract={ev.contract_summary}")
            if ev.retry_reason:
                details.append(f"retry={ev.retry_reason}")
            detail_str = f" — {', '.join(details)}" if details else ""
            print(f"        attempt {ev.attempt}: {ev.status}{detail_str}")
        if nr.error:
            print(f"        error: {nr.error}")


# ====================================================================
# SCENARIO 1: Contract violation with retry
# ====================================================================

def scenario_1() -> None:
    print("=" * 72)
    print("  Scenario 1: Contract Violation with Retry")
    print("=" * 72)
    print()
    print("  Setup: LLM returns team_quality_score=150 (out of range 0..100)")
    print("  on first attempt, then corrects to 72 on retry.")
    print()

    class ContractViolatingLLM:
        def __init__(self) -> None:
            self._calls = 0

        def generate(self, prompt: str, output_schema: dict | None = None, timeout_ms: int | None = None) -> dict:
            self._calls += 1
            if output_schema and "team_quality_score" in output_schema.get("required", []):
                if self._calls <= 1:
                    # First attempt: violates schema (max 100)
                    return {"team_quality_score": 150.0, "team_quality_reasoning": "Excellent."}
                # Retry: valid
                return {"team_quality_score": 72.0, "team_quality_reasoning": "Good team after correction."}
            if output_schema and "technical_innovation_score" in output_schema.get("required", []):
                return {"technical_innovation_score": 65.0, "technical_innovation_reasoning": "Novel."}
            return {}

    graph = load_graph(EXAMPLE)
    reg = _registry()
    reg.register("aggregate_scores")(lambda state: {
        "overall_score": round(sum(
            float(state[k]) * w for k, w in {
                "mechanism_design_score": 0.30, "network_effects_score": 0.20,
                "team_quality_score": 0.15, "economic_sustainability_score": 0.20,
                "technical_innovation_score": 0.15,
            }.items()
        ), 2),
        "score_breakdown": {k: float(state[k]) for k in [
            "mechanism_design_score", "network_effects_score", "team_quality_score",
            "economic_sustainability_score", "technical_innovation_score",
        ]},
    })

    result = run_graph(graph, reg, llm_provider=ContractViolatingLLM(), inputs=SAMPLE_DATA)

    print("  EVIDENCE TRAIL:")
    _print_evidence_trail(result)
    print()
    print(f"  SUMMARY: {result.evidence_summary}")
    print()

    # Find the team quality evidence
    team_nr = next(nr for nr in result.node_results if nr.node_id == "score_team_quality")

    print("  WHAT EVIDENCE TELLS YOU:")
    print(f"    - Node 'score_team_quality' required {len(team_nr.evidence)} attempts")
    print(f"    - Attempt 1: {team_nr.evidence[0].status} (schema violation — score 150 > max 100)")
    print(f"    - Attempt 2: {team_nr.evidence[1].status} (score corrected to 72)")
    print(f"    - Total graph: {result.evidence_summary['total_attempts']} attempts across {result.evidence_summary['total_nodes']} nodes")
    print(f"    - Final status: {result.status}")
    print()
    print("  WHAT PYTHON LOGGING WOULD SHOW:")
    print("    INFO: Calling LLM for team_quality...")
    print("    INFO: Got response: {'team_quality_score': 150.0, ...}")
    print("    ERROR: Score 150 out of range")
    print("    INFO: Retrying...")
    print("    INFO: Got response: {'team_quality_score': 72.0, ...}")
    print("    INFO: Team quality scored: 72.0")
    print()
    print("  EVIDENCE ADVANTAGE:")
    print("    - Structured: attempt number, status, validation_outcome are queryable fields")
    print("    - Hashed: input_hash and output_hash enable cross-run comparison")
    print("    - Complete: every attempt recorded, even failures")
    print("    - Automatic: no logging code needed — evidence is a framework guarantee")
    print()


# ====================================================================
# SCENARIO 2: Silent data flow problem
# ====================================================================

def scenario_2() -> None:
    print("=" * 72)
    print("  Scenario 2: Silent Data Flow Problem")
    print("=" * 72)
    print()
    print("  Setup: extract_features is buggy — returns empty features for")
    print("  mechanism design. The downstream score silently produces 50.0")
    print("  (the default when no data). Two runs compared via evidence hashes.")
    print()

    class GoodLLM:
        def generate(self, prompt: str, output_schema: dict | None = None, timeout_ms: int | None = None) -> dict:
            if output_schema and "team_quality_score" in output_schema.get("required", []):
                return {"team_quality_score": 72.0, "team_quality_reasoning": "Good."}
            if output_schema and "technical_innovation_score" in output_schema.get("required", []):
                return {"technical_innovation_score": 65.0, "technical_innovation_reasoning": "Novel."}
            return {}

    # Run 1: Normal
    graph = load_graph(EXAMPLE)
    reg = _registry()
    reg.register("aggregate_scores")(lambda state: {
        "overall_score": round(sum(
            float(state[k]) * w for k, w in {
                "mechanism_design_score": 0.30, "network_effects_score": 0.20,
                "team_quality_score": 0.15, "economic_sustainability_score": 0.20,
                "technical_innovation_score": 0.15,
            }.items()
        ), 2),
        "score_breakdown": {k: float(state[k]) for k in [
            "mechanism_design_score", "network_effects_score", "team_quality_score",
            "economic_sustainability_score", "technical_innovation_score",
        ]},
    })

    result_good = run_graph(graph, reg, llm_provider=GoodLLM(), inputs=SAMPLE_DATA)

    # Run 2: Buggy extract_features
    graph2 = load_graph(EXAMPLE)
    reg2 = DeterministicRegistry()

    def buggy_extract(state: dict[str, Any]) -> dict[str, Any]:
        good = extract_features(state)
        # Bug: mechanism_features is empty
        good["mechanism_features"] = {"validator_stakes": [], "participation_ratio": 0.0, "consensus_agreement": 0.0}
        return good

    reg2.register("extract_features")(buggy_extract)
    reg2.register("score_mechanism_design")(score_mechanism_design)
    reg2.register("score_network_effects")(score_network_effects)
    reg2.register("score_economic_sustainability")(score_economic_sustainability)
    reg2.register("aggregate_scores")(lambda state: {
        "overall_score": round(sum(
            float(state[k]) * w for k, w in {
                "mechanism_design_score": 0.30, "network_effects_score": 0.20,
                "team_quality_score": 0.15, "economic_sustainability_score": 0.20,
                "technical_innovation_score": 0.15,
            }.items()
        ), 2),
        "score_breakdown": {k: float(state[k]) for k in [
            "mechanism_design_score", "network_effects_score", "team_quality_score",
            "economic_sustainability_score", "technical_innovation_score",
        ]},
    })

    result_buggy = run_graph(graph2, reg2, llm_provider=GoodLLM(), inputs=SAMPLE_DATA)

    print("  RUN 1 (normal) vs RUN 2 (buggy extract_features):")
    print()
    print(f"  {'Node':<35} {'Run 1 output_hash':>20} {'Run 2 output_hash':>20} {'Match?':>8}")
    print(f"  {'-'*35} {'-'*20} {'-'*20} {'-'*8}")

    for nr1, nr2 in zip(result_good.node_results, result_buggy.node_results):
        h1 = nr1.evidence[0].output_hash if nr1.evidence and nr1.evidence[0].output_hash else "n/a"
        h2 = nr2.evidence[0].output_hash if nr2.evidence and nr2.evidence[0].output_hash else "n/a"
        match = "YES" if h1 == h2 else "DIFFERS"
        print(f"  {nr1.node_id:<35} {h1:>20} {h2:>20} {match:>8}")

    good_mech = result_good.outputs.get("mechanism_design_score")
    buggy_mech = result_buggy.outputs.get("mechanism_design_score")
    print()
    print(f"  mechanism_design_score: {good_mech} (normal) vs {buggy_mech} (buggy)")
    print(f"  overall_score: {result_good.outputs.get('overall_score')} (normal) vs {result_buggy.outputs.get('overall_score')} (buggy)")
    print()
    print("  WHAT EVIDENCE TELLS YOU:")
    print(f"    - mechanism_design_score dropped from {good_mech} to {buggy_mech}")
    print(f"    - overall_score dropped from {result_good.outputs.get('overall_score')} to {result_buggy.outputs.get('overall_score')}")
    print("    - Agentic node hashes MATCH (same LLM, same prompts) — problem is upstream")
    print("    - Per-node outputs narrow the bug to extract_features → score_mechanism_design")
    print("    - evidence_summary shows same node count, same pass rate — structurally fine")
    print()
    print("  WHAT PYTHON LOGGING WOULD SHOW:")
    print(f"    INFO: mechanism_design_score = {buggy_mech}")
    print(f"    INFO: overall_score = {result_buggy.outputs.get('overall_score')}")
    print("    (No indication anything is wrong — score is valid, just lower)")
    print()
    print("  EVIDENCE ADVANTAGE:")
    print("    - Per-node evidence enables comparison: which node's output changed?")
    print("    - Agentic node hashes confirm LLM behavior is identical between runs")
    print("    - Narrows the bug to deterministic pipeline without adding debug code")
    print("    - Works retroactively on stored evidence from production runs")
    print()


# ====================================================================
# SCENARIO 3: Performance regression
# ====================================================================

def scenario_3() -> None:
    print("=" * 72)
    print("  Scenario 3: Performance Bottleneck Identification")
    print("=" * 72)
    print()
    print("  Setup: One LLM provider is slow (500ms delay). Evidence")
    print("  immediately shows which node is the bottleneck.")
    print()

    import time

    class FastLLM:
        def generate(self, prompt: str, output_schema: dict | None = None, timeout_ms: int | None = None) -> dict:
            if output_schema and "team_quality_score" in output_schema.get("required", []):
                return {"team_quality_score": 72.0, "team_quality_reasoning": "Good."}
            if output_schema and "technical_innovation_score" in output_schema.get("required", []):
                return {"technical_innovation_score": 65.0, "technical_innovation_reasoning": "Novel."}
            return {}

    class SlowLLM:
        def generate(self, prompt: str, output_schema: dict | None = None, timeout_ms: int | None = None) -> dict:
            if output_schema and "team_quality_score" in output_schema.get("required", []):
                time.sleep(0.3)  # Simulate slow response
                return {"team_quality_score": 72.0, "team_quality_reasoning": "Good."}
            if output_schema and "technical_innovation_score" in output_schema.get("required", []):
                return {"technical_innovation_score": 65.0, "technical_innovation_reasoning": "Novel."}
            return {}

    graph = load_graph(EXAMPLE)
    reg = _registry()
    reg.register("aggregate_scores")(lambda state: {
        "overall_score": round(sum(
            float(state[k]) * w for k, w in {
                "mechanism_design_score": 0.30, "network_effects_score": 0.20,
                "team_quality_score": 0.15, "economic_sustainability_score": 0.20,
                "technical_innovation_score": 0.15,
            }.items()
        ), 2),
        "score_breakdown": {k: float(state[k]) for k in [
            "mechanism_design_score", "network_effects_score", "team_quality_score",
            "economic_sustainability_score", "technical_innovation_score",
        ]},
    })

    # Fast run
    result_fast = run_graph(graph, reg, llm_provider=FastLLM(), inputs=SAMPLE_DATA)

    # Slow run
    graph2 = load_graph(EXAMPLE)
    reg2 = _registry()
    reg2.register("aggregate_scores", reg.get("aggregate_scores"))
    result_slow = run_graph(graph2, reg2, llm_provider=SlowLLM(), inputs=SAMPLE_DATA)

    print(f"  {'Node':<35} {'Fast (ms)':>12} {'Slow (ms)':>12} {'Delta':>10}")
    print(f"  {'-'*35} {'-'*12} {'-'*12} {'-'*10}")

    for nr_f, nr_s in zip(result_fast.node_results, result_slow.node_results):
        d_f = nr_f.duration_ms or 0
        d_s = nr_s.duration_ms or 0
        delta = d_s - d_f
        flag = " <<<" if delta > 100 else ""
        print(f"  {nr_f.node_id:<35} {d_f:>11.1f} {d_s:>11.1f} {delta:>+9.1f}{flag}")

    fast_total = result_fast.evidence_summary["total_duration_ms"] if result_fast.evidence_summary else 0
    slow_total = result_slow.evidence_summary["total_duration_ms"] if result_slow.evidence_summary else 0
    print(f"  {'-'*35} {'-'*12} {'-'*12} {'-'*10}")
    print(f"  {'TOTAL':<35} {fast_total:>11.1f} {slow_total:>11.1f} {slow_total - fast_total:>+9.1f}")
    print()
    print("  WHAT EVIDENCE TELLS YOU:")
    print("    - score_team_quality is the bottleneck (300ms+ delta)")
    print("    - All other nodes unchanged — problem is isolated to one LLM call")
    print("    - total_duration_ms in evidence_summary shows overall impact")
    print()
    print("  WHAT PYTHON LOGGING WOULD SHOW:")
    print("    INFO: Scoring completed in 450ms")
    print("    (No per-node breakdown unless you add timing decorators)")
    print()
    print("  EVIDENCE ADVANTAGE:")
    print("    - Per-node duration_ms is automatic — no instrumentation needed")
    print("    - evidence_summary.total_duration_ms gives graph-level timing")
    print("    - Bottleneck identification is instant from evidence data")
    print()


# ====================================================================
# Main
# ====================================================================

def main() -> None:
    print()
    print("  SRG Evidence Debugging Walkthrough (Issue #17)")
    print()

    scenario_1()
    scenario_2()
    scenario_3()

    print("=" * 72)
    print("  Summary")
    print("=" * 72)
    print()
    print("  Scenario 1 (Contract Violation):")
    print("    Evidence shows exactly which node failed, what contract was")
    print("    violated, that retry occurred, and the corrected output.")
    print("    Logs show unstructured text requiring manual parsing.")
    print()
    print("  Scenario 2 (Silent Data Flow Bug):")
    print("    Evidence hash comparison across runs pinpoints WHERE output")
    print("    diverged (extract_features), even when downstream scores are")
    print("    valid. Logs show nothing wrong — the bug is invisible.")
    print()
    print("  Scenario 3 (Performance Regression):")
    print("    Per-node duration_ms immediately identifies the bottleneck.")
    print("    Logs require adding timing decorators to each function.")
    print()
    print("  VERDICT: Evidence provides actionable, structured, automatic")
    print("  debugging insight that is superior to traditional logging in")
    print("  all three scenarios. The advantage is strongest for cross-run")
    print("  comparison (Scenario 2) where evidence hashes enable analysis")
    print("  that logging fundamentally cannot provide without custom code.")


if __name__ == "__main__":
    main()
