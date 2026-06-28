from __future__ import annotations

import yaml


class FrontmatterError(ValueError):
    """Raised when a markdown document lacks valid YAML frontmatter."""


def parse_frontmatter(text: str) -> tuple[dict, str]:
    """Split a markdown doc with leading YAML frontmatter into (metadata, body).

    Accepts LF or CRLF line endings, requires the opening ``---`` on its own
    line, and strips exactly one newline after the closing ``---`` so an
    intentionally blank first body line is preserved.
    """
    normalized = text.replace("\r\n", "\n")
    if not normalized.startswith("---\n"):
        raise FrontmatterError("missing frontmatter: file must start with a '---' line")
    parts = normalized.split("---", 2)
    if len(parts) < 3:
        raise FrontmatterError("unterminated frontmatter block")
    try:
        meta = yaml.safe_load(parts[1]) or {}
    except yaml.YAMLError as exc:
        raise FrontmatterError(f"invalid YAML frontmatter: {exc}") from exc
    if not isinstance(meta, dict):
        raise FrontmatterError("frontmatter must be a mapping")
    body = parts[2][1:] if parts[2].startswith("\n") else parts[2]
    return meta, body
