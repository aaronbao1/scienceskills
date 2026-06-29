# tests/test_forge.py
import json
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
