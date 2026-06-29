# SkillForge Self-Contained Redesign — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace skill-forge's rule-driven hardening machinery with a self-contained, log-driven loop where each skill captures its own session insights, skill-forge distills them into a flat playbook, and only gated, human-approved edits reach the durable SKILL.md.

**Architecture:** Insights are pushed by each target skill at session end (a transcript snapshot + a robust reflection) into a central flat-file store under `skills/skill-forge/insights/<skill>/`. skill-forge distills `raw.jsonl` into a bounded `playbook.md` (fast layer, consulted at use-time, reversible), and crystallizes proven heuristics into attributed SKILL.md edits gated on a held-out benchmark split (slow layer). Deterministic code shrinks to four small modules: capture I/O, one gate decision, one Goodhart monitor, and a slim CLI orchestrator.

**Tech Stack:** Python 3 (stdlib-first; `scipy` used only via lazy optional import), pytest, git, markdown SKILL.md docs.

## Global Constraints

- Python **stdlib-first**. `scipy`/`numpy` are available (1.13.1 / 1.26.4) but the gate core uses only `statistics`; `scipy.stats.wilcoxon` is imported **lazily**, only when `use_sign_test=True`. No new hard dependencies.
- All storage is **flat files** under `skills/skill-forge/insights/<skill>/`. No embeddings, no database.
- `transcripts/` subdirs are **gitignored**; `raw.jsonl`, `playbook.md`, `gate-history.jsonl` are committed.
- Gating uses the **held-out `gate` split only**. Promotions require **human approval** + `git tag` (rollback path).
- Captured insights must be **generalized** — no project- or session-specific content in committed files.
- Follow existing `eval/harness/` style (module-level functions, `from __future__ import annotations`).
- TDD: write the failing test first; commit after each green task.
- Target skills (10): `argumentation-and-sources`, `deep-reasoning`, `deep-reasoning-ultra`, `faithful-implementation`, `humanities-inquiry`, `literature-review`, `research-design`, `research-synthesis`, `rigorous-validation`, `scientific-rigor`. `skill-forge` is **not** a target (self-referential improvement is out of scope). `scientific-rigor` has no benchmark, so its gated loop stays dormant.

---

## File Structure

**Create:**
- `eval/harness/capture.py` — deterministic capture I/O (snapshot transcript, append insight).
- `eval/harness/monitor.py` — Goodhart proxy↔gold tripwire.
- `tests/test_capture.py`, `tests/test_monitor.py`, `tests/test_gate.py` (new), `tests/test_forge.py` (new), `tests/test_capture_sections.py`.

**Rewrite (clean):**
- `eval/harness/gate.py` — single `decide()` promotion decision.
- `eval/harness/forge.py` — slim CLI orchestrator (`evaluate()` + `main()`).
- `skills/skill-forge/SKILL.md` — the self-contained loop.

**Modify:**
- `.gitignore` — add transcript cache.
- The 10 target `skills/<skill>/SKILL.md` — add Capture + Consult sections.

**Delete:** `eval/harness/` → `stats.py`, `tournament.py`, `mutation.py`, `pareto.py`, `goodhart.py`, `anchor.py`, `loop_control.py`, `judge_safety.py`, `forge_report.py`; and tests `test_stats.py`, `test_stats_ci.py`, `test_tournament.py`, `test_tournament_governance.py`, `test_tournament_panel.py`, `test_mutation.py`, `test_pareto.py`, `test_goodhart.py`, `test_anchor.py`, `test_loop_control.py`, `test_judge_safety.py`, `test_forge_report.py`, `test_forge_report_integrity.py`, `test_forge_report_stat.py`, `test_forge_stat.py`, `test_forge_tournament.py`, `test_gate_stat.py`, `test_skill_forge_judge.py`, `test_skill_forge_loop.py` (and old `test_forge.py`, `test_gate.py`, `test_skill_forge.py`, `test_skill_forge_gate.py` are replaced in Tasks 4/6).

**Keep untouched:** `score.py`, `tasks.py`, `blend.py`, `cli.py`, `consensus.py`, `report.py`, `skill_lint.py`, `frontmatter.py` and their tests; benchmark/rubric contract.

---

## Task 1: Capture store + insight append

**Files:**
- Create: `eval/harness/capture.py`
- Modify: `.gitignore`
- Test: `tests/test_capture.py`

**Interfaces:**
- Produces: `capture.INSIGHTS_ROOT: Path`; `capture.validate_insight(record: dict) -> None`; `capture.append_insight(skill: str, record: dict) -> Path` (appends one JSON line to `insights/<skill>/raw.jsonl`).

- [ ] **Step 1: Write the failing test**

