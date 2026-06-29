"""Deterministic capture I/O for skill-forge. File I/O only — no judgment."""
from __future__ import annotations

import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
INSIGHTS_ROOT = REPO_ROOT / "skills" / "skill-forge" / "insights"

REQUIRED_INSIGHT_FIELDS = ("ts", "skill", "session_id", "context", "signals", "lesson", "confidence")


def _store_dir(skill: str) -> Path:
    d = INSIGHTS_ROOT / skill
    d.mkdir(parents=True, exist_ok=True)
    return d


def validate_insight(record: dict) -> None:
    missing = [f for f in REQUIRED_INSIGHT_FIELDS if f not in record]
    if missing:
        raise ValueError(f"insight missing required fields: {missing}")
    if not str(record.get("lesson", "")).strip():
        raise ValueError("insight 'lesson' must be non-empty")
    edit = record.get("proposed_edit")
    if edit is not None:
        if not isinstance(edit, dict) or not {"old", "new", "reason"} <= set(edit):
            raise ValueError("proposed_edit must have old, new, reason")
        if not str(edit["old"]).strip():
            raise ValueError("proposed_edit.old must be non-empty")


def append_insight(skill: str, record: dict) -> Path:
    validate_insight(record)
    path = _store_dir(skill) / "raw.jsonl"
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(record, ensure_ascii=False) + "\n")
    return path
