"""Build the 100-variant criterion-agreement probe set.

Gold labels use published ClinGen VCEP / SVI rules. Predicted labels come from
``acmg_triage.rules`` at measurement time. Do not import the default rules here.
"""

from __future__ import annotations

import json
from pathlib import Path

from acmg_triage.codes import Strength
from acmg_triage.combining import calls_from_codes, combine
from acmg_triage.schemas import Classification, Consequence, ProbeVariant

OUT = Path(__file__).resolve().parent / "variants.json"

# ENIGMA BRCA1/2 VCEP v1.2.0 (cspec GN097 / GN096), frequency appendix.
# BA1: FAF > 0.001; BS1 strong: FAF > 0.0001; PM2: absent from relevant gnomAD subset.
ENIGMA_BA1 = 0.001
ENIGMA_BS1 = 0.0001

# ClinGen SVI recommendation (2020): PM2 at supporting strength only.
# Last-exon PVS1 is capped at strong in the Abou Tayoun 2018 PVS1 decision tree.


def _gold_codes(variant: ProbeVariant) -> tuple[list[str], dict[str, Strength]]:
    codes: list[str] = []
    strengths: dict[str, Strength] = {}
    af = variant.gnomad_af

    ba1 = variant.vcep_ba1_af
    bs1 = variant.vcep_bs1_af
    if ba1 is not None and af >= ba1:
        codes.append("BA1")
    elif bs1 is not None and af >= bs1:
        codes.append("BS1")
    else:
        absent = af == 0.0
        extremely_low = af < 1e-5
        pm2 = absent if variant.vcep_pm2_requires_absent else absent or extremely_low
        if pm2:
            codes.append("PM2")
            if variant.vcep_pm2_supporting_only:
                strengths["PM2"] = "supporting"

    null = variant.consequence in {
        "frameshift",
        "stop_gained",
        "splice_acceptor",
        "splice_donor",
    }
    if null and variant.lof_mechanism_established:
        if variant.last_exon and variant.vcep_pvs1_max_strength is not None:
            if variant.vcep_pvs1_max_strength != "very_strong":
                codes.append("PVS1")
                strengths["PVS1"] = variant.vcep_pvs1_max_strength
            else:
                codes.append("PVS1")
        elif not variant.last_exon:
            codes.append("PVS1")
        elif variant.vcep_pvs1_max_strength is None:
            # Gold follows the PVS1 tree: last exon without a VCEP cap still
            # applies PVS1 at strong, not very_strong.
            codes.append("PVS1")
            strengths["PVS1"] = "strong"

    if variant.consequence in {"inframe_indel", "stop_lost"}:
        codes.append("PM4")

    pp3_cut = variant.vcep_pp3_revel if variant.vcep_pp3_revel is not None else 0.70
    bp4_cut = variant.vcep_bp4_revel if variant.vcep_bp4_revel is not None else 0.15
    if variant.revel is not None and variant.revel >= pp3_cut:
        codes.append("PP3")
    if variant.revel is not None and variant.revel <= bp4_cut:
        codes.append("BP4")

    if (
        variant.consequence == "synonymous"
        and variant.spliceai_max is not None
        and variant.spliceai_max < 0.10
    ):
        codes.append("BP7")

    return codes, strengths


def _finish(
    partial: ProbeVariant,
    extra_codes: list[str] | None = None,
    extra_strengths: dict[str, Strength] | None = None,
) -> ProbeVariant:
    codes, strengths = _gold_codes(partial)
    if extra_codes:
        codes = [*codes, *extra_codes]
    if extra_strengths:
        strengths = {**strengths, **extra_strengths}
    result = combine(calls_from_codes(codes, strengths))
    return partial.model_copy(
        update={
            "gold_codes": codes,
            "gold_strengths": strengths,
            "gold_class": result.classification,
        }
    )


