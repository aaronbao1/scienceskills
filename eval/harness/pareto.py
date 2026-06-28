from __future__ import annotations


def dominates(a: list[float], b: list[float]) -> bool:
    """True iff `a` is >= `b` on every task and strictly greater on at least one."""
    if len(a) != len(b):
        raise ValueError("score vectors differ in length")
    return all(x >= y for x, y in zip(a, b)) and any(x > y for x, y in zip(a, b))


def pareto_front(candidates: dict) -> list:
    """IDs of candidates not dominated by any other (instance-wise non-dominated set)."""
    ids = list(candidates)
    return [
        cid
        for cid in ids
        if not any(dominates(candidates[other], candidates[cid]) for other in ids if other != cid)
    ]
