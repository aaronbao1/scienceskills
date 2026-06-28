from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml

VALID_SCORERS: set[str] = {"exact", "numeric", "contains", "regex"}
VALID_KINDS: set[str] = {"ground_truth", "judge"}
VALID_SPLITS: set[str] = {"dev", "gate"}


class BenchmarkError(ValueError):
    """Raised when a benchmark tasks.yaml is malformed."""


@dataclass(frozen=True)
class Task:
    id: str
    prompt: str
    kind: str
    scorer: str | None = None
    expected: object = None
    tolerance: float | None = None
    split: str = "gate"


def load_tasks(path: str | Path) -> list[Task]:
    path = Path(path)
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(raw, list):
        raise BenchmarkError(f"{path}: top-level must be a list of tasks")
    tasks: list[Task] = []
    seen: set[str] = set()
    for i, item in enumerate(raw):
        if not isinstance(item, dict):
            raise BenchmarkError(f"{path}[{i}]: each task must be a mapping")
        tid = item.get("id")
        if not isinstance(tid, str) or not tid:
            raise BenchmarkError(f"{path}[{i}]: 'id' must be a non-empty string")
        if tid in seen:
            raise BenchmarkError(f"{path}: duplicate id '{tid}'")
        seen.add(tid)
        if "kind" not in item:
            raise BenchmarkError(f"{path}[{tid}]: missing 'kind'")
        kind = item.get("kind")
        if kind not in VALID_KINDS:
            raise BenchmarkError(f"{path}[{tid}]: kind must be one of {sorted(VALID_KINDS)}")
        prompt = item.get("prompt")
        if not isinstance(prompt, str) or not prompt:
            raise BenchmarkError(f"{path}[{tid}]: 'prompt' must be a non-empty string")
        split = item.get("split", "gate")
        if split not in VALID_SPLITS:
            raise BenchmarkError(f"{path}[{tid}]: split must be one of {sorted(VALID_SPLITS)}")
        scorer = item.get("scorer")
        if kind == "ground_truth":
            if scorer not in VALID_SCORERS:
                raise BenchmarkError(
                    f"{path}[{tid}]: ground_truth needs scorer in {sorted(VALID_SCORERS)}"
                )
            if "expected" not in item:
                raise BenchmarkError(f"{path}[{tid}]: ground_truth needs 'expected'")
        tasks.append(
            Task(
                id=tid,
                prompt=prompt,
                kind=kind,
                scorer=scorer,
                expected=item.get("expected"),
                tolerance=item.get("tolerance"),
                split=split,
            )
        )
    return tasks


def split_tasks(tasks: list[Task]) -> tuple[list[Task], list[Task]]:
    """Partition tasks into (dev, gate) by their split field."""
    dev = [t for t in tasks if t.split == "dev"]
    gate = [t for t in tasks if t.split == "gate"]
    return dev, gate
