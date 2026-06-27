# scienceskills Plan 2 — Lifecycle Skills + Hardening Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add the four remaining lifecycle skills — `research-design`, `literature-review`, `rigorous-validation`, `research-synthesis` — each with a judge rubric and a benchmark slice, and fold in the deferred hardening items from Plan 1's final review.

**Architecture:** Plan 1 shipped the plugin scaffold, the deterministic eval harness (`eval/harness/`), the `scientific-rigor` backbone, the master `CLAUDE.md`, and `faithful-implementation`. This plan reuses that machinery unchanged: each new skill is `skills/<name>/SKILL.md`; its rubric is `eval/rubrics/<name>.md`; its benchmark slice is `eval/benchmarks/<name>/tasks.yaml`. The existing parametrized `tests/test_skills_valid.py` auto-covers each new skill's lint. The `scientific-rigor` router and `CLAUDE.md` already reference all four names, so no edit there.

**Tech Stack:** Python 3.9+, pytest, PyYAML; markdown skills.

## Staging roadmap (this is Plan 2 of 4)

- Plan 1 (done, merged): scaffold + harness + `scientific-rigor` + `CLAUDE.md` + `faithful-implementation`.
- **Plan 2 (this doc):** hardening pass + `research-design`, `literature-review`, `rigorous-validation`, `research-synthesis` (each + rubric + slice).
- Plan 3: `humanities-inquiry`, `argumentation-and-sources` (+ slices).
- Plan 4: `skill-forge` engine — live `run.py`/`judge.py`/`tournament.py`, candidate generation, gating, human-approved promotion.

## Global Constraints

- Run pytest as `python3 -m pytest` (no `pytest` on PATH); pyyaml + pytest already installed for system `python3` (3.9.6); no venv.
- Any harness module starts with `from __future__ import annotations` (Task 1 edits existing modules that already have it; do not remove it).
- Every new `SKILL.md` frontmatter has `name` == its directory name and a non-empty `description` ≤ 1024 chars; body starts with an H1; no literal `TODO`/`TBD`/`FIXME` tokens (the lint enforces this).
- Every benchmark `tasks.yaml` loads via `eval.harness.tasks.load_tasks`.
- Skill prose is the product: use the EXACT content from each task verbatim — section names and the composition-contract wording are asserted by tests and depended on by later plans. Sentence case.
- DRY, YAGNI, TDD, frequent commits. Never implement on `main`/`master` without consent — work on a feature branch.

---

### Task 1: Harness hardening (fold in Plan 1 final-review items)

**Files:**
- Modify: `.gitignore`
- Modify: `eval/harness/score.py` (numeric branch)
- Modify: `eval/harness/tasks.py` (id/prompt/kind guards)
- Test: `tests/test_score.py` (append), `tests/test_skill_lint.py` (append), `tests/test_tasks_loader.py` (append)

**Interfaces:**
- Consumes: existing `score_output`, `lint_skill`, `load_tasks`.
- Produces: same public signatures; `load_tasks` now raises `BenchmarkError` with clearer messages for non-string/missing `id`, missing `kind`, and non-string/missing `prompt`.

- [ ] **Step 1: Append the new tests**

Append to `tests/test_tasks_loader.py`:
```python
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
    with pytest.raises(BenchmarkError, match="string"):
        load_tasks(p)
```

Append to `tests/test_score.py`:
```python
def test_failing_result_scores_zero():
    assert score_output("exact", "a", "b").score == 0.0


def test_numeric_default_tolerance_exact():
    assert score_output("numeric", 2.0, "2.0").passed


def test_numeric_default_tolerance_rejects_near_miss():
    assert not score_output("numeric", 2.0, "2.0001").passed
```

