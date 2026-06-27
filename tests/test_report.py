from eval.harness.report import render_comparison


def test_renders_markdown_table_with_rows():
    rows = [
        {"version": "v1", "task_id": "t1", "passed": True, "score": 1.0, "detail": "ok"},
        {"version": "v2", "task_id": "t1", "passed": False, "score": 0.0, "detail": "miss"},
    ]
    md = render_comparison("faithful-implementation", rows)
    assert "# Eval report — faithful-implementation" in md
    assert "| version | task | passed | score | detail |" in md
    assert "t1" in md
    assert "v1" in md and "v2" in md


def test_per_version_summary_present():
    rows = [
        {"version": "v1", "task_id": "t1", "passed": True, "score": 1.0, "detail": "ok"},
        {"version": "v1", "task_id": "t2", "passed": False, "score": 0.0, "detail": "miss"},
    ]
    md = render_comparison("s", rows)
    assert "v1" in md
    assert "1/2" in md  # passed 1 of 2
