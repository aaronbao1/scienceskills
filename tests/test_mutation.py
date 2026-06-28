import pytest
from eval.harness.mutation import apply_line_edits, MutationError

DOC = "# Skill\n\n- Always cite sources.\n- Be concise.\n"


def test_applies_single_attributed_edit():
    edits = [{"old": "- Be concise.", "new": "- Be concise and specific.", "reason": "task t3 was vague"}]
    out = apply_line_edits(DOC, edits)
    assert "- Be concise and specific." in out
    assert "- Always cite sources." in out  # untouched lines preserved


def test_empty_edits_is_noop():
    assert apply_line_edits(DOC, []) == DOC


def test_missing_line_raises():
    with pytest.raises(MutationError):
        apply_line_edits(DOC, [{"old": "- Nonexistent line.", "new": "x", "reason": "r"}])


def test_ambiguous_edit_raises():
    doc = "- dup\n- dup\n"
    with pytest.raises(MutationError):
        apply_line_edits(doc, [{"old": "- dup", "new": "- once", "reason": "r"}])


def test_missing_reason_raises():
    with pytest.raises(MutationError):
        apply_line_edits(DOC, [{"old": "- Be concise.", "new": "x", "reason": ""}])
    with pytest.raises(MutationError):
        apply_line_edits(DOC, [{"old": "- Be concise.", "new": "x"}])


def test_multiple_edits_apply():
    edits = [
        {"old": "- Always cite sources.", "new": "- Always cite primary sources.", "reason": "t1"},
        {"old": "- Be concise.", "new": "- Be concise and specific.", "reason": "t3"},
    ]
    out = apply_line_edits(DOC, edits)
    assert "- Always cite primary sources." in out
    assert "- Be concise and specific." in out
