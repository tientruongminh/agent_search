from __future__ import annotations


def weighted_score(weights: dict[str, float], scores: dict[str, float]) -> tuple[float, dict[str, float]]:
    breakdown: dict[str, float] = {}
    total = 0.0
    for key, weight in weights.items():
        value = max(0.0, min(1.0, scores.get(key, 0.0)))
        component = round(weight * value, 4)
        breakdown[key] = component
        total += component
    return round(total, 4), breakdown

