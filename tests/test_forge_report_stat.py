from eval.harness.forge_report import render_stat_proposal
from eval.harness.gate import PromotionDecision
from eval.harness.stats import StatVerdict


def test_renders_significant_proposal():
    verdict = StatVerdict(0.10, 0.02, 0.18, 0.031, 0.05, True)
    decision = PromotionDecision(True, "promote: mean +0.100, CI low +0.020, p=0.031, alpha=0.050 (CI low > 0 and p < alpha)")
    tournament = {"candidate_wins": 3, "incumbent_wins": 1, "ties": 0, "candidate_win_rate": 0.75}
    per_task = [{"task_id": "g1", "incumbent": 0.70, "candidate": 0.80, "critical": False}]
    md = render_stat_proposal("literature-review", verdict, decision, tournament, per_task, n_obs=18)
    assert "# Promotion proposal — literature-review" in md
    assert "PROMOTE" in md
    assert "Held-out observations: 18" in md
    assert "p = 0.031" in md
    assert "g1" in md


def test_renders_no_holdout_reject():
    decision = PromotionDecision(False, "no held-out (gate) observations to test")
    tournament = {"candidate_wins": 0, "incumbent_wins": 0, "ties": 0, "candidate_win_rate": 0.0}
    md = render_stat_proposal("research-design", None, decision, tournament, [], n_obs=0)
    assert "REJECT" in md
    assert "no held-out" in md
