from __future__ import annotations

from pathlib import Path

from eval.harness.frontmatter import FrontmatterError, parse_frontmatter

PLACEHOLDER_TOKENS: tuple[str, ...] = ("TODO", "TBD", "FIXME")
MAX_DESCRIPTION_CHARS: int = 1024


def lint_skill(skill_dir: str | Path) -> list[str]:
    """Return a list of issue strings for a skill directory. Empty == valid."""
    skill_dir = Path(skill_dir)
    md = skill_dir / "SKILL.md"
    if not md.exists():
        return [f"{skill_dir}: missing SKILL.md"]
    text = md.read_text(encoding="utf-8")
    try:
        meta, body = parse_frontmatter(text)
    except FrontmatterError as exc:
        return [f"{md}: {exc}"]

    issues: list[str] = []
    name = meta.get("name")
    if not name:
        issues.append(f"{md}: frontmatter missing 'name'")
    elif name != skill_dir.name:
        issues.append(f"{md}: name '{name}' != directory '{skill_dir.name}'")

    desc = meta.get("description")
    if not desc:
        issues.append(f"{md}: frontmatter missing 'description'")
    elif len(desc) > MAX_DESCRIPTION_CHARS:
        issues.append(f"{md}: description too long ({len(desc)} > {MAX_DESCRIPTION_CHARS})")

    if not body.strip():
        issues.append(f"{md}: empty body")
    elif not body.lstrip().startswith("#"):
        issues.append(f"{md}: body must start with an H1 heading")

    for token in PLACEHOLDER_TOKENS:
        if token in body:
            issues.append(f"{md}: contains placeholder token '{token}'")
    return issues
