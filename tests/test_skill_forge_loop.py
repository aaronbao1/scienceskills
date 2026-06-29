from pathlib import Path
from eval.harness.tasks import load_tasks, split_tasks

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "skills" / "skill-forge" / "SKILL.md"
RUBRIC = ROOT / "eval" / "rubrics" / "skill-forge.md"
TASKS = ROOT / "eval" / "benchmarks" / "skill-forge" / "tasks.yaml"


def test_skill_documents_reflective_generation_and_loop_control():
    body = SKILL.read_text(encoding="utf-8").lower()
    assert "reflective" in body
    assert "pareto" in body
    assert "accumulate" in body or "anchor" in body
    assert "halt" in body            # goodhart over-optimization halt
    assert "loop_control" in body    # eval.harness.loop_control
    for needle in ("writing-skills", "deep-research", "eval.harness.forge", "human"):
        assert needle in body


def test_rubric_mentions_generation_grounding_or_overopt():
    text = RUBRIC.read_text(encoding="utf-8").lower()
    assert "reflective" in text or "trace" in text or "over-optim" in text or "goodhart" in text
    for dim in ("evidence quality", "evaluation rigor", "gating soundness", "honesty", "reversibility"):
        assert dim in text


def test_benchmark_has_overoptimization_task():
    tasks = load_tasks(TASKS)
    dev, gate = split_tasks(tasks)
    assert dev and gate
    assert any(t.kind == "ground_truth" for t in tasks)
    assert any(t.id == "overoptimization_halt" for t in tasks)
