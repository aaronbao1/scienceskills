import json
import pytest
from eval.harness import capture

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