Append to `tests/test_skill_lint.py`:
```python
def test_description_too_long_flagged(tmp_path):
    d = _make_skill(tmp_path, "good", f"name: good\ndescription: {'x' * 1025}", "# Good\n\nBody.")
    assert any("description" in i for i in lint_skill(d))


def test_empty_body_flagged(tmp_path):
    d = _make_skill(tmp_path, "good", "name: good\ndescription: Use when testing.", "")
    assert any("empty" in i for i in lint_skill(d))


def test_body_missing_heading_flagged(tmp_path):
    d = _make_skill(tmp_path, "good", "name: good\ndescription: Use when testing.", "No heading here.")
    assert any("heading" in i.lower() for i in lint_skill(d))
```

- [ ] **Step 2: Run the new tests to see the RED**

Run: `python3 -m pytest tests/test_tasks_loader.py::test_non_string_id_message_mentions_string -v`
Expected: FAIL — current message is "missing 'id'", which does not match "string". (The other appended tests pass already — they characterize existing branches; this one drives the code change.)

- [ ] **Step 3: Apply the source edits**

In `eval/harness/score.py`, replace the numeric-branch tolerance line:
```python
        tol = tolerance or 0.0
```
with:
```python
        tol = 0.0 if tolerance is None else tolerance
```

In `eval/harness/tasks.py`, replace the id/kind/prompt guard block (the lines from `tid = item.get("id")` through the `prompt` check) with:
```python
        tid = item.get("id")
        if not isinstance(tid, str) or not tid:
            raise BenchmarkError(f"{path}[{i}]: 'id' must be a non-empty string")
        if tid in seen:
            raise BenchmarkError(f"{path}: duplicate id '{tid}'")
        seen.add(tid)
        if "kind" not in item:
            raise BenchmarkError(f"{path}[{tid}]: missing 'kind'")
        kind = item.get("kind")
        if kind not in VALID_KINDS:
            raise BenchmarkError(f"{path}[{tid}]: kind must be one of {sorted(VALID_KINDS)}")
        prompt = item.get("prompt")
        if not isinstance(prompt, str) or not prompt:
            raise BenchmarkError(f"{path}[{tid}]: 'prompt' must be a non-empty string")
```
(Leave the rest of the function — the `ground_truth` scorer/expected checks and the `tasks.append(Task(...))` call — unchanged.)

In `.gitignore`, add two lines after the existing entries:
```gitignore
*.egg-info/
dist/
```

- [ ] **Step 4: Run the full suite to see GREEN**

Run: `python3 -m pytest -q`
Expected: PASS — all Plan 1 tests plus the 11 new tests (36 + 11 = 47 passing).

- [ ] **Step 5: Commit**

```bash
git add .gitignore eval/harness/score.py eval/harness/tasks.py tests/test_score.py tests/test_skill_lint.py tests/test_tasks_loader.py
git commit -m "fix: harden tasks loader guards + scorer tolerance, add branch tests"
```

---

### Task 2: `research-design` skill + rubric + benchmark slice

**Files:**
- Create: `skills/research-design/SKILL.md`
- Create: `eval/rubrics/research-design.md`
- Create: `eval/benchmarks/research-design/tasks.yaml`
- Test: `tests/test_research_design.py`

**Interfaces:**
- Consumes: `eval.harness.tasks.load_tasks`. The existing `tests/test_skills_valid.py` parametrization auto-covers the new skill's lint.
- Produces: the `research-design` lifecycle skill.

- [ ] **Step 1: Write the failing test**

`tests/test_research_design.py`:
```python
from pathlib import Path
from eval.harness.tasks import load_tasks

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "skills" / "research-design" / "SKILL.md"
RUBRIC = ROOT / "eval" / "rubrics" / "research-design.md"
TASKS = ROOT / "eval" / "benchmarks" / "research-design" / "tasks.yaml"


def test_skill_declares_composition_contract():
    body = SKILL.read_text(encoding="utf-8")
    assert "writing-plans" in body
    assert "research spec" in body.lower()


def test_rubric_has_core_dimensions():
    text = RUBRIC.read_text(encoding="utf-8").lower()
    for dim in ("falsifiability", "metric", "honesty"):
        assert dim in text


def test_benchmark_slice_loads_with_ground_truth():
    tasks = load_tasks(TASKS)
    assert len(tasks) >= 2
    assert any(t.kind == "ground_truth" for t in tasks)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m pytest tests/test_research_design.py -v`
