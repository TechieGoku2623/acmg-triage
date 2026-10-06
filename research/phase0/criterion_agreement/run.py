"""Per-code precision/recall of default 2015 rules vs VCEP-style gold."""

from __future__ import annotations

import sys
from pathlib import Path

from acmg_triage.codes import RULES_CODES
from acmg_triage.rules import applied_codes, apply_default_rules

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from _lib import load_probe_variants, md_table, pct, write_json  # noqa: E402

HERE = Path(__file__).resolve().parent
PROBE = HERE / "probe_set" / "variants.json"
RESULTS = HERE / "results"


def _prf(tp: int, fp: int, fn: int) -> tuple[float, float, float]:
    precision = tp / (tp + fp) if (tp + fp) else 0.0
    recall = tp / (tp + fn) if (tp + fn) else 0.0
    f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) else 0.0
    return precision, recall, f1


def main() -> None:
    variants = load_probe_variants(PROBE)
    per_code: dict[str, dict[str, int]] = {
        code: {"tp": 0, "fp": 0, "fn": 0, "tn": 0, "strength_match": 0, "strength_mismatch": 0}
        for code in RULES_CODES
    }

    for variant in variants:
        predicted = set(applied_codes(apply_default_rules(variant)))
        gold = set(variant.gold_codes)
        pred_calls = {c.code: c for c in apply_default_rules(variant)}
        for code in RULES_CODES:
            in_pred = code in predicted
            in_gold = code in gold
            bucket = per_code[code]
            if in_pred and in_gold:
                bucket["tp"] += 1
                pred_strength = pred_calls[code].strength
                gold_strength = variant.gold_strengths.get(code, pred_strength)
                if pred_strength == gold_strength:
                    bucket["strength_match"] += 1
                else:
                    bucket["strength_mismatch"] += 1
            elif in_pred and not in_gold:
                bucket["fp"] += 1
            elif (not in_pred) and in_gold:
                bucket["fn"] += 1
            else:
                bucket["tn"] += 1

    rows_md: list[list[str]] = []
    codes_out: dict[str, object] = {}
    ship_default: list[str] = []
    needs_vcep: list[str] = []
    for code in RULES_CODES:
        stats = per_code[code]
        precision, recall, f1 = _prf(stats["tp"], stats["fp"], stats["fn"])
        support = stats["tp"] + stats["fn"]
        if support == 0:
            decision = "unmeasured (no gold positives)"
        elif f1 >= 0.90 and stats["strength_mismatch"] == 0:
            decision = "default-only"
            ship_default.append(code)
        else:
            decision = "needs VCEP overlay"
            needs_vcep.append(code)
        codes_out[code] = {
            **stats,
            "precision": precision,
            "recall": recall,
            "f1": f1,
            "gold_positive": support,
            "ship_default_only": decision == "default-only",
            "decision": decision,
        }
        rows_md.append(
            [
                code,
                str(support),
                str(stats["tp"]),
                str(stats["fp"]),
                str(stats["fn"]),
                pct(precision),
                pct(recall),
                pct(f1),
                str(stats["strength_mismatch"]),
                decision,
            ]
        )

    payload = {
        "n_variants": len(variants),
        "decision_rule": "ship default-only if F1>=0.90 and zero strength mismatches",
        "ship_default_only": ship_default,
        "needs_vcep_overlay": needs_vcep,
        "codes": codes_out,
        "gold_source": (
            "Committed probe set. Gold follows ENIGMA v1.2.0 frequency cutoffs, "
            "ClinGen SVI PM2-as-supporting, and Abou Tayoun 2018 last-exon PVS1 cap. "
            "Not a live ClinGen Evidence Repository dump."
        ),
    }
    RESULTS.mkdir(parents=True, exist_ok=True)
    write_json(RESULTS / "results.json", payload)
    table = md_table(
        [
            "code",
            "gold+",
            "TP",
            "FP",
            "FN",
            "precision",
            "recall",
            "F1",
            "strength mismatches",
            "decision",
        ],
        rows_md,
    )
    md = (
        "# criterion_agreement results\n\n"
        f"n = {len(variants)} committed probe variants.\n\n"
        f"Ship default-only: {', '.join(ship_default) or '(none)'}\n\n"
        f"Needs VCEP overlay: {', '.join(needs_vcep) or '(none)'}\n\n"
        f"{table}\n"
    )
    (RESULTS / "results.md").write_text(md, encoding="utf-8")
    print(md)


if __name__ == "__main__":
    main()
