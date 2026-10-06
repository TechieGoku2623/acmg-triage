"""Phase 0 CLI. Classification, API, and batch VCF scoring are Phase 2."""

from __future__ import annotations

import json
from pathlib import Path

import typer
from rich.console import Console

from acmg_triage import SAFETY_DISCLAIMER, __version__
from acmg_triage.config import get_settings
from acmg_triage.logging import configure_logging
from acmg_triage.schemas import SampleVariant

app = typer.Typer(no_args_is_help=True, add_completion=False)
console = Console(width=140)


def _load_samples() -> list[SampleVariant]:
    path = get_settings().sample_dir / "variants.json"
    raw = json.loads(path.read_text(encoding="utf-8"))
    return [SampleVariant.model_validate(item) for item in raw["variants"]]


@app.callback()
def _main() -> None:
    configure_logging()


@app.command("version")
def version() -> None:
    """Print the package version."""

    console.print(f"acmg-triage {__version__}")


@app.command("demo-plan")
def demo_plan(
    dry_run: bool = typer.Option(True, "--dry-run/--no-dry-run"),
) -> None:
    """Print the five designed sample variants and the path each exercises."""

    samples = _load_samples()
    console.print("[bold]acmg-triage designed sample variants[/bold]\n")
    for sample in samples:
        console.print(f"[bold]{sample.sample_id}[/bold]  {sample.hgvs}  {sample.gene}")
        console.print(f"  path:     {sample.path_exercised}")
        console.print(f"  expected: {sample.expected_behavior}\n")
    console.print()
    console.print(SAFETY_DISCLAIMER)
    if dry_run:
        console.print(
            "\nDry run only. Classification (`acmg classify`) is Phase 2; "
            "this command exists so `make demo` can show that the sample set "
            "is designed, not sampled."
        )
    console.print(f"Sample manifest: {get_settings().sample_dir / 'variants.json'}")


@app.command("sample-path")
def sample_path() -> None:
    """Print the committed sample directory path."""

    console.print(str(get_settings().sample_dir.resolve()))


def repo_root() -> Path:
    return get_settings().repo_root