Expected: FAIL — `FileNotFoundError` (skill, rubric, tasks absent).

- [ ] **Step 3: Write the skill, rubric, and benchmark files**

`skills/research-design/SKILL.md`:
```markdown
---
name: research-design
description: Use when starting a research project or defining what to test — frames the question, states falsifiable hypotheses and success metrics, and plans experiments and ablations before any data is seen.
---

# Research Design

Decide what you are testing, why it matters, and how you will know you were right —
before you touch data or code. Good design is what makes later results trustworthy.

## Produce a research spec

Work through, in order:

1. **Question.** One sentence. What do you want to know? Narrow it until it is answerable.
2. **Novelty.** What is already known (from `literature-review`), and what specifically is
   new here? If nothing is new, say so.
3. **Hypotheses and predictions.** State each hypothesis and the concrete, **falsifiable**
   prediction it makes — the observation that would prove it wrong.
4. **Metrics.** Fix the primary metric and any secondary metrics now, and define how each
   is computed. The primary metric is chosen before seeing results — no moving the goalposts.
5. **Design.** Conditions, controls, baselines, and the **ablations** that isolate each
   claimed contribution. Decide sample size or compute budget and the stopping rule up front.
6. **Analysis plan.** State the analyses before running them (preregistration mindset) so
   results cannot be reverse-engineered into hypotheses.
7. **Threats.** List confounds, leakage risks, and validity threats, and how the design
   controls each.

Output: a **research spec** that downstream work consumes.

## Composes with

- `superpowers:brainstorming` upstream when the idea is still vague.
- The research spec feeds `superpowers:writing-plans`, which turns it into an
  implementation plan; `faithful-implementation` then supplies the literature-derived
  test oracles.
- For interpretive or non-empirical work, use `humanities-inquiry` instead.

## Domain lenses

- **ML/AI:** fix the eval set, metric, and seeds; pre-commit one ablation per component.
- **Computational science:** state the validation case (analytical or known-good) the
  method must reproduce.
- **Data science:** state the estimand and identification assumptions before modeling.

## Red flags (stop)

- A hypothesis with no observation that could falsify it.
- Choosing or changing the primary metric after seeing results.
- No baselines or ablations — you will not be able to attribute any effect.
```

`eval/rubrics/research-design.md`:
```markdown
# Rubric — research-design

Score an output produced under this skill on each dimension, 0–4.

- **Falsifiability (weight 0.30):** Each hypothesis has a concrete prediction that could be wrong.
- **Metric validity (weight 0.25):** Primary metric fixed up front, well-defined, and measures the question.
- **Design completeness (weight 0.20):** Controls, baselines, and ablations isolate each claim.
- **Novelty and framing (weight 0.15):** Question is answerable and positioned against prior work.
- **Honesty (weight 0.10):** Threats to validity and limits are stated, not hidden.

Blended score = Σ(weight × dimension / 4). A design that leaves the primary metric unfixed
scores 0 on metric validity.
```

`eval/benchmarks/research-design/tasks.yaml`:
```yaml
- id: hypothesis_falsifiability
  kind: judge
  prompt: >
    A team claims "our model understands physics." Turn this into a falsifiable research
    design: a sharp question, a hypothesis with a concrete prediction that could fail, a
    primary metric fixed in advance, and one ablation. Judged on falsifiability and metric
    validity per the rubric.
- id: choose_primary_metric
  kind: judge
  prompt: >
    Given a study comparing three recommendation algorithms on click-through, dwell time,
    and revenue, specify which single primary metric you would pre-register and why, and
    how you would control multiple comparisons across the secondary metrics.
- id: bonferroni_threshold
  kind: ground_truth
  prompt: >
    A design pre-registers 5 independent primary comparisons at a family-wise alpha of
    0.05 using a Bonferroni correction. Report the per-comparison significance threshold
    to 4 decimal places.
  scorer: numeric
  expected: 0.01
  tolerance: 0.0001
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python3 -m pytest tests/test_research_design.py tests/test_skills_valid.py -v`
Expected: PASS (contract, rubric, benchmark tests pass; `research-design` lints clean under the parametrized skill test).

