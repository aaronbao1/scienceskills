# scienceskills Plan 3 — Humanities Skills Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add the two dedicated humanities skills — `humanities-inquiry` and `argumentation-and-sources` — each with a judge rubric and a benchmark slice, so the suite covers interpretive and argument-driven research alongside the empirical lifecycle.

**Architecture:** Reuses the Plan 1 harness unchanged. Each skill is `skills/<name>/SKILL.md`; its rubric is `eval/rubrics/<name>.md`; its benchmark slice is `eval/benchmarks/<name>/tasks.yaml`. The existing parametrized `tests/test_skills_valid.py` auto-covers each new skill's lint. The `scientific-rigor` router and `CLAUDE.md` already forward-reference both names, so no edit there — these skills satisfy those references. The two humanities skills are the interpretive counterparts that "swap into" the lifecycle: `humanities-inquiry` plays the `research-design` role for non-empirical work; `argumentation-and-sources` plays the `literature-review` + `rigorous-validation` roles for argument-driven work.

**Tech Stack:** Python 3.9+, pytest, PyYAML; markdown skills.

## Staging roadmap (this is Plan 3 of 4)

- Plan 1 (merged): scaffold + harness + `scientific-rigor` + `CLAUDE.md` + `faithful-implementation`.
- Plan 2 (merged): hardening + `research-design`, `literature-review`, `rigorous-validation`, `research-synthesis`.
- **Plan 3 (this doc):** `humanities-inquiry`, `argumentation-and-sources` (+ rubric + slice each).
- Plan 4: `skill-forge` engine — live `run.py`/`judge.py`/`tournament.py`, candidate generation, gating, human-approved promotion.

## Global Constraints

- Run pytest as `python3 -m pytest` (no `pytest` on PATH); pyyaml + pytest already installed for system `python3` (3.9.6); no venv.
- Every new `SKILL.md` frontmatter has `name` == its directory name and a non-empty `description` ≤ 1024 chars; body starts with an H1; no literal `TODO`/`TBD`/`FIXME` tokens (the lint enforces this).
- Every benchmark `tasks.yaml` loads via `eval.harness.tasks.load_tasks`.
- Skill prose is the product: use the EXACT content from each task verbatim — section names and composition-contract wording are asserted by tests. Sentence case.
- DRY, YAGNI, TDD, frequent commits. Never implement on `main`/`master` without consent — work on a feature branch.

---

### Task 1: `humanities-inquiry` skill + rubric + benchmark slice

**Files:**
- Create: `skills/humanities-inquiry/SKILL.md`
- Create: `eval/rubrics/humanities-inquiry.md`
- Create: `eval/benchmarks/humanities-inquiry/tasks.yaml`
- Test: `tests/test_humanities_inquiry.py`

**Interfaces:**
- Consumes: `eval.harness.tasks.load_tasks`; auto-covered by `tests/test_skills_valid.py` lint.
- Produces: the `humanities-inquiry` skill.

- [ ] **Step 1: Write the failing test**

`tests/test_humanities_inquiry.py`:
```python
from pathlib import Path
from eval.harness.tasks import load_tasks

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "skills" / "humanities-inquiry" / "SKILL.md"
RUBRIC = ROOT / "eval" / "rubrics" / "humanities-inquiry.md"
TASKS = ROOT / "eval" / "benchmarks" / "humanities-inquiry" / "tasks.yaml"


def test_skill_declares_composition_contract():
    body = SKILL.read_text(encoding="utf-8")
    assert "argumentation-and-sources" in body
    assert "research-synthesis" in body
    assert "positionality" in body.lower()


def test_rubric_has_core_dimensions():
    text = RUBRIC.read_text(encoding="utf-8").lower()
    for dim in ("interpretive validity", "methodological fit", "reflexivity", "ethics"):
        assert dim in text


def test_benchmark_slice_loads():
    tasks = load_tasks(TASKS)
    assert len(tasks) >= 2
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m pytest tests/test_humanities_inquiry.py -v`
Expected: FAIL — `FileNotFoundError` (files absent).

