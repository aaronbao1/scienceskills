# tests/test_capture_sections.py
from pathlib import Path

TARGETS = ["argumentation-and-sources", "deep-reasoning", "deep-reasoning-ultra",
           "faithful-implementation", "humanities-inquiry", "literature-review",
           "research-design", "research-synthesis", "rigorous-validation", "scientific-rigor"]

def test_every_target_has_capture_and_consult():
    root = Path(__file__).resolve().parents[1] / "skills"
    for skill in TARGETS:
        text = (root / skill / "SKILL.md").read_text()
        assert "## Capture (run at session end)" in text, f"{skill} missing Capture"
        assert f"insights/{skill}/playbook.md" in text, f"{skill} missing Consult pointer"
