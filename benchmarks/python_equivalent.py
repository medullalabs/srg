"""Pure Python equivalent of the subnet_scorer SRG graph.

This implements the exact same 5-factor scoring pipeline without SRG,
for token efficiency comparison (Issue #2).
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any


@dataclass
class ScoringResult:
    overall_score: float
    score_breakdown: dict[str, float]
    team_quality_reasoning: str
    technical_innovation_reasoning: str
    confidence: float = 1.0


def _gini(values: list[float]) -> float:
    if not values or all(v == 0 for v in values):
        return 0.0
    sorted_vals = sorted(values)
    n = len(sorted_vals)
    cumulative = sum((2 * (i + 1) - n - 1) * v for i, v in enumerate(sorted_vals))
    return cumulative / (n * sum(sorted_vals))


def score_mechanism_design(subnet_data: dict[str, Any]) -> float:
    stakes = [float(s) for s in subnet_data.get("validator_stakes", [])]
    participation = float(subnet_data.get("participation_ratio", 0.0))
    consensus = float(subnet_data.get("consensus_agreement", 0.0))

    gini = _gini(stakes) if stakes else 0.5
    distribution_score = (1.0 - gini) * 100.0
    participation_score = participation * 100.0
    consensus_score = consensus * 100.0

    score = (
        distribution_score * 0.40
        + participation_score * 0.35
        + consensus_score * 0.25
    )
    return round(max(0.0, min(100.0, score)), 2)


def score_network_effects(subnet_data: dict[str, Any]) -> float:
    network_size = max(1, int(subnet_data.get("network_size", 1)))
    validator_count = max(1, int(subnet_data.get("validator_count", 1)))
    concentration = float(subnet_data.get("coldkey_concentration", 0.0))
    emission = float(subnet_data.get("emission", 0.0))

    size_score = min(30.0, 5.0 + math.log10(network_size) * 8.0)
    diversity_score = min(25.0, 3.0 + math.log10(validator_count + 1) * 13.0)

    if concentration < 0.10:
        concentration_adj = (0.10 - concentration) * 50.0
    else:
        concentration_adj = -min(20.0, (concentration - 0.10) * 50.0)

    emission_score = min(20.0, emission * 20.0) if emission > 0 else 0.0

    score = size_score + diversity_score + concentration_adj + emission_score
    return round(max(0.0, min(100.0, score)), 2)


def score_team_quality(subnet_data: dict[str, Any], llm_call: Any) -> tuple[float, str]:
    team_features = {
        "github_stars": subnet_data.get("github_stars", 0),
        "commit_count_90d": subnet_data.get("commit_count_90d", 0),
        "contributor_count": subnet_data.get("contributor_count", 0),
        "has_ci": subnet_data.get("has_ci", False),
        "has_tests": subnet_data.get("has_tests", False),
    }
    prompt = (
        f"Assess the development team quality for a Bittensor subnet based on "
        f"the following GitHub metrics:\n{team_features}\n\n"
        f"Score the team from 0 to 100 and provide reasoning."
    )
    result = llm_call(prompt)
    score = float(result["team_quality_score"])
    reasoning = str(result["team_quality_reasoning"])
    if not (0 <= score <= 100):
        raise ValueError(f"team_quality_score {score} not in 0..100")
    if not reasoning:
        raise ValueError("team_quality_reasoning is empty")
    return score, reasoning


def score_economic_sustainability(subnet_data: dict[str, Any]) -> float:
    real_emission = float(subnet_data.get("real_emission", 0.0))
    fairness = float(subnet_data.get("distribution_fairness", 0.0))
    stability = float(subnet_data.get("price_stability", 0.0))
    liquidity = float(subnet_data.get("pool_liquidity", 0.0))

    emission_score = min(30.0, real_emission * 30.0)
    fairness_score = fairness * 25.0
    stability_score = stability * 25.0

    if liquidity > 0:
        liquidity_score = min(20.0, math.log10(max(1.0, liquidity / 50.0)) * 10.0)
    else:
        liquidity_score = 0.0

    score = emission_score + fairness_score + stability_score + liquidity_score
    return round(max(0.0, min(100.0, score)), 2)


def score_technical_innovation(
    subnet_data: dict[str, Any], llm_call: Any
) -> tuple[float, str]:
    innovation_features = {
        "description": subnet_data.get("subnet_description", ""),
        "unique_mechanisms": subnet_data.get("unique_mechanisms", []),
    }
    prompt = (
        f"Assess the technical innovation of a Bittensor subnet based on "
        f"the following information:\n{innovation_features}\n\n"
        f"Score the technical innovation from 0 to 100 and provide reasoning."
    )
    result = llm_call(prompt)
    score = float(result["technical_innovation_score"])
    reasoning = str(result["technical_innovation_reasoning"])
    if not (0 <= score <= 100):
        raise ValueError(f"technical_innovation_score {score} not in 0..100")
    if not reasoning:
        raise ValueError("technical_innovation_reasoning is empty")
    return score, reasoning


def score_subnet(subnet_data: dict[str, Any], llm_call: Any) -> ScoringResult:
    mechanism_score = score_mechanism_design(subnet_data)
    network_score = score_network_effects(subnet_data)
    team_score, team_reasoning = score_team_quality(subnet_data, llm_call)
    economic_score = score_economic_sustainability(subnet_data)
    innovation_score, innovation_reasoning = score_technical_innovation(
        subnet_data, llm_call
    )

    weights = {
        "mechanism_design_score": 0.30,
        "network_effects_score": 0.20,
        "team_quality_score": 0.15,
        "economic_sustainability_score": 0.20,
        "technical_innovation_score": 0.15,
    }

    scores = {
        "mechanism_design_score": mechanism_score,
        "network_effects_score": network_score,
        "team_quality_score": team_score,
        "economic_sustainability_score": economic_score,
        "technical_innovation_score": innovation_score,
    }

    overall = sum(scores[k] * weights[k] for k in weights)

    return ScoringResult(
        overall_score=round(overall, 2),
        score_breakdown=scores,
        team_quality_reasoning=team_reasoning,
        technical_innovation_reasoning=innovation_reasoning,
    )