- [ ] **Step 3: Write the skill, rubric, and benchmark files**

`skills/humanities-inquiry/SKILL.md`:
```markdown
---
name: humanities-inquiry
description: Use for interpretive or qualitative research — close reading, hermeneutics, historiography, theoretical framing, and qualitative coding — where the goal is a defensible interpretation rather than an empirical measurement.
---

# Humanities Inquiry

Interpretive research asks what something means, not what value it takes. Rigor here is the
defensibility of the reading, the fit of the method, and honesty about your own position —
not statistical significance.

## Frame the inquiry

1. **Question.** What text, artifact, practice, or period are you interpreting, and what
   interpretive question are you asking of it?
2. **Method.** Choose the interpretive method that fits — close reading, hermeneutics,
   historiography, discourse analysis, qualitative coding — and say why it fits this material.
3. **Theoretical frame.** Name the lens (a critical, historical, or theoretical tradition)
   you read through, and what it foregrounds and hides.
4. **Evidence.** Ground every claim in specific passages, sources, or observations, with
   source criticism from `argumentation-and-sources`. An interpretation with no anchor is
   assertion.
5. **Reflexivity and positionality.** State your standpoint and how it shapes the reading;
   name rival interpretations and why yours is better supported.
6. **Ethics.** Address consent, representation, and harm when working with human subjects,
   communities, or sensitive material.

Output: a framed interpretation with its method, evidence, and acknowledged limits.

## Composes with

- `argumentation-and-sources` for source criticism and for stress-testing the argument.
- `research-synthesis` downstream to write up the interpretation with calibrated claims.
- This is the interpretive counterpart to `research-design`; use it instead for non-empirical
  work. `scientific-rigor` still governs honesty and reasoning.

## Red flags (stop)

- An interpretation with no textual or archival anchor.
- A reading that ignores the strongest rival interpretation.
- Positionality and ethics omitted when the material demands them.
```

`eval/rubrics/humanities-inquiry.md`:
```markdown
# Rubric — humanities-inquiry

Score an output produced under this skill on each dimension, 0–4.

- **Interpretive validity (weight 0.30):** Reading is grounded in specific evidence and engages rival interpretations.
- **Methodological fit (weight 0.25):** The interpretive method suits the material and is applied consistently.
- **Theoretical framing (weight 0.20):** The lens is named and used, with awareness of what it foregrounds and hides.
- **Reflexivity (weight 0.15):** Positionality is stated and its effect on the reading acknowledged.
- **Ethics (weight 0.10):** Consent, representation, and harm are addressed where the material demands.

Blended score = Σ(weight × dimension / 4). An interpretation with no evidence anchor scores
0 on interpretive validity.
```

`eval/benchmarks/humanities-inquiry/tasks.yaml`:
```yaml
- id: ground_interpretation
  kind: judge
  prompt: >
    Offer an interpretation of a recurring image in a novel of your choice, anchoring each
    claim to specific passages, naming the interpretive method and theoretical lens, and
    engaging the strongest rival reading. Judged on interpretive validity and methodological
    fit per the rubric.
- id: positionality
  kind: judge
  prompt: >
    You are analyzing oral histories from a community you do not belong to. State the
    positionality and ethics considerations that must shape the interpretation and the
    write-up.
- id: method_fit
  kind: judge
  prompt: >
    A researcher wants to study how a concept's meaning shifted across a century of
    pamphlets. Recommend an interpretive method, with reasons, and one rival method you
    would reject and why.
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python3 -m pytest tests/test_humanities_inquiry.py tests/test_skills_valid.py -v`
Expected: PASS (contract, rubric, benchmark tests pass; `humanities-inquiry` lints clean under the parametrized skill test).

- [ ] **Step 5: Commit**

