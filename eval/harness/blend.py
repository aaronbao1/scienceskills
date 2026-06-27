from __future__ import annotations

import re

_DIM_RE = re.compile(r"\*\*(.+?)\s*\(weight\s+([0-9.]+)\)\s*:\*\*")


class RubricError(ValueError):
    """Raised when a rubric cannot be parsed or its weights are invalid."""


def parse_rubric_weights(rubric_text: str) -> dict[str, float]:
    """Extract {dimension (lowercased): weight} from a rubric's markdown."""
    weights: dict[str, float] = {}
    for match in _DIM_RE.finditer(rubric_text):
        weights[match.group(1).strip().lower()] = float(match.group(2))
    if not weights:
        raise RubricError("no weighted dimensions found")
    total = sum(weights.values())
    if abs(total - 1.0) > 0.001:
        raise RubricError(f"weights sum to {total}, expected 1.0")
    return weights


def blend_dimension_scores(weights: dict[str, float], scores: dict[str, float]) -> float:
    """Blend 0-4 dimension scores by weight into a [0, 1] value."""
    total = 0.0
    for dim, weight in weights.items():
        if dim not in scores:
            raise RubricError(f"missing score for dimension '{dim}'")
        value = scores[dim]
        if not 0 <= value <= 4:
            raise RubricError(f"score for '{dim}' out of range 0-4: {value}")
        total += weight * (value / 4.0)
    return total


def overall_score(task_scores: list[float]) -> float:
    """Mean of per-task [0, 1] scores."""
    if not task_scores:
        raise ValueError("no task scores")
    return sum(task_scores) / len(task_scores)
