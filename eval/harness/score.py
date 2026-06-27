from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class ScoreResult:
    passed: bool
    score: float
    detail: str


def _binary(passed: bool, detail_ok: str, detail_no: str) -> ScoreResult:
    return ScoreResult(passed, 1.0 if passed else 0.0, detail_ok if passed else detail_no)


def score_output(scorer: str, expected, actual: str, tolerance: float | None = None) -> ScoreResult:
    if scorer == "exact":
        ok = str(expected).strip() == str(actual).strip()
        return _binary(ok, "exact match", f"expected {expected!r}, got {actual!r}")
    if scorer == "contains":
        ok = str(expected) in str(actual)
        return _binary(ok, "substring found", f"{expected!r} not in output")
    if scorer == "regex":
        ok = re.search(str(expected), str(actual)) is not None
        return _binary(ok, "regex matched", f"/{expected}/ did not match")
    if scorer == "numeric":
        tol = 0.0 if tolerance is None else tolerance
        try:
            a, e = float(actual), float(expected)
        except (TypeError, ValueError):
            return ScoreResult(False, 0.0, f"non-numeric: expected {expected!r}, got {actual!r}")
        diff = abs(a - e)
        return _binary(diff <= tol, f"|{a}-{e}|={diff} <= {tol}", f"|{a}-{e}|={diff} > {tol}")
    raise ValueError(f"unknown scorer: {scorer!r}")
