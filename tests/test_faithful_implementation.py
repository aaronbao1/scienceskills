from pathlib import Path
from eval.harness.tasks import load_tasks

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "skills" / "faithful-implementation" / "SKILL.md"
RUBRIC = ROOT / "eval" / "rubrics" / "faithful-implementation.md"
TASKS = ROOT / "eval" / "benchmarks" / "faithful-implementation" / "tasks.yaml"


def test_skill_declares_composition_contract():
    body = SKILL.read_text(encoding="utf-8")
    for dep in ("writing-plans", "subagent-driven-development", "test-driven-development"):
        assert dep in body, f"composition contract missing {dep}"
    assert "oracle" in body.lower()


def test_rubric_has_core_dimensions():
    text = RUBRIC.read_text(encoding="utf-8").lower()
    for dim in ("faithfulness", "correctness", "rigor", "honesty"):
        assert dim in text


def test_benchmark_slice_loads_and_has_ground_truth():
    tasks = load_tasks(TASKS)
    assert len(tasks) >= 2
    assert any(t.kind == "ground_truth" for t in tasks)
