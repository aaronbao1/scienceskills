# tests/test_monitor.py
import json
from eval.harness import monitor

def _seed(tmp_path, skill, approvals, golds):
    d = tmp_path / skill
    d.mkdir(parents=True)
    (d / "raw.jsonl").write_text(
        "\n".join(json.dumps({"signals": {"approval": a}}) for a in approvals) + "\n")
    (d / "gate-history.jsonl").write_text(
        "\n".join(json.dumps({"gold_gate_mean": g}) for g in golds) + "\n")

def test_halt_when_proxy_up_gold_down(tmp_path, monkeypatch):
    monkeypatch.setattr(monitor, "INSIGHTS_ROOT", tmp_path)
    _seed(tmp_path, "research-design", approvals=[False, True, True], golds=[0.6, 0.55, 0.5])
    assert monitor.check("research-design")["status"] == "halt"

def test_ok_when_both_rise(tmp_path, monkeypatch):
    monkeypatch.setattr(monitor, "INSIGHTS_ROOT", tmp_path)
    _seed(tmp_path, "research-design", approvals=[False, True, True], golds=[0.5, 0.55, 0.6])
    assert monitor.check("research-design")["status"] == "ok"

def test_ok_when_history_too_short(tmp_path, monkeypatch):
    monkeypatch.setattr(monitor, "INSIGHTS_ROOT", tmp_path)
    _seed(tmp_path, "research-design", approvals=[True], golds=[0.5])
    assert monitor.check("research-design")["status"] == "ok"
