import pytest
from eval.harness.tasks import load_tasks, BenchmarkError, Task


def _write(tmp_path, text):
    p = tmp_path / "tasks.yaml"
    p.write_text(text, encoding="utf-8")
    return p


def test_loads_ground_truth_and_judge_tasks(tmp_path):
    p = _write(tmp_path, """
- id: t1
  kind: ground_truth
  prompt: Compute the mean of [1,2,3].
  scorer: numeric
  expected: 2.0
  tolerance: 0.001
- id: t2
  kind: judge
  prompt: Critique this method choice.
""")
    tasks = load_tasks(p)
    assert [t.id for t in tasks] == ["t1", "t2"]
    assert isinstance(tasks[0], Task)
    assert tasks[0].scorer == "numeric"
    assert tasks[1].kind == "judge"


def test_duplicate_id_raises(tmp_path):
    p = _write(tmp_path, """
- id: dup
  kind: judge
  prompt: a
- id: dup
  kind: judge
  prompt: b
""")
    with pytest.raises(BenchmarkError):
        load_tasks(p)


def test_ground_truth_without_scorer_raises(tmp_path):
    p = _write(tmp_path, """
- id: t1
  kind: ground_truth
  prompt: a
  expected: 1
""")
    with pytest.raises(BenchmarkError):
        load_tasks(p)


def test_unknown_kind_raises(tmp_path):
    p = _write(tmp_path, """
- id: t1
  kind: nonsense
  prompt: a
""")
    with pytest.raises(BenchmarkError):
        load_tasks(p)


def test_non_list_top_level_raises(tmp_path):
    p = _write(tmp_path, "id: x\nkind: judge\nprompt: a\n")
    with pytest.raises(BenchmarkError):
        load_tasks(p)


def test_non_mapping_item_raises(tmp_path):
    p = _write(tmp_path, "- just a string\n")
    with pytest.raises(BenchmarkError):
        load_tasks(p)


def test_missing_prompt_raises(tmp_path):
    p = _write(tmp_path, "- id: t1\n  kind: judge\n")
    with pytest.raises(BenchmarkError):
        load_tasks(p)


def test_ground_truth_without_expected_raises(tmp_path):
    p = _write(tmp_path, "- id: t1\n  kind: ground_truth\n  prompt: a\n  scorer: exact\n")
    with pytest.raises(BenchmarkError):
        load_tasks(p)


def test_non_string_id_message_mentions_string(tmp_path):
    p = _write(tmp_path, "- id: 0\n  kind: judge\n  prompt: a\n")
    with pytest.raises(BenchmarkError, match="non-empty string"):
        load_tasks(p)


def test_non_string_prompt_raises(tmp_path):
    p = _write(tmp_path, "- id: t1\n  kind: judge\n  prompt: 0\n")
    with pytest.raises(BenchmarkError, match="non-empty string"):
        load_tasks(p)
