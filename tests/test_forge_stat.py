import json
import pytest
from eval.harness.forge import build_paired_deltas, aggregate_per_task, evaluate, main
from eval.harness.gate import PromotionDecision


def _run(tid, score, seed=0, split="gate", critical=False):
    return {"task_id": tid, "split": split, "seed": seed, "score": score, "critical": critical}


def test_build_paired_deltas_gate_only_matched_by_task_and_seed():
    inc = [_run("g1", 0.7, 0), _run("g1", 0.7, 1), _run("d1", 0.5, 0, split="dev")]
    cand = [_run("g1", 0.8, 0), _run("g1", 0.9, 1), _run("d1", 0.9, 0, split="dev")]
    deltas = build_paired_deltas(inc, cand)
    assert sorted(deltas) == pytest.approx([0.1, 0.2])  # dev pair excluded


def test_aggregate_per_task_seed_means():
    inc = [_run("g1", 0.6, 0), _run("g1", 0.8, 1)]
    cand = [_run("g1", 0.7, 0), _run("g1", 0.9, 1)]
    per_task = aggregate_per_task(inc, cand)
    assert per_task[0]["task_id"] == "g1"
    assert per_task[0]["incumbent"] == 0.7
    assert per_task[0]["candidate"] == 0.8


def _results(inc_scores, cand_scores, n_candidates=1, critical=False):
    inc = [_run(f"g{i}", s, 0, critical=critical) for i, s in enumerate(inc_scores)]
    cand = [_run(f"g{i}", s, 0, critical=critical) for i, s in enumerate(cand_scores)]
    return {
        "skill": "demo",
        "alpha": 0.05,
        "n_candidates": n_candidates,
        "seed": 0,
        "incumbent": {"hash": "i", "runs": inc},
        "candidate": {"hash": "c", "runs": cand},
        "tournament": [{"task_id": "g0", "winner": "candidate"}],
    }


def test_evaluate_promotes_on_significant_holdout():
    # 6 gate tasks, candidate +0.1 each -> p = 0.03125, CI low > 0.
    res = _results([0.7] * 6, [0.8] * 6)
    decision, report = evaluate(res)
    assert isinstance(decision, PromotionDecision)
    assert decision.promote
    assert "# Promotion proposal — demo" in report
    assert "Held-out observations: 6" in report


def test_evaluate_rejects_underpowered_holdout():
    # 5 gate tasks -> p = 0.0625, cannot clear alpha.
    res = _results([0.7] * 5, [0.8] * 5)
    decision, _ = evaluate(res)
    assert not decision.promote


def test_evaluate_bonferroni_blocks_three_candidates():
    res = _results([0.7] * 6, [0.8] * 6, n_candidates=3)
    decision, _ = evaluate(res)
    assert not decision.promote  # 0.03125 >= 0.05/3


def test_legacy_task_scores_path_still_works():
    legacy = {
        "skill": "demo",
        "margin": 0.02,
        "incumbent": {"hash": "i", "task_scores": [{"task_id": "t1", "score": 0.70, "critical": False}]},
        "candidate": {"hash": "c", "task_scores": [{"task_id": "t1", "score": 0.90, "critical": False}]},
        "tournament": [{"task_id": "t1", "winner": "candidate"}],
    }
    decision, report = evaluate(legacy)
    assert decision.promote
    assert "# Promotion proposal — demo" in report


def test_main_exit_codes(tmp_path):
    promote = tmp_path / "p.json"
    promote.write_text(json.dumps(_results([0.7] * 6, [0.8] * 6)), encoding="utf-8")
    assert main([str(promote)]) == 0

    reject = tmp_path / "r.json"
    reject.write_text(json.dumps(_results([0.7] * 5, [0.8] * 5)), encoding="utf-8")
    assert main([str(reject)]) == 1
