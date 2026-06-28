# Harness Hardening Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Apply the high-value, low-risk hardening items the code reviews deferred during the five build plans — friendlier/robust error handling and a few real robustness fixes in the eval harness — without changing any public behavior the suite relies on.

**Architecture:** A focused pass over existing `eval/harness/` modules and `.gitignore`. Each task modifies one or two files plus tests. All 114 existing tests must stay green; these changes add robustness and coverage, they do not alter the documented contracts. Items already fixed by the Plan-2 hardening pass (tasks-loader type guards, scorer `tolerance is None`, lint branch-coverage tests) are intentionally excluded.

**Tech Stack:** Python 3.9+, pytest, PyYAML.

## Global Constraints

- Run pytest as `python3 -m pytest` (no `pytest` on PATH); pyyaml + pytest already installed for system `python3` (3.9.6); no venv.
- Every harness module keeps its `from __future__ import annotations` first line.
- **Preserve all existing behavior and tests:** the full suite (currently 114 tests) must remain green; these are additive hardening changes. Do not change public function signatures.
- No `TODO`/`TBD`/`FIXME` tokens. DRY, YAGNI, TDD, frequent commits.
- Never implement on `main`/`master` without consent — work on a feature branch.

---

### Task 1: `.gitignore` + frontmatter parser hardening

**Files:**
- Modify: `.gitignore`
- Modify: `eval/harness/frontmatter.py`
- Modify: `tests/test_frontmatter.py` (append tests)

**Interfaces:**
- Consumes/produces: `parse_frontmatter(text) -> tuple[dict, str]` — same signature; now accepts CRLF, requires the opening `---` on its own line, and strips exactly one newline after the closing `---`.

- [ ] **Step 1: Append the new tests**

Append to `tests/test_frontmatter.py`:
```python
def test_handles_crlf_line_endings():
    text = "---\r\nname: foo\r\ndescription: bar\r\n---\r\n# Title\r\n\r\nBody.\r\n"
    meta, body = parse_frontmatter(text)
    assert meta == {"name": "foo", "description": "bar"}
    assert body.startswith("# Title")


def test_strips_exactly_one_leading_newline():
    text = "---\nname: foo\n---\n\n# Title\n"
    _, body = parse_frontmatter(text)
    assert body == "\n# Title\n"
```

- [ ] **Step 2: Run the new tests to see them fail**

Run: `python3 -m pytest tests/test_frontmatter.py::test_handles_crlf_line_endings tests/test_frontmatter.py::test_strips_exactly_one_leading_newline -v`
Expected: FAIL — current `parse_frontmatter` mishandles CRLF (the body starts with a stray `\r\n` so `body.startswith("# Title")` is false), and `lstrip("\n")` strips all leading newlines (so body would be `# Title\n` not `\n# Title\n`). (The new code also tightens the opening delimiter to `---\n`, a safe hardening exercised by the existing missing-frontmatter test.)

- [ ] **Step 3: Replace `parse_frontmatter`**

Replace the body of `eval/harness/frontmatter.py` (keep the `from __future__ import annotations` and `import yaml` lines and the `FrontmatterError` class) so the function reads:
```python
def parse_frontmatter(text: str) -> tuple[dict, str]:
    """Split a markdown doc with leading YAML frontmatter into (metadata, body).

    Accepts LF or CRLF line endings, requires the opening ``---`` on its own
    line, and strips exactly one newline after the closing ``---`` so an
    intentionally blank first body line is preserved.
    """
    normalized = text.replace("\r\n", "\n")
    if not normalized.startswith("---\n"):
        raise FrontmatterError("missing frontmatter: file must start with a '---' line")
    parts = normalized.split("---", 2)
    if len(parts) < 3:
        raise FrontmatterError("unterminated frontmatter block")
    try:
        meta = yaml.safe_load(parts[1]) or {}
    except yaml.YAMLError as exc:
        raise FrontmatterError(f"invalid YAML frontmatter: {exc}") from exc
    if not isinstance(meta, dict):
        raise FrontmatterError("frontmatter must be a mapping")
    body = parts[2][1:] if parts[2].startswith("\n") else parts[2]
    return meta, body
```

Add `*.egg-info/` and `dist/` to `.gitignore` (after the existing entries):
```gitignore
*.egg-info/
dist/
```

- [ ] **Step 4: Run the full suite to confirm green**

Run: `python3 -m pytest -q`
Expected: PASS — the three new frontmatter tests pass, and all existing tests (including `tests/test_skills_valid.py`, which lints every SKILL.md through `parse_frontmatter`) stay green. Total 116 passing.

- [ ] **Step 5: Commit**

```bash
git add .gitignore eval/harness/frontmatter.py tests/test_frontmatter.py
git commit -m "fix: harden frontmatter parser (CRLF, one-newline strip, strict delimiter) + gitignore"
```

---

### Task 2: `blend.py` weight-parse hardening

**Files:**
- Modify: `eval/harness/blend.py`
- Modify: `tests/test_blend.py` (append a test)

