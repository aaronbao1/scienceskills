import json
from eval.harness.forge import content_hash, evaluate, main
from eval.harness.gate import PromotionDecision


def _results(cand_score, critical=False):
    return {
        "skill": "demo",
        "margin": 0.02,
        "incumbent": {"hash": "i", "task_scores": [{"task_id": "t1", "score": 0.70, "critical": critical}]},
        "candidate": {"hash": "c", "task_scores": [{"task_id": "t1", "score": cand_score, "critical": critical}]},
        "tournament": [{"task_id": "t1", "winner": "candidate"}],
    }


def test_content_hash_stable_and_short():
    h1 = content_hash("hello")
    h2 = content_hash("hello")
    assert h1 == h2
    assert len(h1) == 12
    assert content_hash("world") != h1


def test_evaluate_promotes_on_gain():
    decision, report = evaluate(_results(0.90))
    assert isinstance(decision, PromotionDecision)
    assert decision.promote
    assert "# Promotion proposal — demo" in report


def test_evaluate_rejects_small_gain():
    decision, _ = evaluate(_results(0.705))
    assert not decision.promote


def test_main_exit_codes(tmp_path):
    promote_file = tmp_path / "promote.json"
    promote_file.write_text(json.dumps(_results(0.90)), encoding="utf-8")
    assert main([str(promote_file)]) == 0

    reject_file = tmp_path / "reject.json"
    reject_file.write_text(json.dumps(_results(0.705)), encoding="utf-8")
    assert main([str(reject_file)]) == 1


def test_incumbent_critical_regression_blocks_even_with_overall_gain():
    results = {
        "skill": "demo", "margin": 0.02,
        "incumbent": {"hash": "i", "task_scores": [
            {"task_id": "t1", "score": 1.0, "critical": True},
            {"task_id": "t2", "score": 0.0},
            {"task_id": "t3", "score": 0.0}]},
        "candidate": {"hash": "c", "task_scores": [
            {"task_id": "t1", "score": 0.0},
            {"task_id": "t2", "score": 1.0},
            {"task_id": "t3", "score": 1.0}]},
        "tournament": []}
    decision, _ = evaluate(results)
    assert not decision.promote
    assert "t1" in decision.reason


def test_load_results_roundtrip(tmp_path):
    import json
    from eval.harness.forge import load_results
    p = tmp_path / "r.json"
    payload = {"skill": "x", "margin": 0.02, "incumbent": {"hash": "i", "task_scores": []}, "candidate": {"hash": "c", "task_scores": []}, "tournament": []}
    p.write_text(json.dumps(payload), encoding="utf-8")
    assert load_results(p) == payload


def test_main_empty_task_scores_returns_2(tmp_path):
    import json
    p = tmp_path / "e.json"
    p.write_text(
        json.dumps(
            {
                "skill": "x",
                "incumbent": {"task_scores": []},
                "candidate": {"task_scores": []},
                "tournament": [],
            }
        ),
        encoding="utf-8",
    )
    assert main([str(p)]) == 2
