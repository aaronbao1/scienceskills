from pathlib import Path
from eval.harness.tasks import load_tasks

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "skills" / "deep-reasoning" / "SKILL.md"
RUBRIC = ROOT / "eval" / "rubrics" / "deep-reasoning.md"
TASKS = ROOT / "eval" / "benchmarks" / "deep-reasoning" / "tasks.yaml"


def test_skill_is_standalone_and_tiered():
    body = SKILL.read_text(encoding="utf-8")
    assert "dispatching-parallel-agents" in body
    assert "triage" in body.lower()
    assert "verification" in body.lower()
    assert "scientific-rigor" not in body


def test_rubric_has_core_dimensions():
    text = RUBRIC.read_text(encoding="utf-8").lower()
    for dim in ("decomposition", "path diversity", "verification rigor", "calibration"):
        assert dim in text


def test_benchmark_slice_loads_with_ground_truth():
    tasks = load_tasks(TASKS)
    assert len(tasks) >= 2
    assert any(t.kind == "ground_truth" for t in tasks)