- [ ] **Step 5: Commit**

```bash
git add skills/research-design eval/rubrics/research-design.md eval/benchmarks/research-design tests/test_research_design.py
git commit -m "feat: research-design skill + rubric + benchmark slice"
```

---

### Task 3: `literature-review` skill + rubric + benchmark slice

**Files:**
- Create: `skills/literature-review/SKILL.md`
- Create: `eval/rubrics/literature-review.md`
- Create: `eval/benchmarks/literature-review/tasks.yaml`
- Test: `tests/test_literature_review.py`

**Interfaces:**
- Consumes: `eval.harness.tasks.load_tasks`; auto-covered by `tests/test_skills_valid.py` lint.
- Produces: the `literature-review` lifecycle skill.

- [ ] **Step 1: Write the failing test**

`tests/test_literature_review.py`:
```python
from pathlib import Path
from eval.harness.tasks import load_tasks

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "skills" / "literature-review" / "SKILL.md"
RUBRIC = ROOT / "eval" / "rubrics" / "literature-review.md"
TASKS = ROOT / "eval" / "benchmarks" / "literature-review" / "tasks.yaml"


def test_skill_declares_composition_contract():
    body = SKILL.read_text(encoding="utf-8")
    assert "deep-research" in body
    assert "method dossier" in body.lower()
    assert "oracle" in body.lower()


def test_rubric_has_core_dimensions():
    text = RUBRIC.read_text(encoding="utf-8").lower()
    for dim in ("coverage", "appraisal", "comparison", "citation"):
        assert dim in text


def test_benchmark_slice_loads():
    tasks = load_tasks(TASKS)
    assert len(tasks) >= 2
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m pytest tests/test_literature_review.py -v`
Expected: FAIL — `FileNotFoundError` (files absent).

- [ ] **Step 3: Write the skill, rubric, and benchmark files**

`skills/literature-review/SKILL.md`:
```markdown
---
name: literature-review
description: Use when surveying a field or choosing among competing methods — searches and critically appraises sources, maps the state of the art and gaps, and produces a justified ranked comparison of methods with the oracles an implementation must match.
---

# Literature Review

Find what is known, judge it critically, and decide which method to use — with the
evidence to defend the choice. The output drives implementation, so it must be precise.

## Produce a method dossier

1. **Search.** Use `deep-research` to fan out across sources; cover seminal work, recent
   state of the art, and dissenting results. Record queries so the search is reproducible.
2. **Appraise.** For each source, note its claim, evidence quality, sample or benchmark,
   and limitations. Distinguish strong results from weak or unreplicated ones.
3. **Map.** Synthesize the state of the art and the **gaps** — what is unsolved or contested.
4. **Compare and rank.** Lay competing methods side by side against explicit criteria
   (accuracy, assumptions, cost, robustness, fit to your problem). Rank them and **state
   the recommended method with the reason it wins** for this context.
5. **Extract oracles.** Pull the equations, algorithms, hyperparameters, and reported
   numbers the chosen method specifies — these become the test oracles for
   `faithful-implementation`.

Output: a **method dossier** — appraised sources, a state-of-the-art and gap map, a ranked
comparison with the decision, and the extracted oracles.

## Composes with

- `deep-research` for the search and adversarial verification of claims.
- The dossier's oracles feed `faithful-implementation`; its decision feeds `research-design`.
- For argument-driven or primary-source work, defer source criticism to
  `argumentation-and-sources`.

## Domain lenses

- **ML/AI:** prefer results with released code and reported variance; note benchmark leakage.
- **Computational science:** capture the governing equations and validation cases.
- **Data science:** capture identification assumptions and estimator definitions.

## Red flags (stop)

- A method chosen by popularity or recency rather than fit and evidence.
- Citing a claim without recording the evidence behind it.
- No gap analysis — a review that only summarizes cannot justify new work.
```

