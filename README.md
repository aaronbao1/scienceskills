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

    python3 -m eval.harness.cli lint
    python3 -m eval.harness.cli validate
