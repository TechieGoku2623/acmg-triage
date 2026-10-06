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