`eval/rubrics/literature-review.md`:
```markdown
# Rubric — literature-review

Score an output produced under this skill on each dimension, 0–4.

- **Coverage (weight 0.20):** Seminal, recent, and dissenting work all represented; search reproducible.
- **Critical appraisal (weight 0.25):** Evidence quality judged, not just summarized; weak results flagged.
- **Method comparison (weight 0.30):** Explicit criteria, ranked, with a justified recommendation for the context.
- **Oracle extraction (weight 0.15):** Equations and numbers the implementation must match are captured precisely.
- **Citation integrity (weight 0.10):** Every claim traceable to a source.

Blended score = Σ(weight × dimension / 4). A "recommendation" with no comparison criteria
scores 0 on method comparison.
```

`eval/benchmarks/literature-review/tasks.yaml`:
```yaml
- id: rank_methods
  kind: judge
  prompt: >
    Given three optimizers (SGD with momentum, Adam, and a recent variant) for training a
    mid-size transformer under a fixed compute budget, produce a ranked comparison against
    explicit criteria and recommend one for this context, with reasons. Judged on method
    comparison per the rubric.
- id: extract_oracles
  kind: judge
  prompt: >
    From a paper that defines an algorithm by an update equation and reports a benchmark
    accuracy of 92.3%, list the test oracles an implementer should assert to confirm
    fidelity: the equation's behavior, the reported number with a tolerance, and one invariant.
- id: appraisal_over_summary
  kind: judge
  prompt: >
    You find two papers reaching opposite conclusions on the same question. Describe how
    you appraise and reconcile them rather than averaging or simply picking the newer one.
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python3 -m pytest tests/test_literature_review.py tests/test_skills_valid.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add skills/literature-review eval/rubrics/literature-review.md eval/benchmarks/literature-review tests/test_literature_review.py
git commit -m "feat: literature-review skill + rubric + benchmark slice"
```

---

### Task 4: `rigorous-validation` skill + rubric + benchmark slice

**Files:**
- Create: `skills/rigorous-validation/SKILL.md`
- Create: `eval/rubrics/rigorous-validation.md`
- Create: `eval/benchmarks/rigorous-validation/tasks.yaml`
- Test: `tests/test_rigorous_validation.py`

**Interfaces:**
- Consumes: `eval.harness.tasks.load_tasks`; auto-covered by `tests/test_skills_valid.py` lint.
- Produces: the `rigorous-validation` lifecycle skill.

- [ ] **Step 1: Write the failing test**

`tests/test_rigorous_validation.py`:
```python
from pathlib import Path
from eval.harness.tasks import load_tasks

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "skills" / "rigorous-validation" / "SKILL.md"
RUBRIC = ROOT / "eval" / "rubrics" / "rigorous-validation.md"
TASKS = ROOT / "eval" / "benchmarks" / "rigorous-validation" / "tasks.yaml"


def test_skill_declares_composition_contract():
    body = SKILL.read_text(encoding="utf-8")
    assert "statistical-analysis" in body
    assert "verification-before-completion" in body
    assert "leakage" in body.lower()


def test_rubric_has_core_dimensions():
    text = RUBRIC.read_text(encoding="utf-8").lower()
    for dim in ("reproducibility", "statistical", "robustness", "leakage"):
        assert dim in text


def test_benchmark_slice_loads_with_ground_truth():
    tasks = load_tasks(TASKS)
    assert len(tasks) >= 2
    assert any(t.kind == "ground_truth" for t in tasks)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m pytest tests/test_rigorous_validation.py -v`