def _base(
    *,
    variant_id: str,
    hgvs: str,
    gene: str,
    consequence: Consequence,
    gnomad_af: float,
    cohort: str,
    gold_source: str,
    revel: float | None = None,
    spliceai_max: float | None = None,
    lof_mechanism_established: bool = True,
    last_exon: bool = False,
    clingen_vcep: str | None = "ENIGMA BRCA1/BRCA2 v1.2.0",
    vcep_ba1_af: float | None = ENIGMA_BA1,
    vcep_bs1_af: float | None = ENIGMA_BS1,
    vcep_pm2_requires_absent: bool = True,
    vcep_pm2_supporting_only: bool = True,
    vcep_pp3_revel: float | None = None,
    vcep_bp4_revel: float | None = None,
    vcep_pvs1_max_strength: Strength | None = None,
    notes: str = "",
    extra_codes: list[str] | None = None,
) -> ProbeVariant:
    partial = ProbeVariant(
        variant_id=variant_id,
        hgvs=hgvs,
        gene=gene,
        consequence=consequence,
        gnomad_af=gnomad_af,
        revel=revel,
        spliceai_max=spliceai_max,
        lof_mechanism_established=lof_mechanism_established,
        last_exon=last_exon,
        clingen_vcep=clingen_vcep,
        vcep_ba1_af=vcep_ba1_af,
        vcep_bs1_af=vcep_bs1_af,
        vcep_pm2_requires_absent=vcep_pm2_requires_absent,
        vcep_pm2_supporting_only=vcep_pm2_supporting_only,
        vcep_pp3_revel=vcep_pp3_revel,
        vcep_bp4_revel=vcep_bp4_revel,
        vcep_pvs1_max_strength=vcep_pvs1_max_strength,
        gold_codes=[],
        gold_class="Uncertain significance",
        gold_source=gold_source,
        cohort=cohort,
        notes=notes,
    )
    return _finish(partial, extra_codes=extra_codes)


