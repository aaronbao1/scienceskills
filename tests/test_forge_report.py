from eval.harness.forge_report import render_promotion_proposal
from eval.harness.gate import PromotionDecision


def test_renders_proposal():
    decision = PromotionDecision(True, "promote: +0.100 over incumbent, no critical regression")
    tournament = {"candidate_wins": 3, "incumbent_wins": 1, "ties": 0, "candidate_win_rate": 0.75}
    per_task = [{"task_id": "t1", "incumbent": 0.7, "candidate": 0.8, "critical": True}]
    md = render_promotion_proposal("literature-review", 0.70, 0.80, decision, tournament, per_task)
    assert "# Promotion proposal — literature-review" in md
    assert "PROMOTE" in md
    assert "candidate win rate 0.75" in md
    assert "t1" in md


def test_renders_reject():
    decision = PromotionDecision(False, "insufficient gain: +0.005 < margin 0.02")
    tournament = {"candidate_wins": 1, "incumbent_wins": 1, "ties": 2, "candidate_win_rate": 0.25}
    md = render_promotion_proposal("research-design", 0.80, 0.805, decision, tournament, [])
    assert "REJECT" in md
    assert "insufficient gain" in md
