from pathlib import Path
import pytest
from eval.harness.skill_lint import lint_skill

ROOT = Path(__file__).resolve().parents[1]
SKILLS = sorted(p for p in (ROOT / "skills").iterdir() if (p / "SKILL.md").exists())


@pytest.mark.parametrize("skill_dir", SKILLS, ids=[p.name for p in SKILLS])
def test_skill_lints_clean(skill_dir):
    assert lint_skill(skill_dir) == []


def test_scientific_rigor_present_and_routes():
    body = (ROOT / "skills" / "scientific-rigor" / "SKILL.md").read_text(encoding="utf-8")
    for ref in ("research-design", "literature-review", "faithful-implementation",
                "rigorous-validation", "research-synthesis", "skill-forge"):
        assert ref in body, f"router missing reference to {ref}"