```bash
git add skills/humanities-inquiry eval/rubrics/humanities-inquiry.md eval/benchmarks/humanities-inquiry tests/test_humanities_inquiry.py
git commit -m "feat: humanities-inquiry skill + rubric + benchmark slice"
```

---

### Task 2: `argumentation-and-sources` skill + rubric + benchmark slice

**Files:**
- Create: `skills/argumentation-and-sources/SKILL.md`
- Create: `eval/rubrics/argumentation-and-sources.md`
- Create: `eval/benchmarks/argumentation-and-sources/tasks.yaml`
- Test: `tests/test_argumentation_and_sources.py`

**Interfaces:**
- Consumes: `eval.harness.tasks.load_tasks`; auto-covered by `tests/test_skills_valid.py` lint.
- Produces: the `argumentation-and-sources` skill.

- [ ] **Step 1: Write the failing test**

`tests/test_argumentation_and_sources.py`:
```python
from pathlib import Path
from eval.harness.tasks import load_tasks

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "skills" / "argumentation-and-sources" / "SKILL.md"
RUBRIC = ROOT / "eval" / "rubrics" / "argumentation-and-sources.md"
TASKS = ROOT / "eval" / "benchmarks" / "argumentation-and-sources" / "tasks.yaml"


def test_skill_declares_composition_contract():
    body = SKILL.read_text(encoding="utf-8")
    assert "humanities-inquiry" in body
    assert "literature-review" in body
    assert "fallacy" in body.lower()
    assert "source" in body.lower()


def test_rubric_has_core_dimensions():
    text = RUBRIC.read_text(encoding="utf-8").lower()
    for dim in ("source appraisal", "argument soundness", "evidence sufficiency", "fallacy"):
        assert dim in text


def test_benchmark_slice_loads_with_ground_truth():
    tasks = load_tasks(TASKS)
    assert len(tasks) >= 2
    assert any(t.kind == "ground_truth" for t in tasks)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m pytest tests/test_argumentation_and_sources.py -v`
Expected: FAIL — `FileNotFoundError` (files absent).

- [ ] **Step 3: Write the skill, rubric, and benchmark files**

`skills/argumentation-and-sources/SKILL.md`:
```markdown
---
name: argumentation-and-sources
description: Use for evidence and source criticism in argument-driven work — appraising primary and secondary sources, constructing and stress-testing arguments, mapping scholarly debate, and catching fallacies and unsupported leaps.
---

# Argumentation and Sources

In argument-driven scholarship, validity is the soundness of the argument and the quality
of its sources — the counterpart to statistical validation. Build the case, then try to
break it.

## Appraise sources

- **Provenance.** Who produced the source, when, why, and for whom? Distinguish primary
  from secondary; weigh bias, distance from events, and reliability.
- **Corroboration.** Triangulate claims across independent sources; flag a claim that rests
  on a single uncorroborated source.
- **Citation integrity.** Every claim is traceable to a source you have actually examined.

## Build and stress-test the argument

- **Structure.** State the thesis, the premises, and how each premise is supported.
- **Stress-test.** Steelman the strongest counterargument and answer it. Map the scholarly
  debate rather than citing only allies.
- **Fallacy check.** Scan for informal fallacies — appeal to popularity or authority, hasty
  generalization, false dilemma, circularity — and for leaps the evidence does not carry.

Output: a sourced, stress-tested argument with its debate map and residual weaknesses.

## Composes with

- Supplies source criticism to `humanities-inquiry` and `literature-review`.
- For argument-driven work this plays the validation role that `rigorous-validation` plays
  for empirical work; `research-synthesis` writes up the result.

## Red flags (stop)

- A thesis supported only by sources that already agree with it.
- A claim resting on one uncorroborated or unexamined source.
- The strongest counterargument left unaddressed.
```