Expected: FAIL — `FileNotFoundError` (files absent).

- [ ] **Step 3: Write the skill, rubric, and benchmark files**

`skills/rigorous-validation/SKILL.md`:
```markdown
---
name: rigorous-validation
description: Use when results exist and must be validated before they are believed — checks reproducibility, statistical validity, robustness, baselines, and leakage and bias, and red-teams your own findings.
---

# Rigorous Validation

A result is not a result until you have tried to break it. Validate the end product, not
just unit correctness, before any claim is made.

## The validation pass

1. **Reproduce.** Re-run from a clean state with fixed seeds and a captured environment. A
   result you cannot reproduce is not yet a result.
2. **Baselines.** Compare against trivial and strong baselines. An effect with no baseline
   is uninterpretable.
3. **Ablate.** Remove each claimed component and confirm the effect tracks it.
4. **Statistics.** Test significance with appropriate methods; report effect sizes and
   intervals; control multiple comparisons; check power. Delegate to `data:statistical-analysis`.
5. **Robustness.** Sweep seeds, splits, and reasonable settings. Report where the result
   holds and where it breaks.
6. **Leakage and bias.** Check train/test (or source/derived) separation, label leakage,
   and selection bias. This is where most false results come from.
7. **Red-team.** Ask "how could this number be wrong, inflated, or fabricated?" and test
   the most likely failure before publishing it.

Output: a **validation report** — claims, the evidence for each, the threats addressed,
and residual risks.

## Composes with

- `data:statistical-analysis` and `data:validate-data` for the statistics and QA.
- `/code-review` and `superpowers:requesting-code-review` for code correctness.
- `superpowers:verification-before-completion` as the evidence-before-claims gate.
- For argument-driven work, validity is argument soundness — use `argumentation-and-sources`.

## Domain lenses

- **ML/AI:** seed variance, data leakage, train/test contamination, metric gaming.
- **Computational science:** convergence, conservation, sensitivity to discretization.
- **Data science:** identification assumptions, confounding, robustness of the estimate.

## Red flags (stop)

- A single-run number reported as the result.
- "Significant" without a stated test, correction, or effect size.
- No leakage check on a surprisingly good result.
```

`eval/rubrics/rigorous-validation.md`:
```markdown
# Rubric — rigorous-validation

Score an output produced under this skill on each dimension, 0–4.

- **Reproducibility (weight 0.25):** Clean re-run, fixed seeds, captured environment.
- **Statistical validity (weight 0.25):** Right test, effect sizes and intervals, multiple-comparison control.
- **Robustness (weight 0.20):** Seeds, splits, and settings swept; where it holds and breaks is reported.
- **Leakage and bias (weight 0.20):** Separation and selection checked; surprising results red-teamed.
- **Honesty (weight 0.10):** Residual risks and negative findings reported.

Blended score = Σ(weight × dimension / 4). A surprising result with no leakage check scores
0 on leakage and bias.
```

`eval/benchmarks/rigorous-validation/tasks.yaml`:
```yaml
- id: bonferroni_validation
  kind: ground_truth
  prompt: >
    An experiment runs 20 independent significance tests and wants a family-wise error
    rate of 0.05 via a Bonferroni correction. Report the per-test threshold to 4 decimal
    places.
  scorer: numeric
  expected: 0.0025
  tolerance: 0.0001
- id: leakage_audit
  kind: judge
  prompt: >
    A model reports 99% accuracy on a medical imaging task. Enumerate, in priority order,
    the leakage and bias checks you would run before believing it, and what each would
    catch. Judged on leakage and bias per the rubric.
- id: single_run_pushback
  kind: judge
  prompt: >
    A colleague reports a 2-point improvement from one training run. Describe the
    reproducibility, baseline, and robustness checks required before this is a result.
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python3 -m pytest tests/test_rigorous_validation.py tests/test_skills_valid.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add skills/rigorous-validation eval/rubrics/rigorous-validation.md eval/benchmarks/rigorous-validation tests/test_rigorous_validation.py
git commit -m "feat: rigorous-validation skill + rubric + benchmark slice"
```

