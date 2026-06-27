from pathlib import Path
from eval.harness.tasks import load_tasks

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "skills" / "humanities-inquiry" / "SKILL.md"
RUBRIC = ROOT / "eval" / "rubrics" / "humanities-inquiry.md"
TASKS = ROOT / "eval" / "benchmarks" / "humanities-inquiry" / "tasks.yaml"


def test_skill_declares_composition_contract():
    body = SKILL.read_text(encoding="utf-8")
    assert "argumentation-and-sources" in body
    assert "research-synthesis" in body
    assert "positionality" in body.lower()


def test_rubric_has_core_dimensions():
    text = RUBRIC.read_text(encoding="utf-8").lower()
    for dim in ("interpretive validity", "methodological fit", "reflexivity", "ethics"):
        assert dim in text


def test_benchmark_slice_loads():
    tasks = load_tasks(TASKS)
    assert len(tasks) >= 2
