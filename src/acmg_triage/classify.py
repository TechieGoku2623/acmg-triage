"""Resolve an HGVS against committed samples/probes and run the graph."""

from __future__ import annotations

import json
from pathlib import Path

from acmg_triage import SAFETY_DISCLAIMER
from acmg_triage.config import get_settings
from acmg_triage.graph import GraphState, run_graph
from acmg_triage.schemas import (
    ClassificationResult,
    DecisionTrace,
    ProbeVariant,
    SampleVariant,
)


def load_samples() -> list[SampleVariant]:
    raw = json.loads((get_settings().sample_dir / "variants.json").read_text(encoding="utf-8"))
    return [SampleVariant.model_validate(item) for item in raw["variants"]]


def load_probe_variants() -> list[ProbeVariant]:
    path = get_settings().probe_set_path
    raw = json.loads(path.read_text(encoding="utf-8"))
    return [ProbeVariant.model_validate(item) for item in raw["variants"]]


def resolve_variant(hgvs: str) -> tuple[ProbeVariant, str | None]:
    """Look up committed features. Never invent scores for an unknown HGVS."""

    for sample in load_samples():
        if sample.hgvs == hgvs or sample.sample_id == hgvs:
            return sample.features, sample.sample_id
    for probe in load_probe_variants():
        if probe.hgvs == hgvs or probe.variant_id == hgvs:
            return probe, probe.variant_id
    raise KeyError(
        f"No committed features for {hgvs}. "
        "Classify reads the sample catalog and probe set only; no live annotation."
    )


def _inputs(variant: ProbeVariant) -> dict[str, object]:
    return {
        "hgvs": variant.hgvs,
        "gene": variant.gene,
        "consequence": variant.consequence,
        "gnomad_af": variant.gnomad_af,
        "revel": variant.revel,
        "spliceai_max": variant.spliceai_max,
        "lof_mechanism_established": variant.lof_mechanism_established,
        "last_exon": variant.last_exon,
        "clingen_vcep": variant.clingen_vcep,
    }


def persist_trace(trace: DecisionTrace) -> Path:
    traces = get_settings().traces_dir
    traces.mkdir(parents=True, exist_ok=True)
    slug = trace.hgvs.replace(":", "_").replace(">", "_")
    path = traces / f"{slug}.json"
    path.write_text(trace.model_dump_json(indent=2) + "\n", encoding="utf-8")
    return path


def result_from_state(state: GraphState, sample_id: str | None) -> ClassificationResult:
    variant = state.variant
    applied = [c.code for c in state.final_calls if c.applied]
    if state.insufficient_evidence:
        applied = []
    confidence = 0.0 if state.insufficient_evidence or state.conflicting else 1.0
    calls = state.final_calls if not state.insufficient_evidence else []
    if not state.insufficient_evidence and not state.final_calls:
        calls = [c for c in state.default_by_code.values() if c.applied]
        applied = [c.code for c in calls]
    trace = DecisionTrace(
        hgvs=variant.hgvs,
        gene=variant.gene,
        sample_id=sample_id,
        inputs=_inputs(variant),
        catalog_covered=state.catalog_covered,
        insufficient_evidence=state.insufficient_evidence,
        classification=state.classification,
        default_classification=state.default_classification,
        overlay_classification=state.overlay_classification,
        conflicting=state.conflicting,
        short_circuited_ba1=state.ba1_short_circuit,
        applied_codes=applied,
        skipped_codes=state.skipped_codes,
        calls=calls,
        overlay_diffs=state.overlay_diffs,
        nodes=state.nodes,
        cost_usd=0.0,
        latency_ms=state.latency_ms,
        disclaimer=SAFETY_DISCLAIMER,
    )
    persist_trace(trace)
    return ClassificationResult(
        hgvs=variant.hgvs,
        gene=variant.gene,
        sample_id=sample_id,
        classification=state.classification,
        default_classification=state.default_classification,
        overlay_classification=state.overlay_classification,
        insufficient_evidence=state.insufficient_evidence,
        conflicting=state.conflicting,
        short_circuited_ba1=state.ba1_short_circuit,
        matched_rule=state.matched_rule,
        applied_codes=applied,
        skipped_codes=state.skipped_codes,
        calls=calls,
        overlay_diffs=state.overlay_diffs,
        nodes=state.nodes,
        cost_usd=0.0,
        latency_ms=state.latency_ms,
        confidence=confidence,
        disclaimer=SAFETY_DISCLAIMER,
        trace=trace,
    )


def classify_hgvs(hgvs: str) -> ClassificationResult:
    variant, sample_id = resolve_variant(hgvs)
    return result_from_state(run_graph(variant), sample_id)


def classify_variant(variant: ProbeVariant, sample_id: str | None = None) -> ClassificationResult:
    return result_from_state(run_graph(variant), sample_id)