---

### Task 5: `research-synthesis` skill + rubric + benchmark slice

**Files:**
- Create: `skills/research-synthesis/SKILL.md`
- Create: `eval/rubrics/research-synthesis.md`
- Create: `eval/benchmarks/research-synthesis/tasks.yaml`
- Test: `tests/test_research_synthesis.py`

**Interfaces:**
- Consumes: `eval.harness.tasks.load_tasks`; auto-covered by `tests/test_skills_valid.py` lint.
- Produces: the `research-synthesis` lifecycle skill.

- [ ] **Step 1: Write the failing test**

`tests/test_research_synthesis.py`:
```python
from pathlib import Path
from eval.harness.tasks import load_tasks

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "skills" / "research-synthesis" / "SKILL.md"
RUBRIC = ROOT / "eval" / "rubrics" / "research-synthesis.md"
TASKS = ROOT / "eval" / "benchmarks" / "research-synthesis" / "tasks.yaml"


def test_skill_declares_composition_contract():
    body = SKILL.read_text(encoding="utf-8")
    assert "create-viz" in body
    assert "validation report" in body.lower()
    assert "limitations" in body.lower()


def test_rubric_has_core_dimensions():
    text = RUBRIC.read_text(encoding="utf-8").lower()
    for dim in ("faithfulness", "calibration", "limitations"):
        assert dim in text


def test_benchmark_slice_loads():
    tasks = load_tasks(TASKS)
    assert len(tasks) >= 2
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m pytest tests/test_research_synthesis.py -v`
Expected: FAIL — `FileNotFoundError` (files absent).

- [ ] **Step 3: Write the skill, rubric, and benchmark files**

`skills/research-synthesis/SKILL.md`:
```markdown
---
name: research-synthesis
description: Use when turning validated results into a report, paper, figures, or deck — interprets findings honestly, visualizes them, and writes claims calibrated to the evidence with explicit limitations.
---

# Research Synthesis

Communicate what the evidence supports — no more, no less. The synthesis is where honest
work is most easily undone by overclaiming.

## From results to write-up

1. **Interpret.** State what each validated result means and, equally, what it does not.
   Tie every interpretation to the evidence in the validation report.
2. **Calibrate claims.** Match each claim's strength to its evidence: shown, suggested, or
   speculated. Quantify uncertainty. Cut any claim the evidence does not carry.
3. **Visualize.** Choose figures that show the data honestly — appropriate scales, error
   bars, and baselines; no chart that flatters the result. Delegate to `data:create-viz`.
4. **Limitations.** State the conditions under which the result holds, the threats that
   remain, and what would change the conclusion.
5. **Write.** Produce the artifact (report, paper section, or deck) with claims, evidence,
   and limitations clearly separated.

Output: the write-up plus its figures.

## Composes with

- `data:create-viz` and `data:data-visualization` for figures.
- `anthropic-skills:docx`, `pptx`, `pdf`, and `xlsx` for documents and decks.
- `anthropic-skills:web-artifacts-builder` for interactive results.
- Reads the **validation report** from `rigorous-validation`; never claim beyond it.

## Domain lenses

- **ML/AI:** report variance and the exact eval setup; show baselines beside results.
- **Computational science:** report error bars and the validation case reproduced.
- **Data science:** state the estimand, the assumptions, and what would break the estimate.

## Red flags (stop)

- A claim stronger than the validation report supports.
- A figure with a truncated axis or missing baseline that inflates the effect.
- Limitations omitted because they weaken the story.
```

