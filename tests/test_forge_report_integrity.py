from eval.harness.forge_report import (
    _integrity_lines,
    render_stat_proposal,
    render_promotion_proposal,
)
from eval.harness.gate import PromotionDecision
from eval.harness.stats import StatVerdict


def test_integrity_lines_empty_for_plain_tally():
    plain = {"candidate_wins": 1, "incumbent_wins": 0, "ties": 0, "candidate_win_rate": 1.0}
    assert _integrity_lines(plain) == []


def test_integrity_lines_render_flags():
    rich = {
        "candidate_wins": 1, "incumbent_wins": 0, "ties": 0, "candidate_win_rate": 1.0,
        "panel_independent": False, "panel_reasons": ["a judge shares the agent family: anthropic"],
        "mean_disagreement": 0.33, "verbosity_flags": ["t1"], "injection_flags": ["t1"],
    }
    text = "\n".join(_integrity_lines(rich))
    assert "Judge panel independent: no" in text
    assert "shares the agent family" in text
    assert "Verbosity-flagged tasks: t1" in text
    assert "Judge-injection flagged tasks: t1" in text


def test_stat_proposal_includes_integrity():
    verdict = StatVerdict(0.10, 0.02, 0.18, 0.031, 0.05, True)
    decision = PromotionDecision(True, "promote: ...")
    rich = {
        "candidate_wins": 1, "incumbent_wins": 0, "ties": 0, "candidate_win_rate": 1.0,
        "panel_independent": True, "panel_reasons": [],
        "mean_disagreement": 0.0, "verbosity_flags": [], "injection_flags": [],
    }
    md = render_stat_proposal("demo", verdict, decision, rich, [], n_obs=6)
    assert "Judge panel independent: yes" in md


def test_legacy_proposal_unchanged_without_keys():
    decision = PromotionDecision(True, "promote: +0.100")
    plain = {"candidate_wins": 1, "incumbent_wins": 0, "ties": 0, "candidate_win_rate": 1.0}
    md = render_promotion_proposal("demo", 0.7, 0.8, decision, plain, [])
    assert "Judge panel independent" not in md  # no integrity keys -> no extra lines