```python
# tests/test_capture.py
import json
import pytest
from eval.harness import capture

def _valid():
    return {"ts": "2026-06-28T00:00:00Z", "skill": "research-design", "session_id": "s1",
            "context": "framed a hypothesis", "signals": {"approval": True},
            "lesson": "State the falsifier before supporting a claim.", "confidence": 0.7}

def test_append_insight_writes_one_line(tmp_path, monkeypatch):
    monkeypatch.setattr(capture, "INSIGHTS_ROOT", tmp_path)
    path = capture.append_insight("research-design", _valid())
    lines = path.read_text().splitlines()
    assert len(lines) == 1
    assert json.loads(lines[0])["lesson"].startswith("State the falsifier")

def test_append_insight_rejects_missing_lesson(tmp_path, monkeypatch):
    monkeypatch.setattr(capture, "INSIGHTS_ROOT", tmp_path)
    rec = _valid(); del rec["lesson"]
    with pytest.raises(ValueError):
        capture.append_insight("research-design", rec)

def test_append_insight_rejects_bad_proposed_edit(tmp_path, monkeypatch):
    monkeypatch.setattr(capture, "INSIGHTS_ROOT", tmp_path)
    rec = _valid(); rec["proposed_edit"] = {"old": "", "new": "x", "reason": "y"}
    with pytest.raises(ValueError):
        capture.append_insight("research-design", rec)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m pytest tests/test_capture.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'eval.harness.capture'`.

- [ ] **Step 3: Write minimal implementation**

```python
# eval/harness/capture.py
"""Deterministic capture I/O for skill-forge. File I/O only — no judgment."""
from __future__ import annotations

import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
INSIGHTS_ROOT = REPO_ROOT / "skills" / "skill-forge" / "insights"

REQUIRED_INSIGHT_FIELDS = ("ts", "skill", "session_id", "context", "signals", "lesson", "confidence")


def _store_dir(skill: str) -> Path:
    d = INSIGHTS_ROOT / skill
    d.mkdir(parents=True, exist_ok=True)
    return d


def validate_insight(record: dict) -> None:
    missing = [f for f in REQUIRED_INSIGHT_FIELDS if f not in record]
    if missing:
        raise ValueError(f"insight missing required fields: {missing}")
    if not str(record.get("lesson", "")).strip():
        raise ValueError("insight 'lesson' must be non-empty")
    edit = record.get("proposed_edit")
    if edit is not None:
        if not isinstance(edit, dict) or not {"old", "new", "reason"} <= set(edit):
            raise ValueError("proposed_edit must have old, new, reason")
        if not str(edit["old"]).strip():
            raise ValueError("proposed_edit.old must be non-empty")


def append_insight(skill: str, record: dict) -> Path:
    validate_insight(record)
    path = _store_dir(skill) / "raw.jsonl"
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(record, ensure_ascii=False) + "\n")
    return path
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python3 -m pytest tests/test_capture.py -v`
Expected: PASS (3 passed).

- [ ] **Step 5: Update `.gitignore`**

Add this line to `.gitignore`:

```
skills/skill-forge/insights/*/transcripts/
```

- [ ] **Step 6: Commit**

```bash
git add eval/harness/capture.py tests/test_capture.py .gitignore
git commit -m "feat(skill-forge): insight append store + transcript gitignore"
```

---

## Task 2: Capture transcript snapshot

**Files:**
- Modify: `eval/harness/capture.py`
- Test: `tests/test_capture.py`

**Interfaces:**
- Consumes: `capture.INSIGHTS_ROOT`, `capture._store_dir`.
- Produces: `capture.snapshot(skill: str, session_id: str | None = None, transcripts_dir: Path | None = None) -> Path | None` — writes the skill-attributed records (plus sidechain descendants) to `insights/<skill>/transcripts/<session-id>.jsonl`; returns the path, or `None` if no transcript / no attributed records.

- [ ] **Step 1: Write the failing test**

```python
# append to tests/test_capture.py
def _write_transcript(tmp_path):
    tdir = tmp_path / "proj"
    tdir.mkdir()
    rows = [
        {"uuid": "a", "attributionSkill": "research-design", "type": "assistant"},
        {"uuid": "b", "parentUuid": "a", "isSidechain": True, "type": "assistant"},
        {"uuid": "c", "attributionSkill": "other-skill", "type": "assistant"},
    ]
    f = tdir / "sess1.jsonl"
    f.write_text("\n".join(__import__("json").dumps(r) for r in rows) + "\n")
    return tdir

def test_snapshot_filters_by_attribution(tmp_path, monkeypatch):
    monkeypatch.setattr(capture, "INSIGHTS_ROOT", tmp_path / "store")
    tdir = _write_transcript(tmp_path)
    out = capture.snapshot("research-design", session_id="sess1", transcripts_dir=tdir)
    assert out is not None
    uuids = {json.loads(l)["uuid"] for l in out.read_text().splitlines()}
    assert uuids == {"a", "b"}  # attributed record + its sidechain; not "c"

def test_snapshot_returns_none_when_missing(tmp_path, monkeypatch):
    monkeypatch.setattr(capture, "INSIGHTS_ROOT", tmp_path / "store")
    assert capture.snapshot("research-design", session_id="nope", transcripts_dir=tmp_path) is None
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m pytest tests/test_capture.py -k snapshot -v`
Expected: FAIL with `AttributeError: module 'eval.harness.capture' has no attribute 'snapshot'`.

- [ ] **Step 3: Write minimal implementation**

Add to `eval/harness/capture.py` (imports `os` at top):

