# scienceskills — A Self-Improving Skill Suite for Scientific Research

> **Status:** Design approved (brainstorming). Next step: `superpowers:writing-plans`.
> **Date:** 2026-06-27
> **Author:** aaron.bao64@gmail.com (with Claude)

## 1. Overview

`scienceskills` is a Claude Code **plugin** (a versioned git repo) that delivers a
small, comprehensive suite of skills for conducting rigorous scientific research —
from literature review through faithful implementation to validated results — plus a
**self-improvement engine** (`skill-forge`) that adaptively evolves those skills by
generating candidate versions, evaluating them against a benchmark + judge + A/B
harness, and promoting the winner on human approval. It ships with a **master prompt**
(`CLAUDE.md`) that activates and routes the suite.

The guiding principle: **the suite does not reinvent planning, TDD, code review,
statistics, or document generation — it delegates to the best-in-class skills already
installed and adds only the research-specific layer on top.** This keeps the suite
minimal and makes it compose cleanly with `superpowers`, the Anthropic `data:*` skills,
and `deep-research`.

### 1.1 Goals

- A **minimal, comprehensive** set of skills covering every step of computational/
  empirical research, with a **domain-agnostic spine** and pluggable lenses for
  computational science, ML/AI, data science, and the humanities.
- **Rigor + robustness + structured creativity** baked into every skill, with hard
  reasoning and room for innovation.
- **Faithful implementation**: code provably matches the literature; competing methods
  are compared and the best one is chosen with explicit justification; the end result
  is rigorously tested.
- A **self-improving pipeline** that auto-researches improvements, compares versions on
  measurable output quality, and promotes better versions (human-approved), with full
  version history.
- A **drop-in master prompt** for `CLAUDE.md` that qualifies everything needed for
  scientific research and for implementing its codebase.

### 1.2 Non-goals (YAGNI)

- Not a domain knowledge base (no field-specific facts baked in; the skills are
  *method* skills, parameterized per project).
- Not a replacement for `superpowers`/`data:*` — it orchestrates them.
- No fully autonomous unattended promotion in v1 (promotion is human-gated; a future
  cron mode is out of scope for the first plan).
- No bespoke web UI; evaluation reporting is markdown + the existing `data:*`/widget
  tooling.

## 2. Locked Decisions

| Decision | Choice | Rationale |
|---|---|---|
| Domain | Domain-agnostic spine + lenses (comp-sci, ML/AI, data-sci first-class; humanities explicit) | One rigor core; specialization activates per project. |
| Eval signal | **Hybrid**: ground-truth benchmark + LLM-judge rubric + A/B tournament | Objective anchor where possible, flexible judge elsewhere, relative ranking always. |
| Automation | Auto-run + auto-evaluate; **human approves promotion** | Maximally automatic generation/eval; safe gate before replacing an active skill. |
| Packaging | Git repo structured as a Claude Code plugin in `scienceskills/` | Git gives the loop version history + rollback; plugin makes it loadable anywhere. |
| Taxonomy | Approach A — lifecycle-phase skills | Smallest set where each unit is independently A/B-testable (loop requirement). |
| Humanities | Two dedicated skills | User request; interpretive method is distinct enough to warrant its own units. |
| Integration | Explicit "Composes with" contracts (artifact + timing + path) per skill | Makes the suite work smoothly with existing skills rather than duplicating them. |

## 3. Architecture — The 9 Skills

Three groups: one **backbone** (always-on), five **lifecycle** skills, two **humanities**
skills, and one **meta** engine. Each skill is a directory `skills/<name>/SKILL.md`
with optional reference files. Every skill's SKILL.md MUST contain:
- a tight `description:` frontmatter tuned for trigger accuracy,
- a **Composes with** section (which existing skill, when, what artifact),
- a **Domain lenses** section (how it adapts across comp-sci / ML-AI / data-sci /
  humanities), where relevant,
- an **Anti-patterns / red flags** section.

### 3.1 Backbone

**`scientific-rigor`** (always-on, flexible)
- *Purpose:* the reasoning constitution applied to all research work — falsifiability,
  intellectual honesty, calibrated uncertainty, anti-bias / anti-p-hacking / anti-HARKing,
  robustness thinking, **and** structured creativity (divergent generation → hard
  convergent pruning with explicit criteria). Acts as the **lifecycle router** pointing
  to the right phase skill.
- *Trigger:* any research, analysis, or scientific-implementation task.
- *Output:* not an artifact producer; it sets standards and routes.
- *Composes with:* every other skill. Its **condensed form is the master `CLAUDE.md`**.
- *Reference files:* `reasoning-and-creativity.md` (divergent/convergent technique,
  red-teaming your own ideas), `rigor-checklists.md` (falsifiability, bias, honesty).

