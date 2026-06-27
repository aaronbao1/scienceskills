from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_master_prompt_is_condensed_and_routes():
    text = (ROOT / "CLAUDE.md").read_text(encoding="utf-8")
    assert len(text) <= 4000, f"CLAUDE.md too long: {len(text)} chars"
    for skill in ("research-design", "literature-review", "faithful-implementation",
                  "rigorous-validation", "research-synthesis", "skill-forge",
                  "scientific-rigor"):
        assert skill in text, f"missing route to {skill}"
    for token in ("TODO", "TBD", "FIXME"):
        assert token not in text