```python
import os


def _project_slug(cwd: Path | None = None) -> str:
    return str((cwd or Path.cwd()).resolve()).replace(os.sep, "-")


def _default_transcripts_dir(cwd: Path | None = None) -> Path:
    return Path.home() / ".claude" / "projects" / _project_slug(cwd)


def _parse_jsonl(path: Path) -> list[dict]:
    out: list[dict] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            out.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return out


def snapshot(skill: str, session_id: str | None = None,
             transcripts_dir: Path | None = None) -> Path | None:
    tdir = transcripts_dir or _default_transcripts_dir()
    if session_id:
        src = tdir / f"{session_id}.jsonl"
        if not src.exists():
            return None
    else:
        candidates = sorted(tdir.glob("*.jsonl"), key=lambda p: p.stat().st_mtime, reverse=True)
        if not candidates:
            return None
        src = candidates[0]
        session_id = src.stem
    try:
        records = _parse_jsonl(src)
    except OSError:
        return None
    by_uuid = {r.get("uuid"): r for r in records}
    attributed = {r.get("uuid") for r in records if r.get("attributionSkill") == skill}

    def reaches_attributed(rec: dict) -> bool:
        seen: set = set()
        cur = rec
        while cur is not None:
            u = cur.get("uuid")
            if u in attributed:
                return True
            if u in seen:
                break
            seen.add(u)
            cur = by_uuid.get(cur.get("parentUuid"))
        return False

    selected = [r for r in records
                if r.get("uuid") in attributed or (r.get("isSidechain") and reaches_attributed(r))]
    if not selected:
        return None
    out_dir = _store_dir(skill) / "transcripts"
    out_dir.mkdir(parents=True, exist_ok=True)
    out = out_dir / f"{session_id}.jsonl"
    with out.open("w", encoding="utf-8") as fh:
        for r in selected:
            fh.write(json.dumps(r, ensure_ascii=False) + "\n")
    return out
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python3 -m pytest tests/test_capture.py -v`
Expected: PASS (5 passed).

- [ ] **Step 5: Commit**

```bash
git add eval/harness/capture.py tests/test_capture.py
git commit -m "feat(skill-forge): transcript snapshot filtered by attributionSkill"
```

---

## Task 3: Capture CLI

**Files:**
- Modify: `eval/harness/capture.py`
- Test: `tests/test_capture.py`

**Interfaces:**
- Consumes: `capture.snapshot`, `capture.append_insight`.
- Produces: `capture.main(argv: list[str] | None = None) -> int`; CLI `python3 -m eval.harness.capture snapshot <skill>` / `insight <skill>` (insight reads a JSON record from stdin).

- [ ] **Step 1: Write the failing test**

```python
# append to tests/test_capture.py
import io

def test_cli_insight_appends_from_stdin(tmp_path, monkeypatch):
    monkeypatch.setattr(capture, "INSIGHTS_ROOT", tmp_path)
    monkeypatch.setattr("sys.stdin", io.StringIO(json.dumps(_valid())))
    rc = capture.main(["insight", "research-design"])
    assert rc == 0
    assert (tmp_path / "research-design" / "raw.jsonl").read_text().strip()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m pytest tests/test_capture.py -k cli -v`
Expected: FAIL with `AttributeError: module 'eval.harness.capture' has no attribute 'main'`.

- [ ] **Step 3: Write minimal implementation**

Add to `eval/harness/capture.py` (`import sys`, `import argparse` at top):

```python
import sys
import argparse


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="capture")
    sub = parser.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("snapshot"); s.add_argument("skill")
    i = sub.add_parser("insight"); i.add_argument("skill")
    args = parser.parse_args(argv)
    if args.cmd == "snapshot":
        path = snapshot(args.skill)
        print(str(path) if path else "no transcript found")
        return 0
    record = json.loads(sys.stdin.read())
    record.setdefault("skill", args.skill)
    append_insight(args.skill, record)
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python3 -m pytest tests/test_capture.py -v`
Expected: PASS (6 passed).

- [ ] **Step 5: Commit**

```bash
git add eval/harness/capture.py tests/test_capture.py
git commit -m "feat(skill-forge): capture CLI (snapshot/insight)"
```

---

## Task 4: Simplified gate

**Files:**
- Rewrite: `eval/harness/gate.py`
- Test: replace `tests/test_gate.py`

**Interfaces:**
- Produces: `gate.Decision` (dataclass: `promote: bool`, `reason: str`, `mean_delta: float`, `per_seed_delta: dict`, `noise_floor: float`, `critical_regression: bool`); `gate.decide(incumbent_runs, candidate_runs, *, eps=1e-9, use_sign_test=False, alpha=0.05) -> Decision`. Each run is `{"task_id","seed","score","critical"}`.

- [ ] **Step 1: Write the failing test (replace file contents)**