### 3.2 Lifecycle (5 phases)

**`research-design`**
- *Purpose:* frame the research question; state hypotheses and **falsifiable
  predictions**; position novelty against the field; define success metrics and the
  experiment + ablation plan; adopt a preregistration mindset (decide analyses before
  seeing results).
- *Trigger:* starting a research project / defining what to test and why.
- *Input:* a research idea (and optionally an existing brainstorming spec).
- *Output:* a **research spec** = the brainstorming spec extended with hypotheses,
  predictions, metrics, planned analyses, and placeholders for literature-derived
  oracles. Saved to `docs/superpowers/specs/` (research projects use their own repo).
- *Composes with:* `superpowers:brainstorming` (upstream) → `superpowers:writing-plans`
  (downstream consumes the research spec).
- *Lenses:* humanities projects route to `humanities-inquiry` instead.

**`literature-review`**
- *Purpose:* systematic discovery, retrieval, and **critical appraisal** of sources;
  synthesis into a SOTA map and explicit gap analysis; **a ranked comparison of
  competing methods/implementations ending in one justified recommendation** for the
  project's context (this absorbs the "no conflicting/better method — evaluate which is
  best" requirement). Extracts the equations, algorithms, hyperparameters, and reported
  numbers that become **test oracles** downstream.
- *Trigger:* "what does the literature say", "which method should we use", method survey.
- *Output:* a **method dossier** = (a) annotated source list with appraisal, (b) SOTA +
  gaps, (c) ranked method comparison with selection criteria + decision, (d) the extracted
  oracles (equations / reference outputs / numbers / tolerances) keyed for the spec.
- *Composes with:* `deep-research` (delegated fan-out search + adversarial verification).
- *Lenses:* humanities → defer source criticism to `argumentation-and-sources`.

**`faithful-implementation`**
- *Purpose:* the **fidelity-oracle layer**. It does NOT replace TDD/plan/execution —
  it defines *what each failing test must assert* so that "green" means "faithful to the
  literature": paper equations, reference implementation outputs, conserved quantities /
  invariants, numerical tolerances, edge-case behavior named in the source. Detects
  silent divergence and conflicts between the implementation and the chosen method.
- *Trigger:* implementing a method/algorithm from a paper; verifying an implementation
  matches the literature.
- *Input:* the method dossier (oracles) + the implementation plan.
- *Output:* fidelity test specifications injected into the TDD plan + a fidelity report
  (matches / divergences / unresolved).
