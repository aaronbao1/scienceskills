from pathlib import Path
from eval.harness.tasks import load_tasks

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "skills" / "literature-review" / "SKILL.md"
RUBRIC = ROOT / "eval" / "rubrics" / "literature-review.md"
TASKS = ROOT / "eval" / "benchmarks" / "literature-review" / "tasks.yaml"


def test_skill_declares_composition_contract():
    body = SKILL.read_text(encoding="utf-8")
    assert "deep-research" in body
    assert "method dossier" in body.lower()
    assert "oracle" in body.lower()


def test_rubric_has_core_dimensions():
    text = RUBRIC.read_text(encoding="utf-8").lower()
    for dim in ("coverage", "appraisal", "comparison", "citation"):
        assert dim in text


def test_benchmark_slice_loads():
    tasks = load_tasks(TASKS)
    assert len(tasks) >= 2
