"""CLI: demo-plan, classify, and a small committed VCF batch."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console
from rich.table import Table

from acmg_triage import SAFETY_DISCLAIMER, __version__
from acmg_triage.batch import classify_vcf
from acmg_triage.classify import classify_hgvs, load_samples
from acmg_triage.config import get_settings
from acmg_triage.logging import configure_logging
from acmg_triage.schemas import ClassificationResult, SampleVariant

app = typer.Typer(no_args_is_help=True, add_completion=False)
console = Console(width=140)


def _load_samples() -> list[SampleVariant]:
    return load_samples()


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
            "\nDry run only. Classification (`acmg classify`) is the next walkthrough "
            "step; this command exists so `make demo` can show that the sample set "
            "is designed, not sampled."
        )
    console.print(f"Sample manifest: {get_settings().sample_dir / 'variants.json'}")


@app.command("sample-path")
def sample_path() -> None:
    """Print the committed sample directory path."""

    console.print(str(get_settings().sample_dir.resolve()))


def _print_result(result: ClassificationResult, explain: bool) -> None:
    console.print(f"[bold]{result.hgvs}[/bold]  {result.gene}")
    if result.sample_id:
        console.print(f"sample: {result.sample_id}")
    if result.insufficient_evidence:
        console.print("[bold red]INSUFFICIENT EVIDENCE[/bold red]")
        console.print(
            "No catalog coverage. No ACMG tier is emitted. Confidence is 0. "
            "This is a refusal, not a guess."
        )
        console.print(f"confidence: {result.confidence}")
    elif result.conflicting:
        console.print("[bold yellow]CONFLICTING EVIDENCE[/bold yellow]")
        console.print(
            "Both pathogenic-leaning and benign-leaning codes applied. "
            "No single ACMG tier is emitted."
        )
        console.print(f"classification: {result.classification}")
    else:
        console.print(f"classification: [bold]{result.classification}[/bold]")
        if result.matched_rule:
            console.print(f"matched rule: {result.matched_rule}")
    if result.short_circuited_ba1:
        console.print("BA1 stand-alone short-circuit. Remaining criteria listed as skipped.")
    console.print(f"applied: {', '.join(result.applied_codes) or '(none)'}")
    if result.skipped_codes:
        shown = ", ".join(result.skipped_codes)
        console.print(f"skipped: {shown}")
    if explain:
        console.print("\n[bold]Evidence trail[/bold]")
        table = Table(show_header=True, header_style="bold")
        table.add_column("code")
        table.add_column("applied")
        table.add_column("strength")
        table.add_column("rationale")
        for call in result.calls:
            table.add_row(
                call.code,
                "yes" if call.applied else "no",
                call.strength or "",
                call.rationale,
            )
        if result.calls:
            console.print(table)
        if result.overlay_diffs:
            console.print("\n[bold]VCEP overlay (default vs gene-specific)[/bold]")
            console.print(
                f"default classification: {result.default_classification}  |  "
                f"overlay classification: {result.overlay_classification}"
            )
            od = Table(show_header=True, header_style="bold")
            od.add_column("code")
            od.add_column("default")
            od.add_column("overlay")
            od.add_column("note")
            n_changed = 0
            for diff in result.overlay_diffs:
                changed = (
                    diff.default_applied != diff.overlay_applied
                    or diff.default_strength != diff.overlay_strength
                )
                if not changed:
                    continue
                n_changed += 1
                od.add_row(
                    diff.code,
                    f"{diff.default_applied}/{diff.default_strength}",
                    f"{diff.overlay_applied}/{diff.overlay_strength}",
                    diff.overlay_rationale,
                )
            if n_changed:
                console.print(od)
            else:
                console.print(
                    "No strength or apply/decline disagreement on overlay-sensitive codes."
                )
        console.print("\n[bold]Node trace[/bold]")
        for node in result.nodes:
            flag = "skip" if node.skipped else ("on" if node.applied else "off")
            label = node.code or node.node
            console.print(f"  {label:8} {flag:4}  {node.rationale}")
    console.print(
        f"\ncost: ${result.cost_usd:.4f} (cache-only)  latency: {result.latency_ms:.2f} ms"
    )
    console.print()
    console.print(result.disclaimer)


@app.command("classify")
def classify_cmd(
    hgvs: str = typer.Option(..., "--hgvs", help="HGVS from the committed sample or probe set"),
    explain: bool = typer.Option(False, "--explain", help="Print the full evidence trail"),
    as_json: bool = typer.Option(False, "--json", help="Emit ClassificationResult JSON"),
) -> None:
    """Classify a committed HGVS. Research tool; not clinical interpretation."""

    try:
        result = classify_hgvs(hgvs)
    except KeyError as exc:
        console.print(f"[red]{exc}[/red]")
        console.print(SAFETY_DISCLAIMER)
        raise typer.Exit(code=2) from exc
    if as_json:
        console.print_json(result.model_dump_json())
        return
    _print_result(result, explain=explain)


@app.command("batch")
def batch_cmd(
    vcf: Annotated[
        Path | None,
        typer.Argument(help="VCF path. Defaults to the committed 5-row demo VCF."),
    ] = None,
    as_json: bool = typer.Option(False, "--json"),
) -> None:
    """Classify a small committed VCF (five designed rows)."""

    path = vcf or (get_settings().sample_dir / "demo.vcf")
    pairs = classify_vcf(path)
    if as_json:
        payload = [
            {"row": row.model_dump(), "result": result.model_dump()} for row, result in pairs
        ]
        console.print_json(json.dumps(payload))
        return
    table = Table(title="acmg batch")
    table.add_column("id")
    table.add_column("hgvs")
    table.add_column("gene")
    table.add_column("classification")
    table.add_column("applied")
    for row, result in pairs:
        label = (
            "INSUFFICIENT EVIDENCE"
            if result.insufficient_evidence
            else ("CONFLICTING" if result.conflicting else str(result.classification))
        )
        table.add_row(row.row_id, row.hgvs, row.gene, label, ",".join(result.applied_codes))
    console.print(table)
    console.print()
    console.print(SAFETY_DISCLAIMER)


def repo_root() -> Path:
    return get_settings().repo_root
