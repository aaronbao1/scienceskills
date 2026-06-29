from pathlib import Path
from eval.harness.tasks import load_tasks, split_tasks

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "skills" / "skill-forge" / "SKILL.md"
RUBRIC = ROOT / "eval" / "rubrics" / "skill-forge.md"
TASKS = ROOT / "eval" / "benchmarks" / "skill-forge" / "tasks.yaml"


def test_skill_documents_judge_controls():
    body = SKILL.read_text(encoding="utf-8").lower()
    assert "order-swapped" in body or "order swap" in body
    assert "disjoint" in body or "different family" in body or "distinct families" in body
    assert "sanitiz" in body  # sanitize / sanitization
    # protected substrings still present
    for needle in ("writing-skills", "deep-research", "eval.harness.forge", "human"):
        assert needle in body


def test_rubric_mentions_judge_integrity():
    text = RUBRIC.read_text(encoding="utf-8").lower()
    assert "order-swap" in text or "position bias" in text or "disjoint" in text
    for dim in ("evidence quality", "evaluation rigor", "gating soundness", "reversibility"):
        assert dim in text


def test_benchmark_has_order_swap_task_and_splits():
    tasks = load_tasks(TASKS)
    dev, gate = split_tasks(tasks)
    assert dev and gate
    assert any(t.kind == "ground_truth" for t in tasks)
    assert any(t.id == "order_swap_consistency" for t in tasks)
