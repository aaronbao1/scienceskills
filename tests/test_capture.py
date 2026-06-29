import io
import json
import pytest
from eval.harness import capture
import sys

def _valid():
    return {"ts": "2026-06-28T00:00:00Z", "skill": "research-design", "session_id": "s1",
            "context": "framed a hypothesis", "signals": {"approval": True},
            "lesson": "State the falsifier before supporting a claim.", "confidence": 0.7}

def test_append_insight_writes_one_line(tmp_path, monkeypatch):
    monkeypatch.setattr(capture, "INSIGHTS_ROOT", tmp_path)
    path = capture.append_insight("research-design", _valid())
    lines = path.read_text().splitlines()
    assert len(lines) == 1
    assert json.loads(lines[0])["lesson"].startswith("State the falsifier")

def test_append_insight_rejects_missing_lesson(tmp_path, monkeypatch):
    monkeypatch.setattr(capture, "INSIGHTS_ROOT", tmp_path)
    rec = _valid(); del rec["lesson"]
    with pytest.raises(ValueError):
        capture.append_insight("research-design", rec)

def test_append_insight_rejects_bad_proposed_edit(tmp_path, monkeypatch):
    monkeypatch.setattr(capture, "INSIGHTS_ROOT", tmp_path)
    rec = _valid(); rec["proposed_edit"] = {"old": "", "new": "x", "reason": "y"}
    with pytest.raises(ValueError):
        capture.append_insight("research-design", rec)


def _write_transcript(tmp_path):
    tdir = tmp_path / "proj"
    tdir.mkdir()
    rows = [
        {"uuid": "a", "attributionSkill": "research-design", "type": "assistant"},
        {"uuid": "b", "parentUuid": "a", "isSidechain": True, "type": "assistant"},
        {"uuid": "c", "attributionSkill": "other-skill", "type": "assistant"},
    ]
    f = tdir / "sess1.jsonl"
    f.write_text("\n".join(__import__("json").dumps(r) for r in rows) + "\n")
    return tdir

def test_snapshot_filters_by_attribution(tmp_path, monkeypatch):
    monkeypatch.setattr(capture, "INSIGHTS_ROOT", tmp_path / "store")
    tdir = _write_transcript(tmp_path)
    out = capture.snapshot("research-design", session_id="sess1", transcripts_dir=tdir)
    assert out is not None
    uuids = {json.loads(l)["uuid"] for l in out.read_text().splitlines()}
    assert uuids == {"a", "b"}  # attributed record + its sidechain; not "c"

def test_snapshot_returns_none_when_missing(tmp_path, monkeypatch):
    monkeypatch.setattr(capture, "INSIGHTS_ROOT", tmp_path / "store")
    assert capture.snapshot("research-design", session_id="nope", transcripts_dir=tmp_path) is None

def test_snapshot_uuid_less_record_not_attributed(tmp_path, monkeypatch):
    """A record with no uuid and attributionSkill for a different skill must not
    appear in the snapshot for the target skill (guards finding #1: None poisoning)."""
    monkeypatch.setattr(capture, "INSIGHTS_ROOT", tmp_path / "store")
    tdir = tmp_path / "proj"
    tdir.mkdir()
    rows = [
        {"uuid": "a", "attributionSkill": "research-design", "type": "assistant"},
        # no uuid, different skill — must NOT be selected
        {"attributionSkill": "other-skill", "type": "tool"},
        # no uuid, no attributionSkill — must NOT be selected
        {"type": "tool"},
    ]
    f = tdir / "sess2.jsonl"
    f.write_text("\n".join(json.dumps(r) for r in rows) + "\n")
    out = capture.snapshot("research-design", session_id="sess2", transcripts_dir=tdir)
    assert out is not None
    result_rows = [json.loads(l) for l in out.read_text().splitlines() if l.strip()]
    uuids = [r.get("uuid") for r in result_rows]
    assert uuids == ["a"]  # only the properly attributed record

def test_snapshot_nonexistent_transcripts_dir_returns_none(tmp_path, monkeypatch):
    """snapshot() with a nonexistent transcripts_dir and no session_id returns None
    instead of raising (guards finding #3)."""
    monkeypatch.setattr(capture, "INSIGHTS_ROOT", tmp_path / "store")
    nonexistent = tmp_path / "no_such_dir"
    assert capture.snapshot("research-design", transcripts_dir=nonexistent) is None

def test_cli_insight_appends_from_stdin(tmp_path, monkeypatch):
    monkeypatch.setattr(capture, "INSIGHTS_ROOT", tmp_path)
    monkeypatch.setattr("sys.stdin", io.StringIO(json.dumps(_valid())))
    rc = capture.main(["insight", "research-design"])
    assert rc == 0
    assert (tmp_path / "research-design" / "raw.jsonl").read_text().strip()
