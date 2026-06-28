from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path


def normalize_answer(s: str) -> str:
    """Lowercase, strip, and collapse whitespace so equivalent answers group together."""
    return " ".join(str(s).strip().lower().split())


def tally_answers(answers: list[str]) -> dict:
    """Tally normalized answers into the top answer, counts, agreement rate, and n."""
    if not answers:
        raise ValueError("no answers")
    counts: dict[str, int] = {}
    for a in answers:
        key = normalize_answer(a)
        counts[key] = counts.get(key, 0) + 1
    top = max(counts, key=lambda k: counts[k])
    n = len(answers)
    return {"top": top, "counts": counts, "agreement_rate": counts[top] / n, "n": n}


@dataclass(frozen=True)
class Aggregate:
    answer: str
    agreement_rate: float
    verifier_pass_rate: float | None
    confidence: float
    converged: bool
    escalate: bool


def aggregate(
    answers: list[str],
    verifier_verdicts: list[bool] | None = None,
    agreement_threshold: float = 0.6,
    confidence_threshold: float = 0.7,
) -> Aggregate:
    """Combine parallel-path answers (+ optional verifier verdicts) into a calibrated decision."""
    tally = tally_answers(answers)
    agreement = tally["agreement_rate"]
    if verifier_verdicts:
        vpr: float | None = sum(1 for v in verifier_verdicts if v) / len(verifier_verdicts)
        confidence = 0.5 * agreement + 0.5 * vpr
    else:
        vpr = None
        confidence = agreement
    converged = agreement >= agreement_threshold and (vpr is None or vpr >= 0.5)
    escalate = confidence < confidence_threshold
    return Aggregate(
        answer=tally["top"],
        agreement_rate=agreement,
        verifier_pass_rate=vpr,
        confidence=confidence,
        converged=converged,
        escalate=escalate,
    )


def render(agg: Aggregate) -> str:
    vpr = "n/a" if agg.verifier_pass_rate is None else f"{agg.verifier_pass_rate:.2f}"
    return (
        "# Consensus\n\n"
        f"- Answer: {agg.answer}\n"
        f"- Agreement rate: {agg.agreement_rate:.2f}\n"
        f"- Verifier pass rate: {vpr}\n"
        f"- Confidence: {agg.confidence:.2f}\n"
        f"- Converged: {'yes' if agg.converged else 'no'}\n"
        f"- Escalate: {'yes' if agg.escalate else 'no'}\n"
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="eval.harness.consensus")
    parser.add_argument("results", help="path to a reasoning results JSON file")
    args = parser.parse_args(argv)
    data = json.loads(Path(args.results).read_text(encoding="utf-8"))
    agg = aggregate(
        data["answers"],
        data.get("verifier_verdicts"),
        data.get("agreement_threshold", 0.6),
        data.get("confidence_threshold", 0.7),
    )
    print(render(agg))
    return 0 if agg.converged else 1


if __name__ == "__main__":
    raise SystemExit(main())
