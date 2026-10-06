"""Phase 3 evaluation on the committed 100-variant probe set.

Does not replace Phase 0 harnesses. Adds frequency-threshold-only and full-system
(cache literature, VCEP overlay reported) columns. Literature-disabled must equal
the rules-only baseline.
"""

from __future__ import annotations

import sys
from collections import Counter
from pathlib import Path

from acmg_triage.classify import classify_variant
from acmg_triage.combining import combine
from acmg_triage.rules import apply_default_rules
from acmg_triage.schemas import Classification, ProbeVariant

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "phase0"))
from _lib import load_probe_variants, md_table, write_json  # noqa: E402

HERE = Path(__file__).resolve().parent
PROBE = HERE.parent / "phase0" / "criterion_agreement" / "probe_set" / "variants.json"
RESULTS = HERE / "results"

TIERS: tuple[Classification, ...] = (
    "Pathogenic",
    "Likely pathogenic",
    "Uncertain significance",
    "Likely benign",
    "Benign",
    "Conflicting",
)
FREQ_CODES = {"BA1", "BS1", "PM2"}


def _freq_only(variant: ProbeVariant) -> Classification:
    calls = [c for c in apply_default_rules(variant) if c.code in FREQ_CODES]
    return combine(calls).classification


def _rules_only(variant: ProbeVariant) -> Classification:
    return combine(apply_default_rules(variant)).classification


def _full(variant: ProbeVariant, *, literature: bool) -> Classification | None:
    result = classify_variant(variant, sample_id=variant.variant_id)
    if not literature:
        # Literature-disabled path is default rules + combine.
        return _rules_only(variant)
    if result.insufficient_evidence:
        return None
    return result.classification


def _concordance(
    variants: list[ProbeVariant],
    predicted: list[Classification | None],
) -> tuple[float, int]:
    n_correct = 0
    n = 0
    for variant, pred in zip(variants, predicted, strict=True):
        n += 1
        if pred == variant.gold_class:
            n_correct += 1
    return (n_correct / n if n else 0.0), n_correct


def main() -> None:
    variants = load_probe_variants(PROBE)
    rules = [_rules_only(v) for v in variants]
    freq = [_freq_only(v) for v in variants]
    llm_off = [_full(v, literature=False) for v in variants]
    llm_on = [_full(v, literature=True) for v in variants]

    rules_acc, rules_ok = _concordance(variants, rules)
    freq_acc, freq_ok = _concordance(variants, freq)
    off_acc, off_ok = _concordance(variants, llm_off)
    on_acc, on_ok = _concordance(variants, llm_on)

    if llm_off != rules:
        raise RuntimeError("LLM-off full system must equal rules-only predictions")

    payload = {
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
    RESULTS.mkdir(parents=True, exist_ok=True)
    write_json(RESULTS / "results.json", payload)
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
    table = md_table(["System", "Concordance", "n", "Notes"], rows)
    md = f"# phase3 evaluation\n\n{payload['decision']}\n\n{table}\n"
    (RESULTS / "results.md").write_text(md, encoding="utf-8")
    print(md)


if __name__ == "__main__":
    main()
