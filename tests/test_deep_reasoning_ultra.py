from pathlib import Path
from eval.harness.tasks import load_tasks

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "skills" / "deep-reasoning-ultra" / "SKILL.md"
RUBRIC = ROOT / "eval" / "rubrics" / "deep-reasoning-ultra.md"
TASKS = ROOT / "eval" / "benchmarks" / "deep-reasoning-ultra" / "tasks.yaml"


def test_skill_references_consensus_core_and_is_standalone():
    body = SKILL.read_text(encoding="utf-8")
    assert "eval.harness.consensus" in body
    assert "dispatching-parallel-agents" in body
    assert "scientific-rigor" not in body


def test_rubric_has_core_dimensions():
    text = RUBRIC.read_text(encoding="utf-8").lower()
    for dim in ("path diversity", "verification rigor", "aggregation soundness", "calibration"):
        assert dim in text


def test_benchmark_slice_loads_with_ground_truth():
    tasks = load_tasks(TASKS)
    assert len(tasks) >= 2
    assert any(t.kind == "ground_truth" for t in tasks)
