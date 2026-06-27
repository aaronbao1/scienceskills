from __future__ import annotations

from collections import defaultdict


def render_comparison(skill: str, rows: list[dict]) -> str:
    lines = [
        f"# Eval report — {skill}",
        "",
        "| version | task | passed | score | detail |",
        "| --- | --- | --- | --- | --- |",
    ]
    for r in rows:
        mark = "✅" if r["passed"] else "❌"
        lines.append(f"| {r['version']} | {r['task_id']} | {mark} | {r['score']:.2f} | {r['detail']} |")

    totals: dict[str, list[int]] = defaultdict(lambda: [0, 0])  # version -> [passed, total]
    for r in rows:
        totals[r["version"]][1] += 1
        if r["passed"]:
            totals[r["version"]][0] += 1

    lines += ["", "## Summary", ""]
    for version, (passed, total) in totals.items():
        lines.append(f"- {version}: {passed}/{total} passed")
    return "\n".join(lines) + "\n"
