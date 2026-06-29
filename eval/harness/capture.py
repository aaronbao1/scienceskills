"""Deterministic capture I/O for skill-forge. File I/O only — no judgment."""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
INSIGHTS_ROOT = _REPO_ROOT / "skills" / "skill-forge" / "insights"

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


def _project_slug(cwd: Path | None = None) -> str:
    return str((cwd or Path.cwd()).resolve()).replace(os.sep, "-")


def _default_transcripts_dir(cwd: Path | None = None) -> Path:
    return Path.home() / ".claude" / "projects" / _project_slug(cwd)


def _parse_jsonl(path: Path) -> list[dict]:
    out: list[dict] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            out.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return out


def snapshot(skill: str, session_id: str | None = None,
             transcripts_dir: Path | None = None) -> Path | None:
    tdir = transcripts_dir or _default_transcripts_dir()
    if session_id:
        src = tdir / f"{session_id}.jsonl"
        if not src.exists():
            return None
    else:
        if not tdir.exists():
            return None
        candidates = sorted(tdir.glob("*.jsonl"), key=lambda p: p.stat().st_mtime, reverse=True)
        if not candidates:
            return None
        src = candidates[0]
        session_id = src.stem
    try:
        records = _parse_jsonl(src)
    except OSError:
        return None
    by_uuid = {r["uuid"]: r for r in records if r.get("uuid") is not None}
    attributed = {r["uuid"] for r in records if r.get("uuid") is not None and r.get("attributionSkill") == skill}

    def reaches_attributed(rec: dict) -> bool:
        seen: set = set()
        cur = rec
        while cur is not None:
            u = cur.get("uuid")
            if u in attributed:
                return True
            if u in seen:
                break
            seen.add(u)
            cur = by_uuid.get(cur.get("parentUuid"))
        return False

    selected = [r for r in records
                if r.get("uuid") in attributed or (r.get("isSidechain") and reaches_attributed(r))]
    if not selected:
        return None
    out_dir = _store_dir(skill) / "transcripts"
    out_dir.mkdir(parents=True, exist_ok=True)
    out = out_dir / f"{session_id}.jsonl"
    with out.open("w", encoding="utf-8") as fh:
        for r in selected:
            fh.write(json.dumps(r, ensure_ascii=False) + "\n")
    return out


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="capture")
    sub = parser.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("snapshot"); s.add_argument("skill")
    i = sub.add_parser("insight"); i.add_argument("skill")
    args = parser.parse_args(argv)
    if args.cmd == "snapshot":
        path = snapshot(args.skill)
        print(str(path) if path else "no transcript found")
        return 0
    record = json.loads(sys.stdin.read())
    record.setdefault("skill", args.skill)
    append_insight(args.skill, record)
    return 0


if __name__ == "__main__":
    sys.exit(main())