**Interfaces:**
- Consumes/produces: `parse_rubric_weights(rubric_text) -> dict[str, float]` — same signature; a malformed weight now raises `RubricError` instead of an unhandled `ValueError`.

- [ ] **Step 1: Append the new test**

Append to `tests/test_blend.py`:
```python
def test_parse_rubric_weights_rejects_malformed_weight():
    bad = "- **A (weight 0.1.2):** x\n- **B (weight 0.8):** y\n"
    with pytest.raises(RubricError):
        parse_rubric_weights(bad)
```

- [ ] **Step 2: Run the new test to see it fail**

Run: `python3 -m pytest tests/test_blend.py::test_parse_rubric_weights_rejects_malformed_weight -v`
Expected: FAIL — current code calls `float("0.1.2")`, which raises a bare `ValueError` (not `RubricError`), so `pytest.raises(RubricError)` does not catch it.

- [ ] **Step 3: Wrap the `float()` call**

In `eval/harness/blend.py`, replace the loop body of `parse_rubric_weights` so the `float()` call is guarded:
```python
def parse_rubric_weights(rubric_text: str) -> dict[str, float]:
    """Extract {dimension (lowercased): weight} from a rubric's markdown."""
    weights: dict[str, float] = {}
    for match in _DIM_RE.finditer(rubric_text):
        name = match.group(1).strip().lower()
        try:
            weights[name] = float(match.group(2))
        except ValueError as exc:
            raise RubricError(f"invalid weight for '{name}': {match.group(2)!r}") from exc
    if not weights:
        raise RubricError("no weighted dimensions found")
    total = sum(weights.values())
    if abs(total - 1.0) > 0.001:
        raise RubricError(f"weights sum to {total}, expected 1.0")
    return weights
```
(Leave `_DIM_RE`, `RubricError`, `blend_dimension_scores`, and `overall_score` unchanged.)

- [ ] **Step 4: Run the full suite to confirm green**

Run: `python3 -m pytest -q`
Expected: PASS — the new test passes; all existing blend tests still pass. Total 117 passing.

- [ ] **Step 5: Commit**

```bash
git add eval/harness/blend.py tests/test_blend.py
git commit -m "fix: blend raises RubricError on malformed rubric weight"
```

---

### Task 3: `consensus.py` + `forge.py` CLI error robustness

**Files:**
- Modify: `eval/harness/consensus.py` (add `import sys`; harden `main`)
- Modify: `eval/harness/forge.py` (add `import sys`; harden `main`)
- Modify: `tests/test_consensus.py` (append tests)
- Modify: `tests/test_forge.py` (append a test)

**Interfaces:**
- Consumes/produces: both `main(argv) -> int` keep exit 0 (success path) and 1 (negative-but-valid path); they now return **2** with a stderr message on an unreadable/malformed results file or missing required fields, instead of raising an unhandled traceback.

- [ ] **Step 1: Append the new tests**

Append to `tests/test_consensus.py`:
```python
def test_main_missing_answers_returns_2(tmp_path):
    p = tmp_path / "bad.json"
    p.write_text(json.dumps({"verifier_verdicts": [True]}), encoding="utf-8")
    assert main([str(p)]) == 2


def test_main_malformed_json_returns_2(tmp_path):
    p = tmp_path / "bad.json"
    p.write_text("{not json", encoding="utf-8")
    assert main([str(p)]) == 2
```

Append to `tests/test_forge.py`:
```python
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
```

- [ ] **Step 2: Run the new tests to see them fail**

Run: `python3 -m pytest tests/test_consensus.py::test_main_missing_answers_returns_2 tests/test_consensus.py::test_main_malformed_json_returns_2 tests/test_forge.py::test_main_empty_task_scores_returns_2 -v`
Expected: FAIL — current `main`s raise an unhandled `KeyError`/`json.JSONDecodeError`/`ValueError` (not a clean return of 2).

- [ ] **Step 3: Harden the two `main` functions**

In `eval/harness/consensus.py`, add `import sys` (with the other imports) and replace `main` with:
```python
def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="eval.harness.consensus")
    parser.add_argument("results", help="path to a reasoning results JSON file")
    args = parser.parse_args(argv)
    try:
        data = json.loads(Path(args.results).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"error: cannot read results file: {exc}", file=sys.stderr)
        return 2
    if not data.get("answers"):
        print("error: results JSON must contain a non-empty 'answers' list", file=sys.stderr)
        return 2
    agg = aggregate(
        data["answers"],
        data.get("verifier_verdicts"),
        data.get("agreement_threshold", 0.6),
        data.get("confidence_threshold", 0.7),
    )
    print(render(agg))
    return 0 if agg.converged else 1
```

In `eval/harness/forge.py`, add `import sys` (with the other imports) and replace `main` with:
```python
def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="eval.harness.forge")
    parser.add_argument("results", help="path to a forge results JSON file")
    args = parser.parse_args(argv)
    try:
        results = load_results(args.results)
    except (OSError, json.JSONDecodeError) as exc:
        print(f"error: cannot read results file: {exc}", file=sys.stderr)
        return 2
    try:
        decision, report = evaluate(results)
    except (KeyError, ValueError) as exc:
        print(f"error: malformed results: {exc}", file=sys.stderr)
        return 2
    print(report)
    return 0 if decision.promote else 1
```