`eval/rubrics/argumentation-and-sources.md`:
```markdown
# Rubric — argumentation-and-sources

Score an output produced under this skill on each dimension, 0–4.

- **Source appraisal (weight 0.25):** Provenance, bias, and reliability judged; primary vs secondary distinguished.
- **Argument soundness (weight 0.25):** Thesis and premises explicit; inferences valid.
- **Evidence sufficiency (weight 0.20):** Claims corroborated; single-source claims flagged.
- **Fallacy detection (weight 0.20):** Informal fallacies and unsupported leaps caught.
- **Citation integrity (weight 0.10):** Every claim traceable to an examined source.

Blended score = Σ(weight × dimension / 4). A thesis supported only by agreeing sources scores
0 on evidence sufficiency.
```

`eval/benchmarks/argumentation-and-sources/tasks.yaml`:
```yaml
- id: name_the_fallacy
  kind: ground_truth
  prompt: >
    Name the informal fallacy in this argument: "No one has proven the claim false, so it
    must be true." Answer with the standard name of the fallacy.
  scorer: contains
  expected: ignorance
- id: appraise_source
  kind: judge
  prompt: >
    You are handed a memoir written 40 years after the events it describes, by a participant
    with a stake in how they are remembered. Describe how you appraise its reliability and
    what corroboration you would seek. Judged on source appraisal per the rubric.
- id: steelman
  kind: judge
  prompt: >
    Given a thesis you find persuasive, state the strongest counterargument against it and a
    fair response, and explain why mapping the debate matters more than citing only allies.
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python3 -m pytest tests/test_argumentation_and_sources.py tests/test_skills_valid.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add skills/argumentation-and-sources eval/rubrics/argumentation-and-sources.md eval/benchmarks/argumentation-and-sources tests/test_argumentation_and_sources.py
git commit -m "feat: argumentation-and-sources skill + rubric + benchmark slice"
```

---

### Task 3: Full-suite green + validate

**Files:**
- Modify: none (verification task; fold any fix into the file that needs it).

**Interfaces:**
- Consumes: everything above.
- Produces: a verified Plan 3 increment.

- [ ] **Step 1: Run the whole test suite**

Run: `python3 -m pytest -q`
Expected: PASS — all prior tests plus the two new per-skill test files (3 tests each) and the two extra `test_skills_valid` lint params, all green, no warnings.

- [ ] **Step 2: Run the harness against the real repo**

Run: `python3 -m eval.harness.cli lint`
Expected: `lint: OK`, exit 0 (now covers eight skills).

Run: `python3 -m eval.harness.cli validate`
Expected: `validate: OK`, exit 0 (now covers seven benchmark slices).

- [ ] **Step 3: Confirm clean tree**

Run: `git status` (expect clean).

- [ ] **Step 4: Commit (only if any fix was needed)**

```bash
git add -A
git commit -m "test: verify Plan 3 humanities skills suite green"
```

## Self-Review

**Spec coverage (design spec §3.3):** `humanities-inquiry` → Task 1; `argumentation-and-sources` → Task 2. Each ships SKILL.md + rubric + benchmark slice + a contract/rubric/benchmark test, matching the established lifecycle-skill pattern. These satisfy the forward-references already present in the `scientific-rigor` router and `CLAUDE.md`. `skill-forge` (§3.4) remains in Plan 4.

**Placeholder scan:** No `TODO`/`TBD`/`FIXME` in any new skill, rubric, or benchmark (enforced by lint + `test_skills_valid.py`). All content steps show complete content.

**Type consistency:** New tests import `load_tasks` from `eval.harness.tasks` and read files via `Path(__file__).resolve().parents[1]`, identical to the established pattern. Composition-contract assertions reference real skill names that the SKILL.md bodies contain verbatim. The `argumentation-and-sources` ground-truth task uses the `contains` scorer with `expected: ignorance` — the argument ("no one has proven it false, so it must be true") is an appeal to ignorance, whose standard name contains the word "ignorance".
