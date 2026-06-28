from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

from eval.harness.blend import overall_score
from eval.harness.forge_report import render_promotion_proposal, render_stat_proposal
from eval.harness.gate import decide_promotion, decide_promotion_stat
from eval.harness.stats import significant_improvement
from eval.harness.tournament import (
    tally_tournament,
    resolve_swapped,
    aggregate_panel,
    panel_disagreement,
    check_panel_independence,
    verbosity_flag,
)
from eval.harness.judge_safety import detect_injection


def content_hash(text: str) -> str:
    """Stable 12-hex content hash for identifying a skill version."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:12]


def load_results(path: str | Path) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def build_paired_deltas(inc_runs: list, cand_runs: list, split: str = "gate") -> list:
    """Per-(task, seed) candidate-minus-incumbent deltas on held-out runs only."""
    def index(runs):
        return {
            (r["task_id"], r.get("seed", 0)): r["score"]
            for r in runs
            if r.get("split", "gate") == split
        }
    inc = index(inc_runs)
    cand = index(cand_runs)
    keys = sorted(set(inc) & set(cand))
    return [cand[k] - inc[k] for k in keys]


def aggregate_per_task(inc_runs: list, cand_runs: list, split: str = "gate") -> list:
    """Seed-averaged per-task incumbent/candidate scores (held-out split only)."""
    def fold(runs):
        sums: dict = {}
        counts: dict = {}
        crit: dict = {}
        for r in runs:
            if r.get("split", "gate") != split:
                continue
            tid = r["task_id"]
            sums[tid] = sums.get(tid, 0.0) + r["score"]
            counts[tid] = counts.get(tid, 0) + 1
            crit[tid] = crit.get(tid, False) or bool(r.get("critical"))
        means = {t: sums[t] / counts[t] for t in sums}
        return means, crit
    inc_m, inc_c = fold(inc_runs)
    cand_m, cand_c = fold(cand_runs)
    per_task = []
    for tid in sorted(set(inc_m) & set(cand_m)):
        per_task.append(
            {
                "task_id": tid,
                "incumbent": inc_m[tid],
                "candidate": cand_m[tid],
                "critical": inc_c.get(tid, False) or cand_c.get(tid, False),
            }
        )
    return per_task


def summarize_tournament(tournament) -> dict:
    """Flat list -> legacy tally; robust dict -> bias-controlled tally + integrity flags."""
    if not isinstance(tournament, dict):
        return tally_tournament(tournament or [])
    comparisons = tournament.get("comparisons", [])
    panel = tournament.get("panel", {})
    task_verdicts = []
    disagreements = []
    verbosity = []
    injections = []
    for comp in comparisons:
        tid = comp["task_id"]
        resolved = [resolve_swapped(v["first"], v["second"]) for v in comp.get("votes", [])]
        winner = aggregate_panel(resolved) if resolved else "tie"
        task_verdicts.append({"task_id": tid, "winner": winner})
        if resolved:
            disagreements.append(panel_disagreement(resolved))
        if verbosity_flag(winner, comp.get("incumbent_chars", 0), comp.get("candidate_chars", 0)):
            verbosity.append(tid)
        text = comp.get("candidate_text")
        if text and detect_injection(text):
            injections.append(tid)
    summary = tally_tournament(task_verdicts)
    independence = check_panel_independence(panel.get("judge_families", []), panel.get("agent_family"))
    summary["panel_independent"] = independence["independent"]
    summary["panel_reasons"] = independence["reasons"]
    summary["mean_disagreement"] = sum(disagreements) / len(disagreements) if disagreements else 0.0
    summary["verbosity_flags"] = verbosity
    summary["injection_flags"] = injections
    return summary


def evaluate(results: dict) -> tuple:
    """Statistical held-out gate when 'runs' are present; else the legacy margin gate."""
    skill = results["skill"]
    inc = results["incumbent"]
    cand = results["candidate"]
    tournament = summarize_tournament(results.get("tournament", []))

    if "runs" in inc and "runs" in cand:
        alpha = results.get("alpha", 0.05)
        n_candidates = results.get("n_candidates", 1)
        seed = results.get("seed", 0)
        deltas = build_paired_deltas(inc["runs"], cand["runs"])
        per_task = aggregate_per_task(inc["runs"], cand["runs"])
        verdict = (
            significant_improvement(deltas, alpha=alpha, n_candidates=n_candidates, seed=seed)
            if deltas
            else None
        )
        decision = decide_promotion_stat(verdict, per_task)
        report = render_stat_proposal(skill, verdict, decision, tournament, per_task, len(deltas))
        return decision, report

    # Legacy margin path (unchanged).
    margin = results.get("margin", 0.02)
    inc_tasks = inc["task_scores"]
    cand_tasks = cand["task_scores"]
    inc_overall = overall_score([t["score"] for t in inc_tasks])
    cand_overall = overall_score([t["score"] for t in cand_tasks])
    inc_by_id = {t["task_id"]: t for t in inc_tasks}
    per_task = []
    for ct in cand_tasks:
        it = inc_by_id.get(ct["task_id"])
        if it is None:
            continue
        per_task.append(
            {
                "task_id": ct["task_id"],
                "incumbent": it["score"],
                "candidate": ct["score"],
                "critical": bool(it.get("critical")) or bool(ct.get("critical")),
            }
        )
    decision = decide_promotion(inc_overall, cand_overall, per_task, margin)
    report = render_promotion_proposal(skill, inc_overall, cand_overall, decision, tournament, per_task)
    return decision, report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="eval.harness.forge")
    parser.add_argument("results", help="path to a forge results JSON file")
    args = parser.parse_args(argv)
    try:
        results = load_results(args.results)
    except (OSError, json.JSONDecodeError) as exc:
        print(f"error: cannot read results file: {exc}", file=sys.stderr)
        return 2
    try:
        decision, report = evaluate(results)
    except (KeyError, ValueError, TypeError) as exc:
        print(f"error: malformed results: {exc}", file=sys.stderr)
        return 2
    print(report)
    return 0 if decision.promote else 1


if __name__ == "__main__":
    raise SystemExit(main())
