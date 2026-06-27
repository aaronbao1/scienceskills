from pathlib import Path
from eval.harness.tasks import load_tasks

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "skills" / "research-synthesis" / "SKILL.md"
RUBRIC = ROOT / "eval" / "rubrics" / "research-synthesis.md"
TASKS = ROOT / "eval" / "benchmarks" / "research-synthesis" / "tasks.yaml"


def test_skill_declares_composition_contract():
    body = SKILL.read_text(encoding="utf-8")
    assert "create-viz" in body
    assert "validation report" in body.lower()
    assert "limitations" in body.lower()


def test_rubric_has_core_dimensions():
    text = RUBRIC.read_text(encoding="utf-8").lower()
    for dim in ("faithfulness", "calibration", "limitations"):
        assert dim in text


def test_benchmark_slice_loads():
    tasks = load_tasks(TASKS)
    assert len(tasks) >= 2
