import json
from eval.harness.loop_control import loop_decision, render_loop_report, main


def _continue_history():
    return {
        "rounds": [{"proxy": 0.70, "gold": 0.70}, {"proxy": 0.78, "gold": 0.76}, {"proxy": 0.85, "gold": 0.82}],
        "promotions": ["ground_truth", "judge_only"],
        "seed_ids": ["s1", "s2"], "current_ids": ["s1", "s2", "n1"],
        "dev_gate_deltas": [0.0] * 8,
    }


def _halt_history():
    h = _continue_history()
    h["rounds"] = [{"proxy": 0.70, "gold": 0.80}, {"proxy": 0.78, "gold": 0.78}, {"proxy": 0.85, "gold": 0.75}]
    return h


def test_continue_decision():
    d = loop_decision(_continue_history())
    assert d["halt"] is False
    assert d["goodhart"]["halt"] is False


def test_halt_on_overoptimization():
    d = loop_decision(_halt_history())
    assert d["halt"] is True
    assert d["goodhart"]["halt"] is True


def test_halt_on_broken_anchor():
    h = _continue_history()
    h["current_ids"] = ["s2", "n1"]  # dropped s1
    d = loop_decision(h)
    assert d["halt"] is True
    assert d["anchor"]["intact"] is False


def test_render_mentions_decision():
    md = render_loop_report(loop_decision(_halt_history()))
    assert "# Loop control" in md
    assert "HALT" in md


def test_main_exit_codes(tmp_path):
    cont = tmp_path / "cont.json"
    cont.write_text(json.dumps(_continue_history()), encoding="utf-8")
    assert main([str(cont)]) == 0

    halt = tmp_path / "halt.json"
    halt.write_text(json.dumps(_halt_history()), encoding="utf-8")
    assert main([str(halt)]) == 1


def test_main_bad_input(tmp_path):
    bad = tmp_path / "bad.json"
    bad.write_text("not json", encoding="utf-8")
    assert main([str(bad)]) == 2
