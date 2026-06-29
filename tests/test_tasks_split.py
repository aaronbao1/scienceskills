import pytest
from eval.harness.tasks import load_tasks, split_tasks, BenchmarkError


def _write(tmp_path, text):
    p = tmp_path / "tasks.yaml"
    p.write_text(text, encoding="utf-8")
    return p


def test_split_defaults_to_gate(tmp_path):
    path = _write(tmp_path, "- id: t1\n  kind: judge\n  prompt: do a thing\n")
    tasks = load_tasks(path)
    assert tasks[0].split == "gate"


def test_split_parsed_and_partitioned(tmp_path):
    path = _write(
        tmp_path,
        "- id: d1\n  kind: judge\n  prompt: dev one\n  split: dev\n"
        "- id: g1\n  kind: judge\n  prompt: gate one\n  split: gate\n"
        "- id: g2\n  kind: ground_truth\n  prompt: gate two\n  scorer: exact\n"
        "  expected: x\n  split: gate\n",
    )
    tasks = load_tasks(path)
    dev, gate = split_tasks(tasks)
    assert [t.id for t in dev] == ["d1"]
    assert [t.id for t in gate] == ["g1", "g2"]


def test_invalid_split_raises(tmp_path):
    path = _write(tmp_path, "- id: t1\n  kind: judge\n  prompt: x\n  split: holdout\n")
    with pytest.raises(BenchmarkError):
        load_tasks(path)
