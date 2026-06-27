from pathlib import Path
from eval.harness.skill_lint import lint_skill


def _make_skill(tmp_path: Path, name: str, frontmatter: str, body: str) -> Path:
    d = tmp_path / name
    d.mkdir()
    (d / "SKILL.md").write_text(f"---\n{frontmatter}\n---\n{body}\n", encoding="utf-8")
    return d


def test_valid_skill_has_no_issues(tmp_path):
    d = _make_skill(tmp_path, "good", "name: good\ndescription: Use when testing.", "# Good\n\nBody.")
    assert lint_skill(d) == []


def test_name_mismatch_flagged(tmp_path):
    d = _make_skill(tmp_path, "good", "name: wrong\ndescription: Use when testing.", "# Good\n\nBody.")
    assert any("name" in i for i in lint_skill(d))


def test_missing_description_flagged(tmp_path):
    d = _make_skill(tmp_path, "good", "name: good", "# Good\n\nBody.")
    assert any("description" in i for i in lint_skill(d))


def test_placeholder_token_flagged(tmp_path):
    d = _make_skill(tmp_path, "good", "name: good\ndescription: Use when testing.", "# Good\n\nTODO finish this.")
    assert any("placeholder" in i.lower() for i in lint_skill(d))


def test_missing_skill_md_flagged(tmp_path):
    d = tmp_path / "empty"
    d.mkdir()
    assert any("SKILL.md" in i for i in lint_skill(d))
