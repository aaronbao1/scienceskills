"""Goodhart tripwire: halt crystallization when proxy rises while gold stalls/drops."""
from __future__ import annotations

import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
INSIGHTS_ROOT = REPO_ROOT / "skills" / "skill-forge" / "insights"


def _read_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    out: list[dict] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            try:
                out.append(json.loads(line))
            except json.JSONDecodeError:
                pass
    return out


def _trend(xs: list[float]) -> float:
    return 0.0 if len(xs) < 2 else xs[-1] - xs[0]


def proxy_series(skill: str, lookback: int = 5) -> list[float]:
    raw = _read_jsonl(INSIGHTS_ROOT / skill / "raw.jsonl")
    vals = [1.0 if r.get("signals", {}).get("approval") else 0.0 for r in raw]
    return vals[-lookback:]


def gold_series(skill: str, lookback: int = 5) -> list[float]:
    hist = _read_jsonl(INSIGHTS_ROOT / skill / "gate-history.jsonl")
    return [h.get("gold_gate_mean", 0.0) for h in hist][-lookback:]


def check(skill: str, lookback: int = 5) -> dict:
    gold = gold_series(skill, lookback)
    if len(gold) < 2:
        return {"status": "ok", "reason": "insufficient gold history"}
    if _trend(proxy_series(skill, lookback)) > 0 and _trend(gold) <= 0:
        return {"status": "halt",
                "reason": "proxy up while gold stalled/dropped (possible reward hacking)"}
    return {"status": "ok", "reason": "proxy/gold not diverging"}
