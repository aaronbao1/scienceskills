# SkillForge — self-contained, log-driven redesign (design spec)

- **Date:** 2026-06-28
- **Status:** Approved design, pre-plan
- **Branch:** `skillforge-self-contained-redesign`
- **Supersedes:** the Tier 1–3 "research-derived hardening" of skill-forge (`stats.py`, `tournament.py`,
  `mutation.py`, `pareto.py`, `goodhart.py`, `anchor.py`, `loop_control.py`, `judge_safety.py`).

## 1. Context & motivation

An audit of the current skill-forge found it is **rule-driven, not log-driven**. Nothing under `eval/`
writes a file; the "history" consumed by `loop_control.py`/`goodhart.py`/`anchor.py` is re-typed by the
agent each round. Of the eight hardening modules, two are dead code (`mutation.py`, `pareto.py` — zero
production importers), two only emit advisory flags that never gate (`tournament.py`, `judge_safety.py`),
and ~90 lines of `stats.py` reimplement `scipy` under a self-imposed "no numpy" rule — near-vacuous at
skill-forge's tiny sample sizes. The irreducible core that earns its keep is small: a held-out benchmark,
one promotion gate, a critical-regression veto, and git rollback.

A deep-research pass (self-evolving-agent surveys [2508.07407](https://arxiv.org/abs/2508.07407),
[2507.21046](https://arxiv.org/pdf/2507.21046); ExpeL [2308.10144](https://arxiv.org/abs/2308.10144);
Agent Workflow Memory [2409.07429](https://arxiv.org/abs/2409.07429); ProTeGi
[EMNLP'23](https://aclanthology.org/2023.emnlp-main.494/); reward-hacking
[ICLR'26 wksp](https://openreview.net/forum?id=ikrQWGgxYg); misevolution
[2509.26354](https://arxiv.org/abs/2509.26354)) supports a **log → distill → retrieve/edit** loop with
no weight updates, and is emphatic that the one non-negotiable guard is a **held-out true-task gate the
optimizer cannot see** (≈47–74% of self-improving code-agent "gains" are illusory without it).

This redesign keeps that one guard, deletes the rest, and adds the missing substrate — driven by insights
captured **by the skills themselves**, held **inside skill-forge**, with **no outside system**.

## 2. Goals & non-goals

**Goals**
- Self-contained: all capture, storage, distillation, gating, and editing live under `skills/skill-forge/`
  and the existing `eval/` harness. No dependency on an external system at forge-time.
- Log-driven: improvement is driven by insights collected from running the skills repeatedly.
- Streamlined: deterministic surface reduced to **log I/O, the scorer, one gate decision, one monitor**.
  Everything else (mining, distilling, crystallizing, judging) is LLM-orchestrated via prose.
- Robust: a held-out synthetic gate + critical-regression veto + Goodhart monitor + git rollback guard
  against reward hacking and overfitting.

**Non-goals (YAGNI)**
- Self-referential improvement (skill-forge editing itself, Darwin-Gödel style) — highest risk; deferred.
- Embedding/retrieval store — rejected in favor of a flat playbook.
- A separate LLM-judge labeling pass over real traces — rejected in favor of in-skill self-reflection.
- An external transcript-scanning daemon — rejected in favor of in-skill push capture.

## 3. Design decisions (locked)

| # | Decision | Choice |
|---|---|---|
| D1 | Overarching framework | **Hybrid**: fast experience layer (playbook) + slow gated edits to SKILL.md |
| D2 | Signal source | Insights captured **by each skill at session end** (push), from its own session |
| D3 | Success signal | **Behavioral / self-reflection** (the five signals below) — weak/probabilistic; no judge |
| D4 | Migration | **Clean rebuild** — keep only the spine; delete the 8 hardening modules |
| D5 | Memory form | **Flat files** (markdown + jsonl); no embeddings/retrieval |
| D6 | Storage location | **Central, in skill-forge** (`skills/skill-forge/insights/<skill>/`) |
| D7 | Capture outputs | **Two per session**: a transcript log **and** a robust insight reflection |
| D8 | Raw transcripts | Snapshotted to a **gitignored** local cache; distilled artifacts are committed |
| D9 | Capture trigger | In-skill (manual at session end), with an **optional Stop hook** to automate |

**The five behavioral signals** (used as the reflection rubric, all observable from the session itself):
user correction / redo · abandonment (session ends unresolved) · approval (explicit, or work committed)
· hard failure (tool errors, hook errors, retries) · self-assessed struggle (the agent's own
"this isn't working, let me reconsider").

## 4. Architecture overview

Two roles, one self-contained system:

- **Target skills** (`argumentation-and-sources`, `deep-reasoning`, `deep-reasoning-ultra`,
  `faithful-implementation`, `humanities-inquiry`, `literature-review`, `research-design`,
  `research-synthesis`, `rigorous-validation`, `scientific-rigor`) — each gains one standard **Capture**
  section that *pushes* a session record + insight into skill-forge's store, and a **Consult** pointer to
  its playbook.
- **skill-forge** — holds the store; **distills** raw insights into a bounded playbook; **crystallizes**
  proven heuristics into attributed SKILL.md edits; **gates** each edit on a held-out split; **monitors**
  proxy↔gold divergence.

Maturity ladder: **raw** (per session) → **distilled** (playbook, consulted at use-time, reversible,
no gate) → **crystallized** (edited into the target SKILL.md, gated + human-approved + git-tagged).

## 5. Components

Each component states its purpose, interface, and dependencies so it can be built and tested in isolation.

### 5.1 Per-skill Capture section (prose, added to every target skill)

**Purpose:** at session end, push two outputs into skill-forge's store.
**Interface:** a standard markdown block appended to each target `SKILL.md`. Template:

```markdown
## Capture (run at session end)
When you finish a task that used this skill, record what happened so skill-forge can learn:
1. Snapshot this session: `python3 -m eval.harness.capture snapshot <skill>`
2. Reflect against the five signals (correction/redo · abandonment · approval · hard failure ·
   self-assessed struggle) and append ONE generalized insight (no project-specifics):
   `python3 -m eval.harness.capture insight <skill>` then provide the record fields when prompted.
Record the *lesson*, not the incident. If you can name a specific line of this SKILL.md that caused a
failure, include a `proposed_edit`.
```

**Consult pointer** (also added near the top of each target skill): *"Before starting, consult your
playbook: `skills/skill-forge/insights/<skill>/playbook.md`."*
**Dependencies:** `eval.harness.capture`.

### 5.2 Central store

**Purpose:** hold all insight data at every maturity tier.
**Layout (per target skill):**

```
skills/skill-forge/insights/<skill>/
  transcripts/<session-id>.jsonl   # raw session snapshot (skill-attributed span)  [gitignored]
  raw.jsonl                        # robust per-session insight records             [committed]
  playbook.md                      # curated, bounded heuristics w/ inline vote tags [committed]
  gate-history.jsonl               # one line per gate round: gold + decision        [committed]
```

**Schemas.**

`raw.jsonl` record:
```json
{"ts":"<iso8601>","skill":"<name>","skill_hash":"<git-sha-of-SKILL.md>","session_id":"<uuid>",
 "context":"<one-line task description, generalized>",
 "signals":{"user_correction":false,"redo":false,"abandonment":false,"approval":true,
            "tool_errors":0,"self_struggle":false},
 "what_worked":"<text>","what_failed":"<text>","lesson":"<generalized, reusable>",
 "proposed_edit":{"old":"<exact SKILL.md line>","new":"<replacement>","reason":"<why>"}|null,
 "confidence":0.0-1.0,"evidence":["<session_id or transcript path>"]}
```

`playbook.md` entry (flat, human-readable; vote/status inline):
```markdown
- [id:ab12 votes:+5 status:active] When X, do Y instead of Z. (why: …)
```
`status ∈ {active, crystallized, retired}`. Bounded to a max entry count (default 25); on overflow the
distiller prunes the lowest net-vote `active` entries.

`gate-history.jsonl` record:
```json
{"round":N,"ts":"…","skill":"…","incumbent_hash":"…","candidate_hash":"…",
 "gold_gate_mean":0.0,"gold_per_seed":[…],"proxy":0.0,"decision":"promote|reject|halt","reason":"…"}
```

**Dependencies:** none (plain files). `transcripts/` is added to `.gitignore`.

### 5.3 `eval/harness/capture.py`

**Purpose:** deterministic file I/O for capture; no judgment.
**Interface:**
- `snapshot(skill: str, session_id: str | None = None) -> Path` — locate the current session transcript
  (most-recently-modified `*.jsonl` under `~/.claude/projects/<slug>/`, or the file matching
  `session_id`), extract records where `attributionSkill == skill` (plus their sidechains via
  `parentUuid`/`isSidechain`), and write them to `insights/<skill>/transcripts/<session-id>.jsonl`.
  Returns the path. Idempotent per session id.
- `append_insight(skill: str, record: dict) -> None` — validate required fields (schema 5.2) and append
  to `insights/<skill>/raw.jsonl`. Reject records missing `lesson` or with malformed `proposed_edit`.
- CLI: `python3 -m eval.harness.capture snapshot <skill>` and
  `python3 -m eval.harness.capture insight <skill>` (reads a JSON record from stdin or an interactive
  template).
**Dependencies:** stdlib only (`json`, `glob`, `pathlib`). Tolerant of absent/locked transcript files
(logs a warning, still records the insight).

### 5.4 Distillation (LLM-orchestrated; described in skill-forge `SKILL.md`)

**Purpose:** turn `raw.jsonl` into a bounded, curated `playbook.md`.
**Process:** read recent `raw.jsonl` (and `transcripts/` for detail), contrast failure-labeled vs
success-labeled records (ExpeL method), and maintain `playbook.md` via **ADD / EDIT / UPVOTE / DOWNVOTE**:
agreeing evidence increments votes, contradicting evidence decrements; prune lowest-vote entries over the
cap. Insights must be **generalized** (no other-session/other-project specifics). No bespoke code — this
is prose guidance executed by the agent.
**Dependencies:** the store (5.2). Output: rewritten `playbook.md`.

### 5.5 Crystallization (LLM-orchestrated)

**Purpose:** propose a durable SKILL.md edit from a proven playbook heuristic.
**Trigger:** a `status:active` heuristic whose net votes ≥ threshold (default +4) and that recurs across
≥ N distinct sessions (default 3). Express the change as a structured, attributed line edit
(`{old, new, reason}`) — a specific failure → a specific line (textual-gradient style). Produce 1–2
candidate edits in isolated git worktrees.
**Dependencies:** `playbook.md`, the target `SKILL.md`, `using-git-worktrees`.

### 5.6 `eval/harness/gate.py` (simplified)

**Purpose:** the single deterministic promotion decision.
**Interface:** `decide(incumbent_runs, candidate_runs, *, k_seeds, alpha=0.05) -> Decision` where runs are
per-`(task, seed)` scores on the **held-out `gate` split only**, scored by `score.py` (ground-truth,
`critical=True`) or `blend.py` (judge panel).
**Algorithm:**
1. **Critical veto** — if any `critical` ground-truth task regresses (candidate < incumbent) on *any*
   seed → `reject`.
2. **Per-seed aggregate gold delta** — for each seed, mean over gate tasks of (candidate − incumbent).
3. **Promote iff** mean delta across all `(task, seed)` > 0 **AND** every seed's aggregate delta > 0
   (wins on every seed) **AND** mean delta > `noise_floor`, where `noise_floor` = stdev of the
   incumbent's per-seed aggregate gold (run-to-run noise; small ε if ~0). Optional corroboration: a
   `scipy` paired sign / Wilcoxon test with `p < alpha`.
4. Otherwise `reject`. A `promote` still requires **human approval** downstream.
**Dependencies:** `score.py`, `blend.py`, `tasks.py`; numpy/scipy now permitted (no hand-rolled stats).
Replaces `stats.py` entirely.

### 5.7 `eval/harness/monitor.py` (Goodhart tripwire)

**Purpose:** detect reward hacking by watching proxy vs gold over rounds.
**Interface:** `check(skill, lookback=5) -> {ok|halt, reason}`. Proxy trend = recent approval/success rate
from `raw.jsonl`; gold trend = `gold_gate_mean` series from `gate-history.jsonl`. **Halt** when proxy
rises while gold stalls/drops over the lookback window (empirical divergence — no closed-form curve).
**Dependencies:** the store. Output gates crystallization (5.5).

### 5.8 `eval/harness/forge.py` (slim CLI orchestrator)

**Purpose:** tie scoring + gate + monitor + round logging into one entry point.
**Interface:** `python3 -m eval.harness.forge <skill> <results.json>` →
runs `monitor.check`; if halted, prints alert and exits 2. Else builds paired held-out deltas from
results, calls `gate.decide`, appends a `gate-history.jsonl` round record, and prints a markdown proposal
(reusing the kept renderer). Exit 0 = promote-pending-approval, 1 = reject, 2 = halt.
**Dependencies:** `gate.py`, `monitor.py`, `tasks.py`, `score.py`, `blend.py`, store.

## 6. End-to-end data flow

1. **Use** — a target skill runs; the agent consults `playbook.md` (fast layer, immediate effect).
2. **Capture** — at session end, the Capture section snapshots the transcript and appends a robust insight
   to `raw.jsonl`.
3. **Distill** (skill-forge, periodic) — `raw.jsonl` → curated `playbook.md` with votes; bounded.
4. **Crystallize** — a proven heuristic → 1–2 attributed candidate SKILL.md edits in worktrees.
5. **Gate** — run candidates vs incumbent on the held-out `gate` split; `forge.py` runs the monitor, then
   `gate.decide`; logs a round to `gate-history.jsonl`.
6. **Promote** — on pass + human approval: replace SKILL.md, mark the heuristic `crystallized` and retire
   it from the playbook (keeps consulted context small), `git tag` the new version.

## 7. Migration plan (clean rebuild)

- **Delete (code + tests):** `eval/harness/` → `mutation.py`, `pareto.py`, `tournament.py`,
  `judge_safety.py`, `stats.py`, `anchor.py`, `goodhart.py`, `loop_control.py`, `forge_report.py`
  (fold the one kept renderer into `forge.py`), and their tests (`test_mutation`, `test_pareto`,
  `test_tournament`, `test_judge_safety`, `test_stats*`, `test_anchor`, `test_goodhart`,
  `test_loop_control`, and the legacy `test_forge*`/`test_skill_forge*` paths that exercise removed
  behavior).
- **Keep (unchanged):** `score.py`, `tasks.py`, `blend.py` (+ their tests); the general harness
  `cli.py`, `consensus.py`, `report.py`, `skill_lint.py`, `frontmatter.py` (unrelated to forge); the
  benchmark/rubric contract; the critical-regression veto; git-tag rollback.
- **New (small):** `capture.py`, `monitor.py`, simplified `gate.py`, slim `forge.py` + their tests.
- **Move to prose** (skill-forge `SKILL.md`, not code): judge-panel diversity, order-swap A/B,
  candidate-text sanitization, the Goodhart-watch description.
- **Edit every target skill** (10 files): add the Capture section + Consult pointer (5.1). Note: 9 of
  the 10 have a benchmark under `eval/benchmarks/`; **`scientific-rigor` has none**, so its slow/gated
  loop is dormant (fast playbook layer still works) until a benchmark + rubric are added. `skill-forge`
  itself is **not** a target (self-referential improvement is out of scope, §2).
- **`.gitignore`:** add `skills/skill-forge/insights/*/transcripts/`.
- **Update** `skills/skill-forge/SKILL.md` to describe the new self-contained loop and retire references
  to the deleted modules.

Net deterministic surface: ~11 modules / ~820 LOC / ~219 tests → ~4–5 forge modules / ~250 LOC / ~40
tests, reduced to log I/O + scorer + one gate + one monitor.

## 8. Error handling & edge cases

- **Missing/locked transcript** (5.3): warn, still append the insight; the lesson is the durable part.
- **Cold start** (empty `playbook.md`): Consult is a no-op; Capture still records. Distillation needs
  enough successes — note that few records yield weak playbooks (ExpeL caveat).
- **Reward hacking:** the monitor halts crystallization on proxy↑/gold↓; the held-out gate is the hard
  guard; behavioral labels never gate.
- **Playbook drift / bloat:** bounded entry cap + vote-based pruning + retirement on crystallization.
- **Generalization risk:** the literature *refuted* the claim that distilled abstractions resist
  distribution shift — so crystallization always re-validates on the held-out gate before a durable edit.
- **Privacy:** raw transcripts stay in the gitignored cache; committed insights are generalized lessons.

## 9. Testing strategy

- `capture.py`: schema validation (reject missing `lesson`, malformed `proposed_edit`); snapshot filters
  by `attributionSkill` and includes sidechains; idempotent per session id; tolerates a missing transcript.
- `gate.py`: critical veto fires on any-seed regression; promote requires win-on-every-seed AND
  mean > noise_floor; rejects sub-noise margins; optional sign-test path.
- `monitor.py`: halts on synthetic proxy↑/gold↓ series; passes when both rise; handles short history.
- `forge.py`: exit codes 0/1/2; appends exactly one `gate-history.jsonl` round; honors a monitor halt.
- Kept modules retain their existing tests. Target: ~40 forge tests total.

## 10. Suggested build sequence (for the plan)

1. Store layout + `.gitignore` + `capture.py` (+ tests).
2. Add Capture/Consult sections to the 10 target skills.
3. Simplified `gate.py` (+ tests); delete `stats.py`.
4. `monitor.py` (+ tests).
5. Slim `forge.py` (+ tests); delete `forge_report.py`/legacy paths.
6. Delete the remaining hardening modules + their tests.
7. Rewrite skill-forge `SKILL.md` for the self-contained loop.
8. Full suite green; manual dry-run of capture → distill → gate on one skill.
