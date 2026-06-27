from __future__ import annotations

import yaml


class FrontmatterError(ValueError):
    """Raised when a markdown document lacks valid YAML frontmatter."""


def parse_frontmatter(text: str) -> tuple[dict, str]:
    """Split a markdown doc with leading YAML frontmatter into (metadata, body)."""
    if not text.startswith("---"):
        raise FrontmatterError("missing frontmatter: file must start with '---'")
    parts = text.split("---", 2)
    if len(parts) < 3:
        raise FrontmatterError("unterminated frontmatter block")
    try:
        meta = yaml.safe_load(parts[1]) or {}
    except yaml.YAMLError as exc:
        raise FrontmatterError(f"invalid YAML frontmatter: {exc}") from exc
    if not isinstance(meta, dict):
        raise FrontmatterError("frontmatter must be a mapping")
    return meta, parts[2].lstrip("\n")
