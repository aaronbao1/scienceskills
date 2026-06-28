from eval.harness.tournament import check_panel_independence, verbosity_flag


def test_panel_independent_when_disjoint():
    out = check_panel_independence(["openai", "cohere", "google"], "anthropic")
    assert out["independent"] is True
    assert out["reasons"] == []


def test_panel_not_independent_too_few_families():
    out = check_panel_independence(["openai", "openai", "cohere"], "anthropic")
    assert out["independent"] is False
    assert any("distinct families" in r for r in out["reasons"])


def test_panel_not_independent_shares_agent_family():
    out = check_panel_independence(["openai", "cohere", "anthropic"], "anthropic")
    assert out["independent"] is False
    assert any("agent family" in r for r in out["reasons"])


def test_panel_not_independent_too_few_judges():
    out = check_panel_independence(["openai", "cohere"], "anthropic")
    assert out["independent"] is False
    assert any("judges" in r for r in out["reasons"])


def test_verbosity_flag_triggers_when_winner_longer():
    assert verbosity_flag("candidate", 100, 200) is True
    assert verbosity_flag("incumbent", 300, 100) is True


def test_verbosity_flag_quiet_when_similar_or_no_winner():
    assert verbosity_flag("candidate", 100, 110) is False
    assert verbosity_flag("tie", 100, 999) is False
