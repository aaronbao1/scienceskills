# tests/test_forge.py
from __future__ import annotations

import json
import pytest
from eval.harness import forge, monitor

def _version(hash_, score):
    return {"hash": hash_, "runs": [
        {"task_id": "t", "seed": s, "score": score, "critical": False, "split": "gate"} for s in (1, 2, 3)]}

def _results(inc_score, cand_score):
    return {"skill": "research-design",
            "incumbent": _version("h0", inc_score), "candidate": _version("h1", cand_score)}

def test_promote_exit0_appends_one_round(tmp_path, monkeypatch):
    monkeypatch.setattr(forge, "INSIGHTS_ROOT", tmp_path)
    monkeypatch.setattr(monitor, "INSIGHTS_ROOT", tmp_path)
    out = forge.evaluate(_results(0.50, 0.70), now_iso="2026-06-28T00:00:00Z")
    assert out["exit"] == 0 and out["decision"] == "promote"
    hist = (tmp_path / "research-design" / "gate-history.jsonl").read_text().splitlines()
    assert len(hist) == 1 and json.loads(hist[0])["round"] == 1

def test_reject_exit1(tmp_path, monkeypatch):
    monkeypatch.setattr(forge, "INSIGHTS_ROOT", tmp_path)
    monkeypatch.setattr(monitor, "INSIGHTS_ROOT", tmp_path)
    out = forge.evaluate(_results(0.50, 0.50), now_iso="2026-06-28T00:00:00Z")
    assert out["exit"] == 1 and out["decision"] == "reject"

def test_halt_exit2_when_monitor_halts(tmp_path, monkeypatch):
    monkeypatch.setattr(forge, "INSIGHTS_ROOT", tmp_path)
    monkeypatch.setattr(monitor, "INSIGHTS_ROOT", tmp_path)
    d = tmp_path / "research-design"; d.mkdir(parents=True)
    (d / "raw.jsonl").write_text("\n".join(json.dumps({"signals": {"approval": a}}) for a in (False, True, True)) + "\n")
    (d / "gate-history.jsonl").write_text("\n".join(json.dumps({"gold_gate_mean": g}) for g in (0.6, 0.55, 0.5)) + "\n")
    out = forge.evaluate(_results(0.50, 0.90), now_iso="2026-06-28T00:00:00Z")
    assert out["exit"] == 2 and out["decision"] == "halt"


def test_main_bad_input_returns_2(tmp_path):
    # Missing file — should return 2, not raise.
    assert forge.main(["research-design", "/no/such/file.json"]) == 2

    # Malformed JSON — should return 2, not raise.
    bad = tmp_path / "bad.json"
    bad.write_text("{ not valid json }")
    assert forge.main(["research-design", str(bad)]) == 2


def _results_per_seed(inc_score: float, cand_scores: list[float]) -> dict:
    """Build results with one run per seed for each of seeds 1/2/3."""
    inc_runs = [
        {"task_id": "t", "seed": s, "score": inc_score, "critical": False, "split": "gate"}
        for s in (1, 2, 3)
    ]
    cand_runs = [
        {"task_id": "t", "seed": s, "score": sc, "critical": False, "split": "gate"}
        for s, sc in zip((1, 2, 3), cand_scores)
    ]
    return {
        "skill": "research-design",
        "incumbent": {"hash": "h0", "runs": inc_runs},
        "candidate": {"hash": "h1", "runs": cand_runs},
    }


def test_gold_per_seed_is_absolute(tmp_path, monkeypatch):
    monkeypatch.setattr(forge, "INSIGHTS_ROOT", tmp_path)
    monkeypatch.setattr(monitor, "INSIGHTS_ROOT", tmp_path)
    cand_scores = [0.7, 0.72, 0.71]
    results = _results_per_seed(0.5, cand_scores)
    forge.evaluate(results, now_iso="2026-06-28T00:00:00Z")
    hist = (tmp_path / "research-design" / "gate-history.jsonl").read_text().splitlines()
    rec = json.loads(hist[0])
    assert rec["gold_per_seed"] == pytest.approx([0.7, 0.72, 0.71])
