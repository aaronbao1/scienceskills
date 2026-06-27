from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from eval.harness.blend import overall_score
from eval.harness.forge_report import render_promotion_proposal
from eval.harness.gate import decide_promotion
from eval.harness.tournament import tally_tournament


def content_hash(text: str) -> str:
    """Stable 12-hex content hash for identifying a skill version."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:12]


def load_results(path: str | Path) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def evaluate(results: dict) -> tuple:
    """Blend scores, apply the gate, tally the tournament, render the proposal."""
    skill = results["skill"]
    margin = results.get("margin", 0.02)
    inc_tasks = results["incumbent"]["task_scores"]
    cand_tasks = results["candidate"]["task_scores"]
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
    tournament = tally_tournament(results.get("tournament", []))
    report = render_promotion_proposal(skill, inc_overall, cand_overall, decision, tournament, per_task)
    return decision, report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="eval.harness.forge")
    parser.add_argument("results", help="path to a forge results JSON file")
    args = parser.parse_args(argv)
    decision, report = evaluate(load_results(args.results))
    print(report)
    return 0 if decision.promote else 1


if __name__ == "__main__":
    raise SystemExit(main())
