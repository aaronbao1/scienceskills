# scienceskills Plan 1 — Foundation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Stand up the `scienceskills` plugin as an installable Claude Code plugin with a deterministic eval-harness core, the `scientific-rigor` backbone, the master `CLAUDE.md`, and the first lifecycle skill (`faithful-implementation`) proven end-to-end with its benchmark slice.

**Architecture:** A git repo that is simultaneously a Claude Code plugin (skills auto-discovered from `skills/`) and a small Python project (`eval/harness/`, a Python package providing skill linting, benchmark loading, objective scoring, and report rendering — all TDD'd). Skills are markdown (`SKILL.md`); their *structure* is validated by the harness lint, their *content* is the product. This plan ships only the deterministic pieces; live agent-dispatched evaluation and the `skill-forge` loop come in later plans.

**Tech Stack:** Python 3.11+, pytest, PyYAML. Claude Code plugin manifests (JSON). Markdown skills.

## Staging roadmap (this is Plan 1 of 4)

- **Plan 1 (this doc):** scaffold + plugin manifests + deterministic harness core + `scientific-rigor` + master `CLAUDE.md` + `faithful-implementation` + its benchmark slice + composition-contract test.
- **Plan 2:** remaining lifecycle skills — `research-design`, `literature-review`, `rigorous-validation`, `research-synthesis` — each with a benchmark slice + rubric.
- **Plan 3:** humanities skills — `humanities-inquiry`, `argumentation-and-sources` — with slices.
- **Plan 4:** `skill-forge` engine — live `run.py`/`judge.py`/`tournament.py` (agent-dispatched), candidate generation, gating, human-approved promotion, full-loop smoke test.

## Global Constraints

- Plugin name: `scienceskills`. Skills auto-discovered from `skills/<name>/SKILL.md`; do NOT enumerate them in a manifest.
- Every `SKILL.md` frontmatter MUST have `name` (equal to its directory name) and `description` (non-empty, ≤ 1024 chars).
- Skills and `CLAUDE.md` MUST NOT contain the literal placeholder tokens `TODO`, `TBD`, or `FIXME`.
- `CLAUDE.md` MUST stay condensed: ≤ 4000 characters.
- Harness code is a Python package importable as `eval.harness.<module>`; pytest resolves it via `pythonpath = ["."]`.
- Sentence case in all prose and labels. DRY, YAGNI, TDD, frequent commits.
- Python: 3.11+ syntax (`str | None` unions, `dataclass`). Only dependencies: `pyyaml` (runtime), `pytest` (dev).
- Never start implementation on `main`/`master` without explicit user consent; work on a feature branch / worktree.

---

### Task 1: Repo scaffold, Python project, and plugin manifests

**Files:**
- Create: `pyproject.toml`
- Create: `.gitignore`
- Create: `README.md`
- Create: `.claude-plugin/plugin.json`
- Create: `.claude-plugin/marketplace.json`
- Create: `eval/__init__.py` (empty)
- Create: `eval/harness/__init__.py` (empty)
- Create: `tests/__init__.py` (empty)
- Test: `tests/test_plugin_manifest.py`

**Interfaces:**
- Consumes: nothing.
- Produces: a valid plugin repo. Import root: repo root on `sys.path` (via pytest `pythonpath`). Package `eval.harness` exists (empty for now).

- [ ] **Step 1: Write the failing test**

`tests/test_plugin_manifest.py`:
```python
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_plugin_json_is_valid():
    data = json.loads((ROOT / ".claude-plugin" / "plugin.json").read_text())
    assert data["name"] == "scienceskills"
    assert data["version"]
    assert data["description"]


def test_marketplace_lists_the_plugin():
    data = json.loads((ROOT / ".claude-plugin" / "marketplace.json").read_text())
    names = [p["name"] for p in data["plugins"]]
    assert "scienceskills" in names
    plugin = next(p for p in data["plugins"] if p["name"] == "scienceskills")
    assert plugin["source"] == "./"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_plugin_manifest.py -v`
Expected: FAIL — `FileNotFoundError` / collection error (manifests and `pyproject` absent, `pythonpath` not set).

- [ ] **Step 3: Create the scaffold files**

`pyproject.toml`:
```toml
[project]
name = "scienceskills-eval"
version = "0.1.0"
description = "Eval harness for the scienceskills plugin"
requires-python = ">=3.11"
dependencies = ["pyyaml>=6"]

[project.optional-dependencies]
dev = ["pytest>=8"]

[tool.pytest.ini_options]
pythonpath = ["."]
testpaths = ["tests"]
```

`.gitignore`:
```gitignore
__pycache__/
*.pyc
.pytest_cache/
.venv/
eval/reports/
```

`.claude-plugin/plugin.json`:
```json
{
  "name": "scienceskills",
  "description": "A self-improving suite of skills for rigorous scientific research: design, literature review, faithful implementation, validation, synthesis, humanities inquiry, and a skill-improvement engine.",
  "version": "0.1.0",
  "author": {
    "name": "Aaron Bao",
    "email": "aaron.bao64@gmail.com"
  },
  "license": "MIT",
  "keywords": ["science", "research", "rigor", "reproducibility", "skills"]
}
```

`.claude-plugin/marketplace.json`:
```json
{
  "name": "scienceskills-dev",
  "description": "Development marketplace for the scienceskills research skill suite",
  "owner": {
    "name": "Aaron Bao",
    "email": "aaron.bao64@gmail.com"
  },
  "plugins": [
    {
      "name": "scienceskills",
      "description": "A self-improving suite of skills for rigorous scientific research.",
      "version": "0.1.0",
      "source": "./",
      "author": { "name": "Aaron Bao", "email": "aaron.bao64@gmail.com" }
    }
  ]
}
```

`README.md`:
```markdown
# scienceskills

A self-improving Claude Code skill suite for rigorous scientific research.

See `docs/superpowers/specs/2026-06-27-scienceskills-design.md` for the design and
`CLAUDE.md` for the operating standards. Skills live in `skills/`; the eval harness
lives in `eval/`.

## Dev setup

    python -m venv .venv && source .venv/bin/activate
    pip install -e ".[dev]"
    pytest

## Lint skills / validate benchmarks

    python -m eval.harness.cli lint
    python -m eval.harness.cli validate
```

Create the empty `__init__.py` files:
```bash
mkdir -p eval/harness tests
: > eval/__init__.py
: > eval/harness/__init__.py
: > tests/__init__.py
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_plugin_manifest.py -v`
Expected: PASS (2 passed).

- [ ] **Step 5: Commit**

```bash
git add pyproject.toml .gitignore README.md .claude-plugin eval tests
git commit -m "feat: scaffold scienceskills plugin + python project"
```

---

### Task 2: Frontmatter parser

**Files:**
- Create: `eval/harness/frontmatter.py`
- Test: `tests/test_frontmatter.py`

**Interfaces:**
- Consumes: nothing.
- Produces: `parse_frontmatter(text: str) -> tuple[dict, str]` returning `(metadata, body)`; raises `FrontmatterError(ValueError)` on malformed input.

- [ ] **Step 1: Write the failing test**

`tests/test_frontmatter.py`:
```python
import pytest
from eval.harness.frontmatter import parse_frontmatter, FrontmatterError


def test_parses_metadata_and_body():
    text = "---\nname: foo\ndescription: bar\n---\n# Title\n\nBody.\n"
    meta, body = parse_frontmatter(text)
    assert meta == {"name": "foo", "description": "bar"}
    assert body.startswith("# Title")


def test_missing_frontmatter_raises():
    with pytest.raises(FrontmatterError):
        parse_frontmatter("# No frontmatter here\n")


def test_unterminated_frontmatter_raises():
    with pytest.raises(FrontmatterError):
        parse_frontmatter("---\nname: foo\n")


def test_non_mapping_frontmatter_raises():
    with pytest.raises(FrontmatterError):
        parse_frontmatter("---\n- a\n- b\n---\nbody\n")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_frontmatter.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'eval.harness.frontmatter'`.

- [ ] **Step 3: Write minimal implementation**

`eval/harness/frontmatter.py`:
```python
import yaml


class FrontmatterError(ValueError):
    """Raised when a markdown document lacks valid YAML frontmatter."""


def parse_frontmatter(text: str) -> tuple[dict, str]:
    """Split a markdown doc with leading YAML frontmatter into (metadata, body)."""
    if not text.startswith("---"):
        raise FrontmatterError("missing frontmatter: file must start with '---'")
    parts = text.split("---", 2)
    if len(parts) < 3:
        raise FrontmatterError("unterminated frontmatter block")
    try:
        meta = yaml.safe_load(parts[1]) or {}
    except yaml.YAMLError as exc:
        raise FrontmatterError(f"invalid YAML frontmatter: {exc}") from exc
    if not isinstance(meta, dict):
        raise FrontmatterError("frontmatter must be a mapping")
    return meta, parts[2].lstrip("\n")
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_frontmatter.py -v`
Expected: PASS (4 passed).

- [ ] **Step 5: Commit**

```bash
git add eval/harness/frontmatter.py tests/test_frontmatter.py
git commit -m "feat: frontmatter parser for skill markdown"
```

---

### Task 3: Skill structure lint

**Files:**
- Create: `eval/harness/skill_lint.py`
- Test: `tests/test_skill_lint.py`

**Interfaces:**
- Consumes: `eval.harness.frontmatter.parse_frontmatter`, `FrontmatterError`.
- Produces: `lint_skill(skill_dir: str | Path) -> list[str]` (empty list == valid); module constants `PLACEHOLDER_TOKENS: tuple[str, ...]`, `MAX_DESCRIPTION_CHARS: int = 1024`.

- [ ] **Step 1: Write the failing test**

`tests/test_skill_lint.py`:
```python
from pathlib import Path
from eval.harness.skill_lint import lint_skill


def _make_skill(tmp_path: Path, name: str, frontmatter: str, body: str) -> Path:
    d = tmp_path / name
    d.mkdir()
    (d / "SKILL.md").write_text(f"---\n{frontmatter}\n---\n{body}\n", encoding="utf-8")
    return d


def test_valid_skill_has_no_issues(tmp_path):
    d = _make_skill(tmp_path, "good", "name: good\ndescription: Use when testing.", "# Good\n\nBody.")
    assert lint_skill(d) == []


def test_name_mismatch_flagged(tmp_path):
    d = _make_skill(tmp_path, "good", "name: wrong\ndescription: Use when testing.", "# Good\n\nBody.")
    assert any("name" in i for i in lint_skill(d))


def test_missing_description_flagged(tmp_path):
    d = _make_skill(tmp_path, "good", "name: good", "# Good\n\nBody.")
    assert any("description" in i for i in lint_skill(d))


def test_placeholder_token_flagged(tmp_path):
    d = _make_skill(tmp_path, "good", "name: good\ndescription: Use when testing.", "# Good\n\nTODO finish this.")
    assert any("placeholder" in i.lower() for i in lint_skill(d))


def test_missing_skill_md_flagged(tmp_path):
    d = tmp_path / "empty"
    d.mkdir()
    assert any("SKILL.md" in i for i in lint_skill(d))
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_skill_lint.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'eval.harness.skill_lint'`.

- [ ] **Step 3: Write minimal implementation**

`eval/harness/skill_lint.py`:
```python
from pathlib import Path

from eval.harness.frontmatter import FrontmatterError, parse_frontmatter

PLACEHOLDER_TOKENS: tuple[str, ...] = ("TODO", "TBD", "FIXME")
MAX_DESCRIPTION_CHARS: int = 1024


def lint_skill(skill_dir: str | Path) -> list[str]:
    """Return a list of issue strings for a skill directory. Empty == valid."""
    skill_dir = Path(skill_dir)
    md = skill_dir / "SKILL.md"
    if not md.exists():
        return [f"{skill_dir}: missing SKILL.md"]
    text = md.read_text(encoding="utf-8")
    try:
        meta, body = parse_frontmatter(text)
    except FrontmatterError as exc:
        return [f"{md}: {exc}"]

    issues: list[str] = []
    name = meta.get("name")
    if not name:
        issues.append(f"{md}: frontmatter missing 'name'")
    elif name != skill_dir.name:
        issues.append(f"{md}: name '{name}' != directory '{skill_dir.name}'")

    desc = meta.get("description")
    if not desc:
        issues.append(f"{md}: frontmatter missing 'description'")
    elif len(desc) > MAX_DESCRIPTION_CHARS:
        issues.append(f"{md}: description too long ({len(desc)} > {MAX_DESCRIPTION_CHARS})")

    if not body.strip():
        issues.append(f"{md}: empty body")
    elif not body.lstrip().startswith("#"):
        issues.append(f"{md}: body must start with an H1 heading")

    for token in PLACEHOLDER_TOKENS:
        if token in body:
            issues.append(f"{md}: contains placeholder token '{token}'")
    return issues
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_skill_lint.py -v`
Expected: PASS (5 passed).

- [ ] **Step 5: Commit**

```bash
git add eval/harness/skill_lint.py tests/test_skill_lint.py
git commit -m "feat: skill structure lint"
```

---

### Task 4: Benchmark task loader + schema

**Files:**
- Create: `eval/harness/tasks.py`
- Test: `tests/test_tasks_loader.py`

**Interfaces:**
- Consumes: nothing (reads YAML).
- Produces: `@dataclass(frozen=True) Task(id: str, prompt: str, kind: str, scorer: str | None = None, expected: object = None, tolerance: float | None = None)`; `load_tasks(path: str | Path) -> list[Task]`; `BenchmarkError(ValueError)`; constants `VALID_SCORERS`, `VALID_KINDS`.

- [ ] **Step 1: Write the failing test**

`tests/test_tasks_loader.py`:
```python
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_tasks_loader.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'eval.harness.tasks'`.

- [ ] **Step 3: Write minimal implementation**

`eval/harness/tasks.py`:
```python
from dataclasses import dataclass
from pathlib import Path

import yaml

VALID_SCORERS: set[str] = {"exact", "numeric", "contains", "regex"}
VALID_KINDS: set[str] = {"ground_truth", "judge"}


class BenchmarkError(ValueError):
    """Raised when a benchmark tasks.yaml is malformed."""


@dataclass(frozen=True)
class Task:
    id: str
    prompt: str
    kind: str
    scorer: str | None = None
    expected: object = None
    tolerance: float | None = None


def load_tasks(path: str | Path) -> list[Task]:
    path = Path(path)
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(raw, list):
        raise BenchmarkError(f"{path}: top-level must be a list of tasks")
    tasks: list[Task] = []
    seen: set[str] = set()
    for i, item in enumerate(raw):
        if not isinstance(item, dict):
            raise BenchmarkError(f"{path}[{i}]: each task must be a mapping")
        tid = item.get("id")
        if not tid:
            raise BenchmarkError(f"{path}[{i}]: missing 'id'")
        if tid in seen:
            raise BenchmarkError(f"{path}: duplicate id '{tid}'")
        seen.add(tid)
        kind = item.get("kind")
        if kind not in VALID_KINDS:
            raise BenchmarkError(f"{path}[{tid}]: kind must be one of {sorted(VALID_KINDS)}")
        if not item.get("prompt"):
            raise BenchmarkError(f"{path}[{tid}]: missing 'prompt'")
        scorer = item.get("scorer")
        if kind == "ground_truth":
            if scorer not in VALID_SCORERS:
                raise BenchmarkError(
                    f"{path}[{tid}]: ground_truth needs scorer in {sorted(VALID_SCORERS)}"
                )
            if "expected" not in item:
                raise BenchmarkError(f"{path}[{tid}]: ground_truth needs 'expected'")
        tasks.append(
            Task(
                id=tid,
                prompt=item["prompt"],
                kind=kind,
                scorer=scorer,
                expected=item.get("expected"),
                tolerance=item.get("tolerance"),
            )
        )
    return tasks
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_tasks_loader.py -v`
Expected: PASS (4 passed).

- [ ] **Step 5: Commit**

```bash
git add eval/harness/tasks.py tests/test_tasks_loader.py
git commit -m "feat: benchmark task loader + schema"
```

---

### Task 5: Objective scorers

**Files:**
- Create: `eval/harness/score.py`
- Test: `tests/test_score.py`

**Interfaces:**
- Consumes: nothing.
- Produces: `@dataclass(frozen=True) ScoreResult(passed: bool, score: float, detail: str)`; `score_output(scorer: str, expected, actual: str, tolerance: float | None = None) -> ScoreResult`; raises `ValueError` on unknown scorer.

- [ ] **Step 1: Write the failing test**

`tests/test_score.py`:
```python
import pytest
from eval.harness.score import score_output, ScoreResult


def test_exact_match():
    r = score_output("exact", "hello", " hello ")
    assert isinstance(r, ScoreResult)
    assert r.passed and r.score == 1.0


def test_exact_mismatch():
    assert not score_output("exact", "a", "b").passed


def test_numeric_within_tolerance():
    assert score_output("numeric", 2.0, "2.0005", tolerance=0.001).passed


def test_numeric_outside_tolerance():
    assert not score_output("numeric", 2.0, "2.5", tolerance=0.001).passed


def test_numeric_non_numeric_actual():
    assert not score_output("numeric", 2.0, "not a number", tolerance=0.1).passed


def test_contains():
    assert score_output("contains", "needle", "a needle in hay").passed


def test_regex():
    assert score_output("regex", r"\d{3}", "abc123").passed


def test_unknown_scorer_raises():
    with pytest.raises(ValueError):
        score_output("bogus", 1, "1")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_score.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'eval.harness.score'`.

- [ ] **Step 3: Write minimal implementation**

`eval/harness/score.py`:
```python
import re
from dataclasses import dataclass


@dataclass(frozen=True)
class ScoreResult:
    passed: bool
    score: float
    detail: str


def _binary(passed: bool, detail_ok: str, detail_no: str) -> ScoreResult:
    return ScoreResult(passed, 1.0 if passed else 0.0, detail_ok if passed else detail_no)


def score_output(scorer: str, expected, actual: str, tolerance: float | None = None) -> ScoreResult:
    if scorer == "exact":
        ok = str(expected).strip() == str(actual).strip()
        return _binary(ok, "exact match", f"expected {expected!r}, got {actual!r}")
    if scorer == "contains":
        ok = str(expected) in str(actual)
        return _binary(ok, "substring found", f"{expected!r} not in output")
    if scorer == "regex":
        ok = re.search(str(expected), str(actual)) is not None
        return _binary(ok, "regex matched", f"/{expected}/ did not match")
    if scorer == "numeric":
        tol = tolerance or 0.0
        try:
            a, e = float(actual), float(expected)
        except (TypeError, ValueError):
            return ScoreResult(False, 0.0, f"non-numeric: expected {expected!r}, got {actual!r}")
        diff = abs(a - e)
        return _binary(diff <= tol, f"|{a}-{e}|={diff} <= {tol}", f"|{a}-{e}|={diff} > {tol}")
    raise ValueError(f"unknown scorer: {scorer!r}")
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_score.py -v`
Expected: PASS (8 passed).

- [ ] **Step 5: Commit**

```bash
git add eval/harness/score.py tests/test_score.py
git commit -m "feat: objective scorers for benchmark tasks"
```

---

### Task 6: Comparison report renderer

**Files:**
- Create: `eval/harness/report.py`
- Test: `tests/test_report.py`

**Interfaces:**
- Consumes: nothing (operates on plain dicts).
- Produces: `render_comparison(skill: str, rows: list[dict]) -> str`. Each row dict has keys `version, task_id, passed (bool), score (float), detail`.

- [ ] **Step 1: Write the failing test**

`tests/test_report.py`:
```python
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_report.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'eval.harness.report'`.

- [ ] **Step 3: Write minimal implementation**

`eval/harness/report.py`:
```python
from collections import defaultdict


def render_comparison(skill: str, rows: list[dict]) -> str:
    lines = [
        f"# Eval report — {skill}",
        "",
        "| version | task | passed | score | detail |",
        "| --- | --- | --- | --- | --- |",
    ]
    for r in rows:
        mark = "✅" if r["passed"] else "❌"
        lines.append(f"| {r['version']} | {r['task_id']} | {mark} | {r['score']:.2f} | {r['detail']} |")

    totals: dict[str, list[int]] = defaultdict(lambda: [0, 0])  # version -> [passed, total]
    for r in rows:
        totals[r["version"]][1] += 1
        if r["passed"]:
            totals[r["version"]][0] += 1

    lines += ["", "## Summary", ""]
    for version, (passed, total) in totals.items():
        lines.append(f"- {version}: {passed}/{total} passed")
    return "\n".join(lines) + "\n"
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_report.py -v`
Expected: PASS (2 passed).

- [ ] **Step 5: Commit**

```bash
git add eval/harness/report.py tests/test_report.py
git commit -m "feat: comparison report renderer"
```

---

### Task 7: Harness CLI (`lint` + `validate`)

**Files:**
- Create: `eval/harness/cli.py`
- Test: `tests/test_cli.py`

**Interfaces:**
- Consumes: `eval.harness.skill_lint.lint_skill`, `eval.harness.tasks.load_tasks`, `BenchmarkError`.
- Produces: `main(argv: list[str] | None = None) -> int` (process exit code: 0 ok, 1 issues found, 2 usage). Subcommands `lint --skills <dir>` and `validate --benchmarks <dir>`. Runnable as `python -m eval.harness.cli`.

- [ ] **Step 1: Write the failing test**

`tests/test_cli.py`:
```python
from pathlib import Path
from eval.harness.cli import main


def _skill(dirpath: Path, name: str, body: str):
    d = dirpath / name
    d.mkdir(parents=True)
    (d / "SKILL.md").write_text(
        f"---\nname: {name}\ndescription: Use when testing.\n---\n{body}\n", encoding="utf-8"
    )


def test_lint_passes_on_valid_skills(tmp_path):
    skills = tmp_path / "skills"
    _skill(skills, "alpha", "# Alpha\n\nBody.")
    assert main(["lint", "--skills", str(skills)]) == 0


def test_lint_fails_on_invalid_skill(tmp_path):
    skills = tmp_path / "skills"
    _skill(skills, "beta", "# Beta\n\nTODO.")
    assert main(["lint", "--skills", str(skills)]) == 1


def test_validate_passes_on_good_benchmark(tmp_path):
    bench = tmp_path / "benchmarks" / "alpha"
    bench.mkdir(parents=True)
    (bench / "tasks.yaml").write_text(
        "- id: t1\n  kind: judge\n  prompt: do a thing\n", encoding="utf-8"
    )
    assert main(["validate", "--benchmarks", str(tmp_path / "benchmarks")]) == 0


def test_validate_fails_on_bad_benchmark(tmp_path):
    bench = tmp_path / "benchmarks" / "alpha"
    bench.mkdir(parents=True)
    (bench / "tasks.yaml").write_text(
        "- id: t1\n  kind: bogus\n  prompt: x\n", encoding="utf-8"
    )
    assert main(["validate", "--benchmarks", str(tmp_path / "benchmarks")]) == 1
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_cli.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'eval.harness.cli'`.

- [ ] **Step 3: Write minimal implementation**

`eval/harness/cli.py`:
```python
import argparse
from pathlib import Path

from eval.harness.skill_lint import lint_skill
from eval.harness.tasks import BenchmarkError, load_tasks


def cmd_lint(skills_dir: Path) -> int:
    issues: list[str] = []
    for d in sorted(p for p in skills_dir.iterdir() if (p / "SKILL.md").exists()):
        issues.extend(lint_skill(d))
    for issue in issues:
        print(issue)
    print(f"lint: {'OK' if not issues else f'{len(issues)} issue(s)'}")
    return 1 if issues else 0


def cmd_validate(bench_dir: Path) -> int:
    errors: list[str] = []
    for tasks_file in sorted(bench_dir.glob("*/tasks.yaml")):
        try:
            load_tasks(tasks_file)
        except BenchmarkError as exc:
            errors.append(str(exc))
    for err in errors:
        print(err)
    print(f"validate: {'OK' if not errors else f'{len(errors)} error(s)'}")
    return 1 if errors else 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="eval.harness")
    sub = parser.add_subparsers(dest="cmd", required=True)
    p_lint = sub.add_parser("lint")
    p_lint.add_argument("--skills", default="skills")
    p_val = sub.add_parser("validate")
    p_val.add_argument("--benchmarks", default="eval/benchmarks")
    args = parser.parse_args(argv)
    if args.cmd == "lint":
        return cmd_lint(Path(args.skills))
    if args.cmd == "validate":
        return cmd_validate(Path(args.benchmarks))
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_cli.py -v`
Expected: PASS (4 passed).

- [ ] **Step 5: Commit**

```bash
git add eval/harness/cli.py tests/test_cli.py
git commit -m "feat: harness CLI (lint + validate)"
```

---

### Task 8: `scientific-rigor` backbone skill

**Files:**
- Create: `skills/scientific-rigor/SKILL.md`
- Create: `skills/scientific-rigor/reasoning-and-creativity.md`
- Create: `skills/scientific-rigor/rigor-checklists.md`
- Test: `tests/test_skills_valid.py`

**Interfaces:**
- Consumes: `eval.harness.skill_lint.lint_skill`.
- Produces: a parametrized test that lints every directory under `skills/`. This test grows automatically as later tasks add skills.

- [ ] **Step 1: Write the failing test**

`tests/test_skills_valid.py`:
```python
from pathlib import Path
import pytest
from eval.harness.skill_lint import lint_skill

ROOT = Path(__file__).resolve().parents[1]
SKILLS = sorted(p for p in (ROOT / "skills").iterdir() if (p / "SKILL.md").exists())


@pytest.mark.parametrize("skill_dir", SKILLS, ids=[p.name for p in SKILLS])
def test_skill_lints_clean(skill_dir):
    assert lint_skill(skill_dir) == []


def test_scientific_rigor_present_and_routes():
    body = (ROOT / "skills" / "scientific-rigor" / "SKILL.md").read_text(encoding="utf-8")
    for ref in ("research-design", "literature-review", "faithful-implementation",
                "rigorous-validation", "research-synthesis", "skill-forge"):
        assert ref in body, f"router missing reference to {ref}"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_skills_valid.py -v`
Expected: FAIL — `test_scientific_rigor_present_and_routes` errors (file missing); parametrized test collects nothing (empty `skills/`).

- [ ] **Step 3: Write the skill files**

`skills/scientific-rigor/SKILL.md`:
```markdown
---
name: scientific-rigor
description: Use for any scientific research, analysis, or research-codebase task — sets the rigor, honesty, and creativity standards and routes to the right research-phase skill.
---

# Scientific Rigor

The always-on backbone for research work. It holds the **standards** (how rigorous,
honest, and creative the work must be) and **routes** to the phase skill for the task.

## Standards (apply to everything)

1. **Falsifiability first.** State what would prove a claim wrong before gathering
   evidence for it. A claim nothing could disconfirm is not a result.
2. **Intellectual honesty.** Report what happened — failures, negative results, skipped
   steps. Never present a hoped-for outcome as an observed one.
3. **Calibrated uncertainty.** Attach confidence; distinguish shown, suggested, and
   speculated. Prefer intervals to point claims.
4. **Anti-bias discipline.** Decide analyses before seeing results (no HARKing); fix the
   metric before optimizing it (no p-hacking); seek disconfirming evidence; never
   cherry-pick.
5. **Robustness.** A result that holds only at one seed, split, or setting is fragile —
   say so, and stress every important claim.
6. **Structured creativity.** Generate widely, then prune hard with explicit criteria.
   Innovation and rigor are partners — see
   [reasoning-and-creativity.md](reasoning-and-creativity.md).

Detailed checklists: [rigor-checklists.md](rigor-checklists.md).

## Router — which skill for this moment

| You are about to… | Use |
| --- | --- |
| Frame a question, hypotheses, metrics, experiment plan | `research-design` (empirical) or `humanities-inquiry` (interpretive) |
| Survey the field or choose among competing methods | `literature-review` or `argumentation-and-sources` |
| Implement a method faithfully to its source | `faithful-implementation` (with `writing-plans`, `subagent-driven-development`, `test-driven-development`) |
| Validate results before believing them | `rigorous-validation` (with `data:statistical-analysis`, `/code-review`) |
| Turn validated results into a write-up | `research-synthesis` (with `data:create-viz`, `docx`/`pptx`) |
| Improve these skills themselves | `skill-forge` |

## Composition rule

Delegate. This suite never reinvents planning, TDD, code review, statistics, or document
generation — it adds the scientific layer and hands the rest to the existing skill.

## Red flags (stop)

- Optimizing a metric you defined after seeing the data.
- "It worked when I ran it" standing in for a reproducible result.
- An implementation "based on" a paper with no check that it matches the paper.
- Claims broader than the evidence; limitations omitted.
```

`skills/scientific-rigor/reasoning-and-creativity.md`:
```markdown
# Reasoning and creativity

Hard reasoning and creativity are one loop, run twice: diverge, then converge.

## Diverge (generate)

- List at least three genuinely different approaches before committing to one. If they
  are minor variants of each other, you have not diverged.
- Borrow across fields: how would a physicist, a statistician, and an engineer each frame
  this? Cross-domain analogy is where non-obvious methods come from.
- Invert the problem: what would guarantee failure? Avoiding that often reveals the path.
- Steelman the approach you like least; it may carry an idea worth grafting.

## Converge (prune)

- Score approaches against explicit, pre-stated criteria (correctness, cost, risk,
  novelty, falsifiability), not against a gut feel formed after the fact.
- Red-team your favorite: how could it be wrong, fragile, or already done better?
- Keep the best idea and graft the strongest element of each runner-up.

## Reasoning hygiene

- Make assumptions explicit and testable.
- Reason from mechanisms, not from authority or vibes.
- When stuck, reduce to the smallest case that still has the difficulty.
- Distinguish "I derived this" from "I recall this" — verify recalls.
```

`skills/scientific-rigor/rigor-checklists.md`:
```markdown
# Rigor checklists

## Before claiming a result

- [ ] The hypothesis and primary metric were fixed before looking at outcomes.
- [ ] What would falsify this claim is stated, and was tested.
- [ ] Confidence is calibrated and uncertainty is quantified.
- [ ] The result is robust across seeds / splits / reasonable settings.
- [ ] Limitations and threats to validity are written down.

## Anti-bias

- [ ] No HARKing: no hypothesis invented after seeing the data is reported as a priori.
- [ ] No p-hacking: no metric, subgroup, or stopping rule chosen to make it significant.
- [ ] No cherry-picking: representative results shown, not just the best run.
- [ ] No leakage: train/test (or source/derived) separation is intact.

## Honesty

- [ ] Negative and null results reported alongside positive ones.
- [ ] Every claim maps to specific evidence; none overreaches it.
- [ ] Steps that were skipped or approximated are disclosed.
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_skills_valid.py -v`
Expected: PASS (`scientific-rigor` lints clean; router test passes).

- [ ] **Step 5: Commit**

```bash
git add skills/scientific-rigor tests/test_skills_valid.py
git commit -m "feat: scientific-rigor backbone skill"
```

---

### Task 9: Master `CLAUDE.md` prompt

**Files:**
- Create: `CLAUDE.md`
- Test: `tests/test_master_prompt.py`

**Interfaces:**
- Consumes: nothing.
- Produces: the condensed operating-standards prompt at repo root.

- [ ] **Step 1: Write the failing test**

`tests/test_master_prompt.py`:
```python
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_master_prompt_is_condensed_and_routes():
    text = (ROOT / "CLAUDE.md").read_text(encoding="utf-8")
    assert len(text) <= 4000, f"CLAUDE.md too long: {len(text)} chars"
    for skill in ("research-design", "literature-review", "faithful-implementation",
                  "rigorous-validation", "research-synthesis", "skill-forge",
                  "scientific-rigor"):
        assert skill in text, f"missing route to {skill}"
    for token in ("TODO", "TBD", "FIXME"):
        assert token not in text
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_master_prompt.py -v`
Expected: FAIL — `FileNotFoundError` (`CLAUDE.md` absent).

- [ ] **Step 3: Write `CLAUDE.md`**

`CLAUDE.md`:
```markdown
# Scientific research — operating standards

You are doing scientific research and/or building its codebase. Hold these standards on
every task, and route to the matching skill.

## Standards
- Falsifiability first: state what would disprove a claim before supporting it.
- Intellectual honesty: report failures, negatives, and skipped steps. Never present a
  hoped-for outcome as observed.
- Calibrated uncertainty: separate shown / suggested / speculated; prefer intervals.
- No p-hacking, no HARKing, no cherry-picking. Fix metrics and analyses before looking.
- Robustness: stress every important claim across seeds, splits, and settings.
- Structured creativity: diverge widely, then prune with explicit criteria. Be
  innovative and rigorous at once.

## Route to a skill
- Framing question / hypotheses / metrics → `research-design` (or `humanities-inquiry`).
- Survey field / pick the best method → `literature-review` (or `argumentation-and-sources`).
- Implement a method from the literature → `faithful-implementation`, with
  `writing-plans` + `subagent-driven-development` + `test-driven-development`.
- Validate results → `rigorous-validation` (with `data:statistical-analysis`, `/code-review`).
- Write up → `research-synthesis` (with `data:create-viz`, `docx`/`pptx`).
- Improve these skills → `skill-forge`.
- Deep technique and standards → `scientific-rigor`.

## Composition rule
Delegate; never reinvent planning, TDD, code review, statistics, or document generation.
Add the scientific layer; hand the rest to the existing skill.

## Anti-patterns
p-hacking · HARKing · cherry-picking · unfaithful reproduction · overclaiming beyond
evidence · uncontrolled data leakage.
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_master_prompt.py -v`
Expected: PASS (1 passed).

- [ ] **Step 5: Commit**

```bash
git add CLAUDE.md tests/test_master_prompt.py
git commit -m "feat: master CLAUDE.md operating-standards prompt"
```

---

### Task 10: `faithful-implementation` skill + benchmark slice + rubric + contract test

**Files:**
- Create: `skills/faithful-implementation/SKILL.md`
- Create: `eval/rubrics/faithful-implementation.md`
- Create: `eval/benchmarks/faithful-implementation/tasks.yaml`
- Create: `eval/benchmarks/faithful-implementation/fixtures/logsumexp.md`
- Test: `tests/test_faithful_implementation.py`

**Interfaces:**
- Consumes: `eval.harness.tasks.load_tasks`. The parametrized `tests/test_skills_valid.py::test_skill_lints_clean` from Task 8 will automatically also cover this new skill.
- Produces: the first lifecycle skill, its rubric, and a validated benchmark slice. Establishes the composition-contract pattern (SKILL.md names the existing skills it delegates to).

- [ ] **Step 1: Write the failing test**

`tests/test_faithful_implementation.py`:
```python
from pathlib import Path
from eval.harness.tasks import load_tasks

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "skills" / "faithful-implementation" / "SKILL.md"
RUBRIC = ROOT / "eval" / "rubrics" / "faithful-implementation.md"
TASKS = ROOT / "eval" / "benchmarks" / "faithful-implementation" / "tasks.yaml"


def test_skill_declares_composition_contract():
    body = SKILL.read_text(encoding="utf-8")
    for dep in ("writing-plans", "subagent-driven-development", "test-driven-development"):
        assert dep in body, f"composition contract missing {dep}"
    assert "oracle" in body.lower()


def test_rubric_has_core_dimensions():
    text = RUBRIC.read_text(encoding="utf-8").lower()
    for dim in ("faithfulness", "correctness", "rigor", "honesty"):
        assert dim in text


def test_benchmark_slice_loads_and_has_ground_truth():
    tasks = load_tasks(TASKS)
    assert len(tasks) >= 2
    assert any(t.kind == "ground_truth" for t in tasks)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_faithful_implementation.py -v`
Expected: FAIL — `FileNotFoundError` (skill, rubric, and tasks absent).

- [ ] **Step 3: Write the skill, rubric, and benchmark files**

`skills/faithful-implementation/SKILL.md`:
```markdown
---
name: faithful-implementation
description: Use when implementing a method, algorithm, or model from the literature — defines the literature-derived test oracles so TDD proves the code matches the source, and detects divergence from it.
---

# Faithful Implementation

Implementing a method from a paper is not "write code that runs" — it is "write code that
**provably matches the source**". This skill is the *oracle layer*: it decides what each
test must assert so that a passing test means *faithful to the literature*. It plugs into
the existing build loop; it does not replace it.

## The core move: derive oracles before coding

From the method dossier (the `literature-review` output), extract for the method:

- **Equations / update rules** → assertions on intermediate and final values.
- **Reference outputs / reported numbers** → expected values, each with a tolerance.
- **Invariants** → properties that must always hold (conservation, normalization,
  monotonicity, shape, units, symmetry).
- **Edge cases named in the source** → explicit tests.
- **Numerical tolerance** → the allowed error, justified by float precision or the
  reported spread — never chosen just to make a test pass.

Each oracle becomes a failing test *before* implementation.

## Composes with (the contract)

1. `literature-review` produces the **method dossier** carrying the oracles.
2. `superpowers:writing-plans` turns the spec + oracles into a TDD plan; **each oracle
   becomes a task's failing test**.
3. `superpowers:subagent-driven-development` (or `superpowers:executing-plans`) executes
   the plan.
4. `superpowers:test-driven-development` runs each red→green cycle — green now means
   "matches the source", because the test asserts an oracle.
5. `superpowers:systematic-debugging` when a fidelity test fails and the cause is unclear.

You supply the oracles and the fidelity report; the superpowers skills supply the
machinery. This is why "faithful-implementation + writing-plans" and "+
subagent-driven-development" compose without friction.

## Fidelity report

After implementation, record for each oracle: matched / diverged / unverifiable, with the
evidence. A divergence is a result to explain, not to hide. A "better" alternative
implementation discovered mid-build is a `literature-review` decision (re-rank the
methods), not a silent swap.

## Domain lenses

- **Computational science:** tolerance and error analysis; conservation and convergence;
  compare against analytical or known-good solutions.
- **ML/AI:** control seeds; match the reported metric within its confidence interval;
  diff against a reference implementation; watch for data leakage.
- **Data science / statistics:** verify estimator formulas and identification
  assumptions, not just that the code runs.

## Red flags (stop)

- No oracle for a core equation — you are testing that it runs, not that it is right.
- Tolerances chosen to make the test pass rather than derived from the source.
- Divergence from the paper quietly "fixed" by editing the expected value.
```

`eval/rubrics/faithful-implementation.md`:
```markdown
# Rubric — faithful-implementation

Score an output produced under this skill on each dimension, 0–4.

- **Faithfulness (weight 0.35):** Does the implementation provably match the source?
  Are equations, reference numbers, and invariants asserted as oracles?
- **Correctness (weight 0.25):** Is the code actually correct and tested (real tests,
  watched to fail first)?
- **Rigor (weight 0.20):** Tolerances justified; edge cases from the source covered;
  divergences investigated rather than hidden.
- **Honesty (weight 0.10):** Fidelity report records matched / diverged / unverifiable
  truthfully, including failures.
- **Creativity (weight 0.10):** Where the source is ambiguous, are reasonable,
  well-justified choices made and documented?

Blended score = Σ(weight × dimension / 4). A submission that edits expected values to
force a pass scores 0 on faithfulness regardless of other dimensions.
```

`eval/benchmarks/faithful-implementation/fixtures/logsumexp.md`:
```markdown
# Fixture — numerically stable log-sum-exp

Reference definition: logsumexp(x) = m + log(Σ_i exp(x_i − m)), where m = max_i x_i.

Properties (oracles):
- logsumexp([0, 0]) = log(2) ≈ 0.6931471805599453.
- Shift invariance: logsumexp(x + c) = logsumexp(x) + c for any scalar c.
- Stability: logsumexp([1000, 1000]) must be finite (≈ 1000 + log 2), not inf.
```

`eval/benchmarks/faithful-implementation/tasks.yaml`:
```yaml
- id: logsumexp_value
  kind: ground_truth
  prompt: >
    Using fixtures/logsumexp.md, implement a numerically stable log-sum-exp and
    report logsumexp([0, 0]) to at least 6 decimal places.
  scorer: numeric
  expected: 0.6931471805599453
  tolerance: 0.000001
- id: logsumexp_stability
  kind: ground_truth
  prompt: >
    Report logsumexp([1000, 1000]) using a stable implementation; it must be finite.
  scorer: numeric
  expected: 1000.6931471805599
  tolerance: 0.001
- id: oracle_design_quality
  kind: judge
  prompt: >
    Given fixtures/logsumexp.md, enumerate the test oracles you would write BEFORE
    coding (values, shift invariance, stability) and justify each tolerance from the
    source. Judged on faithfulness and rigor per the rubric.
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_faithful_implementation.py tests/test_skills_valid.py -v`
Expected: PASS (contract, rubric, and benchmark tests pass; `faithful-implementation` now also lints clean under the parametrized skill test).

- [ ] **Step 5: Commit**

```bash
git add skills/faithful-implementation eval/rubrics eval/benchmarks tests/test_faithful_implementation.py
git commit -m "feat: faithful-implementation skill + benchmark slice + rubric"
```

---

### Task 11: Full-suite green + validate command

**Files:**
- Modify: none (verification task; fold any fixes into the file that needs them).
- Test: the whole suite plus the two CLI commands run against the real repo.

**Interfaces:**
- Consumes: everything above.
- Produces: a verified, working foundation.

- [ ] **Step 1: Run the whole test suite**

Run: `pytest -v`
Expected: PASS — all tests from Tasks 1–10 green, no warnings.

- [ ] **Step 2: Run the harness against the real repo**

Run: `python -m eval.harness.cli lint`
Expected: prints `lint: OK`, exit 0.

Run: `python -m eval.harness.cli validate`
Expected: prints `validate: OK`, exit 0.

- [ ] **Step 3: Confirm condensed master prompt and clean tree**

Run: `wc -c CLAUDE.md` (expect ≤ 4000) and `git status` (expect clean).

- [ ] **Step 4: Commit (only if any fix was needed)**

```bash
git add -A
git commit -m "test: verify full foundation suite green"
```

## Self-Review

**Spec coverage (against the design spec):**
- §3.1 `scientific-rigor` → Task 8. §3.2 `faithful-implementation` → Task 10. (Other §3.2/§3.3 lifecycle + humanities skills are explicitly deferred to Plans 2–3 per the staging roadmap.)
- §4 composition contracts → Task 10 SKILL.md + `test_skill_declares_composition_contract`.
- §5.1 eval harness (deterministic core: frontmatter, lint, tasks, score, report, CLI) → Tasks 2–7. Live agent-dispatched `run/judge/tournament` and the loop → deferred to Plan 4 (noted in roadmap).
- §6 master prompt → Task 9. §7 repo layout → Tasks 1, 8, 10. §8 lenses → Task 10 SKILL.md (faithful-implementation lenses; others in later plans). §9 testing strategy (TDD harness, lint-validated skills, contract test) → Tasks 2–11.
- §12 build order steps 1–4 → this plan. Steps 5–8 → Plans 2–4.

**Placeholder scan:** No `TODO`/`TBD`/`FIXME` in shipped skills or `CLAUDE.md` (enforced by lint + `test_master_prompt`). All code steps show complete code; all skill/prompt steps show complete prose.

**Type consistency:** `Task`, `ScoreResult`, `lint_skill`, `load_tasks`, `score_output`, `render_comparison`, `main` signatures are defined once (Tasks 2–7) and referenced consistently in Tasks 8–11. Import path `eval.harness.<module>` is uniform throughout.