```python
# tests/test_gate.py
from eval.harness.gate import decide

def _runs(scores_by_seed, critical=False):
    # scores_by_seed: {seed: [(task_id, score), ...]}
    out = []
    for seed, pairs in scores_by_seed.items():
        for task_id, score in pairs:
            out.append({"task_id": task_id, "seed": seed, "score": score, "critical": critical})
    return out

def test_promote_when_wins_every_seed_above_noise():
    inc = _runs({1: [("t", 0.50)], 2: [("t", 0.50)], 3: [("t", 0.50)]})
    cand = _runs({1: [("t", 0.70)], 2: [("t", 0.72)], 3: [("t", 0.71)]})
    d = decide(inc, cand)
    assert d.promote and d.mean_delta > d.noise_floor

def test_reject_sub_noise_gain():
    inc = _runs({1: [("t", 0.40)], 2: [("t", 0.60)], 3: [("t", 0.50)]})  # noisy incumbent
    cand = _runs({1: [("t", 0.41)], 2: [("t", 0.61)], 3: [("t", 0.51)]})  # tiny gain
    d = decide(inc, cand)
    assert not d.promote and "noise floor" in d.reason

def test_critical_regression_vetoes():
    inc = _runs({1: [("t", 0.50)]}, critical=True)
    cand = _runs({1: [("t", 0.40)]}, critical=True)
    d = decide(inc, cand)
    assert not d.promote and d.critical_regression

def test_reject_when_loses_one_seed():
    inc = _runs({1: [("t", 0.50)], 2: [("t", 0.50)]})
    cand = _runs({1: [("t", 0.70)], 2: [("t", 0.45)]})  # regresses on seed 2
    d = decide(inc, cand)
    assert not d.promote and "seed" in d.reason
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m pytest tests/test_gate.py -v`
Expected: FAIL (old `gate.py` has no `decide`).

- [ ] **Step 3: Rewrite `eval/harness/gate.py`**

```python
# eval/harness/gate.py
"""Single deterministic promotion decision for skill-forge."""
from __future__ import annotations

from dataclasses import dataclass
from statistics import fmean, pstdev


@dataclass
class Decision:
    promote: bool
    reason: str
    mean_delta: float
    per_seed_delta: dict
    noise_floor: float
    critical_regression: bool


def decide(incumbent_runs, candidate_runs, *, eps=1e-9, use_sign_test=False, alpha=0.05) -> Decision:
    inc = {(r["task_id"], r["seed"]): r for r in incumbent_runs}
    cand = {(r["task_id"], r["seed"]): r for r in candidate_runs}
    keys = sorted(set(inc) & set(cand))
    if not keys:
        return Decision(False, "no paired runs", 0.0, {}, 0.0, False)

    critical = False
    for k in keys:
        if (inc[k].get("critical") or cand[k].get("critical")) and cand[k]["score"] < inc[k]["score"]:
            critical = True
            break

    deltas = {k: cand[k]["score"] - inc[k]["score"] for k in keys}
    mean_delta = fmean(deltas.values())
    seeds = sorted({s for (_, s) in keys})
    per_seed = {s: fmean([deltas[k] for k in keys if k[1] == s]) for s in seeds}
    inc_seed_means = [fmean([inc[k]["score"] for k in keys if k[1] == s]) for s in seeds]
    noise_floor = max(pstdev(inc_seed_means) if len(inc_seed_means) > 1 else 0.0, eps)

    if critical:
        return Decision(False, "critical-task regression", mean_delta, per_seed, noise_floor, True)

    reasons = []
    if not mean_delta > 0:
        reasons.append("mean delta not positive")
    wins_every_seed = all(d > 0 for d in per_seed.values())
    if not wins_every_seed:
        reasons.append("loses on >=1 seed")
    beats_noise = mean_delta > noise_floor
    if not beats_noise:
        reasons.append(f"gain {mean_delta:.4f} <= noise floor {noise_floor:.4f}")

    promote = (mean_delta > 0) and wins_every_seed and beats_noise
    if promote and use_sign_test:
        from scipy.stats import wilcoxon
        try:
            _, p = wilcoxon(list(deltas.values()))
            if p >= alpha:
                promote = False
                reasons.append(f"sign test p={p:.3f} >= alpha")
        except ValueError:
            pass

    return Decision(promote, "promote" if promote else "; ".join(reasons), mean_delta, per_seed,
                    noise_floor, False)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python3 -m pytest tests/test_gate.py -v`
Expected: PASS (4 passed).

- [ ] **Step 5: Commit**

```bash
git add eval/harness/gate.py tests/test_gate.py
git commit -m "feat(skill-forge): simplified promotion gate (win-every-seed + noise floor)"
```

---

## Task 5: Goodhart monitor

**Files:**
- Create: `eval/harness/monitor.py`
- Test: `tests/test_monitor.py`

**Interfaces:**
- Produces: `monitor.INSIGHTS_ROOT`; `monitor.check(skill: str, lookback: int = 5) -> dict` returning `{"status": "ok"|"halt", "reason": str}`. Reads proxy from `raw.jsonl` (`signals.approval`) and gold from `gate-history.jsonl` (`gold_gate_mean`).

- [ ] **Step 1: Write the failing test**

```python
# tests/test_monitor.py
import json
from eval.harness import monitor

def _seed(tmp_path, skill, approvals, golds):
    d = tmp_path / skill
    d.mkdir(parents=True)
    (d / "raw.jsonl").write_text(
        "\n".join(json.dumps({"signals": {"approval": a}}) for a in approvals) + "\n")
    (d / "gate-history.jsonl").write_text(
        "\n".join(json.dumps({"gold_gate_mean": g}) for g in golds) + "\n")

def test_halt_when_proxy_up_gold_down(tmp_path, monkeypatch):
    monkeypatch.setattr(monitor, "INSIGHTS_ROOT", tmp_path)
    _seed(tmp_path, "research-design", approvals=[False, True, True], golds=[0.6, 0.55, 0.5])
    assert monitor.check("research-design")["status"] == "halt"

def test_ok_when_both_rise(tmp_path, monkeypatch):
    monkeypatch.setattr(monitor, "INSIGHTS_ROOT", tmp_path)
    _seed(tmp_path, "research-design", approvals=[False, True, True], golds=[0.5, 0.55, 0.6])
    assert monitor.check("research-design")["status"] == "ok"

def test_ok_when_history_too_short(tmp_path, monkeypatch):
    monkeypatch.setattr(monitor, "INSIGHTS_ROOT", tmp_path)
    _seed(tmp_path, "research-design", approvals=[True], golds=[0.5])
    assert monitor.check("research-design")["status"] == "ok"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m pytest tests/test_monitor.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'eval.harness.monitor'`.