- [ ] **Step 4: Run the full suite to confirm green**

Run: `python3 -m pytest -q`
Expected: PASS — the three new tests pass; existing consensus/forge CLI tests (exit 0/1 paths) still pass. Total 120 passing.

- [ ] **Step 5: Commit**

```bash
git add eval/harness/consensus.py eval/harness/forge.py tests/test_consensus.py tests/test_forge.py
git commit -m "fix: consensus + forge CLIs return 2 with a clean message on bad input"
```

---

### Task 4: `tasks.py` tidy + non-string-prompt coverage

**Files:**
- Modify: `eval/harness/tasks.py` (one-line tidy)
- Modify: `tests/test_tasks_loader.py` (append a test)

**Interfaces:**
- Consumes/produces: `load_tasks(path) -> list[Task]` — unchanged behavior; the `Task(...)` construction now uses the already-validated local `prompt` variable instead of re-indexing `item["prompt"]`.

- [ ] **Step 1: Append the new test**

Append to `tests/test_tasks_loader.py`:
```python
def test_non_string_prompt_raises(tmp_path):
    p = _write(tmp_path, "- id: t1\n  kind: judge\n  prompt: 0\n")
    with pytest.raises(BenchmarkError, match="non-empty string"):
        load_tasks(p)
```

- [ ] **Step 2: Run the new test**

Run: `python3 -m pytest tests/test_tasks_loader.py::test_non_string_prompt_raises -v`
Expected: PASS immediately — the `isinstance(prompt, str)` guard added in the Plan-2 hardening already rejects `prompt: 0` with a "must be a non-empty string" message. This test adds regression coverage for that existing guard (no code change needed to pass it).

- [ ] **Step 3: Tidy the `Task` construction**

In `eval/harness/tasks.py`, in `load_tasks`, change the `Task(...)` call's `prompt=item["prompt"]` to use the validated local variable:
```python
        tasks.append(
            Task(
                id=tid,
                prompt=prompt,
                kind=kind,
                scorer=scorer,
                expected=item.get("expected"),
                tolerance=item.get("tolerance"),
            )
        )
```
(The local `prompt` was already validated as a non-empty string earlier in the loop; this removes a redundant dict re-index. No behavior change.)

- [ ] **Step 4: Run the full suite to confirm green**

Run: `python3 -m pytest -q`
Expected: PASS — the new test passes and all existing tasks-loader tests stay green. Total 121 passing.

- [ ] **Step 5: Commit**

```bash
git add eval/harness/tasks.py tests/test_tasks_loader.py
git commit -m "test: cover non-string prompt guard; use validated local in Task construction"
```

---

### Task 5: Full-suite green + validate

**Files:**
- Modify: none (verification task; fold any fix into the file that needs it).

- [ ] **Step 1: Run the whole test suite**

Run: `python3 -m pytest -q`
Expected: PASS — 121 tests, no warnings.

- [ ] **Step 2: Run the harness against the real repo**

Run: `python3 -m eval.harness.cli lint`
Expected: `lint: OK`, exit 0 (11 skills — the hardened frontmatter parser must still lint every SKILL.md cleanly).

Run: `python3 -m eval.harness.cli validate`
Expected: `validate: OK`, exit 0 (10 slices).

- [ ] **Step 3: Spot-check the new CLI error paths**

```bash
echo '{not json' > /tmp/bad.json && python3 -m eval.harness.consensus /tmp/bad.json; echo "exit=$?"
```
Expected: a `error: cannot read results file:` line on stderr and `exit=2`.

- [ ] **Step 4: Confirm clean tree**

Run: `git status` (expect clean).

- [ ] **Step 5: Commit (only if any fix was needed)**

```bash
git add -A
git commit -m "test: verify harness hardening suite green"
```

## Self-Review

**Scope coverage:** the high-value deferred items map to tasks — `.gitignore` egg-info + frontmatter robustness (Task 1), blend malformed-weight (Task 2), consensus/forge CLI error robustness (Task 3), tasks tidy + non-string-prompt coverage (Task 4). Excluded as already-fixed: tasks-loader type guards, scorer `tolerance is None`, lint branch-coverage tests (all done in the Plan-2 hardening pass). Excluded as cosmetic per scope: trailing-newline normalization, dead-code comment removal, test-name nits.

**Placeholder scan:** no `TODO`/`TBD`/`FIXME`; all code steps show complete code.

**Type consistency:** all changes preserve existing signatures (`parse_frontmatter`, `parse_rubric_weights`, `main`, `load_tasks`). The frontmatter change keeps all 11 SKILL.md files linting cleanly (they use LF and start with `---\n`). The CLI hardening preserves the existing 0/1 exit contract and adds 2 only for bad input. Each task ends green and is independently reviewable.