- *Composes with:* `superpowers:writing-plans` (oracles → plan tasks),
  `superpowers:subagent-driven-development` / `superpowers:executing-plans` (execution),
  `superpowers:test-driven-development` (each task's red-green loop asserts the oracles),
  `superpowers:systematic-debugging` (when fidelity tests fail).
- *Lenses:* comp-sci (numerical tolerance, conservation/convergence), ML/AI (match
  reported metric within CI, seed control, reference-impl diffing), data-sci (estimator
  correctness, identification assumptions).

**`rigorous-validation`**
- *Purpose:* test the *end result*, not just unit correctness — reproducibility (re-run
  from clean state, seeds, environment capture), ablations, statistical validity
  (significance, power, multiple-comparison control), robustness/sensitivity sweeps,
  sanity baselines, **leakage / bias / error checks**, and adversarial red-teaming of
  your own results ("how could this number be wrong or fake?").
- *Trigger:* results exist and need to be validated before they are believed/reported.
- *Output:* a **validation report** (claims, evidence, threats addressed, residual risks).
- *Composes with:* `data:statistical-analysis` (stats), `data:validate-data` (QA),
  `/code-review` + `superpowers:requesting-code-review` (code correctness),
  `superpowers:verification-before-completion` (evidence-before-claims gate).
- *Lenses:* humanities → `argumentation-and-sources` for argument-validity instead of
  statistical validity.

**`research-synthesis`**
- *Purpose:* honest analysis and interpretation; visualization; write-up with
  **calibrated claims and explicit limitations**; align every claim to its evidence in
  the validation report (no overclaiming).
- *Trigger:* turning validated results into a report / paper / deck / figures.
- *Output:* the research write-up + figures.
- *Composes with:* `data:create-viz` / `data:data-visualization` (figures),
  `anthropic-skills:docx` / `pptx` / `pdf` / `xlsx` (documents),
  `anthropic-skills:web-artifacts-builder` (interactive results).

### 3.3 Humanities track (2 skills)

**`humanities-inquiry`** — interpretive/qualitative method: hermeneutics, close reading,
historiography, theoretical framing, qualitative coding, positionality and research
ethics. Plays the `research-design` role for non-empirical work. *Composes with:*
`literature-review`/`argumentation-and-sources` upstream, `research-synthesis` downstream.

**`argumentation-and-sources`** — evidence and source criticism: primary/secondary source
appraisal, archival/citation rigor, constructing and **stress-testing arguments**,
mapping scholarly debate, detecting fallacies and unsupported leaps. Plays the
`literature-review` + `rigorous-validation` roles for argument-driven work.

### 3.4 Meta engine

**`skill-forge`** — the self-improvement loop (Section 5). *Composes with:*
`superpowers:writing-skills` / `anthropic-skills:skill-creator` (authoring candidates),
`superpowers:dispatching-parallel-agents` + the **Workflow tool** (parallel eval),
`superpowers:using-git-worktrees` (isolated candidate runs).

## 4. Composition Contracts (the hand-off layer)

The suite works *with* existing skills via explicit artifact hand-offs:

```
research-design ──research spec──▶ writing-plans ──TDD plan──▶ subagent-driven-development
       ▲                                                              │ each task:
literature-review ──method dossier (oracles)──────────────┐          ▼ TDD red-green
                                                           └─▶ faithful-implementation
                                                               (oracles = what tests assert)
                                                                        │
results ──▶ rigorous-validation ──validation report──▶ research-synthesis ──write-up──▶ done
   (delegates: data:statistical-analysis, /code-review, verification-before-completion,
    data:create-viz, docx/pptx/pdf/xlsx)
```

**Key invariant:** `faithful-implementation` plugs *into* the superpowers execution loop;
it supplies oracles, it does not fork the workflow. This guarantees
"`faithful-implementation` + `writing-plans`" and "+ `subagent-driven-development`"
compose without friction.

Every SKILL.md's **Composes with** section names: the target skill, the trigger moment,
and the exact artifact (and its file-path convention) that crosses the boundary. During
implementation, each contract is verified against the *actual* current content of the
target skill (descriptions can drift), not just its description.

## 5. The Self-Improvement Loop (`skill-forge`)

One cycle, per target skill:

1. **Mine weaknesses & advances.** Use `deep-research` + the skill's own eval history +
   session transcripts to produce a concrete, evidence-backed list of failure modes and
   new best-practices for that skill.
2. **Generate candidates.** Use `writing-skills` to produce 2–3 variant versions
   (different framing, structure, examples, or emphasis), each in its own git worktree.
3. **Evaluate — hybrid signal.** Run incumbent + each candidate against the skill's
   **benchmark slice**:
   - *Ground-truth tasks* (objective): reproduce-this-number, pass-these-tests,
     extract-this-correctly → automatic pass/fail/score.
   - *Judge-rubric panel* (LLM judges): score on **rigor, correctness, faithfulness,
     creativity, intellectual honesty**; use a panel (≥3) and adversarial/diverse lenses
     to reduce single-judge bias.
   - *A/B tournament*: head-to-head comparisons between versions on the same tasks.
4. **Score & gate.** Blend into a single score with explicit weights; record per-task
   results. A candidate becomes a **promotion proposal** only if it beats the incumbent
   by a configured margin (and regresses on no critical task).
5. **Human-approved promotion.** Present the diff + full eval evidence (scores, judge
   rationales, A/B records, any regressions). On approval, promote and **git-tag a new
   version**; the old version stays in history for instant rollback.

### 5.1 Eval harness (`eval/`)

The harness is the ground truth the loop and the "compare versions / keep the better
output" requirement rest on. It is a first-class deliverable, not an afterthought.

```
eval/
├── benchmarks/<skill>/        # versioned task suites, one slice per skill
│   ├── tasks.yaml             # task id, prompt, inputs, expected (if ground-truth)
│   └── fixtures/              # papers, datasets, reference outputs
├── rubrics/<skill>.md         # judge rubric + weights for that skill
├── harness/                   # runner (Python): executes a skill version on a task, captures output
│   ├── run.py                 # run one (skill-version, task) → output + objective score
│   ├── judge.py               # judge panel scoring against a rubric
│   └── tournament.py          # A/B head-to-head + aggregation
└── reports/<skill>/<date>/    # generated eval reports (markdown)
```

The harness is **Python** (matches the `data:*` skills and scientific-computing norms).
Harness *code* is built with TDD (it has deterministic, testable units: scoring,
aggregation, gating). Skill *prose* is validated by running the benchmark, not by unit
tests. The first plan ships a **seed benchmark** (a handful of strong tasks per skill,
mixing ground-truth and judge-only) that grows over time.

## 6. Master Prompt (`CLAUDE.md`)

A short, always-loaded constitution (target ≲ 1.5 KB of signal, not a wall of text):
- **Standards:** rigor + intellectual honesty + calibrated uncertainty + structured
  creativity, in 5–7 crisp lines.
- **Lifecycle router:** "starting research → `research-design`; surveying the field →
  `literature-review`; implementing a method → `faithful-implementation` (with
  `writing-plans` + `subagent-driven-development`); validating results →
  `rigorous-validation`; writing up → `research-synthesis`; humanities work →
  `humanities-inquiry` / `argumentation-and-sources`."
- **Composition rule:** delegate to existing skills, never reinvent.
- **Anti-patterns:** p-hacking, HARKing, cherry-picking, unfaithful reproduction,
  overclaiming beyond evidence, uncontrolled leakage.
- Points to `scientific-rigor` for the deep techniques.

It is designed to drop into a research project's `CLAUDE.md`/`AGENTS.md` (or go global).

## 7. Repo Layout

```
scienceskills/                         (git repo + Claude Code plugin)
├── .claude-plugin/marketplace.json    # makes the suite installable
├── plugin.json / skills manifest
├── CLAUDE.md                          # the master prompt
├── skills/
│   ├── scientific-rigor/SKILL.md (+ reasoning-and-creativity.md, rigor-checklists.md)
│   ├── research-design/SKILL.md
│   ├── literature-review/SKILL.md
│   ├── faithful-implementation/SKILL.md
│   ├── rigorous-validation/SKILL.md
│   ├── research-synthesis/SKILL.md
│   ├── humanities-inquiry/SKILL.md
│   ├── argumentation-and-sources/SKILL.md
│   └── skill-forge/SKILL.md (+ loop refs)
├── eval/                              # benchmark + harness (Section 5.1)
└── docs/superpowers/specs/2026-06-27-scienceskills-design.md
```

## 8. Domain Lenses

Each lens is a short reference block (in the relevant skills) describing how the method
adapts. Seed lenses:
- **Computational science:** numerical tolerance & error analysis, convergence,
  conservation/invariants, validation against analytical/known solutions.
- **ML/AI:** seed control & variance, match reported metrics within confidence intervals,
  reference-implementation diffing, ablation hygiene, data leakage.
- **Data science / statistics:** identification assumptions, estimator correctness,
  power & multiple-comparison control, causal-inference validity.
- **Humanities:** interpretive validity, source provenance, positionality, argument
  soundness (handled primarily by the two humanities skills).

## 9. Testing Strategy (for the suite itself)

- **Harness code** → TDD (`test-driven-development`); deterministic units.
- **Skill prose** → validated by the `eval/` benchmark; a skill "passes" when it meets
  rubric thresholds on its slice.
- **Trigger accuracy** → `skill-creator`'s eval tooling on each skill's `description`.
- **Composition** → an end-to-end smoke test: run a small real research task through the
  whole pipeline and confirm the hand-offs produce the expected artifacts.

## 10. Risks & Mitigations

| Risk | Mitigation |
|---|---|
| Benchmark too weak → loop optimizes the wrong thing | Treat seed benchmark as first-class; mix ground-truth + judge; grow it; human gate. |
| Judge bias / reward hacking | Panel of ≥3 with diverse/adversarial lenses; keep ground-truth anchor tasks; human review of promotions. |
| Skills overlap / trigger collisions | Tune `description:` per skill; clear router in `CLAUDE.md`; trigger-accuracy evals. |
| Composition contracts drift as target skills change | Verify each contract against live skill content at implementation; smoke test. |
| Scope creep across 9 skills + harness | Plan builds in dependency order: harness + `scientific-rigor` + one lifecycle skill end-to-end first, then the rest. |

## 11. Success Criteria

1. All 9 skills present, each with a tuned description, Composes-with contract, and (where
   relevant) lenses + anti-patterns.
2. A real research task runs end-to-end through the pipeline, delegating correctly to
   `writing-plans` / `subagent-driven-development` / `data:*` / `deep-research`, and
   `faithful-implementation` enforces literature-derived oracles via TDD.
3. `eval/` runs a seed benchmark for every skill and produces a comparison report.
4. `skill-forge` completes one full cycle on at least one skill: generates candidates,
   evaluates, and surfaces a human-approval promotion proposal with evidence.
5. The plugin installs and the master `CLAUDE.md` routes correctly.

## 12. Implementation Order (for the plan)

1. Repo + plugin scaffold + git init.
2. `eval/` harness skeleton (TDD) + rubric format + one seed benchmark slice.
3. `scientific-rigor` backbone + master `CLAUDE.md`.
4. One lifecycle skill end-to-end (`faithful-implementation`) proving the superpowers
   composition, with its benchmark slice.
5. Remaining lifecycle skills + their slices.
6. Two humanities skills + slices.
7. `skill-forge` engine (generate → eval → gate → human-approved promote) using the harness.
8. End-to-end composition smoke test + one full `skill-forge` cycle.