- [ ] **Step 3: Write minimal implementation**

```python
# eval/harness/monitor.py
"""Goodhart tripwire: halt crystallization when proxy rises while gold stalls/drops."""
from __future__ import annotations

import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
INSIGHTS_ROOT = REPO_ROOT / "skills" / "skill-forge" / "insights"


def _read_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    out: list[dict] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            try:
                out.append(json.loads(line))
            except json.JSONDecodeError:
                pass
    return out


def _trend(xs: list[float]) -> float:
    return 0.0 if len(xs) < 2 else xs[-1] - xs[0]


def proxy_series(skill: str, lookback: int = 5) -> list[float]:
    raw = _read_jsonl(INSIGHTS_ROOT / skill / "raw.jsonl")
    vals = [1.0 if r.get("signals", {}).get("approval") else 0.0 for r in raw]
    return vals[-lookback:]


def gold_series(skill: str, lookback: int = 5) -> list[float]:
    hist = _read_jsonl(INSIGHTS_ROOT / skill / "gate-history.jsonl")
    return [h.get("gold_gate_mean", 0.0) for h in hist][-lookback:]


def check(skill: str, lookback: int = 5) -> dict:
    gold = gold_series(skill, lookback)
    if len(gold) < 2:
        return {"status": "ok", "reason": "insufficient gold history"}
    if _trend(proxy_series(skill, lookback)) > 0 and _trend(gold) <= 0:
        return {"status": "halt",
                "reason": "proxy up while gold stalled/dropped (possible reward hacking)"}
    return {"status": "ok", "reason": "proxy/gold not diverging"}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python3 -m pytest tests/test_monitor.py -v`
Expected: PASS (3 passed).

- [ ] **Step 5: Commit**

```bash
git add eval/harness/monitor.py tests/test_monitor.py
git commit -m "feat(skill-forge): Goodhart proxy/gold monitor"
```

---

## Task 6: Slim forge CLI orchestrator

**Files:**
- Rewrite: `eval/harness/forge.py`
- Test: replace `tests/test_forge.py`

**Interfaces:**
- Consumes: `gate.decide`, `monitor.check`.
- Produces: `forge.INSIGHTS_ROOT`; `forge.evaluate(results: dict, *, now_iso: str) -> dict` (keys: `exit`, `decision`, `reason`, `proposal`; appends one `gate-history.jsonl` round unless halted); `forge.main(argv) -> int`. CLI: `python3 -m eval.harness.forge <skill> <results.json>`. `results` = `{"skill","incumbent":{"hash","runs":[{task_id,seed,score,critical,split}]},"candidate":{...},"use_sign_test"?}`.

- [ ] **Step 1: Write the failing test (replace file contents)**

```python
# tests/test_forge.py
import json
from eval.harness import forge, monitor

def _version(hash_, score):
    return {"hash": hash_, "runs": [
        {"task_id": "t", "seed": s, "score": score, "critical": False, "split": "gate"} for s in (1, 2, 3)]}

def _results(inc_score, cand_score):
    return {"skill": "research-design",
            "incumbent": _version("h0", inc_score), "candidate": _version("h1", cand_score)}

def test_promote_exit0_appends_one_round(tmp_path, monkeypatch):
    monkeypatch.setattr(forge, "INSIGHTS_ROOT", tmp_path)
    monkeypatch.setattr(monitor, "INSIGHTS_ROOT", tmp_path)
    out = forge.evaluate(_results(0.50, 0.70), now_iso="2026-06-28T00:00:00Z")
    assert out["exit"] == 0 and out["decision"] == "promote"
    hist = (tmp_path / "research-design" / "gate-history.jsonl").read_text().splitlines()
    assert len(hist) == 1 and json.loads(hist[0])["round"] == 1

def test_reject_exit1(tmp_path, monkeypatch):
    monkeypatch.setattr(forge, "INSIGHTS_ROOT", tmp_path)
    monkeypatch.setattr(monitor, "INSIGHTS_ROOT", tmp_path)
    out = forge.evaluate(_results(0.50, 0.50), now_iso="2026-06-28T00:00:00Z")
    assert out["exit"] == 1 and out["decision"] == "reject"

def test_halt_exit2_when_monitor_halts(tmp_path, monkeypatch):
    monkeypatch.setattr(forge, "INSIGHTS_ROOT", tmp_path)
    monkeypatch.setattr(monitor, "INSIGHTS_ROOT", tmp_path)
    d = tmp_path / "research-design"; d.mkdir(parents=True)
    (d / "raw.jsonl").write_text("\n".join(json.dumps({"signals": {"approval": a}}) for a in (False, True, True)) + "\n")
    (d / "gate-history.jsonl").write_text("\n".join(json.dumps({"gold_gate_mean": g}) for g in (0.6, 0.55, 0.5)) + "\n")
    out = forge.evaluate(_results(0.50, 0.90), now_iso="2026-06-28T00:00:00Z")
    assert out["exit"] == 2 and out["decision"] == "halt"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m pytest tests/test_forge.py -v`
