"""Default ACMG/AMP 2015 computational rules.

These are the rules-only implementations measured in Phase 0. They do not
read ClinGen gene-specific specifications. VCEP overrides live on gold labels
so criterion_agreement can measure the gap.

Default thresholds encoded here:
- BA1: AF >= 0.05 (Richards 2015)
- BS1: AF >= 0.01 (a generic stand-in; gene-specific expected AF is unmeasured
  without a prevalence model)
- PM2: AF == 0 or AF < 1e-5, strength moderate (2015, not ClinGen SVI 2020)
- PP3: REVEL >= 0.70
- BP4: REVEL <= 0.15
- BP7: synonymous and SpliceAI < 0.10
- PVS1: null consequence and established LOF mechanism; last-exon still PVS1
  at very_strong (the PVS1 decision tree is not applied)
"""

from __future__ import annotations

from acmg_triage.codes import CODE_INDEX, RULES_CODES
from acmg_triage.schemas import EvidenceCall, ProbeVariant

DEFAULT_BA1_AF = 0.05
DEFAULT_BS1_AF = 0.01
DEFAULT_PM2_AF = 1e-5
DEFAULT_PP3_REVEL = 0.70
DEFAULT_BP4_REVEL = 0.15
DEFAULT_BP7_SPLICEAI = 0.10

NULL_CONSEQUENCES = {"frameshift", "stop_gained", "splice_acceptor", "splice_donor"}


def _declined(code: str, rationale: str) -> EvidenceCall:
    spec = CODE_INDEX[code]
    return EvidenceCall(
        code=code,
        applied=False,
        strength=spec.default_strength,
        direction=spec.direction,
        rationale=rationale,
        sources=["acmg_triage.rules"],
    )


def _applied(code: str, rationale: str) -> EvidenceCall:
    spec = CODE_INDEX[code]
    return EvidenceCall(
        code=code,
        applied=True,
        strength=spec.default_strength,
        direction=spec.direction,
        rationale=rationale,
        sources=["acmg_triage.rules"],
    )


def apply_default_rules(variant: ProbeVariant) -> list[EvidenceCall]:
    """Evaluate every rules-computable code under default 2015 thresholds."""

    calls: list[EvidenceCall] = []

    if variant.gnomad_af >= DEFAULT_BA1_AF:
        calls.append(
            _applied(
                "BA1",
                f"gnomAD AF {variant.gnomad_af:.6g} >= default BA1 {DEFAULT_BA1_AF}",
            )
        )
    else:
        calls.append(
            _declined(
                "BA1",
                f"gnomAD AF {variant.gnomad_af:.6g} < default BA1 {DEFAULT_BA1_AF}",
            )
        )

    if DEFAULT_BS1_AF <= variant.gnomad_af < DEFAULT_BA1_AF:
        calls.append(
            _applied(
                "BS1",
                f"gnomAD AF {variant.gnomad_af:.6g} >= default BS1 {DEFAULT_BS1_AF}",
            )
        )
    else:
        calls.append(
            _declined(
                "BS1",
                f"gnomAD AF {variant.gnomad_af:.6g} outside [{DEFAULT_BS1_AF}, {DEFAULT_BA1_AF})",
            )
        )

    if variant.gnomad_af == 0.0 or variant.gnomad_af < DEFAULT_PM2_AF:
        calls.append(
            _applied(
                "PM2",
                f"gnomAD AF {variant.gnomad_af:.6g} < default PM2 {DEFAULT_PM2_AF} (2015 moderate)",
            )
        )
    else:
        calls.append(
            _declined(
                "PM2",
                f"gnomAD AF {variant.gnomad_af:.6g} >= default PM2 {DEFAULT_PM2_AF}",
            )
        )

    if variant.consequence in NULL_CONSEQUENCES and variant.lof_mechanism_established:
        extra = " last-exon not downgraded under default rules" if variant.last_exon else ""
        calls.append(_applied("PVS1", f"{variant.consequence} in LOF gene.{extra}"))
    else:
        calls.append(
            _declined(
                "PVS1",
                f"consequence={variant.consequence} lof={variant.lof_mechanism_established}",
            )
        )

    if variant.consequence in {"inframe_indel", "stop_lost"}:
        calls.append(_applied("PM4", f"length-changing consequence {variant.consequence}"))
    else:
        calls.append(_declined("PM4", f"consequence {variant.consequence} is not a length change"))

    if variant.revel is not None and variant.revel >= DEFAULT_PP3_REVEL:
        calls.append(_applied("PP3", f"REVEL {variant.revel:.3f} >= {DEFAULT_PP3_REVEL}"))
    else:
        shown = "None" if variant.revel is None else f"{variant.revel:.3f}"
        calls.append(_declined("PP3", f"REVEL {shown} below default PP3 {DEFAULT_PP3_REVEL}"))

    if variant.revel is not None and variant.revel <= DEFAULT_BP4_REVEL:
        calls.append(_applied("BP4", f"REVEL {variant.revel:.3f} <= {DEFAULT_BP4_REVEL}"))
    else:
        shown = "None" if variant.revel is None else f"{variant.revel:.3f}"
        calls.append(_declined("BP4", f"REVEL {shown} above default BP4 {DEFAULT_BP4_REVEL}"))

    splice = variant.spliceai_max
    if variant.consequence == "synonymous" and splice is not None and splice < DEFAULT_BP7_SPLICEAI:
        calls.append(
            _applied("BP7", f"synonymous and SpliceAI {splice:.3f} < {DEFAULT_BP7_SPLICEAI}")
        )
    else:
        calls.append(
            _declined(
                "BP7",
                f"consequence={variant.consequence} spliceai={splice}",
            )
        )

    predicted = {c.code for c in calls}
    missing = [code for code in RULES_CODES if code not in predicted]
    if missing:  # pragma: no cover - defensive, RULES_CODES is closed
        raise RuntimeError(f"default rules missed codes: {missing}")
    return calls


def applied_codes(calls: list[EvidenceCall]) -> list[str]:
    return [c.code for c in calls if c.applied]
