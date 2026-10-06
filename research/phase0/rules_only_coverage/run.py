"""Zero-LLM coverage of the 28 codes, plus rules-only classification accuracy."""

from __future__ import annotations

import sys
from collections import Counter
from pathlib import Path

from acmg_triage.codes import ACMG_2015_CODES, computability_split
from acmg_triage.combining import calls_from_codes, combine
from acmg_triage.rules import applied_codes, apply_default_rules
from acmg_triage.schemas import Classification

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from _lib import load_probe_variants, md_table, pct, write_json  # noqa: E402

HERE = Path(__file__).resolve().parent
PROBE = HERE.parent / "criterion_agreement" / "probe_set" / "variants.json"
RESULTS = HERE / "results"

TIERS: tuple[Classification, ...] = (
    "Pathogenic",
    "Likely pathogenic",
    "Uncertain significance",
    "Likely benign",
    "Benign",
    "Conflicting",
)


def main() -> None:
    split = computability_split()
    variants = load_probe_variants(PROBE)

    confusion: dict[str, dict[str, int]] = {gold: {pred: 0 for pred in TIERS} for gold in TIERS}
    n_correct = 0
    n_conflict_gold = 0
    n_conflict_pred = 0
    for variant in variants:
        pred = combine(apply_default_rules(variant))
        gold_result = combine(calls_from_codes(variant.gold_codes, variant.gold_strengths))
        # Prefer the stored gold_class; re-combine as a consistency check.
        gold_class = variant.gold_class
        if gold_result.classification != gold_class:
            raise RuntimeError(
                f"{variant.variant_id}: stored gold_class {gold_class} "
                f"!= recomputed {gold_result.classification}"
            )
        confusion[gold_class][pred.classification] += 1
        if pred.classification == gold_class:
            n_correct += 1
        if gold_class == "Conflicting":
            n_conflict_gold += 1
        if pred.classification == "Conflicting":
            n_conflict_pred += 1

    accuracy = n_correct / len(variants)
    code_rows = [
        [spec.code, spec.computability, spec.default_strength, spec.direction]
        for spec in ACMG_2015_CODES
    ]
    confusion_rows = [[gold, *[str(confusion[gold][pred]) for pred in TIERS]] for gold in TIERS]

    payload = {
        "n_codes": split.n_total,
        "n_rules": split.n_rules,
        "n_catalog": split.n_catalog,
        "n_literature_llm": split.n_literature_llm,
        "rules_fraction": split.rules_fraction,
        "zero_llm_fraction": split.zero_llm_fraction,
        "rules_codes": list(split.rules_codes),
        "catalog_codes": list(split.catalog_codes),
        "literature_codes": list(split.literature_codes),
        "n_variants": len(variants),
        "rules_only_concordance": accuracy,
        "n_correct": n_correct,
        "confusion": confusion,
        "gold_class_counts": dict(Counter(v.gold_class for v in variants)),
        "n_predicted_codes_mean": sum(len(applied_codes(apply_default_rules(v))) for v in variants)
        / len(variants),
        "decision": (
            "Rules-only is the published baseline. Phase 3 must beat this "
            f"concordance ({accuracy:.3f}) with literature nodes enabled, "
            "and must report the disabled-LLM score as this number."
        ),
    }
    RESULTS.mkdir(parents=True, exist_ok=True)
    write_json(RESULTS / "results.json", payload)
    coverage = md_table(
        ["code", "computability", "default strength", "direction"],
        code_rows,
    )
    conf = md_table(["gold \\ pred", *TIERS], confusion_rows)
    md = (
        "# rules_only_coverage results\n\n"
        f"Rules-computable: {split.n_rules}/28 = {split.rules_fraction:.3f}\n\n"
        f"Zero-LLM (rules + catalog): {split.n_rules + split.n_catalog}/28 = "
        f"{split.zero_llm_fraction:.3f}\n\n"
        f"Literature/LLM: {split.n_literature_llm}/28\n\n"
        f"Rules-only concordance vs VCEP gold: {n_correct}/{len(variants)} = "
        f"{pct(accuracy)}\n\n"
        f"{payload['decision']}\n\n"
        "## Code computability\n\n"
        f"{coverage}\n\n"
        "## Confusion matrix (rules-only vs gold class)\n\n"
        f"{conf}\n"
    )
    (RESULTS / "results.md").write_text(md, encoding="utf-8")
    print(md)


if __name__ == "__main__":
    main()
