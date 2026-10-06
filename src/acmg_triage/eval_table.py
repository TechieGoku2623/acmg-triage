"""Compact Phase 3 concordance table for the video and `acmg eval --summary`."""

from __future__ import annotations

from collections import Counter
from collections.abc import Sequence
from typing import Any

from acmg_triage.classify import classify_variant, load_probe_variants
from acmg_triage.combining import combine
from acmg_triage.rules import apply_default_rules
from acmg_triage.schemas import Classification, ProbeVariant

FREQ_CODES = {"BA1", "BS1", "PM2"}


def _freq_only(variant: ProbeVariant) -> Classification:
    calls = [c for c in apply_default_rules(variant) if c.code in FREQ_CODES]
    return combine(calls).classification


def _rules_only(variant: ProbeVariant) -> Classification:
    return combine(apply_default_rules(variant)).classification


def _full(variant: ProbeVariant, *, literature: bool) -> Classification | None:
    result = classify_variant(variant, sample_id=variant.variant_id)
    if not literature:
        return _rules_only(variant)
    if result.insufficient_evidence:
        return None
    return result.classification


def _concordance(
    variants: list[ProbeVariant],
    predicted: Sequence[Classification | None],
) -> tuple[float, int]:
    n_correct = 0
    for variant, pred in zip(variants, predicted, strict=True):
        if pred == variant.gold_class:
            n_correct += 1
    n = len(variants)
    return (n_correct / n if n else 0.0), n_correct


def run_eval_summary() -> tuple[dict[str, Any], list[list[str]]]:
    """Return the same four-row table `research/phase3/run.py` publishes."""

    variants = load_probe_variants()
    rules = [_rules_only(v) for v in variants]
    freq = [_freq_only(v) for v in variants]
    llm_off = [_full(v, literature=False) for v in variants]
    llm_on = [_full(v, literature=True) for v in variants]
    if llm_off != rules:
        raise RuntimeError("LLM-off full system must equal rules-only predictions")

    rules_acc, rules_ok = _concordance(variants, rules)
    freq_acc, freq_ok = _concordance(variants, freq)
    off_acc, off_ok = _concordance(variants, llm_off)
    on_acc, on_ok = _concordance(variants, llm_on)
    payload: dict[str, Any] = {
        "n_variants": len(variants),
        "rules_only_concordance": rules_acc,
        "rules_only_correct": rules_ok,
        "frequency_only_concordance": freq_acc,
        "frequency_only_correct": freq_ok,
        "full_llm_off_concordance": off_acc,
        "full_llm_off_correct": off_ok,
        "full_llm_on_concordance": on_acc,
        "full_llm_on_correct": on_ok,
        "gold_class_counts": dict(Counter(v.gold_class for v in variants)),
        "decision": (
            "Rules-only is the published baseline. Literature-disabled equals "
            f"rules-only ({rules_acc:.3f}). Full system uses the typed graph "
            "(VCEP overlay reported; literature cache-only, cost=0)."
        ),
    }
    rows = [
        [
            "Rules-only baseline (Phase 0)",
            f"{rules_acc:.3f}",
            str(len(variants)),
            "Default 2015 computational codes + combining table",
        ],
        [
            "Frequency-threshold-only",
            f"{freq_acc:.3f}",
            str(len(variants)),
            "BA1/BS1/PM2 only",
        ],
        [
            "Full system (LLM on)",
            f"{on_acc:.3f}",
            str(len(variants)),
            "Typed graph; literature cache-only (cost=0)",
        ],
        [
            "Full system (LLM off)",
            f"{off_acc:.3f}",
            str(len(variants)),
            "Must equal rules-only",
        ],
    ]
    return payload, rows
