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