Expected: FAIL (old `forge.py` imports deleted modules / has no `evaluate` with this signature).

- [ ] **Step 3: Rewrite `eval/harness/forge.py`**

```python
# eval/harness/forge.py
"""Slim skill-forge orchestrator: monitor -> gate -> log round -> proposal."""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from statistics import fmean

from eval.harness import gate, monitor

REPO_ROOT = Path(__file__).resolve().parents[2]
INSIGHTS_ROOT = REPO_ROOT / "skills" / "skill-forge" / "insights"


def _gate_runs(version: dict) -> list[dict]:
    return [r for r in version["runs"] if r.get("split", "gate") == "gate"]


def _next_round(hist_path: Path) -> int:
    if not hist_path.exists():
        return 1
    return sum(1 for line in hist_path.read_text().splitlines() if line.strip()) + 1


def _render(skill: str, d: gate.Decision, gold_gate_mean: float) -> str:
    head = "PROMOTE (pending human approval)" if d.promote else "REJECT"
    return (f"## skill-forge proposal — {skill}\n\n"
            f"- decision: **{head}**\n- reason: {d.reason}\n"
            f"- mean gold delta: {d.mean_delta:.4f} (noise floor {d.noise_floor:.4f})\n"
            f"- candidate gold (gate split): {gold_gate_mean:.4f}\n"
            f"- per-seed delta: {d.per_seed_delta}\n")


def evaluate(results: dict, *, now_iso: str) -> dict:
    skill = results["skill"]
    store = INSIGHTS_ROOT / skill
    inc = _gate_runs(results["incumbent"])
    cand = _gate_runs(results["candidate"])

    mon = monitor.check(skill)
    if mon["status"] == "halt":
        return {"exit": 2, "decision": "halt", "reason": mon["reason"],
                "proposal": f"HALT — {mon['reason']}. Crystallization paused; investigate divergence."}

    d = gate.decide(inc, cand, use_sign_test=results.get("use_sign_test", False))
    decision = "promote" if d.promote else "reject"
    gold_gate_mean = fmean([r["score"] for r in cand]) if cand else 0.0

    store.mkdir(parents=True, exist_ok=True)
    hist_path = store / "gate-history.jsonl"
    rec = {"round": _next_round(hist_path), "ts": now_iso, "skill": skill,
           "incumbent_hash": results["incumbent"].get("hash"),
           "candidate_hash": results["candidate"].get("hash"),
           "gold_gate_mean": gold_gate_mean, "gold_per_seed": list(d.per_seed_delta.values()),
           "proxy": 0.0, "decision": decision, "reason": d.reason}
    with hist_path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(rec) + "\n")

    return {"exit": 0 if d.promote else 1, "decision": decision, "reason": d.reason,
            "proposal": _render(skill, d, gold_gate_mean)}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="forge")
    parser.add_argument("skill")
    parser.add_argument("results")
    args = parser.parse_args(argv)
    results = json.loads(Path(args.results).read_text())
    results.setdefault("skill", args.skill)
    out = evaluate(results, now_iso=datetime.now(timezone.utc).isoformat())
    print(out["proposal"])
    return out["exit"]


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python3 -m pytest tests/test_forge.py -v`
Expected: PASS (3 passed).

- [ ] **Step 5: Commit**

```bash
git add eval/harness/forge.py tests/test_forge.py
git commit -m "feat(skill-forge): slim forge orchestrator (monitor/gate/round-log)"
```

---

## Task 7: Delete hardening modules + stale tests

**Files:**
- Delete: 9 modules + 19 test files (see File Structure).

- [ ] **Step 1: Delete the modules and tests**

```bash
cd /Users/aaronbao/Developer/scienceskills
git rm eval/harness/stats.py eval/harness/tournament.py eval/harness/mutation.py \
  eval/harness/pareto.py eval/harness/goodhart.py eval/harness/anchor.py \
  eval/harness/loop_control.py eval/harness/judge_safety.py eval/harness/forge_report.py
git rm tests/test_stats.py tests/test_stats_ci.py tests/test_tournament.py \
  tests/test_tournament_governance.py tests/test_tournament_panel.py tests/test_mutation.py \
  tests/test_pareto.py tests/test_goodhart.py tests/test_anchor.py tests/test_loop_control.py \
  tests/test_judge_safety.py tests/test_forge_report.py tests/test_forge_report_integrity.py \
  tests/test_forge_report_stat.py tests/test_forge_stat.py tests/test_forge_tournament.py \
  tests/test_gate_stat.py tests/test_skill_forge_judge.py tests/test_skill_forge_loop.py
```

- [ ] **Step 2: Remove stale skill-forge tests that exercise deleted behavior**

```bash
git rm tests/test_skill_forge.py tests/test_skill_forge_gate.py
```

(Capture/gate/monitor/forge are now covered by Tasks 1–6.)

- [ ] **Step 3: Verify no dangling imports**

Run: `grep -rEn "stats|tournament|mutation|pareto|goodhart|anchor|loop_control|judge_safety|forge_report" eval/ --include="*.py"`
Expected: no matches (empty output).