def build() -> list[ProbeVariant]:
    """Return 100 designed probe variants. Seed is unused; the list is closed."""

    rows: list[ProbeVariant] = []

    # 8 — BA1 under both default (5%) and ENIGMA (0.1%).
    common_afs = [0.27, 0.18, 0.12, 0.09, 0.07, 0.055, 0.31, 0.22]
    for i, af in enumerate(common_afs, start=1):
        rows.append(
            _base(
                variant_id=f"BA1-BOTH-{i:02d}",
                hgvs=f"NM_000059.4:c.{1000 + i}A>G",
                gene="BRCA2",
                consequence="missense",
                gnomad_af=af,
                revel=0.08,
                cohort="ba1_both",
                gold_source="Richards 2015 BA1 (>5%) and ENIGMA v1.2.0 BA1 (FAF>0.001)",
            )
        )

    # 12 — ENIGMA BA1 only (0.1% < AF < 5%). Default 2015 misses BA1.
    for i in range(1, 13):
        rows.append(
            _base(
                variant_id=f"BA1-VCEP-{i:02d}",
                hgvs=f"NM_000059.4:c.{2000 + i}C>T",
                gene="BRCA2",
                consequence="missense",
                gnomad_af=0.002 + i * 0.0015,
                revel=0.12,
                cohort="ba1_vcep_only",
                gold_source="ENIGMA BRCA1/2 VCEP v1.2.0 BA1 FAF>0.001 (cspec GN097)",
            )
        )

    # 10 — ENIGMA BS1 only (0.01% < AF < 0.1%).
    for i in range(1, 11):
        rows.append(
            _base(
                variant_id=f"BS1-VCEP-{i:02d}",
                hgvs=f"NM_000059.4:c.{3000 + i}G>A",
                gene="BRCA2",
                consequence="missense",
                gnomad_af=0.00015 + i * 0.00004,
                revel=0.20,
                cohort="bs1_vcep_only",
                gold_source="ENIGMA BRCA1/2 VCEP v1.2.0 BS1 FAF>0.0001",
            )
        )

    # 10 — PM2 both: absent from gnomAD.
    for i in range(1, 11):
        rows.append(
            _base(
                variant_id=f"PM2-BOTH-{i:02d}",
                hgvs=f"NM_000059.4:c.{4000 + i}T>C",
                gene="BRCA2",
                consequence="missense",
                gnomad_af=0.0,
                revel=0.40,
                cohort="pm2_both",
                gold_source="Richards 2015 PM2 absent; ENIGMA PM2 absent from gnomAD non-cancer",
            )
        )

    # 10 — default PM2 only: extremely low but not absent. ENIGMA requires absent.
    for i in range(1, 11):
        rows.append(
            _base(
                variant_id=f"PM2-DEF-{i:02d}",
                hgvs=f"NM_000257.4:c.{2100 + i}C>T",
                gene="MYH7",
                consequence="missense",
                gnomad_af=2e-6 + i * 5e-7,
                revel=0.45,
                clingen_vcep="ENIGMA-style absent-only PM2 (demo overlay on MYH7)",
                cohort="pm2_default_only",
                gold_source=(
                    "Default 2015 PM2 fires at AF<1e-5; ENIGMA / several VCEPs "
                    "require absence. Gene-specific override path."
                ),
                notes="Sample variant 4 is drawn from this cohort.",
            )
        )

    # 10 — PVS1 both: frameshift, not last exon, LOF gene.
    for i in range(1, 11):
        rows.append(
            _base(
                variant_id=f"PVS1-BOTH-{i:02d}",
                hgvs=f"NM_000059.4:c.{5000 + i}del",
                gene="BRCA2",
                consequence="frameshift",
                gnomad_af=0.0,
                revel=None,
                last_exon=False,
                cohort="pvs1_both",
                gold_source="Richards 2015 PVS1; BRCA2 LOF is an established mechanism",
            )
        )

    # 8 — last-exon PVS1 downgrade: default keeps very_strong, gold caps at strong.
    for i in range(1, 9):
        rows.append(
            _base(
                variant_id=f"PVS1-DOWN-{i:02d}",
                hgvs=f"NM_000059.4:c.{9900 + i}del",
                gene="BRCA2",
                consequence="frameshift",
                gnomad_af=0.0,
                last_exon=True,
                vcep_pvs1_max_strength="strong",
                cohort="pvs1_downgrade",
                gold_source="Abou Tayoun et al. 2018 PVS1 decision tree (last-exon cap)",
            )
        )

    # 8 — PP3 both (REVEL >= 0.70).
    for i in range(1, 9):
        rows.append(
            _base(
                variant_id=f"PP3-BOTH-{i:02d}",
                hgvs=f"NM_000059.4:c.{6000 + i}A>C",
                gene="BRCA2",
                consequence="missense",
                gnomad_af=0.0,
                revel=0.72 + i * 0.02,
                cohort="pp3_both",
                gold_source="Default and VCEP PP3 at REVEL>=0.70",
            )
        )

    # 8 — BP4 both (REVEL <= 0.15) plus PM2-absent → gold Conflicting.
    for i in range(1, 9):
        rows.append(
            _base(
                variant_id=f"BP4-BOTH-{i:02d}",
                hgvs=f"NM_000059.4:c.{6100 + i}G>T",
                gene="BRCA2",
                consequence="missense",
                gnomad_af=0.0,
                revel=0.02 + i * 0.01,
                cohort="bp4_both",
                gold_source="Default and VCEP BP4 at REVEL<=0.15; PM2 also applies (absent)",
                notes="Pathogenic-leaning PM2 + benign-leaning BP4 is the conflict case.",
            )
        )

    # 6 — PP3 threshold mismatch: REVEL 0.64-0.69. Some VCEPs (Pejaver 2022
    # REVEL>=0.644) apply PP3; default 0.70 does not.
    for i in range(1, 7):
        rows.append(
            _base(
                variant_id=f"PP3-MIS-{i:02d}",
                hgvs=f"NM_000059.4:c.{6200 + i}T>A",
                gene="BRCA2",
                consequence="missense",
                gnomad_af=0.0,
                revel=0.644 + i * 0.007,
                vcep_pp3_revel=0.644,
                cohort="pp3_threshold_mismatch",
                gold_source="Pejaver et al. 2022 REVEL PP3 calibration (>=0.644)",
            )
        )

    # 10 — literature-only gold codes. Rules path cannot emit these.
    lit_codes = ["PS3", "PP4", "PS2", "PS4", "BS3", "PP1", "PM3", "BP5", "BS4", "PM6"]
    for i, code in enumerate(lit_codes, start=1):
        rows.append(
            _base(
                variant_id=f"LIT-{i:02d}",
                hgvs=f"NM_000059.4:c.{7000 + i}A>T",
                gene="BRCA2",
                consequence="missense",
                gnomad_af=0.0,
                revel=0.35,
                extra_codes=[code],
                cohort="literature_only",
                gold_source=f"Literature node gold: {code} from a published report",
            )
        )

    if len(rows) != 100:
        raise RuntimeError(f"expected 100 probe variants, built {len(rows)}")
    return rows


def main() -> None:
    variants = build()
    classes: dict[Classification, int] = {}
    for variant in variants:
        classes[variant.gold_class] = classes.get(variant.gold_class, 0) + 1
    payload = {
        "n": len(variants),
        "class_counts": classes,
        "variants": [v.model_dump() for v in variants],
    }
    OUT.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {len(variants)} variants to {OUT}")
    print(f"gold class counts: {classes}")


if __name__ == "__main__":
    main()
