"""Deterministic functions for the subnet_scorer graph.

Simplified versions of the subnet-scorer-worker's 5-factor scoring
algorithm, suitable for demonstrating the SRG pattern without external
database dependencies.
"""
from __future__ import annotations

import math
from typing import Any


def extract_features(state: dict[str, Any]) -> dict[str, Any]:
    """Destructure raw subnet_data into per-factor feature dicts."""
    data = state["subnet_data"]
    return {
        "mechanism_features": {
            "validator_stakes": data.get("validator_stakes", []),
            "participation_ratio": data.get("participation_ratio", 0.0),
            "consensus_agreement": data.get("consensus_agreement", 0.0),
        },
        "network_features": {
            "network_size": data.get("network_size", 0),
            "validator_count": data.get("validator_count", 0),
            "coldkey_concentration": data.get("coldkey_concentration", 0.0),
            "emission": data.get("emission", 0.0),
        },
        "team_features": {
            "github_stars": data.get("github_stars", 0),
            "commit_count_90d": data.get("commit_count_90d", 0),
            "contributor_count": data.get("contributor_count", 0),
            "has_ci": data.get("has_ci", False),
            "has_tests": data.get("has_tests", False),
        },
        "economic_features": {
            "real_emission": data.get("real_emission", 0.0),
            "distribution_fairness": data.get("distribution_fairness", 0.0),
            "price_stability": data.get("price_stability", 0.0),
            "pool_liquidity": data.get("pool_liquidity", 0.0),
        },
        "innovation_features": {
            "description": data.get("subnet_description", ""),
            "unique_mechanisms": data.get("unique_mechanisms", []),
        },
    }


def _gini(values: list[float]) -> float:
    """Compute the Gini coefficient for a list of non-negative values."""
    if not values or all(v == 0 for v in values):
        return 0.0
    sorted_vals = sorted(values)
    n = len(sorted_vals)
    cumulative = sum((2 * (i + 1) - n - 1) * v for i, v in enumerate(sorted_vals))
    return cumulative / (n * sum(sorted_vals))


def score_mechanism_design(state: dict[str, Any]) -> dict[str, Any]:
    """Score mechanism design: Gini on stakes + participation + consensus."""
    features = state["mechanism_features"]
    stakes = [float(s) for s in features.get("validator_stakes", [])]
    participation = float(features.get("participation_ratio", 0.0))
    consensus = float(features.get("consensus_agreement", 0.0))

    # Stake distribution: lower Gini = better (invert)
    gini = _gini(stakes) if stakes else 0.5
    distribution_score = (1.0 - gini) * 100.0

    # Participation contribution (0-1 → 0-100 range, weighted)
    participation_score = participation * 100.0

    # Consensus contribution
    consensus_score = consensus * 100.0

    # Weighted combination
    score = (
        distribution_score * 0.40
        + participation_score * 0.35
        + consensus_score * 0.25
    )
    return {"mechanism_design_score": round(max(0.0, min(100.0, score)), 2)}


def score_network_effects(state: dict[str, Any]) -> dict[str, Any]:
    """Score network effects: log-scale size + diversity - concentration."""
    features = state["network_features"]
    network_size = max(1, int(features.get("network_size", 1)))
    validator_count = max(1, int(features.get("validator_count", 1)))
    concentration = float(features.get("coldkey_concentration", 0.0))
    emission = float(features.get("emission", 0.0))

    # Log-scale network size (0-30 points)
    size_score = min(30.0, 5.0 + math.log10(network_size) * 8.0)

    # Validator diversity (0-25 points)
    diversity_score = min(25.0, 3.0 + math.log10(validator_count + 1) * 13.0)

    # Coldkey concentration penalty (-20 to +5 points)
    if concentration < 0.10:
        concentration_adj = (0.10 - concentration) * 50.0
    else:
        concentration_adj = -min(20.0, (concentration - 0.10) * 50.0)

    # Emission activity (0-20 points)
    emission_score = min(20.0, emission * 20.0) if emission > 0 else 0.0

    score = size_score + diversity_score + concentration_adj + emission_score
    return {"network_effects_score": round(max(0.0, min(100.0, score)), 2)}


def score_economic_sustainability(state: dict[str, Any]) -> dict[str, Any]:
    """Score economic sustainability: emission, fairness, stability, liquidity."""
    features = state["economic_features"]
    real_emission = float(features.get("real_emission", 0.0))
    fairness = float(features.get("distribution_fairness", 0.0))
    stability = float(features.get("price_stability", 0.0))
    liquidity = float(features.get("pool_liquidity", 0.0))

    # Real emission activity (0-30 points)
    emission_score = min(30.0, real_emission * 30.0)

    # Distribution fairness (0-25 points)
    fairness_score = fairness * 25.0

    # Price stability (0-25 points)
    stability_score = stability * 25.0

    # Pool liquidity (0-20 points, log-scale)
    if liquidity > 0:
        liquidity_score = min(20.0, math.log10(max(1.0, liquidity / 50.0)) * 10.0)
    else:
        liquidity_score = 0.0

    score = emission_score + fairness_score + stability_score + liquidity_score
    return {"economic_sustainability_score": round(max(0.0, min(100.0, score)), 2)}


def aggregate_scores(state: dict[str, Any]) -> dict[str, Any]:
    """Compute weighted average of all 5 factor scores."""
    weights = {
        "mechanism_design_score": 0.30,
        "network_effects_score": 0.20,
        "team_quality_score": 0.15,
        "economic_sustainability_score": 0.20,
        "technical_innovation_score": 0.15,
    }
    overall = sum(float(state[k]) * w for k, w in weights.items())
    breakdown = {k: float(state[k]) for k in weights}
    return {
        "overall_score": round(overall, 2),
        "score_breakdown": breakdown,
    }