- [ ] **Step 4: Run the full suite**

Run: `python3 -m pytest -q`
Expected: PASS — collection succeeds with no import errors; only the new + kept tests run.

- [ ] **Step 5: Commit**

```bash
git add -A
git commit -m "refactor(skill-forge): delete hardening modules + stale tests (clean rebuild)"
```

---

## Task 8: Add Capture + Consult sections to target skills

**Files:**
- Modify: each of the 10 target `skills/<skill>/SKILL.md`.
- Test: `tests/test_capture_sections.py`

**Interfaces:**
- Produces: a `## Capture (run at session end)` section + a Consult pointer in every target skill.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_capture_sections.py
from pathlib import Path

TARGETS = ["argumentation-and-sources", "deep-reasoning", "deep-reasoning-ultra",
           "faithful-implementation", "humanities-inquiry", "literature-review",
           "research-design", "research-synthesis", "rigorous-validation", "scientific-rigor"]

def test_every_target_has_capture_and_consult():
    root = Path(__file__).resolve().parents[1] / "skills"
    for skill in TARGETS:
        text = (root / skill / "SKILL.md").read_text()
        assert "## Capture (run at session end)" in text, f"{skill} missing Capture"
        assert f"insights/{skill}/playbook.md" in text, f"{skill} missing Consult pointer"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m pytest tests/test_capture_sections.py -v`
Expected: FAIL (sections not present yet).

- [ ] **Step 3: Append the block to each target SKILL.md**

For **each** of the 10 target skills, append the following to `skills/<skill>/SKILL.md` (replace `<skill>` with the directory name):

```markdown
## Consult

Before starting, read your playbook of learned heuristics:
`skills/skill-forge/insights/<skill>/playbook.md` (skip if absent).

## Capture (run at session end)

When you finish a task that used this skill, record what happened so skill-forge can learn:

1. Snapshot this session: `python3 -m eval.harness.capture snapshot <skill>`
2. Reflect against the five signals — user correction/redo · abandonment · approval · hard failure
   (tool/hook errors) · self-assessed struggle — then append ONE **generalized** insight (no
   project-specifics): pipe a JSON record to `python3 -m eval.harness.capture insight <skill>` with
   fields `{ts, session_id, context, signals, what_worked, what_failed, lesson, proposed_edit?, confidence}`.

