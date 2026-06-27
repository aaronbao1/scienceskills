from __future__ import annotations

import argparse
from pathlib import Path

from eval.harness.skill_lint import lint_skill
from eval.harness.tasks import BenchmarkError, load_tasks


def cmd_lint(skills_dir: Path) -> int:
    issues: list[str] = []
    for d in sorted(p for p in skills_dir.iterdir() if (p / "SKILL.md").exists()):
        issues.extend(lint_skill(d))
    for issue in issues:
        print(issue)
    print(f"lint: {'OK' if not issues else f'{len(issues)} issue(s)'}")
    return 1 if issues else 0


def cmd_validate(bench_dir: Path) -> int:
    errors: list[str] = []
    for tasks_file in sorted(bench_dir.glob("*/tasks.yaml")):
        try:
            load_tasks(tasks_file)
        except BenchmarkError as exc:
            errors.append(str(exc))
    for err in errors:
        print(err)
    print(f"validate: {'OK' if not errors else f'{len(errors)} error(s)'}")
    return 1 if errors else 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="eval.harness")
    sub = parser.add_subparsers(dest="cmd", required=True)
    p_lint = sub.add_parser("lint")
    p_lint.add_argument("--skills", default="skills")
    p_val = sub.add_parser("validate")
    p_val.add_argument("--benchmarks", default="eval/benchmarks")
    args = parser.parse_args(argv)
    if args.cmd == "lint":
        return cmd_lint(Path(args.skills))
    if args.cmd == "validate":
        return cmd_validate(Path(args.benchmarks))
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