`eval/rubrics/research-synthesis.md`:
```markdown
# Rubric — research-synthesis

Score an output produced under this skill on each dimension, 0–4.

- **Faithfulness to evidence (weight 0.30):** Every claim maps to evidence in the validation report; none overreaches.
- **Calibration (weight 0.25):** Claim strength matches evidence; uncertainty quantified.
- **Honest visualization (weight 0.20):** Figures show data fairly — scales, error bars, baselines.
- **Limitations (weight 0.15):** Conditions, threats, and what would change the conclusion are stated.
- **Clarity (weight 0.10):** Claims, evidence, and limitations are clearly separated.

Blended score = Σ(weight × dimension / 4). A claim beyond the evidence scores 0 on
faithfulness to evidence.
```

`eval/benchmarks/research-synthesis/tasks.yaml`:
```yaml
- id: calibrate_claims
  kind: judge
  prompt: >
    Validation shows a 1.5% improvement (95% CI [0.2%, 2.8%]) on one benchmark, one seed
    family, with no transfer tested. Write the results paragraph with claims calibrated to
    this evidence and explicit limitations. Judged on faithfulness and calibration per the rubric.
- id: honest_figure
  kind: judge
  prompt: >
    Describe how you would visualize a comparison where method A scores 88.1 and method B
    88.4 so the figure does not exaggerate the 0.3-point gap, and what a misleading version
    would do instead.
- id: limitations_section
  kind: judge
  prompt: >
    Given a result that holds only at batch size 32 and was not tested out of distribution,
    write the limitations the synthesis must state.
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python3 -m pytest tests/test_research_synthesis.py tests/test_skills_valid.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add skills/research-synthesis eval/rubrics/research-synthesis.md eval/benchmarks/research-synthesis tests/test_research_synthesis.py
git commit -m "feat: research-synthesis skill + rubric + benchmark slice"
```

---

### Task 6: Full-suite green + validate

**Files:**
- Modify: none (verification task; fold any fix into the file that needs it).

**Interfaces:**
- Consumes: everything above.
- Produces: a verified Plan 2 increment.

- [ ] **Step 1: Run the whole test suite**

Run: `python3 -m pytest -q`
Expected: PASS — Plan 1 tests + Task 1's 11 new tests + the four new per-skill test files (3 tests each), all green, no warnings.

- [ ] **Step 2: Run the harness against the real repo**

Run: `python3 -m eval.harness.cli lint`
Expected: `lint: OK`, exit 0 (now covers six skills: scientific-rigor, faithful-implementation, research-design, literature-review, rigorous-validation, research-synthesis).

Run: `python3 -m eval.harness.cli validate`
Expected: `validate: OK`, exit 0 (now covers five benchmark slices).

- [ ] **Step 3: Confirm clean tree**

Run: `git status` (expect clean).

- [ ] **Step 4: Commit (only if any fix was needed)**

```bash
git add -A
git commit -m "test: verify Plan 2 lifecycle skills suite green"
```

## Self-Review

**Spec coverage (design spec §3.2):** `research-design` → Task 2; `literature-review` → Task 3; `rigorous-validation` → Task 4; `research-synthesis` → Task 5. Each ships SKILL.md + rubric + benchmark slice + a contract/rubric/benchmark test, matching the `faithful-implementation` pattern. §10 hardening (deferred Plan 1 review items) → Task 1. Humanities skills (§3.3) and `skill-forge` (§3.4) remain in Plans 3–4 per the roadmap.

**Placeholder scan:** No `TODO`/`TBD`/`FIXME` in any new skill, rubric, or benchmark (enforced by lint + the parametrized `test_skills_valid.py`). All code and content steps show complete content.

**Type consistency:** New tests import `load_tasks` from `eval.harness.tasks` and read files via `Path(__file__).resolve().parents[1]`, identical to the established Plan 1 pattern. Task 1's edits preserve the existing `score_output` / `load_tasks` signatures; only error messages and internal guards change. Composition-contract assertions reference real skill names (`writing-plans`, `deep-research`, `statistical-analysis`, `verification-before-completion`, `create-viz`) that the SKILL.md bodies contain verbatim.