Record the *lesson*, not the incident. If a specific line of this SKILL.md caused a failure, include a
`proposed_edit` of `{old, new, reason}`.
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python3 -m pytest tests/test_capture_sections.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add skills/*/SKILL.md tests/test_capture_sections.py
git commit -m "feat(skills): add Capture + Consult sections to all target skills"
```

---

## Task 9: Rewrite skill-forge SKILL.md for the self-contained loop

**Files:**
- Rewrite: `skills/skill-forge/SKILL.md`

- [ ] **Step 1: Replace the file contents**

```markdown
---
name: skill-forge
description: Use to improve the research skills themselves — runs a self-contained, log-driven loop that mines insights each skill captured from its own sessions, distills them into a playbook, and proposes human-approved, gated edits to a skill.
---

# Skill Forge

The self-improvement engine for this suite. It is **self-contained**: every target skill captures its own
session insights into a central store under `skills/skill-forge/insights/<skill>/`, and skill-forge turns
those logs into improvements. It evolves one skill at a time and never promotes a durable change without
measured evidence on a held-out benchmark and your approval.

Improvement lives in two layers:
- **Playbook (fast, reversible, no gate).** Distilled heuristics each skill consults at use-time.
- **SKILL.md (slow, gated, rare).** Durable edits, promoted only through the held-out gate + your approval.

## Store

```
skills/skill-forge/insights/<skill>/
  transcripts/<session-id>.jsonl   raw session snapshots (gitignored cache)
  raw.jsonl                        per-session insight records (committed)
  playbook.md                      curated heuristics, bounded, inline vote tags (committed)
  gate-history.jsonl               one line per gate round (committed)
```

## The loop

1. **Capture (in each skill).** At session end, the skill snapshots its transcript and appends a robust,
   generalized insight to `raw.jsonl` (`python3 -m eval.harness.capture`). Behavioral signals only —
   correction/redo, abandonment, approval, hard failure, self-assessed struggle — no judge.
2. **Distill.** Read recent `raw.jsonl` (and `transcripts/` for detail), contrast failures vs successes,
   and curate `playbook.md` with ADD / EDIT / UPVOTE / DOWNVOTE. Keep it **bounded** (default ≤25 entries;
   prune lowest net-vote). Heuristics must be generalized — no project-specifics.
3. **Crystallize.** When a heuristic has earned its keep (net votes ≥4, recurs across ≥3 sessions), express
   it as an attributed line edit `{old, new, reason}` against the target SKILL.md, in 1–2 candidates in
   isolated worktrees (`using-git-worktrees`).
4. **Gate.** Run incumbent vs candidate on the **held-out `gate` split only** (`split: gate` tasks the loop
   never mined against), K seeds, paired on the same tasks/seeds. Collect a results JSON and run
   `python3 -m eval.harness.forge <skill> results.json`. It runs the Goodhart monitor, then promotes only
   when there is **no critical-task regression**, the candidate **wins gold on every seed**, and the mean
   gain **exceeds the incumbent's seed-to-seed noise**. Exit 0 = promote-pending-approval, 1 = reject,
   2 = halt.
5. **Promote.** On pass **and your approval**: replace the SKILL.md, mark the heuristic `crystallized` and
   retire it from the playbook, and `git tag` the new version so the prior one is one `git checkout` away.

## Judging guidance (orchestration, not code)

When a benchmark task is judge-scored: use a panel of ≥3 judges from **disjoint model families, none from
the candidate-generator's family**; compare both A/B orders and count a win only if it wins both; sanitize
candidate-controlled text before it enters the judge template; and always keep deterministic ground-truth
tasks as the non-judge tripwire. A disjoint panel **reduces, not eliminates**, shared bias.

## Results JSON shape

`{"skill", "incumbent": {"hash", "runs": [{"task_id","seed","score","critical","split"}]},
"candidate": {...}, "use_sign_test"?}`

## Composes with

`deep-research` and the captured `raw.jsonl` (mining), `writing-skills` (candidate edits),
`using-git-worktrees` (isolation), `dispatching-parallel-agents` / the Workflow tool (parallel running and
judging), and `eval.harness.forge` (gate + monitor + round log).

## Red flags (stop)

- Promoting without human approval, or without a measured gain over the incumbent on the held-out split.
- Gating on the dev split, on a sub-noise margin, or on a benchmark too small to have power.
- A single judge, a single A/B order, or a judge panel from one family (or the candidate's own family).
- Editing the benchmark/rubric to make a candidate pass — improve the skill, not the test.
- Continuing to crystallize while the monitor reports proxy↑/gold↓ (reward hacking).
- Committing non-generalized, project-specific content into the insight store.
- No rollback path — every promotion must leave the prior version recoverable in git.
```

- [ ] **Step 2: Validate the skill doc**

Run: `python3 -m pytest -q -k "skill" ; python3 -m eval.harness.cli 2>/dev/null || true`
Expected: kept skill-lint/validation tests pass; no reference to deleted modules.

- [ ] **Step 3: Commit**

```bash
git add skills/skill-forge/SKILL.md
git commit -m "docs(skill-forge): rewrite SKILL.md for self-contained log-driven loop"
```

---

## Task 10: Final verification + dry run

**Files:** none (verification only).

- [ ] **Step 1: Full suite green**

Run: `python3 -m pytest -q`
Expected: all tests pass; suite is the kept tests + `test_capture`, `test_gate`, `test_monitor`, `test_forge`, `test_capture_sections`.

- [ ] **Step 2: Manual dry-run of the gate path on one skill**

```bash
cat > /tmp/forge_results.json <<'JSON'
{"incumbent":{"hash":"h0","runs":[{"task_id":"t","seed":1,"score":0.5,"critical":false,"split":"gate"},
{"task_id":"t","seed":2,"score":0.5,"critical":false,"split":"gate"},
{"task_id":"t","seed":3,"score":0.5,"critical":false,"split":"gate"}]},
"candidate":{"hash":"h1","runs":[{"task_id":"t","seed":1,"score":0.7,"critical":false,"split":"gate"},
{"task_id":"t","seed":2,"score":0.72,"critical":false,"split":"gate"},
{"task_id":"t","seed":3,"score":0.71,"critical":false,"split":"gate"}]}}
JSON
python3 -m eval.harness.forge research-design /tmp/forge_results.json ; echo "exit=$?"
```
Expected: prints a PROMOTE proposal, `exit=0`, and appends one line to
`skills/skill-forge/insights/research-design/gate-history.jsonl`.

- [ ] **Step 3: Confirm transcript snapshot ignores cleanly**

Run: `git status --porcelain skills/skill-forge/insights/`
Expected: `gate-history.jsonl` shows up (committed-tracked); no `transcripts/` paths appear (gitignored).

- [ ] **Step 4: Clean up the dry-run artifact**

```bash
git checkout -- skills/skill-forge/insights/research-design/gate-history.jsonl 2>/dev/null || \
  rm -f skills/skill-forge/insights/research-design/gate-history.jsonl
rm -f /tmp/forge_results.json
```

- [ ] **Step 5: Final commit (if any docs/notes changed)**

```bash
git add -A && git commit -m "test(skill-forge): verify self-contained loop end-to-end" --allow-empty
```

---

## Self-Review

- **Spec coverage:** capture/transcript log (Tasks 1–3) · central store + schemas (Tasks 1, 8, 9) · distillation + crystallization (described as orchestration in Task 9, per spec §5.4–5.5) · simplified gate (Task 4) · Goodhart monitor (Task 5) · slim forge (Task 6) · migration delete/keep (Task 7) · Capture/Consult in all skills (Task 8) · skill-forge rewrite (Task 9) · gitignore + privacy boundary (Task 1) · verification (Task 10). `scientific-rigor` dormant-gate caveat carried in Global Constraints.
- **Placeholder scan:** none — every code/test step shows complete content.
- **Type consistency:** `gate.decide` / `gate.Decision` fields used identically in Tasks 4 and 6; `evaluate(results, *, now_iso)` and `results` shape consistent across Task 6 and Task 10; `INSIGHTS_ROOT` monkeypatch pattern consistent across capture/monitor/forge tests.
