from pathlib import Path
from eval.harness.tasks import load_tasks, split_tasks

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "skills" / "skill-forge" / "SKILL.md"
RUBRIC = ROOT / "eval" / "rubrics" / "skill-forge.md"
TASKS = ROOT / "eval" / "benchmarks" / "skill-forge" / "tasks.yaml"


def test_skill_documents_holdout_and_significance():
    body = SKILL.read_text(encoding="utf-8").lower()
    assert "held-out" in body
    assert "significance" in body or "significant" in body
    # Legacy contract assertions must still hold.
    for needle in ("writing-skills", "deep-research", "eval.harness.forge", "human"):
        assert needle in body


def test_rubric_mentions_significance_and_holdout():
    text = RUBRIC.read_text(encoding="utf-8").lower()
    assert "held-out" in text
    assert "significan" in text
    for dim in ("evidence quality", "evaluation rigor", "gating soundness", "reversibility"):
        assert dim in text


def test_benchmark_has_dev_and_gate_splits():
    tasks = load_tasks(TASKS)
    dev, gate = split_tasks(tasks)
    assert dev, "expected at least one dev task"
    assert gate, "expected at least one gate task"
    assert any(t.kind == "ground_truth" for t in tasks)
