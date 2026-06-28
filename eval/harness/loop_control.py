from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from eval.harness.anchor import accumulate_anchor, should_refresh_benchmark
from eval.harness.goodhart import judge_only_streak_exceeded, overoptimization_halt


def loop_decision(history: dict) -> dict:
    """Compose the Goodhart halt, judge-only cap, anchor check, and refresh trigger."""
    goodhart = overoptimization_halt(history.get("rounds", []), history.get("lookback", 2))
    streak = judge_only_streak_exceeded(history.get("promotions", []), history.get("judge_only_cap", 3))
    anchor = accumulate_anchor(history.get("seed_ids", []), history.get("current_ids", []))
    refresh = should_refresh_benchmark(
        history.get("dev_gate_deltas", []),
        history.get("alpha", 0.05),
        history.get("seed", 0),
    )
    halt = goodhart["halt"] or streak or not anchor["intact"]
    return {
        "halt": halt,
        "goodhart": goodhart,
        "judge_only_streak_exceeded": streak,
        "anchor": anchor,
        "refresh": refresh,
    }


def render_loop_report(decision: dict) -> str:
    """Render the loop-control decision as markdown."""
    verdict = "HALT" if decision["halt"] else "CONTINUE"
    anchor = decision["anchor"]
    lines = [
        "# Loop control",
        "",
        f"- Decision: {verdict}",
        f"- Goodhart over-optimization: {'HALT' if decision['goodhart']['halt'] else 'ok'} — {decision['goodhart']['reason']}",
        f"- Judge-only streak exceeded: {'yes' if decision['judge_only_streak_exceeded'] else 'no'}",
        f"- Anchor intact: {'yes' if anchor['intact'] else 'no'}"
        + ("" if anchor["intact"] else f" (missing: {', '.join(anchor['missing'])})"),
        f"- Benchmark refresh: {'yes' if decision['refresh']['refresh'] else 'no'} — {decision['refresh']['reason']}",
    ]
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="eval.harness.loop_control")
    parser.add_argument("history", help="path to a loop-history JSON file")
    args = parser.parse_args(argv)
    try:
        history = json.loads(Path(args.history).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"error: cannot read history file: {exc}", file=sys.stderr)
        return 2
    try:
        decision = loop_decision(history)
    except (KeyError, ValueError, TypeError, AttributeError) as exc:
        print(f"error: malformed history: {exc}", file=sys.stderr)
        return 2
    print(render_loop_report(decision))
    return 1 if decision["halt"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
