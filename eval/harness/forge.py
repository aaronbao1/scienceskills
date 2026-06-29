# eval/harness/forge.py
"""Slim skill-forge orchestrator: monitor -> gate -> log round -> proposal."""
from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from statistics import fmean

from eval.harness import gate, monitor

_REPO_ROOT = Path(__file__).resolve().parents[2]
INSIGHTS_ROOT = _REPO_ROOT / "skills" / "skill-forge" / "insights"


def _gate_runs(version: dict) -> list[dict]:
    return [r for r in version["runs"] if r.get("split", "gate") == "gate"]


def _next_round(hist_path: Path) -> int:
    if not hist_path.exists():
        return 1
    return sum(1 for line in hist_path.read_text().splitlines() if line.strip()) + 1


def _render(skill: str, d: gate.Decision, gold_gate_mean: float) -> str:
    head = "PROMOTE (pending human approval)" if d.promote else "REJECT"
    return (f"## skill-forge proposal — {skill}\n\n"
            f"- decision: **{head}**\n- reason: {d.reason}\n"
            f"- mean gold delta: {d.mean_delta:.4f} (noise floor {d.noise_floor:.4f})\n"
            f"- candidate gold (gate split): {gold_gate_mean:.4f}\n"
            f"- per-seed delta: {d.per_seed_delta}\n")


def evaluate(results: dict, *, now_iso: str) -> dict:
    skill = results["skill"]
    store = INSIGHTS_ROOT / skill
    inc = _gate_runs(results["incumbent"])
    cand = _gate_runs(results["candidate"])

    mon = monitor.check(skill)
    if mon["status"] == "halt":
        return {"exit": 2, "decision": "halt", "reason": mon["reason"],
                "proposal": f"HALT — {mon['reason']}. Crystallization paused; investigate divergence."}

    d = gate.decide(inc, cand, use_sign_test=results.get("use_sign_test", False))
    decision = "promote" if d.promote else "reject"
    gold_gate_mean = fmean([r["score"] for r in cand]) if cand else 0.0

    # Compute absolute per-seed candidate gold (sorted by seed).
    seed_scores: dict[int, list[float]] = defaultdict(list)
    for r in cand:
        seed_scores[r["seed"]].append(r["score"])
    gold_per_seed = [fmean(seed_scores[s]) for s in sorted(seed_scores)] if seed_scores else []

    store.mkdir(parents=True, exist_ok=True)
    hist_path = store / "gate-history.jsonl"
    # `proxy` is reserved/unused: monitor.check() recomputes the proxy trend from
    # raw.jsonl on a per-session clock while gate-history advances per gate round,
    # so the two series are intentionally not aligned and we record a placeholder.
    rec = {"round": _next_round(hist_path), "ts": now_iso, "skill": skill,
           "incumbent_hash": results["incumbent"].get("hash"),
           "candidate_hash": results["candidate"].get("hash"),
           "gold_gate_mean": gold_gate_mean, "gold_per_seed": gold_per_seed,
           "proxy": 0.0, "decision": decision, "reason": d.reason}
    with hist_path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(rec) + "\n")

    return {"exit": 0 if d.promote else 1, "decision": decision, "reason": d.reason,
            "proposal": _render(skill, d, gold_gate_mean)}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="forge")
    parser.add_argument("skill")
    parser.add_argument("results")
    args = parser.parse_args(argv)
    try:
        results = json.loads(Path(args.results).read_text())
    except OSError as exc:
        print(f"forge: cannot read results file: {exc}", file=sys.stderr)
        return 2
    except json.JSONDecodeError as exc:
        print(f"forge: malformed JSON in results file: {exc}", file=sys.stderr)
        return 2
    results.setdefault("skill", args.skill)
    out = evaluate(results, now_iso=datetime.now(timezone.utc).isoformat())
    print(out["proposal"])
    return out["exit"]


if __name__ == "__main__":
    sys.exit(main())
