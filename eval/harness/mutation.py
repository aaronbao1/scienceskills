from __future__ import annotations


class MutationError(ValueError):
    """Raised when a reflective line edit is malformed or does not match the document."""


def apply_line_edits(text: str, edits: list[dict]) -> str:
    """Apply attributed, line-targeted edits to a skill document.

    Each edit is {"old", "new", "reason"}: `old` must match exactly one line, `reason` must be
    a non-empty attribution of the failure it fixes. Anything else raises MutationError — a
    candidate cannot blindly rewrite or target an ambiguous line.
    """
    lines = text.split("\n")
    for edit in edits:
        if not edit.get("reason"):
            raise MutationError(f"edit missing reason/attribution: {edit!r}")
        old = edit["old"]
        matches = [i for i, line in enumerate(lines) if line == old]
        if not matches:
            raise MutationError(f"no line matches: {old!r}")
        if len(matches) > 1:
            raise MutationError(f"ambiguous edit, {len(matches)} lines match: {old!r}")
        lines[matches[0]] = edit["new"]
    return "\n".join(lines)
