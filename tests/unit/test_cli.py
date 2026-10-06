from __future__ import annotations

from typer.testing import CliRunner

from acmg_triage.cli import app

runner = CliRunner()


def test_demo_plan_lists_five_designed_paths() -> None:
    result = runner.invoke(app, ["demo-plan", "--dry-run"])
    assert result.exit_code == 0
    assert "S1-pathogenic-frameshift" in result.stdout
    assert "NM_000059.4:c.5946del" in result.stdout
    assert "S5-insufficient-evidence" in result.stdout
    assert "OR8U1" in result.stdout
    assert "Research tool only" in result.stdout
    assert "Dry run only" in result.stdout


def test_version() -> None:
    result = runner.invoke(app, ["version"])
    assert result.exit_code == 0
    assert "acmg-triage" in result.stdout


def _fits_video_frame(stdout: str) -> None:
    lines = stdout.splitlines()
    assert lines, "expected output"
    assert len(lines) <= 30, f"too many lines for 100x30: {len(lines)}"
    assert max(len(line) for line in lines) <= 100


def test_cli_summary_fits_100x30() -> None:
    cases = (
        "NM_000059.4:c.5946del",
        "NM_000059.4:c.1114A>C",
        "NM_000059.4:c.2311G>A",
        "NM_001005237.2:c.200A>G",
    )
    for hgvs in cases:
        result = runner.invoke(app, ["classify", "--hgvs", hgvs, "--summary"])
        assert result.exit_code == 0, result.stdout
        _fits_video_frame(result.stdout)
    conflict = runner.invoke(app, ["classify", "--hgvs", cases[2], "--summary"])
    assert "CONFLICTING EVIDENCE" in conflict.stdout
    ba1 = runner.invoke(app, ["classify", "--hgvs", cases[1], "--summary"])
    assert "skipped:" in ba1.stdout
    refused = runner.invoke(app, ["classify", "--hgvs", cases[3], "--summary"])
    assert "INSUFFICIENT EVIDENCE" in refused.stdout


def test_cli_eval_summary_matches_published_baseline() -> None:
    result = runner.invoke(app, ["eval", "--summary"])
    assert result.exit_code == 0, result.stdout
    assert "0.670" in result.stdout
    assert "0.770" in result.stdout
    assert "Rules-only" in result.stdout
    _fits_video_frame(result.stdout)
