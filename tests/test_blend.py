import pytest
from eval.harness.blend import (
    parse_rubric_weights,
    blend_dimension_scores,
    overall_score,
    RubricError,
)

RUBRIC = """# Rubric — demo
- **Alpha thing (weight 0.50):** ...
- **Beta thing (weight 0.50):** ...
"""


def test_parse_rubric_weights():
    w = parse_rubric_weights(RUBRIC)
    assert w == {"alpha thing": 0.5, "beta thing": 0.5}


def test_parse_rubric_weights_rejects_bad_sum():
    bad = "- **A (weight 0.50):** x\n- **B (weight 0.40):** y\n"
    with pytest.raises(RubricError):
        parse_rubric_weights(bad)


def test_parse_rubric_weights_rejects_empty():
    with pytest.raises(RubricError):
        parse_rubric_weights("# no dimensions here\n")


def test_blend_dimension_scores():
    weights = {"alpha thing": 0.5, "beta thing": 0.5}
    scores = {"alpha thing": 4.0, "beta thing": 2.0}
    # 0.5*(4/4) + 0.5*(2/4) = 0.5 + 0.25 = 0.75
    assert blend_dimension_scores(weights, scores) == pytest.approx(0.75)


def test_blend_missing_dimension_raises():
    with pytest.raises(RubricError):
        blend_dimension_scores({"a": 1.0}, {})


def test_blend_out_of_range_raises():
    with pytest.raises(RubricError):
        blend_dimension_scores({"a": 1.0}, {"a": 5.0})


def test_overall_score():
    assert overall_score([1.0, 0.0, 0.5]) == pytest.approx(0.5)


def test_overall_score_empty_raises():
    with pytest.raises(ValueError):
        overall_score([])
